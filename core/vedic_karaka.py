"""Char Karaka（七顆指示星）+ Karakamsa Devatas（三神）

Parashara 系統：取 7 顆主行星（不含 Rahu/Ketu），
依「在所在星座內的度數」由高到低排序，分配 7 個角色。
最高度數 = Atmakaraka（靈魂指示星）。

度數越高 = 該星越「成熟」，承擔的人生角色越深。

Karakamsa Devatas（Jaimini）：
從 Karakamsa Lagna（AK 在 D-9 落的星座）算 12/9/6 宮，
該宮主管行星對應的神祇 = Ishta / Dharma / Pala Devata。
"""

from core.vedic_constants import SIGNS, SIGN_NAMES_ZH, SIGN_LORDS, PLANET_NAMES_ZH

# 7 個 Char Karaka 角色（從度數最高到最低）
KARAKA_ROLES = [
    ("AK",  "Atmakaraka",   "靈魂指示星", "這輩子的靈魂主軸、核心功課"),
    ("AmK", "Amatyakaraka", "事業指示星", "事業方向、心智發展、人生顧問"),
    ("BK",  "Bhratrukaraka","兄弟指示星", "兄弟、勇氣、努力與行動力"),
    ("MK",  "Matrukaraka",  "母親指示星", "母親、家庭、情感安定"),
    ("PK",  "Putrakaraka",  "子女指示星", "子女、智力、創造力"),
    ("GK",  "Gnatikaraka",  "親族指示星", "親族、健康、慢性問題"),
    ("DK",  "Darakaraka",   "配偶指示星", "配偶特質、婚姻緣分"),
]

# 用於 Char Karaka 的 7 顆行星（Parashara 系統，不含 Rahu/Ketu）
KARAKA_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]


def calc_char_karakas(planets: dict) -> dict:
    """從本命行星 dict 算 Char Karakas。

    輸入：{"Sun": {"星座": "Cap", "度數": 28.5, ...}, ...}
    回傳：{
        "Atmakaraka": {"行星": "Sun", "度數": 28.5, "星座": "Cap", "意義": "..."},
        "排序": [
            {"角色": "AK", "名稱": "Atmakaraka", "中文": "...", "行星": "Sun",
             "度數": 28.5, "星座": "Cap", "意義": "..."},
            ...
        ],
    }
    """
    pool = []
    for name in KARAKA_PLANETS:
        p = planets.get(name)
        if p is None:
            continue
        pool.append({
            "行星": name,
            "度數": p["度數"],
            "星座": p["星座"],
        })

    # 度數高到低排
    pool.sort(key=lambda x: x["度數"], reverse=True)

    sorted_karakas = []
    for i, planet in enumerate(pool):
        if i >= len(KARAKA_ROLES):
            break
        code, name, zh, meaning = KARAKA_ROLES[i]
        sorted_karakas.append({
            "角色": code,
            "名稱": name,
            "中文": zh,
            "行星": planet["行星"],
            "度數": planet["度數"],
            "星座": planet["星座"],
            "意義": meaning,
        })

    atmakaraka = sorted_karakas[0] if sorted_karakas else None
    result = {"排序": sorted_karakas}
    if atmakaraka:
        result["Atmakaraka"] = {
            "行星": atmakaraka["行星"],
            "度數": atmakaraka["度數"],
            "星座": atmakaraka["星座"],
            "意義": atmakaraka["意義"],
        }
    return result


# Karakamsa Devatas（Jaimini 三神）
# Sanjay Rath / PJC 主流派的行星 → 神祇對照
PLANET_DEITIES = {
    "Sun":     ["Shiva 濕婆", "Rama 羅摩", "Surya 太陽神"],
    "Moon":    ["Krishna 黑天", "Parvati 雪山神女"],
    "Mars":    ["Hanuman 哈奴曼", "Subramanya 室建陀", "Narasimha 人獅"],
    "Mercury": ["Vishnu 毗濕奴", "Buddha 佛陀"],
    "Jupiter": ["Vamana 侏儒", "Brahma 梵天", "Sri Vidya 智慧女神"],
    "Venus":   ["Lakshmi 吉祥天女", "Parashurama 持斧羅摩"],
    "Saturn":  ["Kurma 龜化身", "Hanuman 哈奴曼", "Shani 沙尼"],
    "Rahu":    ["Durga 杜爾迦", "Varaha 野豬化身"],
    "Ketu":    ["Ganesha 象神", "Matsya 魚化身"],
}

