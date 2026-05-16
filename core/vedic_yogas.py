"""Vedic Yogas（行星組合）偵測模組

從本命盤偵測 Parashara 體系中重要的 Yoga（吉凶組合）。
Yoga 是 Vedic 占星的精華，比單看行星位置更能反映命格特質。

涵蓋 15 個主要 Yogas：
- Pancha Mahapurusha（5 大人物）：Ruchaka / Bhadra / Hamsa / Malavya / Shasha
- 重要組合：Gajakesari / Budha-Aditya / Chandra-Mangal / Lakshmi / Saraswati
- Raja / Dhana：Kendra-Trikona Raja / 2-11 Dhana / 5-9 Dhana
- 警示：Kemadruma / Shakata
"""

from core.vedic_constants import (
    SIGNS, SIGN_NAMES_ZH, SIGN_LORDS,
    EXALTATION, DEBILITATION, OWN_SIGNS,
    COMBUSTION_ORB,
)

# 宮位英文 → 數字
HOUSE_NUM = {
    "First_House": 1,  "Second_House": 2,  "Third_House": 3,    "Fourth_House": 4,
    "Fifth_House": 5,  "Sixth_House": 6,   "Seventh_House": 7,  "Eighth_House": 8,
    "Ninth_House": 9,  "Tenth_House": 10,  "Eleventh_House": 11, "Twelfth_House": 12,
}

KENDRAS = {1, 4, 7, 10}     # 角宮 — 行動的舞台
TRIKONAS = {1, 5, 9}        # 三方宮 — 法性與福德
DUSHTANAS = {6, 8, 12}      # 凶宮 — 困難領域

# Vedic 特殊望宮（除了所有行星都望第 7 宮之外的額外望宮）
SPECIAL_ASPECTS = {
    "Mars":    [4, 8],
    "Jupiter": [5, 9],
    "Saturn":  [3, 10],
    "Rahu":    [5, 7, 9],
    "Ketu":    [5, 7, 9],
}

# Yoga → 主要影響領域分類，讓下游不用拆「性質」字串
# 一個 yoga 可以有多個領域（用 list），主領域排第一
YOGA_CATEGORY = {
    # 五大人物
    "Ruchaka":              ["個人能力"],
    "Bhadra":               ["個人能力"],
    "Hamsa":                ["個人能力"],
    "Malavya":              ["個人能力"],
    "Shasha":               ["個人能力"],
    # 月亮系
    "Gajakesari":           ["智慧", "福德"],
    "Sunapha":              ["財富"],
    "Anapha":               ["聲譽", "精神"],
    "Durudhara":            ["物質享受"],
    "Adhi":                 ["領袖", "福氣"],
    "Vasumati":             ["財富"],
    "Chandra-Mangal":       ["財富"],
    # 太陽系
    "Budha-Aditya":         ["智慧", "表達"],
    "Budha-Aditya（焦傷）":  ["智慧", "表達"],
    "Vesi":                 ["個人形象", "表達"],
    "Voshi":                ["慷慨", "學識"],
    "Ubhayachari":          ["地位", "整體福氣"],
    # Raja
    "Kendra-Trikona Raja":  ["王者", "地位"],
    "Neecha Bhanga Raja":   ["王者（弱轉強）"],
    "Vipareeta Raja":       ["王者（凶轉吉）"],
    "Dharma-Karmadhipati":  ["王者", "事業"],
    "Kahala":               ["王者", "根基"],
    # Dhana
    "Lakshmi":              ["財富"],
    "Dhana 1-2":            ["財富"],
    "Dhana 1-5":            ["財富", "智慧"],
    "Dhana 1-9":            ["財富", "福德"],
    "Dhana 1-11":           ["財富"],
    "Dhana 2-5":            ["財富", "智慧"],
    "Dhana 2-9":            ["財富", "福德"],
    "Dhana 2-11":           ["財富"],
    "Dhana 5-9":            ["財富", "福德"],
    "Dhana 5-11":           ["財富"],
    "Dhana 9-11":           ["財富", "福德"],
    # 互換
    "Parivartana":          ["互換", "格局深化"],
    # 其他特殊
    "Saraswati":            ["智慧", "學識"],
    "Kalanidhi":            ["智慧", "藝術"],
    "Maha Bhagya（男性版）": ["整體福氣"],
    "Kala Sarpa":           ["命格特殊"],
    # 警示
    "Kemadruma":            ["警示"],
    "Shakata":              ["警示"],
    "Daridra":              ["警示"],
    # 警示 / Dosha（新增）
    "Mangal Dosha":         ["警示", "婚姻"],
    "Guru Chandal":         ["警示", "信仰"],
    "Combust":              ["警示"],
    "Vish":                 ["警示", "情緒"],
    "Grahan":               ["警示", "父母"],
    "Pitra Dosha":          ["警示", "祖先業力"],
    "Karako Bhava Nashaya": ["警示"],
    "Mars-Saturn Conflict": ["警示"],
    # Sanyasa 出家瑜伽
    "Pravrajya":            ["出家", "靈性"],
    "Sanyasa Yoga":         ["出家", "靈性"],
}

# Pravrajya 主導行星 → 出家派別（4+ 行星合相時最強的那顆決定）
PRAVRAJYA_PATH = {
    "Sun":     "Vanaprastha 隱士派（離群索居、回歸自然）",
    "Moon":    "Brahmin 婆羅門派（吟唱、儀式、潔淨）",
    "Mars":    "Tapasvi 苦行派（嚴格修行、自我鍛煉）",
    "Mercury": "Bauddha 佛教派（觀照、智慧、辯經）",
    "Jupiter": "Sanyasi 出家僧（典型出家、棄世）",
    "Venus":   "Naga 蛇族修行（密續、本尊、咒語）",
    "Saturn":  "Sakya 釋迦派（極簡苦行、無物所有）",
}


def _house_from(from_house: int, n: int) -> int:
    """從 from_house 算第 n 宮（n=1 代表自己）"""
    return ((from_house - 1 + n - 1) % 12) + 1


def _aspects_houses(planet: str, from_house: int) -> set[int]:
    """planet 從 from_house 望見的宮位"""
    targets = {_house_from(from_house, 7)}
    for n in SPECIAL_ASPECTS.get(planet, []):
        targets.add(_house_from(from_house, n))
    return targets


