"""印度占星常數表

Nakshatra（27 星宿）、Vimshottari Dasha 週期、Gochar 吉凶規則。
"""

# 27 Nakshatra：(名稱, 中文, lord)
# 每個 Nakshatra 跨 13°20'（= 13.3333°），從牡羊 0° 開始
NAKSHATRAS = [
    ("Ashwini",            "馬頭",   "Ketu"),
    ("Bharani",            "三女",   "Venus"),
    ("Krittika",           "昴宿",   "Sun"),
    ("Rohini",             "畢宿",   "Moon"),
    ("Mrigashira",         "參宿",   "Mars"),
    ("Ardra",              "參宿增", "Rahu"),
    ("Punarvasu",          "井宿",   "Jupiter"),
    ("Pushya",             "鬼宿",   "Saturn"),
    ("Ashlesha",           "柳宿",   "Mercury"),
    ("Magha",              "星宿",   "Ketu"),
    ("Purva Phalguni",     "張宿",   "Venus"),
    ("Uttara Phalguni",    "翼宿",   "Sun"),
    ("Hasta",              "軫宿",   "Moon"),
    ("Chitra",             "角宿",   "Mars"),
    ("Swati",              "亢宿",   "Rahu"),
    ("Vishakha",           "氐宿",   "Jupiter"),
    ("Anuradha",           "房宿",   "Saturn"),
    ("Jyeshtha",           "心宿",   "Mercury"),
    ("Moola",              "尾宿",   "Ketu"),
    ("Purva Ashadha",      "箕宿",   "Venus"),
    ("Uttara Ashadha",     "斗宿",   "Sun"),
    ("Shravana",           "牛宿",   "Moon"),
    ("Dhanishta",          "女宿",   "Mars"),
    ("Shatabhisha",        "虛宿",   "Rahu"),
    ("Purva Bhadrapada",   "危宿",   "Jupiter"),
    ("Uttara Bhadrapada",  "室宿",   "Saturn"),
    ("Revati",             "壁宿",   "Mercury"),
]

# Vimshottari Dasha 週期（年數），順序固定
DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}

# 恆星年天數（Dasha 計算用）
SIDEREAL_YEAR_DAYS = 365.256363

# 12 星座順序（用於 Gochar 宮位計算）
SIGNS = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]

# 行星中文名
PLANET_NAMES_ZH = {
    "Sun": "太陽", "Moon": "月亮", "Mars": "火星", "Mercury": "水星",
    "Jupiter": "木星", "Venus": "金星", "Saturn": "土星",
    "Rahu": "羅睺", "Ketu": "計都",
    "Uranus": "天王星", "Neptune": "海王星", "Pluto": "冥王星",
}

SIGN_NAMES_ZH = {
    "Ari": "牡羊", "Tau": "金牛", "Gem": "雙子", "Can": "巨蟹",
    "Leo": "獅子", "Vir": "處女", "Lib": "天秤", "Sco": "天蠍",
    "Sag": "射手", "Cap": "摩羯", "Aqu": "水瓶", "Pis": "雙魚",
}

# Gochar 吉凶表：行星在從月亮起算第 N 宮（1-12）的吉凶
# True = 吉, False = 凶
# 來源：Brihat Parashara Hora Shastra 的 Gochar 規則
GOCHAR_RULES = {
    "Sun":     {1: False, 2: False, 3: True,  4: False, 5: False, 6: True,  7: False, 8: False, 9: False, 10: False, 11: True,  12: False},
    "Moon":    {1: True,  2: False, 3: True,  4: False, 5: False, 6: True,  7: True,  8: False, 9: False, 10: True,  11: True,  12: False},
    "Mars":    {1: False, 2: False, 3: True,  4: False, 5: False, 6: True,  7: False, 8: False, 9: False, 10: False, 11: True,  12: False},
    "Mercury": {1: False, 2: True,  3: False, 4: True,  5: False, 6: True,  7: False, 8: True,  9: False, 10: True,  11: True,  12: False},
    "Jupiter": {1: False, 2: True,  3: False, 4: False, 5: True,  6: False, 7: True,  8: False, 9: True,  10: False, 11: True,  12: False},
    "Venus":   {1: False, 2: False, 3: False, 4: True,  5: False, 6: False, 7: False, 8: True,  9: False, 10: False, 11: False, 12: True},
    "Saturn":  {1: False, 2: False, 3: True,  4: False, 5: False, 6: True,  7: False, 8: False, 9: False, 10: False, 11: True,  12: False},
    "Rahu":    {1: False, 2: False, 3: True,  4: False, 5: False, 6: True,  7: False, 8: False, 9: True,  10: False, 11: True,  12: False},
    "Ketu":    {1: False, 2: False, 3: True,  4: False, 5: False, 6: True,  7: False, 8: False, 9: True,  10: False, 11: True,  12: False},
}

