"""西洋占星流年預測模組

提供太陽回歸盤、外行星行運、次限推運、小限法、逆行衝擊計算。
輸入出生資料 + 目標年份，回傳結構化 dict 供 API / MCP tool 使用。
"""

from datetime import datetime, timedelta

from kerykeion import (
    AstrologicalSubject,
    AstrologicalSubjectFactory,
    ChartDataFactory,
    EphemerisDataFactory,
    PlanetaryReturnFactory,
    TransitsTimeRangeFactory,
)
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS

# 在預設基礎上開啟四大小行星，否則 ceres/pallas/juno/vesta 會是 None
_BEBETTER_ACTIVE_POINTS = DEFAULT_ACTIVE_POINTS + ["Ceres", "Pallas", "Juno", "Vesta"]

# 星座守護星（現代制）
SIGN_RULERS = {
    "Ari": "Mars", "Tau": "Venus", "Gem": "Mercury", "Can": "Moon",
    "Leo": "Sun", "Vir": "Mercury", "Lib": "Venus", "Sco": "Pluto",
    "Sag": "Jupiter", "Cap": "Saturn", "Aqu": "Uranus", "Pis": "Neptune",
}

_PLANET_ATTRS = [
    "sun", "moon", "mercury", "venus", "mars",
    "jupiter", "saturn", "uranus", "neptune", "pluto",
]
_EXTRA_POINT_ATTRS = [
    "true_north_lunar_node", "true_south_lunar_node",
    "mean_lilith",
    "chiron", "ceres", "pallas", "juno", "vesta",
]
_HOUSE_ORDINALS = [
    "first", "second", "third", "fourth", "fifth", "sixth",
    "seventh", "eighth", "ninth", "tenth", "eleventh", "twelfth",
]

# 外行星行運用的相位和容許度（比本命盤寬鬆一些）
_TRANSIT_ASPECTS = [
    {"name": "conjunction", "orb": 8},
    {"name": "opposition", "orb": 8},
    {"name": "square", "orb": 6},
    {"name": "trine", "orb": 6},
    {"name": "sextile", "orb": 4},
]

# 行運側只看外行星
_OUTER_PLANETS = {"Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"}

# 本命側看所有行星 + 四軸 + 小行星/月交點/莉莉絲
_NATAL_POINTS = [
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
    "Ascendant", "Medium_Coeli",
    "True_North_Lunar_Node", "True_South_Lunar_Node",
    "Mean_Lilith",
    "Chiron", "Ceres", "Pallas", "Juno", "Vesta",
]

# TransitsTimeRangeFactory 的 active_points 控制兩側共用，
# 必須包含所有要偵測的行星（行運側 + 本命側）
_ALL_ACTIVE_POINTS = list(set(_NATAL_POINTS) | _OUTER_PLANETS)


def _format_planet(d: dict) -> dict:
    return {
        "星座": d["sign"],
        "度數": round(d["position"], 2),
        "宮位": d.get("house", ""),
        "逆行": d.get("retrograde", False),
    }


def _format_house(d: dict) -> dict:
    return {
        "星座": d["sign"],
        "度數": round(d["position"], 2),
    }


def _extract_natal(model_dump: dict) -> dict:
    """從 model_dump 提取行星 + 宮位，對齊 _run_astro() 格式"""
    planets = {}
    for attr in _PLANET_ATTRS:
        p = model_dump[attr]
        planets[p["name"]] = _format_planet(p)

    extra_points = {}
    for attr in _EXTRA_POINT_ATTRS:
        p = model_dump.get(attr)
        if p is not None:
            extra_points[p["name"]] = _format_planet(p)

    houses = {}
    for i, ordinal in enumerate(_HOUSE_ORDINALS):
        h = model_dump[f"{ordinal}_house"]
        houses[f"第{i + 1}宮"] = _format_house(h)

    return {"行星": planets, "其他星體": extra_points, "宮位": houses}


def _house_cusps_abs(model_dump: dict) -> list[float]:
    """取出 12 宮頭的絕對度數，用於判斷行運行星落入哪一宮"""
    cusps = []
    for ordinal in _HOUSE_ORDINALS:
        h = model_dump[f"{ordinal}_house"]
        cusps.append(h["abs_pos"])
    return cusps