def _conjunct(h1: int, h2: int) -> bool:
    return h1 == h2


def _mutual_aspect(p1: str, h1: int, p2: str, h2: int) -> bool:
    """p1 和 p2 互相望"""
    return h2 in _aspects_houses(p1, h1) and h1 in _aspects_houses(p2, h2)


def _aspect_or_conj(p1: str, h1: int, p2: str, h2: int) -> bool:
    """合相或互望"""
    return _conjunct(h1, h2) or _mutual_aspect(p1, h1, p2, h2)


def _dignity(planet: str, sign: str) -> str:
    """行星在該星座的力量狀態"""
    if EXALTATION.get(planet) == sign:
        return "高揚"
    if DEBILITATION.get(planet) == sign:
        return "落陷"
    if sign in OWN_SIGNS.get(planet, []):
        return "廟旺"
    return "中性"


def _is_strong(planet: str, sign: str) -> bool:
    """高揚或廟旺"""
    return _dignity(planet, sign) in ("高揚", "廟旺")


def _normalize_planets(natal: dict) -> dict:
    """把 natal JSON 轉成 {planet_name: {sign, house, deg}}，含 Rahu/Ketu"""
    result = {}
    for name, data in natal.get("行星", {}).items():
        result[name] = {
            "sign": data["星座"],
            "house": HOUSE_NUM[data["宮位"]],
            "deg": data["度數"],
        }
    # Rahu / Ketu 在 其他星體
    nodes_map = {
        "True_North_Lunar_Node": "Rahu",
        "True_South_Lunar_Node": "Ketu",
    }
    for raw_name, alias in nodes_map.items():
        node = natal.get("其他星體", {}).get(raw_name)
        if node:
            result[alias] = {
                "sign": node["星座"],
                "house": HOUSE_NUM[node["宮位"]],
                "deg": node["度數"],
            }
    return result


def _normalize_houses(natal: dict) -> dict:
    """{house_num: {sign, lord}}"""
    result = {}
    for house_key, data in natal.get("宮位", {}).items():
        # "第1宮" → 1
        n = int(house_key.replace("第", "").replace("宮", ""))
        sign = data["星座"]
        result[n] = {"sign": sign, "lord": SIGN_LORDS[sign]}
    return result


# ===== Yogas 偵測 =====

def _check_pancha_mahapurusha(planets: dict) -> list[dict]:
    """5 大人物 yoga：行星高揚/廟旺 + 在 Kendra（1/4/7/10）"""
    config = [
        ("Mars",    "Ruchaka", "戰士、領導力、體能、勇氣"),
        ("Mercury", "Bhadra",  "智者、商人、溝通、學識"),
        ("Jupiter", "Hamsa",   "智慧、福德、宗教、教導"),
        ("Venus",   "Malavya", "美感、藝術、享受、魅力"),
        ("Saturn",  "Shasha",  "領袖、紀律、權威、長壽"),
    ]
    yogas = []
    for planet, name, meaning in config:
        p = planets.get(planet)
        if not p:
            continue
        if _is_strong(planet, p["sign"]) and p["house"] in KENDRAS:
            yogas.append({
                "名稱": name,
                "中文": f"{name} Yoga（五大人物之一）",
                "性質": "吉",
                "行星": planet,
                "說明": f"{planet} 在 {p['sign']}（{_dignity(planet, p['sign'])}）位於第 {p['house']} 宮（角宮）",
                "意義": meaning,
            })
    return yogas


def _check_gajakesari(planets: dict) -> list[dict]:
    """Gajakesari Yoga：月亮和木星互為角宮（1/4/7/10）"""
    moon = planets.get("Moon")
    jup = planets.get("Jupiter")
    if not moon or not jup:
        return []
    # 兩者所在宮的差距 mod 12，0/3/6/9 = 角宮關係
    delta = (jup["house"] - moon["house"]) % 12
    if delta in {0, 3, 6, 9}:
        return [{
            "名稱": "Gajakesari",
            "中文": "象獅 Yoga",
            "性質": "吉",
            "說明": f"月亮（{moon['sign']}, 第{moon['house']}宮）與木星（{jup['sign']}, 第{jup['house']}宮）互為角宮",
            "意義": "智慧、聲望、福德、影響力",
        }]
    return []


def _check_budha_aditya(planets: dict) -> list[dict]:
    """Budha-Aditya Yoga：太陽 + 水星合相（同宮）。需檢查水星不焦傷"""
    sun = planets.get("Sun")
    mer = planets.get("Mercury")
    if not sun or not mer:
        return []
    if not _conjunct(sun["house"], mer["house"]):
        return []
    # 焦傷檢查：太陽水星經度差 < 14° 為焦傷（簡化：用同星座內度數差）
    if sun["sign"] == mer["sign"]:
        if abs(sun["deg"] - mer["deg"]) < 14:
            return [{
                "名稱": "Budha-Aditya（焦傷）",
                "中文": "水星太陽合 — 焦傷",
                "性質": "中性",
                "說明": f"太陽水星在 {sun['sign']} 同宮但度數過近（{abs(sun['deg']-mer['deg']):.1f}°），水星焦傷",
                "意義": "智慧潛力存在但被太陽光芒遮蔽，需透過行運釋放",
            }]
    return [{
        "名稱": "Budha-Aditya",
        "中文": "水星太陽合 Yoga",
        "性質": "吉",
        "說明": f"太陽（第{sun['house']}宮）與水星合相，距離 {abs(sun['deg']-mer['deg']):.1f}°（未焦傷）",
        "意義": "智慧、聲望、表達力、學識被認可",
    }]


def _check_chandra_mangal(planets: dict) -> list[dict]:
    """Chandra-Mangal Yoga：月亮 + 火星合相或互望"""
    moon = planets.get("Moon")
    mars = planets.get("Mars")
    if not moon or not mars:
        return []
    if _aspect_or_conj("Moon", moon["house"], "Mars", mars["house"]):
        relation = "合相" if _conjunct(moon["house"], mars["house"]) else "互望"
        return [{
            "名稱": "Chandra-Mangal",
            "中文": "月火 Yoga",
            "性質": "吉（財富）",
            "說明": f"月亮（第{moon['house']}宮）與火星（第{mars['house']}宮）{relation}",
            "意義": "商業敏銳度、賺錢動力、財富累積能力",
        }]
    return []


