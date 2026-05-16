"""七政四餘排盤模組

七政：太陽、太陰、太白(金)、歲星(木)、辰星(水)、熒惑(火)、鎮星(土)
四餘：羅睺(北交點)、計都(南交點)、紫氣(月孛對點)、月孛(月遠地點)

用 swisseph 計算天體恆星黃道經度。歲差修正用 Lahiri ayanamsa（角宿距星校準）。
十二宮用整宮制，命宮所在十二次為第一宮。

支援本命盤 (run_qizheng) 與流運盤 (run_qizheng_transit，含大限、小限、流年、流月)。
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import swisseph as swe


# ── 十二次：恆星黃道 30° 等分 → 地支宮位 ──
# 索引對應恆星黃道區段：0=白羊(0°-30°), 1=金牛(30°-60°), ...
_TWELVE_CI = [
    ("降婁", "戌", "土"),   # Aries
    ("大梁", "酉", "金"),   # Taurus
    ("實沈", "申", "金"),   # Gemini
    ("鶉首", "未", "土"),   # Cancer
    ("鶉火", "午", "火"),   # Leo
    ("鶉尾", "巳", "火"),   # Virgo
    ("壽星", "辰", "土"),   # Libra
    ("大火", "卯", "木"),   # Scorpio
    ("析木", "寅", "木"),   # Sagittarius
    ("星紀", "丑", "土"),   # Capricorn
    ("玄枵", "子", "水"),   # Aquarius
    ("娵訾", "亥", "水"),   # Pisces
]

# ── 二十八宿 ──
# 從角宿起（恆星黃經 ≈180°），寬度不等分，七曜循環：木金土日月火水
_SEVEN_LUMINARIES = "木金土日月火水"
_MANSION_ANIMALS = "蛟龍貉兔狐虎豹獬牛蝠鼠燕豬貐狼狗雉雞烏猴猿犴羊獐馬鹿蛇蚓"
_MANSIONS = [
    ("角", 12, "東方青龍"), ("亢", 9, "東方青龍"), ("氐", 15, "東方青龍"),
    ("房", 5, "東方青龍"),  ("心", 7, "東方青龍"), ("尾", 18, "東方青龍"),
    ("箕", 11, "東方青龍"),
    ("斗", 26, "北方玄武"), ("牛", 8, "北方玄武"), ("女", 12, "北方玄武"),
    ("虛", 10, "北方玄武"), ("危", 17, "北方玄武"), ("室", 16, "北方玄武"),
    ("壁", 9, "北方玄武"),
    ("奎", 16, "西方白虎"), ("婁", 12, "西方白虎"), ("胃", 14, "西方白虎"),
    ("昴", 11, "西方白虎"), ("畢", 17, "西方白虎"), ("觜", 1, "西方白虎"),
    ("參", 9, "西方白虎"),
    ("井", 33, "南方朱雀"), ("鬼", 4, "南方朱雀"), ("柳", 15, "南方朱雀"),
    ("星", 7, "南方朱雀"),  ("張", 18, "南方朱雀"), ("翼", 18, "南方朱雀"),
    ("軫", 10, "南方朱雀"),
]
_MANSION_START = 180.0  # 角宿起始恆星黃經（Spica 校準點）

# ── 七政 swisseph 天體 ID ──
_PLANETS = [
    ("太陽", swe.SUN),
    ("太陰", swe.MOON),
    ("辰星", swe.MERCURY),
    ("太白", swe.VENUS),
    ("熒惑", swe.MARS),
    ("歲星", swe.JUPITER),
    ("鎮星", swe.SATURN),
]

# ── 廟旺落陷 ──
# 廟=Domicile, 旺=Exaltation, 落=Detriment, 陷=Fall
_DIGNITY = {
    "太陽": {"廟": {"午"}, "旺": {"戌"}, "落": {"子"}, "陷": {"辰"}},
    "太陰": {"廟": {"未"}, "旺": {"酉"}, "落": {"丑"}, "陷": {"卯"}},
    "辰星": {"廟": {"申", "巳"}, "旺": {"巳"}, "落": {"寅", "亥"}, "陷": {"亥"}},
    "太白": {"廟": {"酉", "辰"}, "旺": {"亥"}, "落": {"卯", "戌"}, "陷": {"巳"}},
    "熒惑": {"廟": {"戌", "卯"}, "旺": {"丑"}, "落": {"辰", "酉"}, "陷": {"未"}},
    "歲星": {"廟": {"寅", "亥"}, "旺": {"未"}, "落": {"申", "巳"}, "陷": {"丑"}},
    "鎮星": {"廟": {"丑", "子"}, "旺": {"辰"}, "落": {"未", "午"}, "陷": {"戌"}},
    "羅睺": {"旺": {"寅"}, "陷": {"申"}},
    "計都": {"旺": {"申"}, "陷": {"寅"}},
}

# ── 十二宮名稱 ──
_HOUSE_NAMES = [
    "命宮", "財帛宮", "兄弟宮", "田宅宮", "男女宮", "奴僕宮",
    "夫妻宮", "疾厄宮", "遷移宮", "官祿宮", "福德宮", "相貌宮",
]

# ── 相位定義 (角度, 容許度, 名稱) ──
_ASPECTS = [
    (0, 10, "合"),
    (60, 6, "六合"),
    (90, 8, "刑"),
    (120, 8, "三合"),
    (180, 10, "沖"),
]

# ── 宮主對應：地支 → 宮主星 ──
# 子丑土、寅亥木、卯戌火、辰酉金、巳申水、午日、未月
_ZHI_TO_RULER = {
    "子": "鎮星", "丑": "鎮星",
    "寅": "歲星", "亥": "歲星",
    "卯": "熒惑", "戌": "熒惑",
    "辰": "太白", "酉": "太白",
    "巳": "辰星", "申": "辰星",
    "午": "太陽",
    "未": "太陰",
}

# ── 大限年限表（果老星宗歌訣，簡化為整數）──
# 童限 0-9 歲，大限 10 歲起，順本命宮位序走完一週天約 102 年
_DAYUN_TABLE = [
    ("命宮", 15),
    ("財帛宮", 5),
    ("兄弟宮", 5),
    ("田宅宮", 5),
    ("男女宮", 5),
    ("奴僕宮", 5),
    ("夫妻宮", 11),
    ("疾厄宮", 7),
    ("遷移宮", 8),
    ("官祿宮", 15),
    ("福德宮", 11),
    ("相貌宮", 10),
]
_DAYUN_START_AGE = 10


# ══════════════════════════════════════
# 工具函式
# ══════════════════════════════════════

def _local_to_jd(year, month, day, hour, minute, tz_str):
    """本地時間 → Julian Day (UT)"""
    local = datetime(year, month, day, hour, minute, tzinfo=ZoneInfo(tz_str))
    utc = local.astimezone(ZoneInfo("UTC"))
    hour_ut = utc.hour + utc.minute / 60.0 + utc.second / 3600.0
    return swe.julday(utc.year, utc.month, utc.day, hour_ut)


def _to_sign(lon):
    """恆星黃經 → (sign_index, degree_in_sign)"""
    lon = lon % 360
    idx = int(lon / 30)
    return idx, lon - idx * 30


def _sign_info(idx):
    """十二次索引 → (次名, 地支, 五行)"""
    return _TWELVE_CI[idx]


def _to_mansion(lon):
    """恆星黃經 → 二十八宿資訊"""
    offset = (lon - _MANSION_START) % 360
    cumulative = 0.0
    for i, (name, width, quadrant) in enumerate(_MANSIONS):
        if cumulative + width > offset:
            yao = _SEVEN_LUMINARIES[i % 7]
            animal = _MANSION_ANIMALS[i]
            return {
                "宿": name,
                "全名": f"{name}{yao}{animal}",
                "度": round(offset - cumulative, 2),
                "象限": quadrant,
            }
        cumulative += width
    # fallback（不會走到）
    return {"宿": "軫", "全名": "軫水蚓", "度": 0, "象限": "南方朱雀"}


def _get_dignity(planet, zhi):
    """查星曜在某地支宮位的廟旺落陷"""
    d = _DIGNITY.get(planet, {})
    # 廟 > 旺 > 陷 > 落（同時符合多項時取最強/最弱）
    if zhi in d.get("廟", set()):
        return "廟"
    if zhi in d.get("旺", set()):
        return "旺"
    if zhi in d.get("陷", set()):
        return "陷"
    if zhi in d.get("落", set()):
        return "落"
    return "平"


def _angle_diff(a, b):
    """兩黃經差的最小角度（0-180）"""
    d = abs(a - b) % 360
    return min(d, 360 - d)


def _calc_aspects(longitudes):
    """計算所有天體間的相位"""
    names = list(longitudes.keys())
    aspects = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            diff = _angle_diff(longitudes[names[i]], longitudes[names[j]])
            for angle, orb, aspect_name in _ASPECTS:
                if abs(diff - angle) <= orb:
                    aspects.append({
                        "星1": names[i],
                        "星2": names[j],
                        "相位": aspect_name,
                        "角度": round(diff, 2),
                        "容許度": round(abs(diff - angle), 2),
                    })
                    break
    return aspects


def _find_configurations(planet_data, longitudes, asc_sign_idx):
    """辨識重要格局"""
    configs = []

    def _sign_idx(name):
        return _to_sign(longitudes[name])[0]

    sun_idx = _sign_idx("太陽")
    moon_idx = _sign_idx("太陰")
    prev_sign = (asc_sign_idx - 1) % 12
    next_sign = (asc_sign_idx + 1) % 12

    # 日月夾命：太陽太陰分別在命宮前後一宮
    if {sun_idx, moon_idx} == {prev_sign, next_sign}:
        configs.append({"格局": "日月夾命", "說明": "太陽太陰夾輔命宮，主貴顯"})

    # 日月同宮
    if sun_idx == moon_idx:
        ci = _sign_info(sun_idx)[0]
        configs.append({"格局": "日月同宮", "說明": f"太陽太陰同在{ci}"})

    # 日月拱命（三合：4 宮距離）
    for name in ("太陽", "太陰"):
        diff = (_sign_idx(name) - asc_sign_idx) % 12
        if diff in (4, 8):
            configs.append({"格局": f"{name}拱命", "說明": f"{name}與命宮三合拱照"})

    # 金水交輝：太白、辰星皆在廟或旺
    if (planet_data["太白"]["廟旺"] in ("廟", "旺")
            and planet_data["辰星"]["廟旺"] in ("廟", "旺")):
        configs.append({"格局": "金水交輝", "說明": "太白辰星皆得廟旺，主聰明俊秀"})

    # 吉星守命
    for name in ("歲星", "太白"):
        if _sign_idx(name) == asc_sign_idx:
            configs.append({"格局": f"{name}守命", "說明": f"{name}入命宮，主吉"})

    # 凶星守命
    for name in ("熒惑", "鎮星"):
        if _sign_idx(name) == asc_sign_idx:
            configs.append({"格局": f"{name}守命", "說明": f"{name}入命宮，需吉星化解"})

    # 羅計夾命
    rahu_idx = _sign_idx("羅睺")
    ketu_idx = _sign_idx("計都")
    if {rahu_idx, ketu_idx} == {prev_sign, next_sign}:
        configs.append({"格局": "羅計夾命", "說明": "羅睺計都夾命宮，主災厄，需吉星解"})

    # 三台拱照：3+ 吉星（日月金木）與命宮三合
    benefics_trine = sum(
        1 for name in ("太陽", "太陰", "太白", "歲星")
        if (_sign_idx(name) - asc_sign_idx) % 12 in (4, 8)
    )
    if benefics_trine >= 3:
        configs.append({"格局": "三台拱照", "說明": "三顆以上吉星拱照命宮，大貴格"})

    # 文星拱命
    for name in ("辰星", "歲星"):
        diff = (_sign_idx(name) - asc_sign_idx) % 12
        if diff in (4, 8):
            configs.append({"格局": "文星拱命", "說明": f"{name}拱照命宮，主學業文才"})

    return configs


# ══════════════════════════════════════
# 主函式
# ══════════════════════════════════════

def run_qizheng(year, month, day, hour, minute, lat, lng, tz_str="Asia/Taipei"):
    """七政四餘排盤

    輸入出生西曆年月日時分 + 出生地經緯度。
    回傳十一曜位置（十二次 + 二十八宿 + 廟旺）、十二宮、相位、格局。
    """
    jd = _local_to_jd(year, month, day, hour, minute, tz_str)

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED

    # ── 七政位置 ──
    longitudes = {}
    planet_data = {}

    for name, body_id in _PLANETS:
        pos = swe.calc_ut(jd, body_id, flags)
        lon = pos[0][0] % 360
        longitudes[name] = lon
        sign_idx, deg_in = _to_sign(lon)
        ci, zhi, element = _sign_info(sign_idx)
        planet_data[name] = {
            "黃經": round(lon, 4),
            "十二次": ci,
            "地支": zhi,
            "宮內度數": round(deg_in, 2),
            "五行": element,
            "二十八宿": _to_mansion(lon),
            "廟旺": _get_dignity(name, zhi),
            "速度": round(pos[0][3], 4),
        }

    # ── 四餘位置 ──
    # 羅睺（Mean North Node）
    rahu_lon = swe.calc_ut(jd, swe.MEAN_NODE, flags)[0][0] % 360
    # 月孛（Mean Apogee）
    yuebo_lon = swe.calc_ut(jd, swe.MEAN_APOG, flags)[0][0] % 360
    # 計都 = 羅睺對點，紫氣 = 月孛對點
    ketu_lon = (rahu_lon + 180) % 360
    ziqi_lon = (yuebo_lon + 180) % 360

    for name, lon in [("羅睺", rahu_lon), ("計都", ketu_lon),
                      ("月孛", yuebo_lon), ("紫氣", ziqi_lon)]:
        longitudes[name] = lon
        sign_idx, deg_in = _to_sign(lon)
        ci, zhi, element = _sign_info(sign_idx)
        planet_data[name] = {
            "黃經": round(lon, 4),
            "十二次": ci,
            "地支": zhi,
            "宮內度數": round(deg_in, 2),
            "五行": element,
            "二十八宿": _to_mansion(lon),
            "廟旺": _get_dignity(name, zhi),
        }

    # ── 命宮（Ascendant）、中天（MC）──
    # 用 Placidus 取 ASC/MC 度數，再手動減歲差轉恆星黃道
    cusps, ascmc = swe.houses(jd, lat, lng, b'P')
    ayan = swe.get_ayanamsa_ut(jd)
    asc_lon = (ascmc[0] - ayan) % 360
    mc_lon = (ascmc[1] - ayan) % 360

    asc_sign_idx, asc_deg = _to_sign(asc_lon)
    asc_ci, asc_zhi, _ = _sign_info(asc_sign_idx)

    ascendant = {
        "黃經": round(asc_lon, 4),
        "十二次": asc_ci,
        "地支": asc_zhi,
        "宮內度數": round(asc_deg, 2),
        "二十八宿": _to_mansion(asc_lon),
    }

    mc_sign_idx, mc_deg = _to_sign(mc_lon)
    mc_ci, mc_zhi, _ = _sign_info(mc_sign_idx)

    # ── 十二宮（整宮制：命宮所在十二次為第一宮）──
    houses = []
    for i in range(12):
        h_sign_idx = (asc_sign_idx + i) % 12
        ci, zhi, element = _sign_info(h_sign_idx)
        # 落在此宮的星曜
        stars = [n for n, d in planet_data.items() if d["地支"] == zhi]
        houses.append({
            "宮": i + 1,
            "宮名": _HOUSE_NAMES[i],
            "十二次": ci,
            "地支": zhi,
            "五行": element,
            "星曜": stars,
        })

    # 回填宮位名到星曜資料
    zhi_to_house = {h["地支"]: h["宮名"] for h in houses}
    for pdata in planet_data.values():
        pdata["所在宮位"] = zhi_to_house.get(pdata["地支"], "")

    # ── 相位 ──
    aspects = _calc_aspects(longitudes)

    # ── 格局 ──
    configurations = _find_configurations(planet_data, longitudes, asc_sign_idx)

    # ── 三主（命主 / 身主 / 度主）──
    three_masters = _compute_three_masters(ascendant, planet_data)

    return {
        "系統": "七政四餘",
        "出生資料": {
            "西曆": f"{year}/{month}/{day} {hour:02d}:{minute:02d}",
            "時區": tz_str,
            "經度": lng,
            "緯度": lat,
        },
        "命宮": ascendant,
        "中天": {
            "黃經": round(mc_lon, 4),
            "十二次": mc_ci,
            "地支": mc_zhi,
        },
        "三主": three_masters,
        "星曜": planet_data,
        "十二宮": houses,
        "相位": aspects,
        "格局": configurations,
    }


# ══════════════════════════════════════
# 三主推算
# ══════════════════════════════════════

# 七曜禽中間字 → 星曜名
_YAO_TO_STAR = {
    "日": "太陽", "月": "太陰",
    "木": "歲星", "火": "熒惑",
    "土": "鎮星", "金": "太白",
    "水": "辰星",
}


def _compute_three_masters(ascendant, planet_data):
    """推算命主、身主、度主

    命主 = 命宮地支對應的宮主星
    身主 = 太陰所在地支的宮主星（月為身）
    度主 = 命宮所在二十八宿的七曜禽中間字對應的星曜
    """
    # 命主
    life_ruler_name = _ZHI_TO_RULER.get(ascendant["地支"])

    # 身主（太陰所躔之宮的宮主）
    moon_zhi = planet_data["太陰"]["地支"]
    body_ruler_name = _ZHI_TO_RULER.get(moon_zhi)

    # 度主（從命宮宿名中間字取七曜）
    mansion_full = ascendant["二十八宿"]["全名"]  # e.g. "氐土貉"
    yao_char = mansion_full[1] if len(mansion_full) >= 2 else ""
    degree_ruler_name = _YAO_TO_STAR.get(yao_char)

    def _build(label, star_name):
        if not star_name or star_name not in planet_data:
            return {"主": label, "星曜": star_name or "未知"}
        pdata = planet_data[star_name]
        dignity = pdata["廟旺"]
        strength = "強" if dignity in ("廟", "旺") else ("弱" if dignity in ("落", "陷") else "中")
        return {
            "主": label,
            "星曜": star_name,
            "所在宮位": pdata.get("所在宮位", ""),
            "地支": pdata["地支"],
            "廟旺": dignity,
            "強弱": strength,
        }

    return {
        "命主": _build("命主", life_ruler_name),
        "身主": _build("身主", body_ruler_name),
        "度主": _build("度主", degree_ruler_name),
    }


# ══════════════════════════════════════
# 流運：大限、小限、流年、流月
# ══════════════════════════════════════

def _compute_dayun(natal, age):
    """大限推算

    童限 0-9，大限從命宮起，依十二宮順序各管不同年數。
    回傳當前大限宮 + 完整時間軸。
    """
    house_stars = {h["宮名"]: h["星曜"] for h in natal["十二宮"]}
    house_zhi = {h["宮名"]: h["地支"] for h in natal["十二宮"]}

    if age < _DAYUN_START_AGE:
        return {
            "階段": "童限",
            "年齡區間": f"0-{_DAYUN_START_AGE - 1}",
            "說明": "大限未起，以本命底色論",
            "當前年齡": round(age, 1),
        }

    cumulative = _DAYUN_START_AGE
    timeline = []
    current = None

    for house_name, years in _DAYUN_TABLE:
        start = cumulative
        end = cumulative + years
        zhi = house_zhi.get(house_name, "")
        ruler_star = _ZHI_TO_RULER.get(zhi, "")
        seg = {
            "宮名": house_name,
            "地支": zhi,
            "宮主": ruler_star,
            "年齡區間": f"{start}-{end - 1}",
            "起迄年數": years,
            "宮內星曜": house_stars.get(house_name, []),
        }
        # 補上宮主的本命廟旺與落宮
        if ruler_star and ruler_star in natal["星曜"]:
            rdata = natal["星曜"][ruler_star]
            seg["宮主廟旺"] = rdata["廟旺"]
            seg["宮主落於"] = rdata.get("所在宮位", "")
        if start <= age < end:
            current = dict(seg, 狀態="當前")
        timeline.append(seg)
        cumulative = end

    return {
        "階段": "大限",
        "當前年齡": round(age, 1),
        "當前大限": current,
        "時間軸": timeline,
    }


def _compute_xiaoxian(natal, age):
    """小限推算：每宮一年，從命宮起順本命宮位序，12 年一循環"""
    age_int = int(age)
    idx = age_int % 12
    h = natal["十二宮"][idx]
    return {
        "年齡": age_int,
        "宮名": h["宮名"],
        "地支": h["地支"],
        "宮主": _ZHI_TO_RULER.get(h["地支"], ""),
        "宮內本命星曜": h["星曜"],
    }


def _compute_transit_planets(jd, natal):
    """計算某時刻十一曜位置 + 落入本命何宮 + 廟旺 + 激活本命星曜"""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED

    longitudes = {}
    for name, body_id in _PLANETS:
        pos = swe.calc_ut(jd, body_id, flags)
        longitudes[name] = pos[0][0] % 360

    rahu_lon = swe.calc_ut(jd, swe.MEAN_NODE, flags)[0][0] % 360
    yuebo_lon = swe.calc_ut(jd, swe.MEAN_APOG, flags)[0][0] % 360
    longitudes["羅睺"] = rahu_lon
    longitudes["計都"] = (rahu_lon + 180) % 360
    longitudes["月孛"] = yuebo_lon
    longitudes["紫氣"] = (yuebo_lon + 180) % 360

    zhi_to_house = {h["地支"]: h["宮名"] for h in natal["十二宮"]}
    zhi_to_stars = {h["地支"]: h["星曜"] for h in natal["十二宮"]}

    planets = {}
    for name, lon in longitudes.items():
        sign_idx, deg_in = _to_sign(lon)
        ci, zhi, element = _sign_info(sign_idx)
        planets[name] = {
            "黃經": round(lon, 4),
            "十二次": ci,
            "地支": zhi,
            "宮內度數": round(deg_in, 2),
            "廟旺": _get_dignity(name, zhi),
            "落入本命宮": zhi_to_house.get(zhi, ""),
            "激活本命星曜": zhi_to_stars.get(zhi, []),
        }

    return planets, longitudes


def _compute_cross_aspects(transit_lons, natal):
    """流運星 vs 本命星/命宮 相位（容許度取本命的一半以收緊）"""
    natal_lons = {n: d["黃經"] for n, d in natal["星曜"].items()}
    natal_lons["命宮"] = natal["命宮"]["黃經"]

    results = []
    for t_name, t_lon in transit_lons.items():
        for n_name, n_lon in natal_lons.items():
            diff = _angle_diff(t_lon, n_lon)
            for angle, orb, aspect_name in _ASPECTS:
                tight_orb = orb / 2
                if abs(diff - angle) <= tight_orb:
                    results.append({
                        "流運星": t_name,
                        "本命點": n_name,
                        "相位": aspect_name,
                        "角度": round(diff, 2),
                        "容許度": round(abs(diff - angle), 2),
                    })
                    break
    # 容許度越小優先
    results.sort(key=lambda r: r["容許度"])
    return results


def _compute_taisui_zhi(target_year):
    """流年太歲地支：年地支 = (year - 4) % 12 對應子丑寅卯..."""
    zhi_order = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    return zhi_order[(target_year - 4) % 12]


def run_qizheng_transit(year, month, day, hour, minute, lat, lng,
                         target_year, target_month=None,
                         tz_str="Asia/Taipei"):
    """七政四餘流運盤：大限 + 小限 + 流年 + 流月（月選填）

    輸入本命資料 + 目標年（月選填）。
    回傳當前大限、小限宮、流年流運、流月流運（如有指定月份）、
    以及流運星 vs 本命盤的相位。
    """
    natal = run_qizheng(year, month, day, hour, minute, lat, lng, tz_str)

    # 當前年齡（以目標時間的中點估算）
    birth_d = date(year, month, day)
    if target_month:
        target_d = date(target_year, target_month, 15)
    else:
        target_d = date(target_year, 7, 1)
    age = (target_d - birth_d).days / 365.25

    # 大限 + 小限
    dayun = _compute_dayun(natal, age)
    xiaoxian = _compute_xiaoxian(natal, age)

    # 太歲地支（給參考）
    taisui_zhi = _compute_taisui_zhi(target_year)
    taisui_house = next(
        (h["宮名"] for h in natal["十二宮"] if h["地支"] == taisui_zhi),
        "",
    )

    # 流年：以目標年 7/1 00:00 作為代表時刻計算流運
    jd_year = _local_to_jd(target_year, 7, 1, 0, 0, tz_str)
    liunian_planets, liunian_lons = _compute_transit_planets(jd_year, natal)
    liunian_aspects = _compute_cross_aspects(liunian_lons, natal)

    liunian = {
        "目標年份": target_year,
        "代表時刻": f"{target_year}/7/1 00:00",
        "太歲地支": taisui_zhi,
        "太歲入本命宮": taisui_house,
        "流運星曜": liunian_planets,
        "流運-本命相位": liunian_aspects,
    }

    # 流月（選填）
    liuyue = None
    if target_month:
        jd_month = _local_to_jd(target_year, target_month, 15, 0, 0, tz_str)
        lm_planets, lm_lons = _compute_transit_planets(jd_month, natal)
        lm_aspects = _compute_cross_aspects(lm_lons, natal)
        liuyue = {
            "目標月份": f"{target_year}/{target_month}",
            "代表時刻": f"{target_year}/{target_month}/15 00:00",
            "流運星曜": lm_planets,
            "流運-本命相位": lm_aspects,
        }

    return {
        "系統": "七政四餘流運",
        "本命摘要": {
            "命宮": natal["命宮"],
            "三主": natal["三主"],
            "本命格局": natal["格局"],
        },
        "目標時間": {
            "年": target_year,
            "月": target_month,
            "當前年齡": round(age, 1),
        },
        "大限": dayun,
        "小限": xiaoxian,
        "流年": liunian,
        "流月": liuyue,
    }