def _determine_house(abs_pos: float, cusps: list[float]) -> int:
    """根據絕對度數和宮頭列表，判斷落入第幾宮（1-12）"""
    for i in range(12):
        next_i = (i + 1) % 12
        start = cusps[i]
        end = cusps[next_i]
        if start < end:
            if start <= abs_pos < end:
                return i + 1
        else:
            # 跨 0° 的情況
            if abs_pos >= start or abs_pos < end:
                return i + 1
    return 1


def _rate_significance(transit_planet: str, natal_planet: str,
                       aspect: str, min_orb: float) -> int:
    """評估行運重要性（1-10 分）"""
    planet_weight = {"Pluto": 5, "Neptune": 4, "Uranus": 4, "Saturn": 3, "Jupiter": 2}
    natal_weight = {
        "Sun": 3, "Moon": 3, "Ascendant": 2, "Medium_Coeli": 2,
        "Mercury": 1, "Venus": 1, "Mars": 1,
        "Jupiter": 1, "Saturn": 1,
        "Uranus": 0, "Neptune": 0, "Pluto": 0,
    }
    aspect_weight = {
        "conjunction": 2, "opposition": 2, "square": 2,
        "trine": 1, "sextile": 1,
    }

    score = (
        planet_weight.get(transit_planet, 1)
        + natal_weight.get(natal_planet, 0)
        + aspect_weight.get(aspect, 0)
    )
    # 容許度越小越精確，加分
    if min_orb < 1.0:
        score += 1

    return min(score, 10)


def _calc_solar_return(natal_model, target_year: int,
                       lat: float, lng: float, tz_str: str) -> dict:
    """計算太陽回歸盤 + 回歸盤與本命的相位"""
    factory = PlanetaryReturnFactory(
        natal_model, lat=lat, lng=lng, tz_str=tz_str, online=False,
    )
    sr = factory.next_return_from_date(target_year, 1, 1, return_type="Solar")
    sr_dump = sr.model_dump()

    # 回歸盤行星和宮位
    sr_natal = _extract_natal(sr_dump)

    # 回歸盤 vs 本命盤的相位（用 synastry 方式）
    sr_aspects = []
    syn_data = ChartDataFactory.create_synastry_chart_data(
        sr, natal_model,
        active_aspects=_TRANSIT_ASPECTS,
        include_house_comparison=False,
        include_relationship_score=False,
    )
    for a in syn_data.model_dump().get("aspects", []):
        orb = round(abs(a["orbit"]), 2)
        # 只保留容許度 < 5° 的相位，過濾噪音
        if orb >= 5.0:
            continue
        sr_aspects.append({
            "回歸行星": a["p1_name"],
            "本命行星": a["p2_name"],
            "相位": a["aspect"],
            "容許度": orb,
            "精確度數": a["aspect_degrees"],
        })

    return {
        "年份": target_year,
        "精確時間": sr_dump.get("iso_formatted_local_datetime", ""),
        "回歸盤行星": sr_natal["行星"],
        "回歸盤宮位": sr_natal["宮位"],
        "回歸盤與本命相位": sr_aspects,
    }


