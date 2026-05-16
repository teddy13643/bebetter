"""Shadbala — 印度占星行星六種力量

來源：Brihat Parashara Hora Shastra, Phaladeepika。
單位：Virupa（V），1 Rupa = 60 V。

六項：
1. Sthana Bala  位置力量（5 子項合計）
2. Dik Bala     方位力量
3. Kala Bala    時間力量（簡化：Natonnata + Paksha）
4. Cheshta Bala 動態力量
5. Naisargika   自然力量（查表）
6. Drig Bala    相位力量

註：完整 BPHS 公式涉及多個分項與星曆精算（Yuddha、Tribhaga、Hora 等），
此處為**簡化版**保留主要骨架與比較有意義的子項，與最低需求量（Required Bala）
比對來判定行星強弱，足以支撐人生諮詢層級的判讀。
"""

from core.vedic_constants import (
    SIGNS, SIGN_LORDS, EXALTATION, DEBILITATION, OWN_SIGNS,
    NAISARGIKA_BALA, DIK_BALA_STRONG_HOUSE, EXALTATION_DEGREE,
    NAISARGIKA_MAITRI,
)

SHADBALA_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# 宮位 string 與 int 的雙向相容
_HOUSE_NAME_TO_INT = {
    "First_House": 1,  "Second_House": 2,  "Third_House": 3,    "Fourth_House": 4,
    "Fifth_House": 5,  "Sixth_House": 6,   "Seventh_House": 7,  "Eighth_House": 8,
    "Ninth_House": 9,  "Tenth_House": 10,  "Eleventh_House": 11, "Twelfth_House": 12,
}


def _house_int(h) -> int:
    """容受 'First_House' / 1 / '1' 三種輸入"""
    if isinstance(h, int):
        return h
    if isinstance(h, str):
        if h in _HOUSE_NAME_TO_INT:
            return _HOUSE_NAME_TO_INT[h]
        try:
            return int(h)
        except ValueError:
            return 1
    return 1

# 最低需求力量（單位 V，BPHS 標準）— 行星總力 < 此值 = 弱
SHADBALA_REQUIRED = {
    "Sun":     390,  # 6.5 Rupa
    "Moon":    360,  # 6.0
    "Mars":    300,  # 5.0
    "Mercury": 420,  # 7.0
    "Jupiter": 390,  # 6.5
    "Venus":   330,  # 5.5
    "Saturn":  300,  # 5.0
}

# 行星陰陽屬性（Ojayugma 計算用）
PLANET_GENDER = {
    "Sun": "male", "Mars": "male", "Jupiter": "male",
    "Moon": "female", "Venus": "female",
    "Mercury": "neutral", "Saturn": "neutral",
}

# 星座陰陽（odd index = male, even = female；Aries=0=male）
def _is_male_sign(sign_idx: int) -> bool:
    return sign_idx % 2 == 0


def _sign_idx(sign: str) -> int:
    try:
        return SIGNS.index(sign[:3])
    except ValueError:
        return 0


# ===== 1. Sthana Bala =====

def _uchcha_bala(planet: str, abs_long: float) -> float:
    """高揚力量：距高揚點越近越強，距落陷點 = 0

    距高揚點 0° = 60V，距 180° = 0V，線性
    """
    if planet not in EXALTATION_DEGREE:
        return 0.0
    sign_idx, deg = EXALTATION_DEGREE[planet]
    exalt_long = sign_idx * 30 + deg
    dist = abs(abs_long - exalt_long) % 360
    if dist > 180:
        dist = 360 - dist
    return round((180 - dist) / 180 * 60, 2)


def _saptavargaja_bala(planet: str, sign: str) -> float:
    """簡化版：只看 D1 dignity（完整版要看 7 張分盤合計）

    廟旺 60、自宮 45、Mooltrikona 45、好友 30、中性 15、敵星 7、落陷 2
    """
    if sign == EXALTATION.get(planet):
        return 45.0
    if sign == DEBILITATION.get(planet):
        return 2.0
    if sign in OWN_SIGNS.get(planet, []):
        return 30.0
    sign_lord = SIGN_LORDS.get(sign)
    if not sign_lord or planet not in NAISARGIKA_MAITRI:
        return 15.0
    rel = NAISARGIKA_MAITRI[planet]
    if sign_lord in rel.get("friends", []):
        return 22.5
    if sign_lord in rel.get("enemies", []):
        return 7.5
    return 15.0


def _ojayugma_bala(planet: str, sign_idx: int) -> float:
    """陰陽匹配：男行星在男星座 / 女行星在女星座 = 15V，不匹配 = 0V"""
    gender = PLANET_GENDER.get(planet)
    is_male = _is_male_sign(sign_idx)
    if gender == "male" and is_male:
        return 15.0
    if gender == "female" and not is_male:
        return 15.0
    if gender == "neutral":
        return 7.5  # 中性行星折半
    return 0.0