# 共主管星座（傳統主管 + 現代節點主管）
# 用於 Devata 計算時兩個都列，讓使用者選擇
DUAL_LORDS = {
    "Sco": ["Mars", "Ketu"],
    "Aqu": ["Saturn", "Rahu"],
}


def _sign_lords(sign: str) -> list:
    """回傳星座的主管行星（天蠍/水瓶會回兩顆）"""
    if sign in DUAL_LORDS:
        return DUAL_LORDS[sign]
    return [SIGN_LORDS[sign]]


def _devata_block(role: str, role_zh: str, sign: str, lords: list, meaning: str) -> dict:
    """組一個 Devata 區塊"""
    deities = []
    for lord in lords:
        deities.append({
            "主管行星": lord,
            "主管行星_zh": PLANET_NAMES_ZH.get(lord, lord),
            "對應神祇": PLANET_DEITIES.get(lord, []),
        })
    return {
        "角色": role,
        "中文": role_zh,
        "宮位星座": sign,
        "宮位星座_zh": SIGN_NAMES_ZH.get(sign, sign),
        "宮位意義": meaning,
        "選擇": deities,
    }


def compute_devatas(d9_planets: dict, ak_planet: str) -> dict | None:
    """從 D-9 盤 + AK 行星算 Karakamsa Trinity Devatas。

    輸入：
      d9_planets: D-9 盤的行星 dict {"Sun": {"星座": "Sag", ...}, ...}
      ak_planet:  Atmakaraka 行星名（如 "Sun"）

    回傳：{
        "Karakamsa_Lagna": {星座, 中文, 說明},
        "Ishta_Devata":    KK 12 宮主對應神祇（核心修行 / 此生解脫之路）,
        "Dharma_Devata":   KK 9 宮主對應神祇（生命使命 / 法性方向）,
        "Pala_Devata":     KK 6 宮主對應神祇（守護神 / 對抗業力的力量）,
    }

    AK / D-9 盤資料缺失時回 None。
    """
    if not ak_planet or not d9_planets:
        return None
    ak_d9 = d9_planets.get(ak_planet)
    if not ak_d9 or "星座" not in ak_d9:
        return None

    kl_sign = ak_d9["星座"]
    if kl_sign not in SIGNS:
        return None
    kl_idx = SIGNS.index(kl_sign)

    sign_12 = SIGNS[(kl_idx + 11) % 12]  # KK 12 → Ishta
    sign_9  = SIGNS[(kl_idx + 8) % 12]   # KK 9  → Dharma
    sign_6  = SIGNS[(kl_idx + 5) % 12]   # KK 6  → Pala

    return {
        "Karakamsa_Lagna": {
            "AK": ak_planet,
            "AK_zh": PLANET_NAMES_ZH.get(ak_planet, ak_planet),
            "星座": kl_sign,
            "星座_zh": SIGN_NAMES_ZH.get(kl_sign, kl_sign),
            "說明": "AK 在 D-9 落的星座 = 靈魂在分盤層級的真實落腳點",
        },
        "Ishta_Devata":  _devata_block(
            "Ishta", "本尊神 / 靈性核心修行對象",
            sign_12, _sign_lords(sign_12),
            "KK 12 宮 = 解脫宮，主管此生靈性最高目標、修行方向、與神契合的途徑",
        ),
        "Dharma_Devata": _devata_block(
            "Dharma", "法性神 / 生命使命指引",
            sign_9, _sign_lords(sign_9),
            "KK 9 宮 = 法性宮，主管此生使命、信念、值得追隨的智慧傳承",
        ),
        "Pala_Devata":   _devata_block(
            "Pala", "守護神 / 對抗業力的力量",
            sign_6, _sign_lords(sign_6),
            "KK 6 宮 = 障礙宮，主管化解業力、克服敵手與疾病的守護力量",
        ),
    }