def _calc_outer_transits(natal_model, natal_dump: dict,
                         target_year: int, forecast_years: int,
                         lat: float, lng: float, tz_str: str) -> tuple[list, list]:
    """計算外行星行運 + 逆行衝擊

    回傳 (outer_transits, retrograde_impacts)
    """
    cusps = _house_cusps_abs(natal_dump)

    # 產生整年每週一個 subject
    start = datetime(target_year, 1, 1)
    end = datetime(target_year + forecast_years, 1, 1)
    max_days = (end - start).days + 7
    eph = EphemerisDataFactory(
        start, end, step_type="days", step=7,
        lat=lat, lng=lng, tz_str=tz_str,
        max_days=max_days,
    )
    subjects = eph.get_ephemeris_data_as_astrological_subjects()

    # 行運計算
    transit_factory = TransitsTimeRangeFactory(
        natal_model, subjects,
        active_points=_ALL_ACTIVE_POINTS,
        active_aspects=_TRANSIT_ASPECTS,
    )
    result = transit_factory.get_transit_moments()
    raw = result.model_dump()

    # 去重：連續出現的同組 (行運星, 本命星, 相位) 合併
    # key → list of (date, orb, abs_pos, retrograde, aspect_movement)
    groups = {}
    for moment in raw.get("transits", []):
        date_str = moment["date"][:10]
        for asp in moment["aspects"]:
            # 只取「行運側是外行星 + 本命側是目標行星」的組合
            if asp["p1_owner"] != "Now" or asp["p2_owner"] != "Natal":
                continue
            if asp["p1_name"] not in _OUTER_PLANETS:
                continue
            if asp["p2_name"] not in _NATAL_POINTS:
                continue

            key = (asp["p1_name"], asp["p2_name"], asp["aspect"])
            if key not in groups:
                groups[key] = []
            groups[key].append({
                "date": date_str,
                "orb": abs(asp["orbit"]),
                "abs_pos": asp["p1_abs_pos"],
                "movement": asp.get("aspect_movement", ""),
            })

    # 把每組的連續出現合併成一筆行運
    outer_transits = []
    for (t_planet, n_planet, aspect), entries in groups.items():
        if not entries:
            continue

        # 分段：如果兩個 entry 日期差超過 21 天，視為不同段（逆行造成的分離）
        segments = []
        current_seg = [entries[0]]
        for i in range(1, len(entries)):
            prev_date = datetime.strptime(entries[i - 1]["date"], "%Y-%m-%d")
            curr_date = datetime.strptime(entries[i]["date"], "%Y-%m-%d")
            if (curr_date - prev_date).days > 21:
                segments.append(current_seg)
                current_seg = [entries[i]]
            else:
                current_seg.append(entries[i])
        segments.append(current_seg)

        for seg in segments:
            min_orb_entry = min(seg, key=lambda x: x["orb"])
            significance = _rate_significance(t_planet, n_planet, aspect, min_orb_entry["orb"])

            # 判斷行運行星落入本命哪一宮（用精確日期的位置）
            house = _determine_house(min_orb_entry["abs_pos"], cusps)

            outer_transits.append({
                "行運行星": t_planet,
                "本命行星": n_planet,
                "相位": aspect,
                "重要性": significance,
                "入相日期": seg[0]["date"],
                "精確日期": min_orb_entry["date"],
                "出相日期": seg[-1]["date"],
                "最小容許度": round(min_orb_entry["orb"], 2),
                "行運星座": "",  # 下面補
                "落入本命宮位": house,
            })

    # 補行運星座（從星曆中取精確日期最近的那筆）
    # 建一個日期→行星星座的 lookup
    date_planet_sign = {}
    for moment in raw.get("transits", []):
        d = moment["date"][:10]
        for asp in moment["aspects"]:
            if asp["p1_owner"] == "Now":
                # 從絕對度數推算星座
                sign_idx = int(asp["p1_abs_pos"] / 30)
                signs = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir",
                         "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
                sign = signs[sign_idx % 12]
                date_planet_sign[(d, asp["p1_name"])] = sign

    for t in outer_transits:
        key = (t["精確日期"], t["行運行星"])
        t["行運星座"] = date_planet_sign.get(key, "")

    # 按重要性排序
    outer_transits.sort(key=lambda x: x["重要性"], reverse=True)

    # 逆行衝擊：從星曆中找水金火的逆行區間和觸發的本命相位
    retrograde_impacts = _extract_retrogrades(natal_model, subjects, natal_dump)

    return outer_transits, retrograde_impacts


