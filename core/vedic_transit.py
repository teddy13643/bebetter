"""印度占星流年預測模組

提供 Nakshatra 分析、Vimshottari Dasha 大限、Gochar 行運、Sade Sati 偵測。
輸入出生資料 + 目標年份，回傳結構化 dict 供 API / MCP tool 使用。
"""

from datetime import datetime, timedelta

from core.vedic_pyjhora_adapter import transit_subject, tz_offset_hours

from core.vedic_constants import (
    NAKSHATRAS, DASHA_ORDER, DASHA_YEARS, SIDEREAL_YEAR_DAYS,
    SIGNS, PLANET_NAMES_ZH, SIGN_NAMES_ZH,
    GOCHAR_RULES, EXALTATION, DEBILITATION, OWN_SIGNS,
)

# 每個 Nakshatra 跨度
_NAKSHATRA_SPAN = 360.0 / 27  # 13.3333°
_PADA_SPAN = _NAKSHATRA_SPAN / 4  # 3.3333°


def calc_nakshatra(moon_abs_pos: float) -> dict:
    """從月亮恆星黃道絕對經度算出 Nakshatra。

    回傳 nakshatra 名稱、中文名、pada（1-4）、lord、度數。
    """
    idx = int(moon_abs_pos / _NAKSHATRA_SPAN) % 27
    degree_in_nak = moon_abs_pos % _NAKSHATRA_SPAN
    pada = int(degree_in_nak / _PADA_SPAN) + 1
    # pada 最大為 4（邊界值 13.333° 歸入下一個 nakshatra）
    if pada > 4:
        pada = 4

    name, name_zh, lord = NAKSHATRAS[idx]
    return {
        "名稱": name,
        "中文": name_zh,
        "pada": pada,
        "lord": lord,
        "lord_zh": PLANET_NAMES_ZH.get(lord, lord),
        "度數": round(degree_in_nak, 2),
        "絕對經度": round(moon_abs_pos, 2),
    }


def _calc_antardashas(maha_lord: str, maha_start: datetime,
                      maha_end: datetime) -> list[dict]:
    """計算單一 Mahadasha 內的 Antardasha 子期間。

    Antardasha 順序從 Mahadasha lord 自己開始，按 DASHA_ORDER 走。
    每個 Antardasha 天數 = Mahadasha 總天數 × (Antardasha lord 年數 / 120)
    """
    maha_days = (maha_end - maha_start).total_seconds() / 86400
    lord_idx = DASHA_ORDER.index(maha_lord)

    antardashas = []
    cursor = maha_start

    for i in range(len(DASHA_ORDER)):
        idx = (lord_idx + i) % len(DASHA_ORDER)
        antar_lord = DASHA_ORDER[idx]
        antar_days = maha_days * DASHA_YEARS[antar_lord] / 120
        end = cursor + timedelta(days=antar_days)

        antardashas.append({
            "lord": antar_lord,
            "lord_zh": PLANET_NAMES_ZH.get(antar_lord, antar_lord),
            "起": cursor.strftime("%Y-%m-%d"),
            "迄": end.strftime("%Y-%m-%d"),
        })
        cursor = end

    return antardashas


def _find_current_dasha(dasha_data: dict, target_dt: datetime) -> dict:
    """找出目標日期所在的 Mahadasha + Antardasha。"""
    target_str = target_dt.strftime("%Y-%m-%d")

    for maha in dasha_data["mahadashas"]:
        if maha["起"] <= target_str <= maha["迄"]:
            current_antar = None
            for antar in maha["antardashas"]:
                if antar["起"] <= target_str <= antar["迄"]:
                    current_antar = antar
                    break

            return {
                "mahadasha": {
                    "lord": maha["lord"],
                    "lord_zh": maha["lord_zh"],
                    "起": maha["起"],
                    "迄": maha["迄"],
                },
                "antardasha": current_antar,
            }

    return {"mahadasha": None, "antardasha": None}


def _sign_distance(from_sign: str, to_sign: str) -> int:
    """計算從 from_sign 到 to_sign 的宮位距離（1-12）。

    同星座 = 1（第一宮），下一個星座 = 2，以此類推。
    """
    from_idx = SIGNS.index(from_sign)
    to_idx = SIGNS.index(to_sign)
    return (to_idx - from_idx) % 12 + 1