def _kendradi_bala(house: int) -> float:
    """宮位類型：角宮 60、續宮 30、果宮 15"""
    if house in (1, 4, 7, 10):
        return 60.0
    if house in (2, 5, 8, 11):
        return 30.0
    return 15.0  # 3, 6, 9, 12


def _drekkana_bala(planet: str, deg_in_sign: float) -> float:
    """三分盤陰陽：男行星在前 1/3、中性在中 1/3、女行星在後 1/3 = 15V"""
    gender = PLANET_GENDER.get(planet)
    if deg_in_sign < 10:
        section = "male"
    elif deg_in_sign < 20:
        section = "neutral"
    else:
        section = "female"
    return 15.0 if gender == section else 0.0


def _calc_sthana(planet: str, planet_data: dict) -> dict:
    sign = planet_data["星座"][:3]
    sign_idx = _sign_idx(sign)
    abs_long = planet_data.get("絕對經度", sign_idx * 30 + planet_data.get("度數", 15))
    deg_in_sign = planet_data.get("度數", abs_long - sign_idx * 30)
    house = _house_int(planet_data.get("宮位", 1))

    items = {
        "Uchcha":         _uchcha_bala(planet, abs_long),
        "Saptavargaja":   _saptavargaja_bala(planet, sign),
        "Ojayugma":       _ojayugma_bala(planet, sign_idx),
        "Kendradi":       _kendradi_bala(house),
        "Drekkana":       _drekkana_bala(planet, deg_in_sign),
    }
    items["Total"] = round(sum(items.values()), 2)
    return items


# ===== 2. Dik Bala =====

def _calc_dik(planet: str, house: int) -> float:
    """方位力量：在最強角宮 60V，對宮 0V，距離線性內插"""
    strong = DIK_BALA_STRONG_HOUSE.get(planet)
    if not strong:
        return 0.0
    # 行星距強角宮 N 個宮位，距離 0 = 滿，距離 6 = 0
    diff = abs(house - strong)
    if diff > 6:
        diff = 12 - diff
    return round((6 - diff) / 6 * 60, 2)


# ===== 3. Kala Bala（簡化：Natonnata + Paksha）=====

def _calc_natonnata(planet: str, sun_house: int) -> float:
    """日夜分力量：日生 Sun/Jup/Ven 強，夜生 Moon/Mars/Sat 強，水星永遠 30V"""
    # 太陽在 7-12 宮 = 出生時陽光在地平線之上 = 日生
    diurnal = sun_house >= 7
    if planet == "Mercury":
        return 30.0
    diurnal_planets = {"Sun", "Jupiter", "Venus"}
    nocturnal_planets = {"Moon", "Mars", "Saturn"}
    if planet in diurnal_planets:
        return 60.0 if diurnal else 0.0
    if planet in nocturnal_planets:
        return 0.0 if diurnal else 60.0
    return 0.0


def _calc_paksha(planet: str, sun_long: float, moon_long: float) -> float:
    """月相力量：
    waxing（新月→滿月）: 吉星 + waxing 比例強
    waning: 凶星強
    """
    # Sun-Moon 角距，0-360
    dist = (moon_long - sun_long) % 360
    # 0-180 = waxing, 180-360 = waning（反向計算 waxing %）
    if dist <= 180:
        waxing_pct = dist / 180  # 0 (新月) → 1 (滿月)
    else:
        waxing_pct = (360 - dist) / 180  # 滿月 → 新月

    benefics = {"Moon", "Jupiter", "Venus", "Mercury"}
    malefics = {"Sun", "Mars", "Saturn"}

    if planet in benefics:
        bala = waxing_pct * 60
    elif planet in malefics:
        bala = (1 - waxing_pct) * 60
    else:
        bala = 30.0

    # 月亮 Paksha 加倍（這是 Cheshta 用，Kala 內保持原值）
    return round(bala, 2)


def _calc_kala(planet: str, sun_house: int, sun_long: float, moon_long: float) -> dict:
    items = {
        "Natonnata": _calc_natonnata(planet, sun_house),
        "Paksha":    _calc_paksha(planet, sun_long, moon_long),
    }
    items["Total"] = round(sum(v for k, v in items.items() if k != "Total"), 2)
    return items


# ===== 4. Cheshta Bala =====

def _calc_cheshta(planet: str, retrograde: bool, sun_house: int,
                  sun_long: float, moon_long: float) -> float:
    """動態力量（簡化版）

    Sun = Ayana Bala（用 Natonnata 替代，方向相同）
    Moon = Paksha × 2
    其他：逆行 60V，順行 30V，留位中等
    """
    if planet == "Sun":
        return _calc_natonnata("Sun", sun_house)
    if planet == "Moon":
        return round(_calc_paksha("Moon", sun_long, moon_long) * 2, 2)
    if retrograde:
        return 60.0
    return 30.0  # 順行折中值


