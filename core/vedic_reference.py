"""Vedic 對照表彙整 — API 對外暴露的 single source of truth

把散在 vedic_constants / vedic_karaka / vedic_yogas 的所有對照表
打包成一份 dict，由 GET /vedic/reference 一次回傳。

呼叫端（skill / sub-agent / 外部 caller）需要查表時直接 GET，
不要從 source code 推、不要憑 LLM 記憶。
"""

from core.vedic_constants import (
    NAKSHATRAS, DASHA_ORDER, DASHA_YEARS, SIGNS, PLANET_NAMES_ZH, SIGN_NAMES_ZH,
    GOCHAR_RULES, EXALTATION, DEBILITATION, SIGN_LORDS, OWN_SIGNS,
    SIGN_ELEMENTS, NAVAMSA_ELEMENT_START, NAISARGIKA_MAITRI,
    COMBUSTION_ORB, YOGA_KARAKAS, MARAKA_HOUSES, MARANA_KARAKA_STHANA,
    VARGA_INFO, BHAVA_KARAKA, FUNCTIONAL_NATURE_BY_ASC, FUNCTIONAL_NATURE_ZH,
    NAISARGIKA_BALA, DIK_BALA_STRONG_HOUSE, EXALTATION_DEGREE,
)
from core.vedic_karaka import KARAKA_ROLES, KARAKA_PLANETS, PLANET_DEITIES, DUAL_LORDS
from core.vedic_yogas import (
    YOGA_CATEGORY, KENDRAS, TRIKONAS, DUSHTANAS, SPECIAL_ASPECTS,
    DHANA_PAIRS, CONJUNCTION_DOSHAS, ASPECT_DOSHAS, PRAVRAJYA_PATH,
)
from core.vedic_shadbala import SHADBALA_REQUIRED, PLANET_GENDER
from core.vedic_nabhasa import (
    ASHRAYA_YOGAS, DALA_YOGAS, AKRITI_YOGAS, SANKHYA_YOGAS,
    MOVABLE_SIGNS, FIXED_SIGNS, DUAL_SIGNS,
)


# 自然 Karaka（Naisargika Karaka）— 9 行星固定主題（散在 skill md 但沒在 const，補上）
NAISARGIKA_KARAKA = {
    "Sun":     ["靈魂", "父親", "權威", "生命力", "心臟"],
    "Moon":    ["心智", "母親", "情緒", "群眾", "胃"],
    "Mars":    ["勇氣", "兄弟", "土地", "戰鬥", "意外"],
    "Mercury": ["智力", "溝通", "商業", "學習", "皮膚"],
    "Jupiter": ["智慧", "子女", "老師", "宗教", "肝"],
    "Venus":   ["配偶", "美", "藝術", "享樂", "腎"],
    "Saturn":  ["長壽", "苦難", "紀律", "勞工", "骨骼"],
    "Rahu":    ["欲望", "外國", "創新", "毒物", "幻覺"],
    "Ketu":    ["解脫", "靈性", "祖先", "意外", "皮疹"],
}

# AK 在不同宮位的含義（散在 skill md，補進 API）
AK_HOUSE_MEANING = {
    1:  "身體 / 自我 — 直接活成自己",
    2:  "智識 / 聲音 / 表達 — 用話語兌現靈魂",
    3:  "勇氣 / 努力 — 靠雙手打出來",
    4:  "家庭 / 內在安穩 — 從根基出發",
    5:  "創造 / 性魅力 / 子女 — 透過創作展現靈魂",
    6:  "服務 / 對抗困難 — 在挑戰中精煉",
    7:  "關係 / 合夥 — 透過他人映照自己",
    8:  "轉化 / 神秘 — 經歷死亡與重生",
    9:  "法性 / 高等學習 — 走師者 / 哲學家路",
    10: "事業 / 公眾 — 在社會舞台兌現",
    11: "成就 / 群體 — 在大群體中影響",
    12: "解脫 / 修行 — 走出世修行路",
}

# Karakamsa 三神宮位定義（從 KL 算起）
KARAKAMSA_DEVATA_HOUSES = {
    "Ishta_Devata":  {"宮位": 12, "中文": "本尊神 / 靈性核心修行對象", "意義": "解脫宮，主管此生靈性最高目標、修行方向、與神契合的途徑"},
    "Dharma_Devata": {"宮位": 9,  "中文": "法性神 / 生命使命指引",     "意義": "法性宮，主管此生使命、信念、值得追隨的智慧傳承"},
    "Pala_Devata":   {"宮位": 6,  "中文": "守護神 / 對抗業力的力量",   "意義": "障礙宮，主管化解業力、克服敵手與疾病的守護力量"},
}