# 行星高揚（Exaltation）和落陷（Debilitation）星座
EXALTATION = {
    "Sun": "Ari", "Moon": "Tau", "Mars": "Cap", "Mercury": "Vir",
    "Jupiter": "Can", "Venus": "Pis", "Saturn": "Lib",
    "Rahu": "Tau", "Ketu": "Sco",
}
DEBILITATION = {
    "Sun": "Lib", "Moon": "Sco", "Mars": "Can", "Mercury": "Pis",
    "Jupiter": "Cap", "Venus": "Vir", "Saturn": "Ari",
    "Rahu": "Sco", "Ketu": "Tau",
}

# 星座守護星（Sign Lords）
SIGN_LORDS = {
    "Ari": "Mars",    "Tau": "Venus",   "Gem": "Mercury", "Can": "Moon",
    "Leo": "Sun",     "Vir": "Mercury", "Lib": "Venus",   "Sco": "Mars",
    "Sag": "Jupiter", "Cap": "Saturn",  "Aqu": "Saturn",  "Pis": "Jupiter",
}

# 行星自身星座（Own Sign / Moolatrikona）
OWN_SIGNS = {
    "Sun": ["Leo"],
    "Moon": ["Can"],
    "Mars": ["Ari", "Sco"],
    "Mercury": ["Gem", "Vir"],
    "Jupiter": ["Sag", "Pis"],
    "Venus": ["Tau", "Lib"],
    "Saturn": ["Cap", "Aqu"],
    "Rahu": ["Aqu"],
    "Ketu": ["Sco"],
}

# 星座元素分類（Varga 計算用）
SIGN_ELEMENTS = {
    "Ari": "fire", "Leo": "fire", "Sag": "fire",
    "Tau": "earth", "Vir": "earth", "Cap": "earth",
    "Gem": "air", "Lib": "air", "Aqu": "air",
    "Can": "water", "Sco": "water", "Pis": "water",
}

# Navamsa 元素起算星座（火→Ari, 地→Cap, 風→Lib, 水→Can）
NAVAMSA_ELEMENT_START = {
    "fire": 0,   # Aries
    "earth": 9,  # Capricorn
    "air": 6,    # Libra
    "water": 3,  # Cancer
}

# 行星自然友敵關係（Naisargika Maitri）
# 用於計算 dignity 強度：行星在友星座（friend's sign）力量增強，敵星座力量減弱
# 結構：planet → {"friends": [...], "neutral": [...], "enemies": [...]}
NAISARGIKA_MAITRI = {
    "Sun":     {"friends": ["Moon", "Mars", "Jupiter"],   "neutral": ["Mercury"],                    "enemies": ["Venus", "Saturn"]},
    "Moon":    {"friends": ["Sun", "Mercury"],            "neutral": ["Mars", "Jupiter", "Venus", "Saturn"], "enemies": []},
    "Mars":    {"friends": ["Sun", "Moon", "Jupiter"],    "neutral": ["Venus", "Saturn"],            "enemies": ["Mercury"]},
    "Mercury": {"friends": ["Sun", "Venus"],              "neutral": ["Mars", "Jupiter", "Saturn"],  "enemies": ["Moon"]},
    "Jupiter": {"friends": ["Sun", "Moon", "Mars"],       "neutral": ["Saturn"],                     "enemies": ["Mercury", "Venus"]},
    "Venus":   {"friends": ["Mercury", "Saturn"],         "neutral": ["Mars", "Jupiter"],            "enemies": ["Sun", "Moon"]},
    "Saturn":  {"friends": ["Mercury", "Venus"],          "neutral": ["Jupiter"],                    "enemies": ["Sun", "Moon", "Mars"]},
}