def _extract_retrogrades(natal_model, subjects: list, natal_dump: dict) -> list:
    """找出水星、金星、火星的逆行區間，以及期間觸發的本命相位"""
    inner_planets = ["Mercury", "Venus", "Mars"]
    inner_attrs = {"Mercury": "mercury", "Venus": "venus", "Mars": "mars"}

    # 從星曆中偵測逆行區間
    # subjects 是 AstrologicalSubjectModel 列表
    retro_periods = {}  # planet → list of (start_date, end_date)
    prev_retro = {}

    for subj in subjects:
        d = subj.model_dump()
        date_str = d.get("iso_formatted_local_datetime", "")[:10]

        for planet in inner_planets:
            attr = inner_attrs[planet]
            p_data = d.get(attr, {})
            is_retro = p_data.get("retrograde", False)

            was_retro = prev_retro.get(planet, False)
            if is_retro and not was_retro:
                # 逆行開始
                if planet not in retro_periods:
                    retro_periods[planet] = []
                retro_periods[planet].append({"start": date_str, "end": date_str})
            elif is_retro and was_retro:
                # 逆行持續
                if planet in retro_periods and retro_periods[planet]:
                    retro_periods[planet][-1]["end"] = date_str
            # 逆行結束不需要特別處理

            prev_retro[planet] = is_retro

    # 對每個逆行期間，用 TransitsTimeRangeFactory 找觸發的本命相位
    results = []
    for planet, periods in retro_periods.items():
        for period in periods:
            # 篩選該期間內的 subjects
            start_dt = datetime.strptime(period["start"], "%Y-%m-%d")
            end_dt = datetime.strptime(period["end"], "%Y-%m-%d")
            period_subjects = [
                s for s in subjects
                if start_dt <= datetime.fromisoformat(
                    s.model_dump()["iso_formatted_local_datetime"][:19]
                ) <= end_dt
            ]
            if not period_subjects:
                continue

            transit_factory = TransitsTimeRangeFactory(
                natal_model, period_subjects,
                active_points=[planet],
                active_aspects=_TRANSIT_ASPECTS,
            )
            transit_result = transit_factory.get_transit_moments()
            raw = transit_result.model_dump()

            # 收集觸發的本命行星
            natal_hits = {}
            for moment in raw.get("transits", []):
                for asp in moment["aspects"]:
                    if asp["p2_owner"] == "Natal" and asp["p2_name"] in _NATAL_POINTS:
                        key = (asp["p2_name"], asp["aspect"])
                        if key not in natal_hits or abs(asp["orbit"]) < natal_hits[key]["容許度"]:
                            natal_hits[key] = {
                                "本命行星": asp["p2_name"],
                                "相位": asp["aspect"],
                                "容許度": round(abs(asp["orbit"]), 2),
                            }

            if natal_hits:
                results.append({
                    "行星": planet,
                    "逆行期間": [period["start"], period["end"]],
                    "觸發本命": list(natal_hits.values()),
                })

    return results


def _calc_progressions(natal_model, natal_dump: dict,
                       birth_year: int, birth_month: int, birth_day: int,
                       target_year: int,
                       lat: float, lng: float, tz_str: str) -> dict:
    """次限推運：出生日 + 年齡天數 = 推運日期"""
    age = target_year - birth_year

    # 推運日期 = 出生日 + age 天
    birth_dt = datetime(birth_year, birth_month, birth_day)
    prog_dt = birth_dt + timedelta(days=age)

    prog_subject = AstrologicalSubject(
        "Progressed", prog_dt.year, prog_dt.month, prog_dt.day,
        5, 30,  # 用出生時間
        lat=lat, lng=lng, tz_str=tz_str, zodiac_type="Tropical",
    )
    prog_model_inner = prog_subject.model()
    prog_dump = prog_model_inner.model_dump()

    # 推運月亮和太陽
    prog_moon = _format_planet(prog_dump["moon"])
    prog_sun = _format_planet(prog_dump["sun"])

    # 推運 vs 本命相位
    syn_data = ChartDataFactory.create_synastry_chart_data(
        prog_model_inner, natal_model,
        active_points=["Sun", "Moon", "Mercury", "Venus", "Mars"],
        active_aspects=[
            {"name": "conjunction", "orb": 2},
            {"name": "opposition", "orb": 2},
            {"name": "square", "orb": 2},
            {"name": "trine", "orb": 2},
            {"name": "sextile", "orb": 1},
        ],
        include_house_comparison=False,
        include_relationship_score=False,
    )
    prog_aspects = []
    for a in syn_data.model_dump().get("aspects", []):
        prog_aspects.append({
            "推運行星": a["p1_name"],
            "本命行星": a["p2_name"],
            "相位": a["aspect"],
            "容許度": round(a["orbit"], 2),
        })

    return {
        "推運日期": prog_dt.strftime("%Y-%m-%d"),
        "推運月亮": prog_moon,
        "推運太陽": prog_sun,
        "推運與本命相位": prog_aspects,
    }


