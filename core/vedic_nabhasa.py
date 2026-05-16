"""Nabhasa Yogas — 印度占星「天空形態」組合

依 7 行星（不含 Rahu/Ketu）在星座 / 宮位的整體分布形成的特殊組合。
分四類：

1. Ashraya 依託類 (3)：7 行星全在某類星座（活動 / 固定 / 變動）
2. Dala    行列類 (2)：吉星 / 凶星全在角宮
3. Akriti  形態類 (20)：行星佔據宮位形成幾何圖案
4. Sankhya 數量類 (7)：7 行星佔了幾個不同的星座

來源：Brihat Parashara Hora Shastra, Phaladeepika。
全部表驅動，新增 yoga 只要加一筆資料。
"""

# 星座活動性分組（Ashraya 依據）
MOVABLE_SIGNS = {"Ari", "Can", "Lib", "Cap"}    # Chara 活動宮
FIXED_SIGNS   = {"Tau", "Leo", "Sco", "Aqu"}    # Sthira 固定宮
DUAL_SIGNS    = {"Gem", "Vir", "Sag", "Pis"}    # Dwiswabhava 變動宮

NABHASA_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
BENEFIC_NABHASA = {"Jupiter", "Venus", "Mercury", "Moon"}
MALEFIC_NABHASA = {"Sun", "Mars", "Saturn"}

# 宮位 string 與 int 的雙向相容
_HOUSE_NAME_TO_INT = {
    "First_House": 1,  "Second_House": 2,  "Third_House": 3,    "Fourth_House": 4,
    "Fifth_House": 5,  "Sixth_House": 6,   "Seventh_House": 7,  "Eighth_House": 8,
    "Ninth_House": 9,  "Tenth_House": 10,  "Eleventh_House": 11, "Twelfth_House": 12,
}


def _house_int(h):
    if isinstance(h, int):
        return h
    if isinstance(h, str):
        if h in _HOUSE_NAME_TO_INT:
            return _HOUSE_NAME_TO_INT[h]
        try:
            return int(h)
        except ValueError:
            return None
    return None

# ===== Ashraya 依託類 =====
# (name, zh, sign_set, meaning)
ASHRAYA_YOGAS = [
    ("Rajju",  "繩索", MOVABLE_SIGNS, "好遊歷、頻搬遷、外國緣深；定不下來"),
    ("Musala", "杵",   FIXED_SIGNS,   "穩定富足、毅力強、堅持原則；變通慢"),
    ("Nala",   "蘆葦", DUAL_SIGNS,    "聰穎機巧、雙軌人生、適應力強；缺乏專注"),
]

# ===== Dala 行列類 =====
# 吉星 / 凶星全部落在角宮（1, 4, 7, 10）
KENDRAS = {1, 4, 7, 10}

DALA_YOGAS = [
    ("Mala",  "花環", "benefic_in_kendra", "享樂、貴人、富足、宴飲不斷的好命"),
    ("Sarpa", "蛇",   "malefic_in_kendra", "業力重、艱辛轉化、易被誤解；越苦越成長"),
]

# ===== Sankhya 數量類 =====
# 7 行星總共佔了幾個不同的 sign → 對應 yoga
SANKHYA_YOGAS = {
    7: ("Vallaki",  "魯特琴", "藝術天賦、享樂家、平衡感強；傾向享樂主義"),
    6: ("Damaru",   "雙鼓",   "聲名傳播、忙碌奔波；重感官刺激"),
    5: ("Pushpa",   "花朵",   "創造、繁華、社交圈廣；情慾強"),
    4: ("Kedara",   "田地",   "富足穩定、勤勞耕耘、子孫有福"),
    3: ("Soola",    "矛",     "好戰、競爭心強、軍人或運動員性格"),
    2: ("Yuga",     "枷",     "孤獨、貧困、思想極端；修行者"),
    1: ("Gola",     "球",     "極端命格，全集中一處；非大成即大敗"),
}

