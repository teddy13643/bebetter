"""
西洋地占術（Geomancy）排盤引擎。

16 個 figure 各為 4 排單/雙點（4-bit），
用 XOR 推導出完整 Shield Chart（15 figures）並排入 12 宮位。
"""

import hashlib
from datetime import datetime

# 16 figures：每個 figure 用 4-bit tuple 表示（1=單點, 2=雙點）
# 順序：Fire / Air / Water / Earth（從上到下）
FIGURES = {
    (1, 1, 1, 1): {
        "latin": "Via",
        "name": "道路",
        "meaning": "移動、變化、旅程",
        "planet": "Moon",
        "element": "Water",
        "zodiac": "Cancer",
        "reversed": False,
    },
    (2, 2, 2, 2): {
        "latin": "Populus",
        "name": "群眾",
        "meaning": "群體、被動、等待",
        "planet": "Moon",
        "element": "Water",
        "zodiac": "Cancer",
        "reversed": False,
    },
    (1, 1, 2, 2): {
        "latin": "Carcer",
        "name": "牢獄",
        "meaning": "限制、束縛、穩定",
        "planet": "Saturn",
        "element": "Earth",
        "zodiac": "Capricorn",
        "reversed": False,
    },
    (2, 2, 1, 1): {
        "latin": "Conjunctio",
        "name": "結合",
        "meaning": "聯繫、交流、合作",
        "planet": "Mercury",
        "element": "Air",
        "zodiac": "Virgo",
        "reversed": False,
    },
    (1, 2, 2, 1): {
        "latin": "Fortuna Major",
        "name": "大吉",
        "meaning": "成功、保護、內在力量",
        "planet": "Sun",
        "element": "Fire",
        "zodiac": "Leo",
        "reversed": False,
    },
    (2, 1, 1, 2): {
        "latin": "Fortuna Minor",
        "name": "小吉",
        "meaning": "快速成功、外在助力、短暫",
        "planet": "Sun",
        "element": "Fire",
        "zodiac": "Leo",
        "reversed": True,
    },
    (1, 2, 1, 2): {
        "latin": "Acquisitio",
        "name": "獲得",
        "meaning": "獲利、收穫、擴張",
        "planet": "Jupiter",
        "element": "Fire",
        "zodiac": "Sagittarius",
        "reversed": False,
    },
    (2, 1, 2, 1): {
        "latin": "Amissio",
        "name": "損失",
        "meaning": "失去、放手、流出",
        "planet": "Venus",
        "element": "Fire",
        "zodiac": "Taurus",
        "reversed": True,
    },
    (2, 1, 2, 2): {
        "latin": "Laetitia",
        "name": "喜悅",
        "meaning": "快樂、上升、樂觀",
        "planet": "Jupiter",
        "element": "Fire",
        "zodiac": "Pisces",
        "reversed": False,
    },
    (2, 2, 1, 2): {
        "latin": "Tristitia",
        "name": "悲傷",
        "meaning": "憂鬱、下沉、困難",
        "planet": "Saturn",
        "element": "Earth",
        "zodiac": "Aquarius",
        "reversed": True,
    },
    (1, 2, 2, 2): {
        "latin": "Albus",
        "name": "白",
        "meaning": "智慧、純淨、深思",
        "planet": "Mercury",
        "element": "Air",
        "zodiac": "Gemini",
        "reversed": False,
    },
    (2, 2, 2, 1): {
        "latin": "Rubeus",
        "name": "紅",
        "meaning": "激情、危險、暴力",
        "planet": "Mars",
        "element": "Fire",
        "zodiac": "Scorpio",
        "reversed": True,
    },
    (1, 1, 2, 1): {
        "latin": "Puella",
        "name": "少女",
        "meaning": "美麗、和諧、被動的吸引",
        "planet": "Venus",
        "element": "Water",
        "zodiac": "Libra",
        "reversed": False,
    },
    (1, 2, 1, 1): {
        "latin": "Puer",
        "name": "少年",
        "meaning": "衝動、攻擊、主動",
        "planet": "Mars",
        "element": "Fire",
        "zodiac": "Aries",
        "reversed": True,
    },
    (2, 1, 1, 1): {
        "latin": "Caput Draconis",
        "name": "龍首",
        "meaning": "開始、進入、上升",
        "planet": "North Node",
        "element": "Earth",
        "zodiac": "Virgo",
        "reversed": False,
    },
    (1, 1, 1, 2): {
        "latin": "Cauda Draconis",
        "name": "龍尾",
        "meaning": "結束、離開、下降",
        "planet": "South Node",
        "element": "Fire",
        "zodiac": "Sagittarius",
        "reversed": True,
    },
}


def _xor_row(a: int, b: int) -> int:
    """兩個值相加，奇數→1（單點），偶數→2（雙點）"""
    total = a + b
    return 1 if total % 2 == 1 else 2


def _xor_figure(fig_a: tuple, fig_b: tuple) -> tuple:
    """逐排 XOR 產生新 figure"""
    return tuple(_xor_row(a, b) for a, b in zip(fig_a, fig_b))