def _calc_profection(natal_dump: dict, birth_year: int, target_year: int) -> dict:
    """小限法：年齡 % 12 → 激活宮位 + 宮主星"""
    age = target_year - birth_year
    # 0歲=第1宮, 1歲=第2宮, ... 12歲=第1宮
    activated_house = (age % 12) + 1

    # 找到該宮的星座
    house_key = f"第{activated_house}宮"
    ordinal = _HOUSE_ORDINALS[activated_house - 1]
    house_data = natal_dump[f"{ordinal}_house"]
    sign = house_data["sign"]

    # 宮主星
    ruler = SIGN_RULERS.get(sign, "")

    # 宮主星在本命盤的位置
    ruler_pos = {}
    if ruler:
        ruler_attr = ruler.lower()
        if ruler_attr in natal_dump:
            ruler_pos = _format_planet(natal_dump[ruler_attr])

    return {
        "年齡": age,
        "激活宮位": activated_house,
        "激活星座": sign,
        "宮主星": ruler,
        "宮主星本命位置": ruler_pos,
    }


def _year_overview(outer_transits: list, natal_dump: dict,
                   target_year: int, forecast_years: int) -> dict:
    """年度總覽：行運統計 + 外行星經過宮位"""
    cusps = _house_cusps_abs(natal_dump)

    high_count = sum(1 for t in outer_transits if t["重要性"] >= 7)

    # 外行星經過宮位（從行運清單中提取）
    planet_houses = {}
    for t in outer_transits:
        planet = t["行運行星"]
        house = t["落入本命宮位"]
        if planet not in planet_houses:
            planet_houses[planet] = set()
        planet_houses[planet].add(house)

    # set → sorted list
    planet_houses = {k: sorted(v) for k, v in planet_houses.items()}

    return {
        "行運數量": len(outer_transits),
        "高重要性數量": high_count,
        "外行星經過宮位": planet_houses,
    }


def run_astro_transit(
    year: int, month: int, day: int, hour: int, minute: int,
    lat: float, lng: float, tz_str: str = "Asia/Taipei",
    target_year: int | None = None,
    forecast_years: int = 1,
) -> dict:
    """西洋占星流年預測

    輸入出生資料 + 目標年份，回傳太陽回歸盤、外行星行運、
    次限推運、小限法、逆行衝擊的結構化資料。
    """
    if target_year is None:
        target_year = datetime.now().year
    forecast_years = min(forecast_years, 3)

    # 本命盤（用 Factory 開啟小行星計算）
    natal_model = AstrologicalSubjectFactory.from_birth_data(
        "Natal", year, month, day, hour, minute,
        lat=lat, lng=lng, tz_str=tz_str, zodiac_type="Tropical",
        online=False, active_points=_BEBETTER_ACTIVE_POINTS,
    )
    natal_dump = natal_model.model_dump()

    # 本命盤摘要
    natal_summary = _extract_natal(natal_dump)

    # 太陽回歸（只算第一年，多年時逐年各算一次）
    solar_returns = []
    for y in range(target_year, target_year + forecast_years):
        sr = _calc_solar_return(natal_model, y, lat, lng, tz_str)
        solar_returns.append(sr)

    # 外行星行運 + 逆行衝擊
    outer_transits, retro_impacts = _calc_outer_transits(
        natal_model, natal_dump, target_year, forecast_years, lat, lng, tz_str,
    )

    # 次限推運
    progressions = _calc_progressions(
        natal_model, natal_dump, year, month, day, target_year, lat, lng, tz_str,
    )

    # 小限法
    profection = _calc_profection(natal_dump, year, target_year)

    # 年度總覽
    overview = _year_overview(outer_transits, natal_dump, target_year, forecast_years)

    result = {
        "本命盤摘要": natal_summary,
        "外行星行運": outer_transits,
        "逆行衝擊": retro_impacts,
        "次限推運": progressions,
        "小限法": profection,
        "年度總覽": overview,
    }

    # 太陽回歸：單年直接放 dict，多年放 list
    if forecast_years == 1:
        result["太陽回歸"] = solar_returns[0]
    else:
        result["太陽回歸"] = solar_returns

    return result