def _planet_dignity(planet: str, sign: str) -> str:
    """判斷行星在該星座的力量狀態。"""
    if EXALTATION.get(planet) == sign:
        return "高揚"
    if DEBILITATION.get(planet) == sign:
        return "落陷"
    if sign in OWN_SIGNS.get(planet, []):
        return "廟旺"
    return "一般"


def calc_gochar(natal_moon_sign: str, transit_date: datetime,
                lat: float, lng: float, tz_str: str = "Asia/Taipei") -> dict:
    """計算 Gochar（行運）：行運行星從月亮星座起算的宮位和吉凶。"""
    ts = transit_subject(
        transit_date.year, transit_date.month, transit_date.day, 12, 0,
        lat, lng, tz_offset_hours(tz_str, transit_date.year,
                                  transit_date.month, transit_date.day),
    )

    # 取行運行星位置
    planet_attrs = [
        ("sun", "Sun"), ("moon", "Moon"), ("mercury", "Mercury"),
        ("venus", "Venus"), ("mars", "Mars"), ("jupiter", "Jupiter"),
        ("saturn", "Saturn"),
    ]

    gochar = {}
    for attr, name in planet_attrs:
        p = getattr(ts, attr)
        house_from_moon = _sign_distance(natal_moon_sign, p.sign)
        is_good = GOCHAR_RULES.get(name, {}).get(house_from_moon, False)

        gochar[name] = {
            "行星": PLANET_NAMES_ZH.get(name, name),
            "星座": p.sign,
            "星座_zh": SIGN_NAMES_ZH.get(p.sign, p.sign),
            "從月亮起算宮位": house_from_moon,
            "吉凶": "吉" if is_good else "凶",
            "逆行": p.retrograde,
        }

    # Rahu / Ketu
    rahu = ts.true_north_lunar_node
    if rahu:
        rahu_house = _sign_distance(natal_moon_sign, rahu.sign)
        gochar["Rahu"] = {
            "行星": "羅睺",
            "星座": rahu.sign,
            "星座_zh": SIGN_NAMES_ZH.get(rahu.sign, rahu.sign),
            "從月亮起算宮位": rahu_house,
            "吉凶": "吉" if GOCHAR_RULES.get("Rahu", {}).get(rahu_house, False) else "凶",
            "逆行": rahu.retrograde,
        }
    ketu = ts.true_south_lunar_node
    if ketu:
        ketu_house = _sign_distance(natal_moon_sign, ketu.sign)
        gochar["Ketu"] = {
            "行星": "計都",
            "星座": ketu.sign,
            "星座_zh": SIGN_NAMES_ZH.get(ketu.sign, ketu.sign),
            "從月亮起算宮位": ketu_house,
            "吉凶": "吉" if GOCHAR_RULES.get("Ketu", {}).get(ketu_house, False) else "凶",
            "逆行": ketu.retrograde,
        }

    return gochar