# 焦傷距離（Combustion Orb）— 行星太靠近太陽（經度差）即視為焦傷，力量受損
# 各家略有差異，這裡採 BPHS 主流值。Moon 也可焦傷但實務罕用，先不列
COMBUSTION_ORB = {
    "Mercury": 14.0,  # 逆行時 12°（暫不細分）
    "Venus":   10.0,  # 逆行時 8°
    "Mars":    17.0,
    "Jupiter": 11.0,
    "Saturn":  15.0,
}

# Yoga Karaka — 該上升星座的「同時掌管角宮 + 三方宮」的行星
# 這顆星在該命主的盤裡天然就是大吉星（不需要其他條件配合）
# 只有 6 個上升星座有天然 yoga karaka，其他上升要靠後天組合
YOGA_KARAKAS = {
    "Tau": "Saturn",   # Saturn 掌 9 (Cap) + 10 (Aqu)
    "Can": "Mars",     # Mars 掌 5 (Sco) + 10 (Ari)
    "Leo": "Mars",     # Mars 掌 4 (Sco) + 9 (Ari)
    "Lib": "Saturn",   # Saturn 掌 4 (Cap) + 5 (Aqu)
    "Cap": "Venus",    # Venus 掌 5 (Tau) + 10 (Lib)
    "Aqu": "Venus",    # Venus 掌 4 (Tau) + 9 (Lib)
}

# Maraka 宮位（死亡相關）
# 2 / 7 宮主可能成為「殺手」（Maraka），尤其在凶大限時
MARAKA_HOUSES = [2, 7]

# Marana Karaka Sthana（行星的「死亡位置」）
# 行星在這些宮位天生效力衰弱（不論 dignity）
# 不是「會死」的意思，是「該行星的能量在那個位置最難發揮」
MARANA_KARAKA_STHANA = {
    "Sun":     12,
    "Moon":     8,
    "Mars":     7,
    "Mercury":  7,
    "Jupiter":  3,
    "Venus":    6,
    "Saturn":   1,
    "Rahu":     9,  # 部分典籍
    "Ketu":     6,  # 部分典籍
}

# 分盤資訊
VARGA_INFO = {
    "D2":  {"name": "Hora",            "zh": "時分盤",   "用途": "財富"},
    "D3":  {"name": "Drekkana",        "zh": "三分盤",   "用途": "兄弟、勇氣"},
    "D4":  {"name": "Chaturthamsa",    "zh": "四分盤",   "用途": "家、不動產、心靈安定"},
    "D6":  {"name": "Shashtamsa",      "zh": "六分盤",   "用途": "疾病、債務、敵對（6 宮主題）"},
    "D7":  {"name": "Saptamsa",        "zh": "七分盤",   "用途": "子女"},
    "D8":  {"name": "Ashtamsa",        "zh": "八分盤",   "用途": "壽命、突發災禍、意外（8 宮主題）"},
    "D9":  {"name": "Navamsa",         "zh": "九分盤",   "用途": "婚姻、法性"},
    "D10": {"name": "Dasamsa",         "zh": "十分盤",   "用途": "事業"},
    "D12": {"name": "Dwadasamsa", "zh": "十二分盤", "用途": "父母"},
    "D16": {"name": "Shodasamsa",      "zh": "十六分盤",   "用途": "車輛、奢侈品、物質享受"},
    "D20": {"name": "Vimsamsa",        "zh": "二十分盤",   "用途": "靈性修行、宗教實踐"},
    "D24": {"name": "Chaturvimsamsa",  "zh": "二十四分盤", "用途": "學習、教育、知識成就"},
    "D27": {"name": "Saptavimsamsa",   "zh": "二十七分盤", "用途": "體力、運動能力、優劣"},
    "D30": {"name": "Trimsamsa",       "zh": "三十分盤",   "用途": "災厄、健康危機、心理弱點"},
    "D40": {"name": "Khavedamsa",      "zh": "四十分盤",   "用途": "母系遺產、整體吉凶"},
    "D45": {"name": "Akshavedamsa",    "zh": "四十五分盤", "用途": "父系遺產、整體性格"},
    "D60": {"name": "Shastiamsa", "zh": "六十分盤", "用途": "前世業力、靈魂功課"},
}