def _check_lakshmi(planets: dict, houses: dict) -> list[dict]:
    """Lakshmi Yoga：9 宮主強勢 + 金星強勢"""
    ninth_lord = houses.get(9, {}).get("lord")
    if not ninth_lord:
        return []
    nl = planets.get(ninth_lord)
    venus = planets.get("Venus")
    if not nl or not venus:
        return []
    if _is_strong(ninth_lord, nl["sign"]) and _is_strong("Venus", venus["sign"]) and nl["house"] in KENDRAS:
        return [{
            "名稱": "Lakshmi",
            "中文": "財富女神 Yoga",
            "性質": "吉",
            "說明": f"9 宮主 {ninth_lord} 強勢且在角宮 + 金星強勢",
            "意義": "財富、配偶帶來好運、整體幸福",
        }]
    return []


def _check_saraswati(planets: dict) -> list[dict]:
    """Saraswati Yoga：水、木、金三者皆在角宮/三方宮 + 各自強勢"""
    targets = ["Mercury", "Jupiter", "Venus"]
    for p in targets:
        pl = planets.get(p)
        if not pl:
            return []
        if pl["house"] not in (KENDRAS | TRIKONAS):
            return []
        # 強勢 = 高揚/廟旺（簡化版，不含友星座）
        if not _is_strong(p, pl["sign"]):
            return []
    return [{
        "名稱": "Saraswati",
        "中文": "智慧女神 Yoga",
        "性質": "吉",
        "說明": "水星、木星、金星三者皆在角/三方宮且強勢",
        "意義": "學識、藝術、智慧、教育成就",
    }]


def _check_kendra_trikona_raja(planets: dict, houses: dict) -> list[dict]:
    """Kendra-Trikona Raja Yoga：任一角宮主與任一三方宮主合相或互望"""
    kendra_lords = {houses[h]["lord"] for h in KENDRAS if h in houses}
    trikona_lords = {houses[h]["lord"] for h in TRIKONAS if h in houses}
    found = []
    seen = set()
    for kl in kendra_lords:
        for tl in trikona_lords:
            if kl == tl:
                continue
            pair = tuple(sorted([kl, tl]))
            if pair in seen:
                continue
            kp = planets.get(kl)
            tp = planets.get(tl)
            if not kp or not tp:
                continue
            if _aspect_or_conj(kl, kp["house"], tl, tp["house"]):
                seen.add(pair)
                relation = "合相" if _conjunct(kp["house"], tp["house"]) else "互望"
                found.append({
                    "名稱": "Kendra-Trikona Raja",
                    "中文": f"角三方王者 Yoga（{kl} + {tl}）",
                    "性質": "吉（王者）",
                    "說明": f"角宮主 {kl}（第{kp['house']}宮）與三方宮主 {tl}（第{tp['house']}宮）{relation}",
                    "意義": "權力、地位、領導機會、人生格局提升",
                })
    return found


def _check_two_lord_yoga(
    planets: dict, houses: dict,
    house_a: int, house_b: int,
    name: str, chinese: str, nature: str, meaning: str,
) -> list[dict]:
    """通用：兩個宮主合相或互望時成立的 yoga"""
    la = houses.get(house_a, {}).get("lord")
    lb = houses.get(house_b, {}).get("lord")
    if not la or not lb or la == lb:
        return []
    pa = planets.get(la)
    pb = planets.get(lb)
    if not pa or not pb:
        return []
    if not _aspect_or_conj(la, pa["house"], lb, pb["house"]):
        return []
    return [{
        "名稱": name,
        "中文": chinese,
        "性質": nature,
        "說明": f"{house_a} 宮主 {la} 與 {house_b} 宮主 {lb} 連結",
        "意義": meaning,
    }]


def _check_parivartana(planets: dict) -> list[dict]:
    """Parivartana Yoga（互換）：兩顆行星位於彼此的星座。
    例：Mars 在 Capricorn（Saturn 守護）+ Saturn 在 Aries（Mars 守護） = Mars/Saturn 互換
    互換代表兩顆星管的領域深度連動 — 升降、貴人、職涯轉折常出現
    """
    main_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    found = []
    seen = set()
    for p1 in main_planets:
        pl1 = planets.get(p1)
        if not pl1:
            continue
        lord_of_sign1 = SIGN_LORDS.get(pl1["sign"])
        if not lord_of_sign1 or lord_of_sign1 == p1 or lord_of_sign1 not in main_planets:
            continue
        pl2 = planets.get(lord_of_sign1)
        if not pl2 or pl2["sign"] not in OWN_SIGNS.get(p1, []):
            continue
        pair = tuple(sorted([p1, lord_of_sign1]))
        if pair in seen:
            continue
        seen.add(pair)
        found.append({
            "名稱": f"Parivartana ({p1}-{lord_of_sign1})",
            "中文": f"互換 Yoga（{p1} ↔ {lord_of_sign1}）",
            "性質": "吉",
            "說明": f"{p1} 在 {pl1['sign']}（{lord_of_sign1} 守護），{lord_of_sign1} 在 {pl2['sign']}（{p1} 守護）",
            "意義": f"{p1} 和 {lord_of_sign1} 主管的領域互相換手 — 兩個生命主題深度連動，升降轉折時一起發生",
        })
    return found


def _check_vasumati(planets: dict) -> list[dict]:
    """Vasumati Yoga：水星、木星、金星都在月亮的 upachaya 宮（3/6/10/11）— 持續累積財富"""
    moon = planets.get("Moon")
    if not moon:
        return []
    upachaya = {_house_from(moon["house"], n) for n in (3, 6, 10, 11)}
    benefics = ["Mercury", "Jupiter", "Venus"]
    placements = []
    for p in benefics:
        pl = planets.get(p)
        if not pl or pl["house"] not in upachaya:
            return []
        placements.append(f"{p}（第{pl['house']}宮）")
    return [{
        "名稱": "Vasumati",
        "中文": "Vasumati Yoga",
        "性質": "吉（財富）",
        "說明": f"水星、木星、金星都在月亮的 upachaya 宮（3/6/10/11）：{', '.join(placements)}",
        "意義": "持續累積的物質豐裕，財富透過正當努力穩定增長",
    }]


