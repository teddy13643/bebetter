"""Ashtakavarga（八分系統）

每顆行星在 12 個星座的「能量點數」，由 8 個觀察者
（7 行星 + Asc）按 BPHS 規則給分。

用途：
- BAV（單行星表）：行星 transit 經過高分星座 → 該行星意義會發生
- SAV（總表）：某星座總分高 → 對應宮位這輩子會被反覆啟動
- 跟 transit 結合 → 「具體哪個月」的答案
"""

from core.vedic_constants import SIGNS, SIGN_NAMES_ZH

# 規則：{ 受益行星: { 貢獻者: [從貢獻者算第幾宮給 1 分] } }
# 「第 N 宮」= 從貢獻者所在星座（=第 1 宮）順數的第 N 個星座
ASHTAKAVARGA_RULES = {
    "Sun": {
        "Sun":     [1, 2, 4, 7, 8, 9, 10, 11],
        "Moon":    [3, 6, 10, 11],
        "Mars":    [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury": [3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [5, 6, 9, 11],
        "Venus":   [6, 7, 12],
        "Saturn":  [1, 2, 4, 7, 8, 9, 10, 11],
        "Asc":     [3, 4, 6, 10, 11, 12],
    },
    "Moon": {
        "Sun":     [3, 6, 7, 8, 10, 11],
        "Moon":    [1, 3, 6, 7, 10, 11],
        "Mars":    [2, 3, 5, 6, 9, 10, 11],
        "Mercury": [1, 3, 4, 5, 7, 8, 10, 11],
        "Jupiter": [1, 4, 7, 8, 10, 11, 12],
        "Venus":   [3, 4, 5, 7, 9, 10, 11],
        "Saturn":  [3, 5, 6, 11],
        "Asc":     [3, 6, 10, 11],
    },
    "Mars": {
        "Sun":     [3, 5, 6, 10, 11],
        "Moon":    [3, 6, 11],
        "Mars":    [1, 2, 4, 7, 8, 10, 11],
        "Mercury": [3, 5, 6, 11],
        "Jupiter": [6, 10, 11, 12],
        "Venus":   [6, 8, 11, 12],
        "Saturn":  [1, 4, 7, 8, 9, 10, 11],
        "Asc":     [1, 3, 6, 10, 11],
    },
    "Mercury": {
        "Sun":     [5, 6, 9, 11, 12],
        "Moon":    [2, 4, 6, 8, 10, 11],
        "Mars":    [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury": [1, 3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [6, 8, 11, 12],
        "Venus":   [1, 2, 3, 4, 5, 8, 9, 11],
        "Saturn":  [1, 2, 4, 7, 8, 9, 10, 11],
        "Asc":     [1, 2, 4, 6, 8, 10, 11],
    },
    "Jupiter": {
        "Sun":     [1, 2, 3, 4, 7, 8, 9, 10, 11],
        "Moon":    [2, 5, 7, 9, 11],
        "Mars":    [1, 2, 4, 7, 8, 10, 11],
        "Mercury": [1, 2, 4, 5, 6, 9, 10, 11],
        "Jupiter": [1, 2, 3, 4, 7, 8, 10, 11],
        "Venus":   [2, 5, 6, 9, 10, 11],
        "Saturn":  [3, 5, 6, 12],
        "Asc":     [1, 2, 4, 5, 6, 7, 9, 10, 11],
    },
    "Venus": {
        "Sun":     [8, 11, 12],
        "Moon":    [1, 2, 3, 4, 5, 8, 9, 11, 12],
        "Mars":    [3, 4, 6, 9, 11, 12],
        "Mercury": [3, 5, 6, 9, 11],
        "Jupiter": [5, 8, 9, 10, 11],
        "Venus":   [1, 2, 3, 4, 5, 8, 9, 10, 11],
        "Saturn":  [3, 4, 5, 8, 9, 10, 11],
        "Asc":     [1, 2, 3, 4, 5, 8, 9, 11],
    },
    "Saturn": {
        "Sun":     [1, 2, 4, 7, 8, 10, 11],
        "Moon":    [3, 6, 11],
        "Mars":    [3, 5, 6, 10, 11, 12],
        "Mercury": [6, 8, 9, 10, 11, 12],
        "Jupiter": [5, 6, 11, 12],
        "Venus":   [6, 11, 12],
        "Saturn":  [3, 5, 6, 11],
        "Asc":     [1, 3, 4, 6, 10, 11],
    },
}

# BPHS 標準每顆行星 BAV 滿分（驗證用）
EXPECTED_BAV_TOTAL = {
    "Sun": 48, "Moon": 49, "Mars": 39, "Mercury": 54,
    "Jupiter": 56, "Venus": 52, "Saturn": 39,
}

CONTRIBUTORS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Asc"]


def _sign_to_idx(sign: str) -> int:
    """星座縮寫 → 0-11 index"""
    return SIGNS.index(sign)


def _calc_single_bav(receiver: str, contributor_signs: dict) -> dict:
    """算單一行星的 BAV：12 星座各得幾分

    contributor_signs: {"Sun": 8, "Moon": 7, ..., "Asc": 1}（sign idx 0-11）
    回傳：{"Ari": 3, "Tau": 5, ...}
    """
    points = [0] * 12
    rules = ASHTAKAVARGA_RULES[receiver]
    for contrib, sidx in contributor_signs.items():
        houses = rules.get(contrib, [])
        for h in houses:
            target_sidx = (sidx + h - 1) % 12
            points[target_sidx] += 1
    return {SIGNS[i]: points[i] for i in range(12)}


def calc_ashtakavarga(planets: dict, ascendant_sign: str) -> dict:
    """從本命行星 + 上升星座算 Ashtakavarga。

    planets: {"Sun": {"星座": "Sag", ...}, ...}
    ascendant_sign: 上升星座縮寫（如 "Sco"）

    回傳：{
        "BAV": {"Sun": {"Ari": 3, ...}, "Moon": {...}, ...},
        "SAV": {"Ari": 28, ...},  # 7 顆行星 BAV 加總
        "BAV_總分": {"Sun": 48, ...},
        "SAV_總分": 337,
        "說明": "...",
    }
    """
    contributor_signs = {"Asc": _sign_to_idx(ascendant_sign)}
    for name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        p = planets.get(name)
        if p is None:
            return {"error": f"缺少行星 {name}"}
        contributor_signs[name] = _sign_to_idx(p["星座"])

    bav = {}
    bav_totals = {}
    for receiver in EXPECTED_BAV_TOTAL.keys():
        single = _calc_single_bav(receiver, contributor_signs)
        bav[receiver] = single
        bav_totals[receiver] = sum(single.values())

    sav = {sign: 0 for sign in SIGNS}
    for receiver_table in bav.values():
        for sign, pts in receiver_table.items():
            sav[sign] += pts

    return {
        "BAV": bav,
        "SAV": sav,
        "BAV_總分": bav_totals,
        "SAV_總分": sum(sav.values()),
        "星座中文": SIGN_NAMES_ZH,
        "用法": {
            "BAV": "行星 transit 過高分（≥5）星座 → 該行星帶來的事容易發生",
            "SAV": "某星座 ≥30 分 → 該宮位人生重點；<25 分 → 該領域單薄",
            "Transit_combo": "transit 行星進入 BAV ≥5 + SAV ≥30 的星座 → 該月份事件強度高",
        },
    }