def calc_daily_transit(natal_moon_sign: str, natal_asc_sign: str,
                       transit_date: datetime,
                       lat: float, lng: float,
                       tz_str: str = "Asia/Taipei") -> dict:
    """計算流日：當天 9 行星的星座 / 度數 / 從本命月亮+上升起算的宮位 / 吉凶 / 逆行 / dignity。

    跟 calc_gochar 差別：多帶「從上升宮位」（影響哪個生活面向）、度數、dignity。
    給 sub-agent 推當天具體事件用。
    """
    ts = transit_subject(
        transit_date.year, transit_date.month, transit_date.day, 12, 0,
        lat, lng, tz_offset_hours(tz_str, transit_date.year,
                                  transit_date.month, transit_date.day),
    )

    planet_attrs = [
        ("sun", "Sun"), ("moon", "Moon"), ("mercury", "Mercury"),
        ("venus", "Venus"), ("mars", "Mars"), ("jupiter", "Jupiter"),
        ("saturn", "Saturn"),
    ]

    planets = {}
    for attr, name in planet_attrs:
        p = getattr(ts, attr)
        h_moon = _sign_distance(natal_moon_sign, p.sign)
        h_asc = _sign_distance(natal_asc_sign, p.sign)
        planets[name] = {
            "行星": PLANET_NAMES_ZH.get(name, name),
            "星座": p.sign,
            "星座_zh": SIGN_NAMES_ZH.get(p.sign, p.sign),
            "度數": round(p.position, 2),
            "從月亮宮位": h_moon,
            "從上升宮位": h_asc,
            "吉凶": "吉" if GOCHAR_RULES.get(name, {}).get(h_moon, False) else "凶",
            "逆行": p.retrograde,
            "dignity": _planet_dignity(name, p.sign),
            "nakshatra": calc_nakshatra(p.abs_pos),
        }

    rahu = ts.true_north_lunar_node
    if rahu:
        h_moon = _sign_distance(natal_moon_sign, rahu.sign)
        h_asc = _sign_distance(natal_asc_sign, rahu.sign)
        planets["Rahu"] = {
            "行星": "羅睺",
            "星座": rahu.sign,
            "星座_zh": SIGN_NAMES_ZH.get(rahu.sign, rahu.sign),
            "度數": round(rahu.position, 2),
            "從月亮宮位": h_moon,
            "從上升宮位": h_asc,
            "吉凶": "吉" if GOCHAR_RULES.get("Rahu", {}).get(h_moon, False) else "凶",
            "逆行": rahu.retrograde,
            "dignity": _planet_dignity("Rahu", rahu.sign),
            "nakshatra": calc_nakshatra(rahu.abs_pos),
        }
    ketu = ts.true_south_lunar_node
    if ketu:
        h_moon = _sign_distance(natal_moon_sign, ketu.sign)
        h_asc = _sign_distance(natal_asc_sign, ketu.sign)
        planets["Ketu"] = {
            "行星": "計都",
            "星座": ketu.sign,
            "星座_zh": SIGN_NAMES_ZH.get(ketu.sign, ketu.sign),
            "度數": round(ketu.position, 2),
            "從月亮宮位": h_moon,
            "從上升宮位": h_asc,
            "吉凶": "吉" if GOCHAR_RULES.get("Ketu", {}).get(h_moon, False) else "凶",
            "逆行": ketu.retrograde,
            "dignity": _planet_dignity("Ketu", ketu.sign),
            "nakshatra": calc_nakshatra(ketu.abs_pos),
        }

    return {
        "日期": transit_date.strftime("%Y-%m-%d"),
        "行星": planets,
    }


def calc_monthly_gochar(natal_moon_sign: str, natal_asc_sign: str, year: int,
                         lat: float, lng: float,
                         tz_str: str = "Asia/Taipei") -> list[dict]:
    """每月 1 號的 Gochar 緊湊版（給 sub-agent 推「幾月」用）。

    每個行星附「從月亮宮位」（Gochar 吉凶判斷）+「從上升宮位」（落本命第幾宮判斷感情/事業/...）。
    """
    monthly = []
    for month in range(1, 13):
        s = transit_subject(
            year, month, 1, 12, 0, lat, lng,
            tz_offset_hours(tz_str, year, month, 1),
        )
        planets_now = {}
        attrs = [
            ("sun", "Sun"), ("moon", "Moon"), ("mercury", "Mercury"),
            ("venus", "Venus"), ("mars", "Mars"), ("jupiter", "Jupiter"),
            ("saturn", "Saturn"),
        ]
        for attr, name in attrs:
            p = getattr(s, attr)
            house_from_moon = _sign_distance(natal_moon_sign, p.sign)
            house_from_asc = _sign_distance(natal_asc_sign, p.sign)
            planets_now[name] = {
                "星座": p.sign,
                "從月亮宮位": house_from_moon,
                "從上升宮位": house_from_asc,
                "吉凶": "吉" if GOCHAR_RULES.get(name, {}).get(house_from_moon, False) else "凶",
            }
        for attr, name in [("true_north_lunar_node", "Rahu"),
                            ("true_south_lunar_node", "Ketu")]:
            p = getattr(s, attr, None)
            if p:
                house_from_moon = _sign_distance(natal_moon_sign, p.sign)
                house_from_asc = _sign_distance(natal_asc_sign, p.sign)
                planets_now[name] = {
                    "星座": p.sign,
                    "從月亮宮位": house_from_moon,
                    "從上升宮位": house_from_asc,
                    "吉凶": "吉" if GOCHAR_RULES.get(name, {}).get(house_from_moon, False) else "凶",
                }
        monthly.append({"月": month, "行星": planets_now})
    return monthly


def _slow_planet_attrs():
    """慢行星 attribute 對照（影響領域轉換的關鍵：木/土/羅睺/計都）。"""
    return [
        ("jupiter", "Jupiter"),
        ("saturn", "Saturn"),
        ("true_north_lunar_node", "Rahu"),
        ("true_south_lunar_node", "Ketu"),
    ]