def get_full_reference() -> dict:
    """回傳完整對照表 — 一次給齊，呼叫端自己挑要用的部分。

    結構分區：
      planets    — 9 行星基本對照
      signs      — 12 星座主管 / 元素 / 友敵
      dignities  — 高揚 / 落陷 / 廟旺 / Yoga Karaka / MKS / 燃燒
      nakshatras — 27 宿表
      dashas     — Vimshottari + Char Dasha 規則
      vargas     — 17 張分盤定義
      karakas    — 自然 + Char Karaka + AK 宮位含義
      devatas    — 行星 → 神祇對照 + Karakamsa 三神 + 共主管
      yogas      — Yoga 分類大全 + 角宮 / 三方 / 凶宮 + 特殊相位 + Dhana / Dosha
      gochar     — 月行運 1-12 宮吉凶
      house_groups — 宮位分類（Maraka 等）
    """
    return {
        "planets": {
            "名稱_zh": PLANET_NAMES_ZH,
            "Char_Karaka_用": KARAKA_PLANETS,
            "說明": "Vedic 9 行星（含 Rahu/Ketu）。Char Karaka 系統只用 7 顆主行星",
        },
        "signs": {
            "代碼": SIGNS,
            "名稱_zh": SIGN_NAMES_ZH,
            "主管": SIGN_LORDS,
            "共主管": DUAL_LORDS,
            "元素": SIGN_ELEMENTS,
            "Navamsa_元素起點": NAVAMSA_ELEMENT_START,
            "自然友敵_Naisargika_Maitri": NAISARGIKA_MAITRI,
            "說明": "天蠍 / 水瓶有共主管（傳統 + 節點），Devata 計算時兩個都列",
        },
        "dignities": {
            "高揚_Exaltation": EXALTATION,
            "落陷_Debilitation": DEBILITATION,
            "廟宮_Own_Sign_Moolatrikona": OWN_SIGNS,
            "Yoga_Karaka": YOGA_KARAKAS,
            "Marana_Karaka_Sthana_MKS": MARANA_KARAKA_STHANA,
            "燃燒範圍_Combustion_Orb_度": COMBUSTION_ORB,
            "說明": "dignity 力量排序：高揚 > 廟旺 > 一般 > 落陷。MKS = 該行星在哪一宮會喪失功能",
        },
        "nakshatras": {
            "列表": [
                {"序號": i + 1, "名稱": name, "中文": zh, "守護星": ruler}
                for i, (name, zh, ruler) in enumerate(NAKSHATRAS)
            ],
            "說明": "27 個月亮星宿，每宿跨 13.33°。守護星決定 Vimshottari Dasha 起點",
        },
        "dashas": {
            "Vimshottari_順序": DASHA_ORDER,
            "Vimshottari_年數": DASHA_YEARS,
            "說明": "Vimshottari 從月亮 nakshatra 守護星起跑，總週期 120 年",
        },
        "vargas": {
            "資訊": VARGA_INFO,
            "說明": "17 張分盤（D2/D3/D4/D6/D7/D8/D9/D10/D12/D16/D20/D24/D27/D30/D40/D45/D60）",
        },
        "karakas": {
            "自然_Naisargika": NAISARGIKA_KARAKA,
            "Char_Karaka_角色": [
                {"代碼": code, "名稱": name, "中文": zh, "意義": meaning}
                for code, name, zh, meaning in KARAKA_ROLES
            ],
            "AK_宮位含義": AK_HOUSE_MEANING,
            "說明": "AK 度數最高 → 靈魂主軸；其他角色按度數遞減分配",
        },
        "devatas": {
            "行星_神祇對照": PLANET_DEITIES,
            "Karakamsa_三神宮位": KARAKAMSA_DEVATA_HOUSES,
            "計算步驟": [
                "1. 從 Char_Karakas 取 AK",
                "2. 從 D-9 盤取 AK 落的星座 = Karakamsa Lagna (KL)",
                "3. 從 KL 算 12/9/6 宮的星座",
                "4. 該星座的主管行星 → 對應神祇即三神",
                "5. 共主管星座（Sco/Aqu）兩個主管都列，由使用者選共鳴的那位",
            ],
            "使用紅線": "用『冥想觀想 / 內在原型』框架介紹，不要叫用戶『去拜』",
        },
        "yogas": {
            "分類": YOGA_CATEGORY,
            "宮位分類": {
                "角宮_Kendra": sorted(KENDRAS),
                "三方宮_Trikona": sorted(TRIKONAS),
                "凶宮_Dushthana": sorted(DUSHTANAS),
            },
            "特殊相位": SPECIAL_ASPECTS,
            "Dhana_Pairs_財富組合": [
                {"宮主A": a, "宮主B": b, "名稱": name, "副標": label, "意義": meaning}
                for a, b, name, label, meaning in DHANA_PAIRS
            ],
            "Conjunction_Doshas_合相凶相": [
                {"組合": list(d) if isinstance(d, (tuple, list)) else d}
                for d in CONJUNCTION_DOSHAS
            ],
            "Aspect_Doshas_相位凶相": [
                {"組合": list(d) if isinstance(d, (tuple, list)) else d}
                for d in ASPECT_DOSHAS
            ],
            "說明": "成立條件複雜，個人盤偵測請呼叫 POST /vedic/natal 取 Yogas.已成立",
        },
        "gochar": {
            "規則": {p: {str(h): v for h, v in rules.items()} for p, rules in GOCHAR_RULES.items()},
            "說明": "從月亮起算第 N 宮的吉凶（True=吉, False=凶）。Vedic 流月主要工具",
        },
        "house_groups": {
            "Maraka": MARAKA_HOUSES,
            "說明": "Maraka 宮位的宮主 = 殺星，傳統用於壽命判斷",
        },
        "bhava_karakas": {
            "對照表": {
                str(h): {
                    "主代表星":  info["primary"],
                    "次代表星":  info["secondary"],
                    "主題":     info["theme"],
                }
                for h, info in BHAVA_KARAKA.items()
            },
            "說明": "Parashara 系統 — 12 宮的天然代言行星。分析該宮主題時兼看宮主星 + Bhava Karaka",
        },
        "functional_nature": {
            "對照表": FUNCTIONAL_NATURE_BY_ASC,
            "性質中文": FUNCTIONAL_NATURE_ZH,
            "說明": (
                "依上升星座決定每行星的功能吉凶（BPHS Kendra-Trikona 規則）。"
                "yogakaraka = 同掌角宮 + 三方宮，最強吉星。"
                "Rahu/Ketu 不在表中（依合相 / dispositor 動態判斷）"
            ),
        },
        "shadbala": {
            "Naisargika_Bala_自然力": NAISARGIKA_BALA,
            "Dik_Bala_最強角宮": DIK_BALA_STRONG_HOUSE,
            "高揚精確點": {p: {"sign_idx": s, "deg": d} for p, (s, d) in EXALTATION_DEGREE.items()},
            "最低需求_Required_Bala_V": SHADBALA_REQUIRED,
            "行星陰陽": PLANET_GENDER,
            "六項分類": [
                "Sthana 位置（5 子項：Uchcha / Saptavargaja / Ojayugma / Kendradi / Drekkana）",
                "Dik 方位",
                "Kala 時間（簡化版：Natonnata + Paksha）",
                "Cheshta 動態",
                "Naisargika 自然（查表）",
                "Drig 相位",
            ],
            "說明": "單位 Virupa（V），1 Rupa = 60 V。達成率 ≥ 1.0 = 該行星主題能正常發揮",
        },
        "nabhasa": {
            "Ashraya_依託_3類": [
                {"名稱": n, "中文": z, "星座": sorted(s), "意涵": m}
                for n, z, s, m in ASHRAYA_YOGAS
            ],
            "Dala_行列_2類": [
                {"名稱": n, "中文": z, "規則代碼": r, "意涵": m}
                for n, z, r, m in DALA_YOGAS
            ],
            "Akriti_形態_20類": [
                {"名稱": n, "中文": z, "規則類型": r, "意涵": m}
                for n, z, r, _, m in AKRITI_YOGAS
            ],
            "Sankhya_數量_7類": {
                str(k): {"名稱": v[0], "中文": v[1], "意涵": v[2]}
                for k, v in SANKHYA_YOGAS.items()
            },
            "活動性星座": {
                "活動_movable": sorted(MOVABLE_SIGNS),
                "固定_fixed":   sorted(FIXED_SIGNS),
                "變動_dual":    sorted(DUAL_SIGNS),
            },
            "說明": "32 種 Nabhasa Yoga，看 7 visible 行星整體分布幾何 — 命格的整體形狀",
        },
        "sanyasa": {
            "Pravrajya_主導行星派別": PRAVRAJYA_PATH,
            "說明": "4+ 行星合相時最強的那顆決定派別。現代解讀：未必出家，可能淡薄世俗 / 修行 / 哲學路線",
        },
    }