def _check_solar_yogas(planets: dict) -> list[dict]:
    """太陽系 yoga（Vesi / Voshi / Ubhayachari）— 月亮排除。
    Ubhayachari 最強，Vesi 次之，Voshi 第三
    """
    sun = planets.get("Sun")
    if not sun:
        return []
    h2 = _house_from(sun["house"], 2)
    h12 = _house_from(sun["house"], 12)
    others = ["Mercury", "Mars", "Jupiter", "Venus", "Saturn"]
    in_2 = [p for p in others if planets.get(p) and planets[p]["house"] == h2]
    in_12 = [p for p in others if planets.get(p) and planets[p]["house"] == h12]
    if in_2 and in_12:
        return [{
            "名稱": "Ubhayachari",
            "中文": "Ubhayachari Yoga（太陽兩側）",
            "性質": "吉",
            "說明": f"太陽 2 宮有 {', '.join(in_2)}，12 宮有 {', '.join(in_12)}",
            "意義": "富裕、地位、長壽、被尊敬 — 最強的太陽系 yoga",
        }]
    if in_2:
        return [{
            "名稱": "Vesi",
            "中文": "Vesi Yoga（太陽 2 宮）",
            "性質": "吉",
            "說明": f"太陽 2 宮有 {', '.join(in_2)}",
            "意義": "言語有分量、誠實守信、外觀威嚴",
        }]
    if in_12:
        return [{
            "名稱": "Voshi",
            "中文": "Voshi Yoga（太陽 12 宮）",
            "性質": "吉",
            "說明": f"太陽 12 宮有 {', '.join(in_12)}",
            "意義": "慷慨、學識、適度的精神享受",
        }]
    return []


# Dhana yoga 宮主組合表 — 用統一資料表驅動，新增容易
# (house_a, house_b, name, chinese, meaning)
DHANA_PAIRS = [
    (1, 2,  "Dhana 1-2",  "1-2 主合 Yoga",  "自我直接帶財 — 個人努力即現金流"),
    (1, 5,  "Dhana 1-5",  "1-5 主合 Yoga",  "自我帶來智慧財 / 創意 / 投資收益"),
    (1, 9,  "Dhana 1-9",  "1-9 主合 Yoga",  "自我帶來福德財 — 老天賞飯吃型"),
    (1, 11, "Dhana 1-11", "1-11 主合 Yoga", "自我直接連結收入管道 — 親力親為帶財"),
    (2, 5,  "Dhana 2-5",  "2-5 主合 Yoga",  "言語 / 智慧 / 教學變現"),
    (2, 9,  "Dhana 2-9",  "2-9 主合 Yoga",  "家族 / 福德積累的財富"),
    (5, 11, "Dhana 5-11", "5-11 主合 Yoga", "創意 / 子女 / 投機帶來長期收益"),
    (9, 11, "Dhana 9-11", "9-11 主合 Yoga", "福德直接化為長期收益 — 越老越富"),
]


def _check_mangal_dosha(planets: dict) -> list[dict]:
    """Mangal Dosha（火星缺陷）：Mars 在 1/4/7/8/12 宮（從 Lagna 起算）
    破解：Mars 廟旺（Aries/Scorpio）或高揚（Capricorn）→ 影響大幅減輕
    主要影響：婚姻 / 親密關係 / 商業合作的挑戰
    """
    mars = planets.get("Mars")
    if not mars or mars["house"] not in {1, 4, 7, 8, 12}:
        return []
    sign = mars["sign"]
    cancelled = sign in OWN_SIGNS.get("Mars", []) or EXALTATION.get("Mars") == sign
    nature = "中性（已破解）" if cancelled else "凶（婚姻挑戰）"
    note = "（Mars 廟旺/高揚 → 已破解）" if cancelled else "（無破解條件）"
    return [{
        "名稱": "Mangal Dosha",
        "中文": f"火星缺陷 Yoga（第{mars['house']}宮）",
        "性質": nature,
        "說明": f"Mars 在第 {mars['house']} 宮（{sign}）{note}",
        "意義": "婚姻 / 親密關係 / 商業合作的挑戰：配偶火爆、衝突多、結婚晚、對方家庭難搞" + ("（已破解，影響大幅減輕）" if cancelled else ""),
    }]


# 「兩顆行星同宮」型 dosha — 表驅動
# 新增規則 = 加一筆資料
# (planet1, planet2, name, chinese_template, nature, meaning)
CONJUNCTION_DOSHAS = [
    ("Jupiter", "Rahu", "Guru Chandal (Rahu)", "木羅睺合 Yoga（第{h}宮）",
     "凶（信仰挑戰）",
     "對傳統信仰系統的衝突 / 反叛、精神導師議題、靈修上深度但古怪、與長輩在價值觀上拉扯"),
    ("Jupiter", "Ketu", "Guru Chandal (Ketu)", "木計都合 Yoga（第{h}宮）",
     "凶（信仰挑戰）",
     "對傳統信仰系統的衝突 / 反叛、精神導師議題、靈修上深度但古怪、與長輩在價值觀上拉扯"),
    ("Sun", "Rahu", "Pitra Dosha (Rahu)", "祖先業力 Yoga（Sun + 羅睺，第{h}宮）",
     "凶（祖先業力）",
     "祖先 / 父系業力未了、父親或長輩關係挑戰、繼承類議題、需透過儀式 / 修行清業"),
    ("Sun", "Ketu", "Pitra Dosha (Ketu)", "祖先業力 Yoga（Sun + 計都，第{h}宮）",
     "凶（祖先業力）",
     "祖先 / 父系業力未了、父親或長輩關係挑戰、繼承類議題、需透過儀式 / 修行清業"),
    ("Moon", "Rahu", "Grahan (Moon-Rahu)", "月亮羅睺蝕格（第{h}宮）",
     "凶（業力）",
     "母親 / 情緒相關的業力議題、安全感被遮蔽、母系挑戰"),
    ("Moon", "Ketu", "Grahan (Moon-Ketu)", "月亮計都蝕格（第{h}宮）",
     "凶（業力）",
     "母親 / 情緒相關的業力議題、安全感被遮蔽、母系挑戰"),
]