def _planet_sign_at(attr: str, dt: datetime, lat: float, lng: float,
                    tz_str: str) -> str:
    s = transit_subject(
        dt.year, dt.month, dt.day, 12, 0, lat, lng,
        tz_offset_hours(tz_str, dt.year, dt.month, dt.day),
    )
    return getattr(s, attr).sign


def _binary_search_change(attr: str, start: datetime, end: datetime,
                          from_sign: str, to_sign: str,
                          lat: float, lng: float, tz_str: str) -> datetime:
    """在 [start, end] 內找出 sign 從 from_sign 變 to_sign 的第一天。"""
    while (end - start).days > 1:
        mid = start + (end - start) / 2
        if _planet_sign_at(attr, mid, lat, lng, tz_str) == from_sign:
            start = mid
        else:
            end = mid
    return end


def calc_planet_sign_changes(target_year: int, forecast_years: int,
                             lat: float, lng: float,
                             tz_str: str = "Asia/Taipei") -> list[dict]:
    """偵測慢行星（木/土/Rahu/Ketu）在預測區間內的換座日期。

    sub-agent 用這個資料判斷「機會領域 / 壓力領域」何時轉換。
    每月 1 號掃 snapshot，偵測到月際換座再 binary search 精確到日。
    """
    events = []
    for y in range(target_year, target_year + forecast_years):
        # 月初 snapshot（多取一個次年 1 月當邊界）
        snapshots = []
        for m in range(1, 14):
            yy = y if m <= 12 else y + 1
            mm = m if m <= 12 else 1
            dt = datetime(yy, mm, 1)
            snap = {"date": dt, "signs": {}}
            for attr, name in _slow_planet_attrs():
                snap["signs"][name] = _planet_sign_at(attr, dt, lat, lng, tz_str)
            snapshots.append(snap)

        # 偵測月際換座 → binary search 精確到日
        for i in range(1, len(snapshots)):
            prev, curr = snapshots[i - 1], snapshots[i]
            for attr, name in _slow_planet_attrs():
                if prev["signs"][name] != curr["signs"][name]:
                    exact = _binary_search_change(
                        attr, prev["date"], curr["date"],
                        prev["signs"][name], curr["signs"][name],
                        lat, lng, tz_str,
                    )
                    if exact.year == y:
                        events.append({
                            "行星": name,
                            "行星_zh": PLANET_NAMES_ZH.get(name, name),
                            "日期": exact.strftime("%Y-%m-%d"),
                            "從": prev["signs"][name],
                            "從_zh": SIGN_NAMES_ZH.get(prev["signs"][name], prev["signs"][name]),
                            "到": curr["signs"][name],
                            "到_zh": SIGN_NAMES_ZH.get(curr["signs"][name], curr["signs"][name]),
                        })
    events.sort(key=lambda e: e["日期"])
    return events


def calc_sade_sati(natal_moon_sign: str, target_year: int,
                   lat: float, lng: float, tz_str: str = "Asia/Taipei") -> dict:
    """偵測 Sade Sati（土星過月亮前後共 7.5 年的考驗期）。

    檢查目標年份的每個月初土星位置，判斷是否在月亮的 12/1/2 宮。
    """
    moon_idx = SIGNS.index(natal_moon_sign)
    # Sade Sati 的三個階段
    sade_sati_signs = {
        (moon_idx - 1) % 12: "上升期（12 宮）",
        moon_idx: "高峰期（1 宮）",
        (moon_idx + 1) % 12: "下降期（2 宮）",
    }

    # 取每月 1 日土星位置
    phases = []
    for month in range(1, 13):
        s = transit_subject(
            target_year, month, 1, 12, 0, lat, lng,
            tz_offset_hours(tz_str, target_year, month, 1),
        )
        saturn_sign_idx = SIGNS.index(s.saturn.sign)
        phase = sade_sati_signs.get(saturn_sign_idx)
        phases.append({
            "月份": month,
            "土星星座": s.saturn.sign,
            "土星星座_zh": SIGN_NAMES_ZH.get(s.saturn.sign, s.saturn.sign),
            "階段": phase,
        })

    active_phases = [p for p in phases if p["階段"] is not None]
    is_active = len(active_phases) > 0

    result = {
        "是否在 Sade Sati": is_active,
        "月亮星座": natal_moon_sign,
        "月亮星座_zh": SIGN_NAMES_ZH.get(natal_moon_sign, natal_moon_sign),
    }

    if is_active:
        result["階段"] = active_phases[0]["階段"]
        result["土星星座"] = active_phases[0]["土星星座"]
        result["土星星座_zh"] = active_phases[0]["土星星座_zh"]
        result["影響月份"] = [p["月份"] for p in active_phases]

    return result


