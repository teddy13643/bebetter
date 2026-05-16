"""跨模組整合 hint — sub-agent 拿去組故事用的「素材」

把 Bhava_Karakas / Functional_Nature / Shadbala / dignity 多個欄位
做交叉整理，產出三類 hint：

1. 多重 Bhava Karaka 排名 — 哪顆星擔當多個宮的代表星，影響擴散最大
2. 主軸候選 — functional benefic + Shadbala 達標的行星
3. 雙重要警惕 — functional malefic + dignity 強的行星（凶的影響被放大）

設計原則：
- 提供素材，不下結論。用「候選 / 提示」字眼，留給 sub-agent 解讀空間。
- 不做三維 trade-off 判讀（如「方向對但費力」），避免過度 framing。
"""

from core.vedic_constants import BHAVA_KARAKA, FUNCTIONAL_NATURE_BY_ASC


def calc_cross_insights(natal: dict) -> dict:
    """從本命盤的多個欄位交叉產出整合 hint"""
    planets = natal.get("行星", {})
    asc_sign = natal.get("宮位", {}).get("第1宮", {}).get("星座", "")[:3]
    fn_table = FUNCTIONAL_NATURE_BY_ASC.get(asc_sign, {})
    shadbala = natal.get("Shadbala", {})

    # ===== 多重 Bhava Karaka 排名 =====
    # 對每顆行星，反查 BHAVA_KARAKA 表，列出它擔當哪些宮的主代表星
    planet_to_houses = {}
    for h, info in BHAVA_KARAKA.items():
        planet_to_houses.setdefault(info["primary"], []).append(h)

    multi_bk = []
    for planet, houses in planet_to_houses.items():
        if planet not in planets:
            continue
        pdata = planets[planet]
        sb = shadbala.get(planet, {})
        multi_bk.append({
            "行星":            planet,
            "擔當宮位":         sorted(houses),
            "數量":            len(houses),
            "dignity":         pdata.get("力量"),
            "functional":      fn_table.get(planet, "—"),
            "shadbala_達成率":  sb.get("達成率"),
            "shadbala_強弱":   sb.get("強弱"),
        })
    multi_bk.sort(key=lambda x: (-x["數量"], x["行星"]))

    # ===== 主軸候選 =====
    # 條件：functional benefic / yogakaraka AND Shadbala 達成率 ≥ 1.0
    main_axis = []
    for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        nature = fn_table.get(planet)
        sb = shadbala.get(planet, {})
        ratio = sb.get("達成率", 0)
        if nature in ("benefic", "yogakaraka") and ratio >= 1.0:
            main_axis.append({
                "行星":      planet,
                "functional": nature,
                "達成率":    ratio,
                "dignity":   planets.get(planet, {}).get("力量"),
                "理由":     f"Functional {nature} + Shadbala 達標（達成率 {ratio}）",
            })

    # ===== 雙重要警惕 =====
    # 條件：functional malefic AND dignity in (高揚 / 廟旺) — 強的凶星，影響面大
    strong_malefic = []
    for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        if planet not in planets:
            continue
        nature = fn_table.get(planet)
        dignity = planets[planet].get("力量")
        if nature == "malefic" and dignity in ("高揚", "廟旺"):
            sb = shadbala.get(planet, {})
            strong_malefic.append({
                "行星":      planet,
                "dignity":   dignity,
                "functional": nature,
                "達成率":    sb.get("達成率"),
                "理由":     f"Functional malefic + dignity {dignity}（強的凶星，影響面被放大）",
            })

    return {
        "多重_Bhava_Karaka": multi_bk,
        "主軸候選":         main_axis,
        "雙重要警惕":       strong_malefic,
        "說明": (
            "本區是『素材』不是『結論』，sub-agent 自由判讀，不必照單全收。"
            "多重 Bhava Karaka = 該行星擔當多個宮的天然代言，影響面廣；"
            "主軸候選 = functional 吉 + Shadbala 達標，是命格主軸最有力的候選；"
            "雙重要警惕 = 功能凶星但 dignity 強，凶的影響面被放大，走運期要關注。"
        ),
    }