def _check_conjunction_doshas(planets: dict) -> list[dict]:
    """統一處理 CONJUNCTION_DOSHAS 表 — 兩顆行星同宮即觸發"""
    found = []
    for p1, p2, name, chinese_tmpl, nature, meaning in CONJUNCTION_DOSHAS:
        pl1 = planets.get(p1)
        pl2 = planets.get(p2)
        if not pl1 or not pl2 or pl1["house"] != pl2["house"]:
            continue
        found.append({
            "名稱": name,
            "中文": chinese_tmpl.format(h=pl1["house"]),
            "性質": nature,
            "說明": f"{p1} 與 {p2} 同在第 {pl1['house']} 宮（{pl1['sign']}）",
            "意義": meaning,
        })
    return found


def _check_combust(planets: dict) -> list[dict]:
    """焦傷檢查：行星距太陽經度差 < COMBUSTION_ORB → 該行星力量受損"""
    sun = planets.get("Sun")
    if not sun:
        return []
    sign_idx = {s: i for i, s in enumerate(SIGNS)}
    sun_lon = sign_idx[sun["sign"]] * 30 + sun["deg"]
    found = []
    for planet, orb in COMBUSTION_ORB.items():
        pl = planets.get(planet)
        if not pl:
            continue
        pl_lon = sign_idx[pl["sign"]] * 30 + pl["deg"]
        diff = abs(pl_lon - sun_lon)
        if diff > 180:
            diff = 360 - diff
        if diff < orb:
            found.append({
                "名稱": f"Combust ({planet})",
                "中文": f"{planet} 焦傷",
                "性質": "凶（力量削弱）",
                "說明": f"{planet} 距太陽 {diff:.2f}°（< 焦傷距 {orb}°）",
                "意義": f"{planet} 力量被太陽光遮蔽 — 該行星主管領域要花更多力氣才能發揮，廟旺/高揚也救不了完全",
            })
    return found


# 「兩顆行星合相 OR 互望」型 dosha — 表驅動
# (p1, p2, name, chinese_template_with_{rel}, nature_default, meaning)
# 合相時 nature 自動升級為「強衝突」（如有 nature_strong）
ASPECT_DOSHAS = [
    {
        "planets": ("Moon", "Saturn"),
        "name": "Vish",
        "chinese_tmpl": "毒月 Yoga（{rel}）",
        "nature": "凶（情緒）",
        "nature_strong": "凶（強情緒衝擊）",
        "meaning": "情緒沉重、容易內耗 / 抑鬱、母系或家庭氛圍嚴肅、安全感建立困難",
    },
    {
        "planets": ("Mars", "Saturn"),
        "name": "Mars-Saturn Conflict",
        "chinese_tmpl": "火土衝突 Yoga（{rel}）",
        "nature": "凶（中衝突）",
        "nature_strong": "凶（強衝突）",
        "meaning": "推進力（火）vs 紀律 / 限制（土）的反覆拉扯，做事容易自我消耗",
    },
]


def _check_aspect_doshas(planets: dict) -> list[dict]:
    """統一處理 ASPECT_DOSHAS 表 — 合相或互望即觸發"""
    found = []
    for d in ASPECT_DOSHAS:
        p1, p2 = d["planets"]
        pl1 = planets.get(p1)
        pl2 = planets.get(p2)
        if not pl1 or not pl2:
            continue
        if _conjunct(pl1["house"], pl2["house"]):
            relation = "合相"
            nature = d["nature_strong"]
        elif _mutual_aspect(p1, pl1["house"], p2, pl2["house"]):
            relation = "互望"
            nature = d["nature"]
        else:
            continue
        found.append({
            "名稱": f"{d['name']} ({relation})",
            "中文": d["chinese_tmpl"].format(rel=relation),
            "性質": nature,
            "說明": f"{p1}（第{pl1['house']}宮）與 {p2}（第{pl2['house']}宮）{relation}",
            "意義": d["meaning"],
        })
    return found


def _check_karako_bhava_nashaya(planets: dict) -> list[dict]:
    """Karako Bhava Nashaya：行星 karaka 在自己主管的 bhava 反而削弱該 bhava
    保守版：只查最廣泛被接受的兩個（Venus in 7、Jupiter in 5）
    """
    found = []
    checks = [
        ("Venus", 7, "婚姻", "婚姻宮", "婚姻品質受損 — 過度浪漫期待 vs 現實落差，配偶關係容易反覆"),
        ("Jupiter", 5, "子女", "子女宮", "子女運受損 — 求子困難、子女緣薄、創意輸出不順"),
    ]
    for planet, house, theme, house_zh, meaning in checks:
        pl = planets.get(planet)
        if pl and pl["house"] == house:
            found.append({
                "名稱": f"Karako Bhava Nashaya ({planet})",
                "中文": f"{theme}指示星削弱（{planet} 在第{house}宮）",
                "性質": "凶（karaka 自傷）",
                "說明": f"{planet}（{theme} karaka）落在第 {house} 宮（{house_zh}）",
                "意義": meaning,
            })
    return found


def _check_kemadruma(planets: dict) -> list[dict]:
    """Kemadruma Yoga（凶）：月亮 2/12 宮無行星（除太陽 + Rahu/Ketu）且不在角宮"""
    moon = planets.get("Moon")
    if not moon:
        return []
    # 月亮的 2 宮和 12 宮
    h2 = _house_from(moon["house"], 2)
    h12 = _house_from(moon["house"], 12)
    # 檢查除太陽 / Rahu / Ketu 外的行星
    others = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
    for p in others:
        pl = planets.get(p)
        if pl and pl["house"] in {h2, h12}:
            return []  # 有行星陪 → 不形成
    # 月亮在角宮也可破解
    if moon["house"] in KENDRAS:
        return []
    return [{
        "名稱": "Kemadruma",
        "中文": "孤月 Yoga",
        "性質": "凶",
        "說明": f"月亮第{moon['house']}宮，2 宮和 12 宮無行星陪伴",
        "意義": "情緒孤獨、內在不安、起伏大、難以從他人獲得情感支持",
    }]