def _compute_natal_bundle(
    year: int, month: int, day: int, hour: int, minute: int,
    lat: float, lng: float, tz_str: str,
) -> dict:
    """計算本命盤 + nakshatra + dasha + chara_dasha（確定性資料，可永久快取）。"""
    from core.divination import run_vedic_astro
    from core.vedic_chara_dasha import calc_chara_dasha
    from core.vedic_pyjhora_adapter import vimsottari_from_birth

    natal_full = run_vedic_astro(year, month, day, hour, minute, lat, lng, tz_str)
    natal_planets = natal_full["行星"]
    moon_abs_pos = natal_planets["Moon"]["絕對經度"]

    nakshatra = calc_nakshatra(moon_abs_pos)

    birth_dt = datetime(year, month, day, hour, minute)
    tz_off = tz_offset_hours(tz_str, year, month, day)
    dasha_data = vimsottari_from_birth(
        year, month, day, hour, minute, lat, lng, tz_off
    )

    asc_sign = natal_full["宮位"]["第1宮"]["星座"]
    planet_signs = {name: data["星座"] for name, data in natal_planets.items()}
    chara_data = calc_chara_dasha(planet_signs, asc_sign, birth_dt)

    return {
        "natal_full": natal_full,
        "nakshatra": nakshatra,
        "dasha_data": dasha_data,
        "chara_data": chara_data,
        "moon_abs_pos": moon_abs_pos,
        "natal_moon_sign": natal_planets["Moon"]["星座"],
        "asc_sign": asc_sign,
    }


def _compute_transit_bundle(
    natal_moon_sign: str, asc_sign: str, dasha_data: dict,
    target_year: int, forecast_years: int,
    lat: float, lng: float, tz_str: str,
) -> dict:
    """計算流年行運資料（同一人+同一年的結果確定，可年度快取）。"""
    yearly = []
    for y in range(target_year, target_year + forecast_years):
        mid_year = datetime(y, 7, 1)
        gochar = calc_gochar(natal_moon_sign, mid_year, lat, lng, tz_str)

        year_start = datetime(y, 1, 1)
        year_end = datetime(y, 12, 31)
        current_start = _find_current_dasha(dasha_data, year_start)
        current_end = _find_current_dasha(dasha_data, year_end)

        sade_sati = calc_sade_sati(natal_moon_sign, y, lat, lng, tz_str)

        monthly_gochar = calc_monthly_gochar(
            natal_moon_sign, asc_sign, y, lat, lng, tz_str,
        )

        yearly.append({
            "年份": y,
            "dasha_年初": current_start,
            "dasha_年末": current_end,
            "gochar": gochar,
            "monthly_gochar": monthly_gochar,
            "sade_sati": sade_sati,
        })

    sign_changes = calc_planet_sign_changes(
        target_year, forecast_years, lat, lng, tz_str,
    )

    return {"yearly": yearly, "sign_changes": sign_changes}