def _figure_info(bits: tuple) -> dict:
    """查表取得 figure 詳細資訊"""
    info = FIGURES.get(bits, {})
    return {
        "bits": list(bits),
        "dots": "".join("." if b == 1 else ".." for b in bits),
        "latin": info.get("latin", "Unknown"),
        "name": info.get("name", "未知"),
        "meaning": info.get("meaning", ""),
        "planet": info.get("planet", ""),
        "element": info.get("element", ""),
        "zodiac": info.get("zodiac", ""),
    }


def _generate_mothers(seed: str) -> list[tuple]:
    """
    從種子字串產生 4 個 Mother figure。
    用 SHA-256 取 16 bits（4 figures × 4 rows），奇數→單點，偶數→雙點。
    """
    h = hashlib.sha256(seed.encode()).hexdigest()
    bits = []
    for char in h[:16]:
        val = int(char, 16)
        bits.append(1 if val % 2 == 1 else 2)

    mothers = []
    for i in range(4):
        mothers.append(tuple(bits[i * 4:(i + 1) * 4]))
    return mothers


# 12 宮位含義
HOUSE_MEANINGS = {
    1: "自己、提問者、整體狀態",
    2: "財務、資源、個人價值",
    3: "溝通、短途旅行、兄弟姊妹",
    4: "家庭、根基、結局",
    5: "創造、戀愛、子女、娛樂",
    6: "健康、工作、日常事務",
    7: "伴侶、對手、合作關係",
    8: "危機、死亡與重生、共享資源",
    9: "遠行、學習、信仰、法律",
    10: "事業、社會地位、權威",
    11: "朋友、社群、願望",
    12: "隱藏、敵人、自我毀滅",
}


def run_geomancy(
    question: str = "",
    seed: str | None = None,
    manual_mothers: list[list[int]] | None = None,
) -> dict:
    """
    地占排盤。

    參數:
      question: 想問的問題
      seed: 隨機種子（預設用當前 timestamp）
      manual_mothers: 手動輸入 4 個 mother figure，每個為 [1or2, 1or2, 1or2, 1or2]

    回傳完整 Shield Chart + 12 宮位配置。
    """
    # 產生 4 個 Mother
    if manual_mothers:
        mothers = [tuple(m) for m in manual_mothers[:4]]
        if len(mothers) < 4:
            raise ValueError("需要 4 個 Mother figure")
    else:
        if seed is None:
            # 用時辰（2 小時一個單位）當種子，同一時辰同一問題 = 同一盤
            now = datetime.now()
            shichen = now.hour // 2
            seed = f"{now.year}-{now.month}-{now.day}-{shichen}-{question}"
        mothers = _generate_mothers(seed)

    # 推導 4 個 Daughter：轉置 Mother 的排
    # Daughter 1 = Mother 1~4 的第 1 排，Daughter 2 = 第 2 排，依此類推
    daughters = []
    for row_idx in range(4):
        daughters.append(tuple(mothers[m][row_idx] for m in range(4)))

    # 推導 4 個 Niece（姪輩）：相鄰兩個 XOR
    all_eight = mothers + daughters
    nieces = []
    for i in range(0, 8, 2):
        nieces.append(_xor_figure(all_eight[i], all_eight[i + 1]))

    # 推導 2 個 Witness（證人）
    right_witness = _xor_figure(nieces[0], nieces[1])
    left_witness = _xor_figure(nieces[2], nieces[3])

    # 推導 Judge（法官）
    judge = _xor_figure(right_witness, left_witness)

    # Reconciler（調解者）：Judge XOR 第一個 Mother（提問者的 figure）
    reconciler = _xor_figure(judge, mothers[0])

    # 組裝 Shield Chart
    chart_figures = {
        "mothers": [_figure_info(m) for m in mothers],
        "daughters": [_figure_info(d) for d in daughters],
        "nieces": [_figure_info(n) for n in nieces],
        "right_witness": _figure_info(right_witness),
        "left_witness": _figure_info(left_witness),
        "judge": _figure_info(judge),
        "reconciler": _figure_info(reconciler),
    }

    # 排入 12 宮位（傳統順序：Mother 1~4 → House 1,2,3,4；Daughter 1~4 → House 5,6,7,8 等）
    # 常見的排列：M1→H1, M2→H2, M3→H3, M4→H4, D1→H5, D2→H6, D3→H7, D4→H8,
    #             N1→H9, N2→H10, N3→H11, N4→H12
    house_figures = mothers + daughters + nieces
    houses = []
    for i, fig in enumerate(house_figures, 1):
        info = _figure_info(fig)
        info["house"] = i
        info["house_meaning"] = HOUSE_MEANINGS[i]
        houses.append(info)

    # 判斷整體吉凶傾向
    judge_info = FIGURES.get(judge, {})
    favorability = "吉" if not judge_info.get("reversed", False) else "凶"

    return {
        "question": question,
        "shield_chart": chart_figures,
        "houses": houses,
        "judge_summary": {
            "figure": _figure_info(judge),
            "favorability": favorability,
            "note": "Judge 是整個盤面的最終裁決，代表問題的核心答案",
        },
        "witnesses": {
            "right": {
                **_figure_info(right_witness),
                "note": "右證人代表過去/提問者一方的情況",
            },
            "left": {
                **_figure_info(left_witness),
                "note": "左證人代表未來/對方的情況",
            },
        },
        "reconciler": {
            **_figure_info(reconciler),
            "note": "調解者顯示事態最終的走向與收尾方式",
        },
    }
