"""輔助命盤：Chandra Lagna（身宮盤）+ Surya Lagna（太陽盤）

Vedic 經典強調除了上升盤（Lagna chart），還要看：
- **Chandra Lagna 身宮盤**：以月亮所在星座為第 1 宮，重排 12 宮
  → 反映情感層面、母系業力、Dasha 對心理的衝擊
- **Surya Lagna 太陽盤**：以太陽所在星座為第 1 宮
  → 反映父親 / 自我認同 / 社會角色

實作：行星位置不變，只重編宮位編號。Whole Sign 系統下，這就是把
某顆行星的星座當作 House 1，其他星座順序排成 House 2-12。
"""

from core.vedic_constants import SIGNS


def _normalize_sign(sign: str) -> str:
    """處理 'Aries' / 'Ari' / 'Cap' 等不同寫法 → 標準 3 字縮寫"""
    return sign[:3] if sign else ""


def _sign_idx(sign: str) -> int:
    sign = _normalize_sign(sign)
    return SIGNS.index(sign) if sign in SIGNS else 0


def _house_of_sign_from_lagna(planet_sign: str, lagna_sign: str) -> int:
    """Whole Sign：行星所在星座，從 lagna 起算第幾宮（1-12）"""
    p_idx = _sign_idx(planet_sign)
    l_idx = _sign_idx(lagna_sign)
    return ((p_idx - l_idx) % 12) + 1


def build_lagna_chart(natal: dict, lagna_planet: str) -> dict:
    """以指定行星所在星座為第 1 宮，重編 12 宮鏡像盤

    Args:
        natal: D1 本命盤 result dict（含「行星」「宮位」）
        lagna_planet: "Moon" 或 "Sun"

    Returns:
        {
            "Lagna_行星": "Moon",
            "Lagna_星座": "Sag",
            "行星": {planet → {...原欄位 + 新宮位}},
            "宮位": {第N宮: {星座, 主題提示}},
        }
    """
    planets_src = natal.get("行星", {})
    if lagna_planet not in planets_src:
        return {"error": f"找不到 {lagna_planet}"}

    lagna_sign = _normalize_sign(planets_src[lagna_planet].get("星座", ""))
    if not lagna_sign:
        return {"error": f"{lagna_planet} 沒有星座資料"}

    # 重編行星宮位
    new_planets = {}
    for name, data in planets_src.items():
        psign = _normalize_sign(data.get("星座", ""))
        if not psign:
            continue
        new_house = _house_of_sign_from_lagna(psign, lagna_sign)
        new_planets[name] = {
            **{k: v for k, v in data.items() if k != "宮位"},
            "宮位": new_house,
        }

    # 重編宮位
    l_idx = _sign_idx(lagna_sign)
    new_houses = {}
    for i in range(12):
        sign = SIGNS[(l_idx + i) % 12]
        new_houses[f"第{i + 1}宮"] = {"星座": sign}

    return {
        "Lagna_行星": lagna_planet,
        "Lagna_星座": lagna_sign,
        "說明": (
            "Chandra Lagna 以月亮為命宮，反映情感 / 心理 / 母系；"
            "Surya Lagna 以太陽為命宮，反映自我 / 父親 / 社會角色。"
            "Vedic 經典要求 Lagna + Chandra + Surya 三盤交叉看，落在三盤都凶的宮 = 真凶。"
        ) if lagna_planet in ("Moon", "Sun") else "",
        "行星": new_planets,
        "宮位": new_houses,
    }


def build_chandra_and_surya_lagna(natal: dict) -> dict:
    """一次產出身宮盤 + 太陽盤"""
    return {
        "身宮盤_Chandra_Lagna": build_lagna_chart(natal, "Moon"),
        "太陽盤_Surya_Lagna":   build_lagna_chart(natal, "Sun"),
    }