def _check_shakata(planets: dict) -> list[dict]:
    """Shakata Yoga（凶）：月亮和木星互為 6/8 宮"""
    moon = planets.get("Moon")
    jup = planets.get("Jupiter")
    if not moon or not jup:
        return []
    delta = (jup["house"] - moon["house"]) % 12
    if delta in {5, 7}:  # 6 宮 = +5 step, 8 宮 = +7 step
        return [{
            "名稱": "Shakata",
            "中文": "車輪 Yoga",
            "性質": "凶",
            "說明": f"月亮（第{moon['house']}宮）與木星（第{jup['house']}宮）互為 6/8 軸",
            "意義": "人生起伏明顯、福氣斷續、智慧與情緒拉扯",
        }]
    return []


def _check_kala_sarpa(planets: dict) -> list[dict]:
    """Kala Sarpa Yoga：所有 7 行星都在 Rahu-Ketu 軸的同一側（180° 內）"""
    rahu = planets.get("Rahu")
    ketu = planets.get("Ketu")
    if not rahu or not ketu:
        return []
    # 把 Rahu/Ketu 經度算出來（用宮位估算太粗，改用 sign+deg）
    sign_idx = {s: i for i, s in enumerate(SIGNS)}
    rahu_lon = sign_idx[rahu["sign"]] * 30 + rahu["deg"]
    ketu_lon = sign_idx[ketu["sign"]] * 30 + ketu["deg"]

    # 7 行星經度
    main_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    on_rahu_side = 0
    on_ketu_side = 0
    for p in main_planets:
        pl = planets.get(p)
        if not pl:
            continue
        lon = sign_idx[pl["sign"]] * 30 + pl["deg"]
        # 從 Rahu 順時針到 Ketu 是 180°
        diff = (lon - rahu_lon) % 360
        if diff < 180:
            on_rahu_side += 1
        else:
            on_ketu_side += 1

    if on_rahu_side == 7 or on_ketu_side == 7:
        side = "Rahu" if on_rahu_side == 7 else "Ketu"
        return [{
            "名稱": "Kala Sarpa",
            "中文": "卡爾沙帕（時蛇）Yoga",
            "性質": "雙面（凶中帶吉）",
            "說明": f"所有 7 行星都在 {side} 那一側",
            "意義": "人生有強烈的命運感、起伏大、特定領域有非常規成就，但情感連結與安穩感弱。常見於知名人物、突破常規的人",
        }]
    return []


def _check_vipareeta_raja(planets: dict, houses: dict) -> list[dict]:
    """Vipareeta Raja Yoga：6/8/12 宮主互相落在 6/8/12 宮"""
    dushtana_lords = {h: houses[h]["lord"] for h in DUSHTANAS if h in houses}
    found = []
    seen = set()
    for h, lord in dushtana_lords.items():
        pl = planets.get(lord)
        if not pl:
            continue
        if pl["house"] in DUSHTANAS:
            key = (lord, pl["house"])
            if key in seen:
                continue
            seen.add(key)
            found.append({
                "名稱": "Vipareeta Raja",
                "中文": f"反派王者 Yoga（{lord}）",
                "性質": "吉（凶轉吉）",
                "說明": f"{h} 宮主 {lord} 落在第 {pl['house']} 宮（凶宮）",
                "意義": "敵人 / 困難 / 損失反而成就你 — 透過危機、轉化、處理混亂局面而崛起",
            })
    return found


def _check_neecha_bhanga(planets: dict) -> list[dict]:
    """Neecha Bhanga Raja Yoga：落陷的取消條件（簡化版）

    條件（任一）：
    1. 落陷行星所在星座的守護星在 Lagna 或 Moon 的角宮
    2. 該星座的高揚行星在 Lagna 或 Moon 的角宮
    """
    moon = planets.get("Moon")
    moon_house = moon["house"] if moon else None
    found = []
    for planet, debil_sign in DEBILITATION.items():
        pl = planets.get(planet)
        if not pl or pl["sign"] != debil_sign:
            continue
        # 落陷星座的守護星
        debil_lord = SIGN_LORDS[debil_sign]
        debil_lord_pl = planets.get(debil_lord)
        # 在該星座高揚的行星
        exalt_planet = next((p for p, s in EXALTATION.items() if s == debil_sign), None)
        exalt_pl = planets.get(exalt_planet) if exalt_planet else None

        cancelled = False
        reasons = []
        # 條件 1
        if debil_lord_pl and debil_lord_pl["house"] in KENDRAS:
            cancelled = True
            reasons.append(f"落陷星座守護星 {debil_lord} 在角宮")
        if debil_lord_pl and moon_house and \
           ((debil_lord_pl["house"] - moon_house) % 12) in {0, 3, 6, 9}:
            cancelled = True
            reasons.append(f"落陷星座守護星 {debil_lord} 在月亮角宮")
        # 條件 2
        if exalt_pl and exalt_pl["house"] in KENDRAS:
            cancelled = True
            reasons.append(f"該星座高揚星 {exalt_planet} 在角宮")

        if cancelled:
            found.append({
                "名稱": "Neecha Bhanga Raja",
                "中文": f"落陷取消 Raja Yoga（{planet}）",
                "性質": "吉（弱轉強）",
                "說明": f"{planet} 在 {debil_sign}（落陷），但被取消：{', '.join(reasons)}",
                "意義": "原本的弱點反而成為這輩子最強的能量來源 — 不是補償，是真正的轉化",
            })
    return found


def _check_adhi(planets: dict) -> list[dict]:
    """Adhi Yoga：水星、木星、金星都在月亮的 6 / 7 / 8 宮（任一個）"""
    moon = planets.get("Moon")
    if not moon:
        return []
    target_houses = {_house_from(moon["house"], n) for n in (6, 7, 8)}
    benefics = ["Mercury", "Jupiter", "Venus"]
    if all(planets.get(p) and planets[p]["house"] in target_houses for p in benefics):
        return [{
            "名稱": "Adhi",
            "中文": "Adhi Yoga",
            "性質": "吉（領袖）",
            "說明": "水星、木星、金星都落在月亮的 6/7/8 宮",
            "意義": "領導力、富裕、長壽、被人尊敬",
        }]
    return []