# ===== Akriti 形態類 =====
# 描述方式：
#   "houses": 列舉若干 set，行星集合 == 某個 set 即成立
#   "consecutive_7": 行星佔據 7 個連續宮位（任意起點）
#   "vajra"/"yava": benefic/malefic 分布於 1,7,4,10 的特殊組合
AKRITI_YOGAS = [
    # 集中型
    ("Gada",         "杖",       "houses_any_of", [{1, 2, 3, 4}, {7, 8, 9, 10}],
                                  "勞碌得財，集中力量在連續四宮"),
    ("Shakata",      "車",       "houses_only_in", {1, 7},
                                  "生計奔波、運勢起落、易負債"),
    ("Pakshi",       "鳥",       "houses_only_in", {4, 10},
                                  "頻繁遷移、旅行多、職涯與家兩頭跑"),
    ("Shringataka",  "雙錐",     "houses_only_in", {1, 5, 9},
                                  "榮耀、福澤深厚、得長輩或上師加持"),
    ("Hala",         "犁",       "houses_any_of", [{2, 6, 10}, {3, 7, 11}, {4, 8, 12}],
                                  "勤勉、體力勞動、農業或工匠"),
    ("Vajra",        "金剛",     "vajra", None,
                                  "青年期強健富足，老年衰退；先盛後衰"),
    ("Yava",         "大麥",     "yava", None,
                                  "青年期辛苦，中老年富足；先苦後甘"),
    ("Kamala",       "蓮花",     "houses_only_in", {1, 4, 7, 10},
                                  "全四角宮 — 名譽、地位、富足兼備的王者格"),
    ("Vapi",         "池",       "houses_any_of", [{2, 5, 8, 11}, {3, 6, 9, 12}],
                                  "積累緩慢但穩定，老年享福"),
    ("Yupa",         "祭柱",     "houses_only_in", {1, 2, 3, 4},
                                  "宗教 / 儀式 / 家庭事務纏身；重傳統"),
    ("Shara",        "箭",       "houses_only_in", {4, 5, 6, 7},
                                  "獄卒 / 武器 / 軍人；可能傷害他人"),
    ("Shakti",       "能量",     "houses_only_in", {7, 8, 9, 10},
                                  "晚發命，前期貧困、後期得勢"),
    ("Danda",        "杖（孤立）", "houses_only_in", {10, 11, 12, 1},
                                  "孤立、晚輩緣薄、可能孤兒命"),
    ("Naukha",       "船",       "consecutive_in_range", (1, 7),
                                  "1-7 宮連續 7 宮 — 富裕、海事、跨國事業"),
    ("Koota",        "山堡",     "consecutive_in_range", (4, 10),
                                  "4-10 宮連續 7 宮 — 囚禁、欺騙、與權威衝突"),
    ("Chatra",       "傘",       "consecutive_in_range_wrap", (7, 1),
                                  "7-1 宮連續 7 宮 — 庇護長輩、慈悲、晚年得福"),
    ("Chapa",        "弓",       "consecutive_in_range_wrap", (10, 4),
                                  "10-4 宮連續 7 宮 — 盜賊、欺詐、人際多疑"),
    ("Ardhachandra", "半月",     "consecutive_7", None,
                                  "任意 7 連續宮 — 知名、半月之美、軍事將才"),
    ("Chakra",       "輪",       "houses_only_in", {1, 3, 5, 7, 9, 11},
                                  "全 6 奇數宮 — 帝王之相、領導命格"),
    ("Samudra",      "海洋",     "houses_only_in", {2, 4, 6, 8, 10, 12},
                                  "全 6 偶數宮 — 富商、商業天才、財運雄厚"),
]


# ===== 偵測函式 =====

def _planet_signs(planets: dict) -> dict:
    """取 7 visible planets 的星座（前 3 字標準縮寫）"""
    out = {}
    for p in NABHASA_PLANETS:
        if p in planets:
            sign = planets[p].get("星座", "")[:3]
            if sign:
                out[p] = sign
    return out


def _planet_houses(planets: dict) -> dict:
    """取 7 visible planets 的宮位（容受 'First_House' / int 兩種格式）"""
    out = {}
    for p in NABHASA_PLANETS:
        if p in planets:
            h = _house_int(planets[p].get("宮位"))
            if h is not None:
                out[p] = h
    return out


def _check_ashraya(planet_signs: dict) -> list[dict]:
    """7 行星全在某活動性的星座群"""
    if len(planet_signs) < 7:
        return []
    signs_used = set(planet_signs.values())
    formed = []
    for name, zh, sign_set, meaning in ASHRAYA_YOGAS:
        if signs_used.issubset(sign_set):
            formed.append({
                "類別": "Ashraya 依託",
                "名稱": name,
                "中文": zh,
                "意涵": meaning,
            })
    return formed


def _check_dala(planet_houses: dict) -> list[dict]:
    """所有吉星 / 凶星全在角宮"""
    formed = []
    benefic_houses = {h for p, h in planet_houses.items() if p in BENEFIC_NABHASA}
    malefic_houses = {h for p, h in planet_houses.items() if p in MALEFIC_NABHASA}

    if benefic_houses and benefic_houses.issubset(KENDRAS):
        formed.append({
            "類別": "Dala 行列",
            "名稱": "Mala",
            "中文": "花環",
            "意涵": DALA_YOGAS[0][3],
        })
    if malefic_houses and malefic_houses.issubset(KENDRAS):
        formed.append({
            "類別": "Dala 行列",
            "名稱": "Sarpa",
            "中文": "蛇",
            "意涵": DALA_YOGAS[1][3],
        })
    return formed


def _is_consecutive_7(houses_used: set, start: int = None, wrap: bool = False) -> bool:
    """檢查 houses_used 是否為連續 7 宮的子集

    wrap=False: 只檢查 start 起算 7 宮（含 start, start+1, ..., start+6）
    wrap=True: 檢查環繞（如 7 起算 → 7,8,9,10,11,12,1）
    """
    if start is None:
        # 任意起點
        for s in range(1, 13):
            window = {((s - 1 + i) % 12) + 1 for i in range(7)}
            if houses_used.issubset(window) and len(houses_used) >= 4:
                return True
        return False
    window = {((start - 1 + i) % 12) + 1 for i in range(7)}
    return houses_used.issubset(window)