def run_vedic_transit(
    year: int, month: int, day: int, hour: int, minute: int,
    lat: float, lng: float, tz_str: str = "Asia/Taipei",
    target_year: int = None, forecast_years: int = 1,
    profile_key: str | None = None,
    target_date: str | None = None,
) -> dict:
    """印度占星流年分析主入口。

    兩種模式（同一個入口）：
      1. 流年模式（預設）：依 target_year + forecast_years 算逐年行運。
      2. 流日模式：給 target_date='YYYY-MM-DD' 就只算當天行運，跳過 yearly /
         sign_changes / sade_sati。給的日期那天的 dasha「目前」也跟著對齊。

    兩層快取（流年模式才走 L2，流日不快取因為計算只 ~50ms）：
      L1（永久）：本命盤 + 17 張分盤 + nakshatra + dasha + chara_dasha — 同一人永不變
      L2（年度）：逐年行運 + 行星換座事件 — 同一人 + 同一年不變

    profile_key 給了會出現在快取檔名（main_a1b2c3.json），純 hash 是後備。
    """
    import logging
    import time
    from core.cache import (
        natal_cache_key, transit_cache_key,
        get_natal, set_natal, get_transit, set_transit,
    )
    from core.vedic_chara_dasha import find_current_chara_dasha

    logger = logging.getLogger(__name__)

    # 解析 target_date — 流日模式
    daily_dt: datetime | None = None
    if target_date:
        try:
            daily_dt = datetime.strptime(target_date, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"target_date 格式須為 YYYY-MM-DD: {target_date}") from e

    if target_year is None:
        target_year = daily_dt.year if daily_dt else datetime.now().year

    t0 = time.monotonic()

    # ── L1：本命盤（永久快取，兩種模式都用）──
    nk = natal_cache_key(year, month, day, hour, minute, lat, lng)
    natal_bundle = get_natal(nk, profile_key)
    if natal_bundle is None:
        natal_bundle = _compute_natal_bundle(
            year, month, day, hour, minute, lat, lng, tz_str,
        )
        set_natal(nk, natal_bundle, profile_key)

    natal_full = natal_bundle["natal_full"]
    nakshatra = natal_bundle["nakshatra"]
    dasha_data = natal_bundle["dasha_data"]
    chara_data = natal_bundle["chara_data"]
    natal_moon_sign = natal_bundle["natal_moon_sign"]
    asc_sign = natal_bundle["asc_sign"]

    t1 = time.monotonic()

    # ── 流日模式：只算當天，跳過 yearly / sign_changes / sade_sati ──
    if daily_dt is not None:
        daily = calc_daily_transit(
            natal_moon_sign, asc_sign, daily_dt, lat, lng, tz_str,
        )
        current_dasha = _find_current_dasha(dasha_data, daily_dt)
        current_chara = find_current_chara_dasha(chara_data, daily_dt)

        t2 = time.monotonic()
        logger.info(
            "vedic_transit(daily): natal=%.1fms daily=%.1fms total=%.1fms",
            (t1 - t0) * 1000, (t2 - t1) * 1000, (t2 - t0) * 1000,
        )

        return {
            "本命盤": natal_full,
            "nakshatra": nakshatra,
            "dasha": {
                "mahadashas": dasha_data["mahadashas"],
                "目前": current_dasha,
            },
            "chara_dasha": {
                "起算": chara_data["起算"],
                "方向": chara_data["方向"],
                "mahadashas": chara_data["mahadashas"],
                "目前": current_chara,
            },
            "流日": daily,
        }

    # ── 流年模式：L2 快取 + 逐年行運 ──
    tk = transit_cache_key(nk, target_year, forecast_years)
    transit_bundle = get_transit(tk, target_year, profile_key)
    if transit_bundle is None:
        transit_bundle = _compute_transit_bundle(
            natal_moon_sign, asc_sign, dasha_data,
            target_year, forecast_years, lat, lng, tz_str,
        )
        set_transit(tk, target_year, transit_bundle, profile_key)

    yearly = transit_bundle["yearly"]
    sign_changes = transit_bundle["sign_changes"]

    t2 = time.monotonic()

    # ── 即時計算：Dasha「目前」位置（每天不同，不快取）──
    now = datetime.now()
    target_mid = datetime(target_year, 7, 1)
    current_dasha = _find_current_dasha(dasha_data, now)
    target_dasha = _find_current_dasha(dasha_data, target_mid)
    current_chara = find_current_chara_dasha(chara_data, now)
    target_chara = find_current_chara_dasha(chara_data, target_mid)

    logger.info(
        "vedic_transit: natal=%.1fms transit=%.1fms total=%.1fms",
        (t1 - t0) * 1000, (t2 - t1) * 1000, (t2 - t0) * 1000,
    )

    return {
        "本命盤": natal_full,
        "nakshatra": nakshatra,
        "dasha": {
            "mahadashas": dasha_data["mahadashas"],
            "目前": current_dasha,
            "target_year_中": target_dasha,
        },
        "chara_dasha": {
            "起算": chara_data["起算"],
            "方向": chara_data["方向"],
            "mahadashas": chara_data["mahadashas"],
            "目前": current_chara,
            "target_year_中": target_chara,
        },
        "行星換座事件": sign_changes,
        "逐年分析": yearly,
    }