# ===== 5. Naisargika =====（查表，已在 constants）

# ===== 6. Drig Bala =====

# Vedic 特殊望宮（除全行星望第 7 宮之外）
SPECIAL_ASPECTS = {
    "Mars": [4, 8],
    "Jupiter": [5, 9],
    "Saturn": [3, 10],
}


def _aspect_strength(aspecting_planet: str, target_house: int, aspecting_house: int) -> float:
    """簡化：望中目標宮 = ±15V（吉望 +、凶望 -）

    7 宮對望（所有行星）+ 火/木/土 各自的特殊望
    """
    diff = (target_house - aspecting_house) % 12
    if diff == 0:
        diff = 12
    aspect_houses = {7}
    aspect_houses.update(SPECIAL_ASPECTS.get(aspecting_planet, []))
    if diff not in aspect_houses:
        return 0.0
    benefics = {"Jupiter", "Venus", "Mercury", "Moon"}
    malefics = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
    if aspecting_planet in benefics:
        return 15.0
    if aspecting_planet in malefics:
        return -15.0
    return 0.0


def _calc_drig(planet: str, planet_house: int, all_planets: dict) -> float:
    """所有其他行星望此行星的合計"""
    total = 0.0
    for other, data in all_planets.items():
        if other == planet:
            continue
        if other not in SHADBALA_PLANETS and other not in ("Rahu", "Ketu"):
            continue
        other_house = _house_int(data.get("宮位", 1))
        total += _aspect_strength(other, planet_house, other_house)
    return round(total, 2)


# ===== 主流程 =====

def calc_shadbala(planets: dict, ascendant_sign: str = None) -> dict:
    """印度占星行星六種力量總計

    Args:
        planets: 行星字典（含 Sun, Moon, Mars, Mer, Jup, Ven, Sat），需有「星座」「絕對經度」「宮位」「逆行」
        ascendant_sign: 上升星座（目前 sthana 不直接用，預留擴充）

    Returns:
        {
            "Sun": {六項分數 + Total + Required + Strength_Ratio + 強弱},
            ...
            "排名": [強→弱],
            "說明": "..."
        }
    """
    sun_data = planets.get("Sun", {})
    moon_data = planets.get("Moon", {})
    sun_house = _house_int(sun_data.get("宮位", 1))
    sun_long = sun_data.get("絕對經度", 0)
    moon_long = moon_data.get("絕對經度", 0)

    result = {}
    for planet in SHADBALA_PLANETS:
        if planet not in planets:
            continue
        pdata = planets[planet]
        retrograde = bool(pdata.get("逆行", False))

        sthana = _calc_sthana(planet, pdata)
        dik = _calc_dik(planet, _house_int(pdata.get("宮位", 1)))
        kala = _calc_kala(planet, sun_house, sun_long, moon_long)
        cheshta = _calc_cheshta(planet, retrograde, sun_house, sun_long, moon_long)
        naisargika = NAISARGIKA_BALA[planet]
        drig = _calc_drig(planet, _house_int(pdata.get("宮位", 1)), planets)

        total = sthana["Total"] + dik + kala["Total"] + cheshta + naisargika + drig
        required = SHADBALA_REQUIRED[planet]
        ratio = round(total / required, 2)
        if ratio >= 1.5:
            strength = "極強"
        elif ratio >= 1.2:
            strength = "強"
        elif ratio >= 1.0:
            strength = "達標"
        elif ratio >= 0.8:
            strength = "略弱"
        else:
            strength = "弱"

        result[planet] = {
            "Sthana_位置力": sthana,
            "Dik_方位力":    dik,
            "Kala_時間力":   kala,
            "Cheshta_動態力": cheshta,
            "Naisargika_自然力": naisargika,
            "Drig_相位力":   drig,
            "總分_V":        round(total, 2),
            "總分_Rupa":     round(total / 60, 2),
            "需求_V":        required,
            "達成率":        ratio,
            "強弱":          strength,
        }

    ranked = sorted(
        result.items(),
        key=lambda kv: kv[1]["達成率"],
        reverse=True,
    )
    result["_排名"] = [{"行星": p, "達成率": d["達成率"], "強弱": d["強弱"]} for p, d in ranked]
    result["_說明"] = (
        "Shadbala 六種力量單位 Virupa（V），1 Rupa = 60 V。"
        "達成率 ≥ 1.0 = 該行星有最低力量發揮主題；< 0.8 = 該行星主題（自然 karaka 主題）力不從心。"
        "本實作為簡化版（Sthana 5 子項 + Dik + Kala 簡化兩項 + Cheshta + Naisargika 查表 + Drig 望相位）。"
    )
    return result