def _check_vajra_yava(planet_houses: dict) -> list[dict]:
    """Vajra: benefic 在 1,7 + malefic 在 4,10
       Yava : malefic 在 1,7 + benefic 在 4,10
    """
    formed = []
    benefic_houses = {h for p, h in planet_houses.items() if p in BENEFIC_NABHASA}
    malefic_houses = {h for p, h in planet_houses.items() if p in MALEFIC_NABHASA}

    if benefic_houses == {1, 7} and malefic_houses == {4, 10}:
        formed.append({
            "類別": "Akriti 形態",
            "名稱": "Vajra",
            "中文": "金剛",
            "意涵": "青年富足、老年衰退（先盛後衰）",
        })
    if malefic_houses == {1, 7} and benefic_houses == {4, 10}:
        formed.append({
            "類別": "Akriti 形態",
            "名稱": "Yava",
            "中文": "大麥",
            "意涵": "青年辛苦、中老年富足（先苦後甘）",
        })
    return formed


def _check_akriti(planet_houses: dict) -> list[dict]:
    """Akriti 形態類（除 Vajra/Yava 另外處理）"""
    formed = []
    if len(planet_houses) < 7:
        return formed
    houses_used = set(planet_houses.values())

    for entry in AKRITI_YOGAS:
        name, zh, rule, payload, meaning = entry
        match = False

        if rule == "houses_any_of":
            for target in payload:
                if houses_used == set(target):
                    match = True
                    break
        elif rule == "houses_only_in":
            if houses_used == set(payload):
                match = True
        elif rule == "consecutive_in_range":
            start, end = payload
            window = {((start - 1 + i) % 12) + 1 for i in range(7)}
            # 連續 7 宮 + 行星正好佔滿這個 7 宮
            if houses_used == window:
                match = True
        elif rule == "consecutive_in_range_wrap":
            start, end = payload
            window = {((start - 1 + i) % 12) + 1 for i in range(7)}
            if houses_used == window:
                match = True
        elif rule == "consecutive_7":
            # 任意起點 7 連續宮，且行星佔滿
            for s in range(1, 13):
                window = {((s - 1 + i) % 12) + 1 for i in range(7)}
                if houses_used == window:
                    match = True
                    break
        elif rule == "vajra" or rule == "yava":
            continue  # 由 _check_vajra_yava 處理

        if match:
            formed.append({
                "類別": "Akriti 形態",
                "名稱": name,
                "中文": zh,
                "意涵": meaning,
            })
    return formed


def _check_sankhya(planet_signs: dict) -> list[dict]:
    """7 行星佔了幾個不同的星座 → 唯一一個 Sankhya yoga"""
    if len(planet_signs) < 7:
        return []
    n_signs = len(set(planet_signs.values()))
    if n_signs in SANKHYA_YOGAS:
        name, zh, meaning = SANKHYA_YOGAS[n_signs]
        return [{
            "類別": "Sankhya 數量",
            "名稱": name,
            "中文": zh,
            "意涵": meaning,
            "佔星座數": n_signs,
        }]
    return []


def detect_nabhasa(natal: dict) -> dict:
    """偵測完整 Nabhasa yoga 分布

    Returns:
        {
            "形成的_yogas": [...],
            "依託類_Ashraya": [...],
            "行列類_Dala": [...],
            "形態類_Akriti": [...],
            "數量類_Sankhya": [...],
            "說明": "..."
        }
    """
    planets_raw = natal.get("行星", {})
    planet_signs = _planet_signs(planets_raw)
    planet_houses = _planet_houses(planets_raw)

    formed = []
    formed.extend(_check_ashraya(planet_signs))
    formed.extend(_check_dala(planet_houses))
    formed.extend(_check_akriti(planet_houses))
    formed.extend(_check_vajra_yava(planet_houses))
    formed.extend(_check_sankhya(planet_signs))

    by_type = {
        "Ashraya 依託": [],
        "Dala 行列": [],
        "Akriti 形態": [],
        "Sankhya 數量": [],
    }
    for y in formed:
        by_type[y["類別"]].append(y)

    return {
        "形成的_yogas": formed,
        "總數": len(formed),
        "依託類_Ashraya": by_type["Ashraya 依託"],
        "行列類_Dala":   by_type["Dala 行列"],
        "形態類_Akriti": by_type["Akriti 形態"],
        "數量類_Sankhya": by_type["Sankhya 數量"],
        "說明": (
            "Nabhasa 共 32 種：依託 3 + 行列 2 + 形態 20 + 數量 7。"
            "看的是 7 visible 行星（不含 Rahu/Ketu）的整體分布幾何，"
            "屬於命格的「整體形狀」 — 比個別 yoga 更宏觀。"
            "Sankhya 類必有一個（看佔幾個 sign），其他類視盤面結構而定。"
        ),
    }