def _check_sunapha_anapha_durudhara(planets: dict) -> list[dict]:
    """月亮的 2/12 宮有行星（除太陽）：
       - Sunapha：只有 2 宮有
       - Anapha：只有 12 宮有
       - Durudhara：兩邊都有
    """
    moon = planets.get("Moon")
    if not moon:
        return []
    h2 = _house_from(moon["house"], 2)
    h12 = _house_from(moon["house"], 12)
    others = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
    in_2 = [p for p in others if planets.get(p) and planets[p]["house"] == h2]
    in_12 = [p for p in others if planets.get(p) and planets[p]["house"] == h12]

    if in_2 and in_12:
        return [{
            "名稱": "Durudhara",
            "中文": "Durudhara Yoga",
            "性質": "吉",
            "說明": f"月亮兩側都有行星（2 宮：{', '.join(in_2)}；12 宮：{', '.join(in_12)}）",
            "意義": "物質豐裕、感官享受、舒適生活、貴人輔助",
        }]
    if in_2:
        return [{
            "名稱": "Sunapha",
            "中文": "Sunapha Yoga",
            "性質": "吉",
            "說明": f"月亮 2 宮有 {', '.join(in_2)}",
            "意義": "靠自身努力累積財富、智慧、聲譽",
        }]
    if in_12:
        return [{
            "名稱": "Anapha",
            "中文": "Anapha Yoga",
            "性質": "吉",
            "說明": f"月亮 12 宮有 {', '.join(in_12)}",
            "意義": "聲譽、外型出色、精神生活充實、適度享受",
        }]
    return []


def _check_kalanidhi(planets: dict) -> list[dict]:
    """Kalanidhi Yoga：木星在 2 宮或 5 宮，且與水星 / 金星合相或被其望"""
    jup = planets.get("Jupiter")
    mer = planets.get("Mercury")
    ven = planets.get("Venus")
    if not jup or jup["house"] not in {2, 5}:
        return []
    associated = []
    if mer and _aspect_or_conj("Jupiter", jup["house"], "Mercury", mer["house"]):
        associated.append("Mercury")
    if ven and _aspect_or_conj("Jupiter", jup["house"], "Venus", ven["house"]):
        associated.append("Venus")
    if not associated:
        return []
    return [{
        "名稱": "Kalanidhi",
        "中文": "藝術與學識 Yoga",
        "性質": "吉",
        "說明": f"木星在第 {jup['house']} 宮，與 {' + '.join(associated)} 連結",
        "意義": "藝術、音樂、學識、教育成就，能受智者尊重",
    }]


def _check_daridra(planets: dict, houses: dict) -> list[dict]:
    """Daridra Yoga（凶）：11 宮主在 6/8/12（凶宮）"""
    l11 = houses.get(11, {}).get("lord")
    if not l11:
        return []
    pl = planets.get(l11)
    if not pl:
        return []
    if pl["house"] in DUSHTANAS:
        return [{
            "名稱": "Daridra",
            "中文": "貧困 Yoga",
            "性質": "凶",
            "說明": f"11 宮主 {l11} 落在第 {pl['house']} 宮（凶宮）",
            "意義": "收入管道易受阻、不易留住財富、需特別經營資產配置",
        }]
    return []


def _check_maha_bhagya(natal: dict, planets: dict) -> list[dict]:
    """Maha Bhagya Yoga：
       - 男性：白天出生 + 太陽在奇座 + 月亮在奇座 + Lagna 在奇座
       - 女性：晚上出生 + 太陽在偶座 + 月亮在偶座 + Lagna 在偶座
       這裡簡化只判男性版（無性別資訊預設男性）"""
    sun = planets.get("Sun")
    moon = planets.get("Moon")
    lagna_house = natal.get("宮位", {}).get("第1宮", {})
    if not sun or not moon or not lagna_house:
        return []
    odd_signs = {"Ari", "Gem", "Leo", "Lib", "Sag", "Aqu"}
    if sun["sign"] in odd_signs and moon["sign"] in odd_signs and lagna_house["星座"] in odd_signs:
        return [{
            "名稱": "Maha Bhagya（男性版）",
            "中文": "大福氣 Yoga",
            "性質": "吉",
            "說明": "太陽、月亮、上升皆在奇數星座（男性版）",
            "意義": "整體運氣好、家境穩定、長壽、有貴人扶持",
        }]
    return []


def _check_sanyasa(planets: dict) -> list[dict]:
    """Sanyasa / Pravrajya Yoga（出家瑜伽）

    主要規則：
    A. **Pravrajya（4+ 行星合相）**：4 顆或更多 visible 行星合相在同一宮 →
       強烈出家傾向；最強的那顆決定派別（Pravrajya by 主導行星）
    B. **Sanyasa from Moon**：月亮在 9 / 12 宮 + 月亮 dispositor 被 Saturn 望或合 →
       靈性導向命格

    現代解讀：未必真出家，可能是「對世俗事物淡薄、走修行 / 心理 / 哲學路線」。
    """
    formed = []
    visible = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

    # ----- A. Pravrajya（4+ 行星合相）-----
    house_planets = {}
    for p in visible:
        if p in planets:
            h = planets[p].get("house") or planets[p].get("宮位")
            if h:
                house_planets.setdefault(int(h), []).append(p)

    for house, plist in house_planets.items():
        if len(plist) >= 4:
            # 簡化：先挑高揚的當主導，否則挑自宮，否則挑第一顆
            def _sign_of(p):
                s = planets[p].get("sign") or planets[p].get("星座", "")
                return s[:3]
            leader = None
            for cand in plist:
                if EXALTATION.get(cand) == _sign_of(cand):
                    leader = cand
                    break
            if leader is None:
                for cand in plist:
                    if _sign_of(cand) in OWN_SIGNS.get(cand, []):
                        leader = cand
                        break
            if leader is None:
                leader = plist[0]
            path = PRAVRAJYA_PATH.get(leader, "未明派別")
            formed.append({
                "名稱": "Pravrajya",
                "中文": f"{len(plist)} 行星合相 Yoga（出家傾向）",
                "性質": "中性（修行傾向）",
                "說明": f"{len(plist)} 行星（{', '.join(plist)}）合相於第 {house} 宮",
                "意義": f"靈性 / 哲學 / 出家命格，主導星 {leader} → {path}",
            })
            break  # 一個盤通常只成一次，不重複列

    # ----- B. Sanyasa from Moon（月亮 9/12 + Saturn 影響其 dispositor）-----
    moon = planets.get("Moon")
    saturn = planets.get("Saturn")
    if moon and saturn:
        moon_house = moon.get("house") or moon.get("宮位")
        moon_sign = moon.get("sign") or moon.get("星座", "")[:3]
        if moon_house in (9, 12) and moon_sign:
            disp = SIGN_LORDS.get(moon_sign)
            if disp and disp in planets:
                disp_house = planets[disp].get("house") or planets[disp].get("宮位")
                saturn_house = saturn.get("house") or saturn.get("宮位")
                if disp_house and saturn_house:
                    if _aspect_or_conj("Saturn", int(saturn_house), disp, int(disp_house)):
                        formed.append({
                            "名稱": "Sanyasa Yoga",
                            "中文": "土星影響月亮宮主 Yoga（出家傾向）",
                            "性質": "中性（靈性導向）",
                            "說明": f"月亮在第 {moon_house} 宮，其 dispositor {disp} 被 Saturn 望/合",
                            "意義": "心思偏向出世、研究、隱修；對世俗成就淡薄",
                        })

    return formed


def _tag_category(yoga: dict) -> dict:
    """對成立的 yoga 加上「分類」欄位，供下游分類彙整。
    名稱含括號變體（如 Maha Bhagya（男性版））用前綴匹配。"""
    name = yoga.get("名稱", "")
    cats = YOGA_CATEGORY.get(name)
    if cats is None:
        # 處理變體：用 startswith 去找前綴匹配
        for key, value in YOGA_CATEGORY.items():
            if name.startswith(key):
                cats = value
                break
    yoga["分類"] = cats or ["未分類"]
    return yoga


def _summarize_by_category(formed: list[dict]) -> dict:
    """彙整每個分類有幾個 yoga + 名稱清單。空分類不列。"""
    summary = {}
    for yoga in formed:
        for cat in yoga.get("分類", []):
            if cat not in summary:
                summary[cat] = {"數量": 0, "名稱": []}
            summary[cat]["數量"] += 1
            summary[cat]["名稱"].append(yoga.get("中文") or yoga.get("名稱"))
    return summary


def detect_yogas(natal: dict) -> dict:
    """從本命盤偵測所有 Yogas

    Args:
        natal: run_vedic_astro 回傳的 dict（含 行星 / 宮位 / 其他星體）

    Returns:
        {"已成立": [...], "分類彙整": {...}, "說明": "..."}
    """
    planets = _normalize_planets(natal)
    houses = _normalize_houses(natal)

    formed = []
    # 既有
    formed.extend(_check_pancha_mahapurusha(planets))
    formed.extend(_check_gajakesari(planets))
    formed.extend(_check_budha_aditya(planets))
    formed.extend(_check_chandra_mangal(planets))
    formed.extend(_check_lakshmi(planets, houses))
    formed.extend(_check_saraswati(planets))
    formed.extend(_check_kendra_trikona_raja(planets, houses))
    # Dhana yoga 多組宮主（含 2-11、5-9 與其他 8 組）
    formed.extend(_check_two_lord_yoga(
        planets, houses, 2, 11,
        "Dhana 2-11", "2-11 主合 Yoga", "吉（財富）",
        "正財累積、收入來源穩定、口才換錢",
    ))
    formed.extend(_check_two_lord_yoga(
        planets, houses, 5, 9,
        "Dhana 5-9", "5-9 主合 Yoga", "吉（財富 + 福德）",
        "前世福德帶來財富、創意 / 子女 / 投資管道順",
    ))
    for h_a, h_b, name, chinese, meaning in DHANA_PAIRS:
        formed.extend(_check_two_lord_yoga(
            planets, houses, h_a, h_b,
            name, chinese, "吉（財富）", meaning,
        ))
    # Raja yoga 補：事業福德雙合 / 家根福德
    formed.extend(_check_two_lord_yoga(
        planets, houses, 9, 10,
        "Dharma-Karmadhipati", "9-10 主合 Yoga（事業福德）", "吉（王者）",
        "事業帶來福德 / 福分助事業 — 升遷、貴人、領導機會",
    ))
    formed.extend(_check_two_lord_yoga(
        planets, houses, 4, 9,
        "Kahala", "4-9 主合 Yoga（家根福德）", "吉",
        "家庭穩定 + 學識深厚 — 靠根基和長輩貴人崛起",
    ))
    formed.extend(_check_kemadruma(planets))
    formed.extend(_check_shakata(planets))
    formed.extend(_check_kala_sarpa(planets))
    formed.extend(_check_vipareeta_raja(planets, houses))
    formed.extend(_check_neecha_bhanga(planets))
    formed.extend(_check_adhi(planets))
    formed.extend(_check_sunapha_anapha_durudhara(planets))
    formed.extend(_check_vasumati(planets))
    formed.extend(_check_solar_yogas(planets))
    formed.extend(_check_parivartana(planets))
    formed.extend(_check_kalanidhi(planets))
    formed.extend(_check_daridra(planets, houses))
    formed.extend(_check_maha_bhagya(natal, planets))
    formed.extend(_check_sanyasa(planets))
    # Dosha / 凶 yoga
    formed.extend(_check_mangal_dosha(planets))               # 1-off pattern: Mars in 特定宮
    formed.extend(_check_combust(planets))                    # 表驅動: COMBUSTION_ORB
    formed.extend(_check_conjunction_doshas(planets))         # 表驅動: CONJUNCTION_DOSHAS（6 種）
    formed.extend(_check_aspect_doshas(planets))              # 表驅動: ASPECT_DOSHAS（2 種）
    formed.extend(_check_karako_bhava_nashaya(planets))       # 內嵌表 (2 entries)

    # 對每個成立的 yoga 補上分類欄位
    formed = [_tag_category(y) for y in formed]

    return {
        "已成立": formed,
        "分類彙整": _summarize_by_category(formed),
        "說明": "Yoga 是 Vedic 占星的精華，比單看行星位置更能反映命格特質。吉性 Yoga 越多代表特定領域天賦越強，凶性 Yoga 是要警覺的人生主題",
    }
