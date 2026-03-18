"""八字合盤計算模組

提供個盤擴充（空亡、納音、胎元、命宮、神煞）和跨盤關係計算（天干合、地支合沖刑害破、暗合）。
所有函式都是確定性查表，不涉及 LLM。
"""

from core.constants import (
    GAN, ZHI, GAN_WUXING, GAN_YINYANG, ZHI_CANGGAN, ZHI_ORDER,
    TIANGAN_WUHE, DIZHI_LIUHE, DIZHI_LIUCHONG, DIZHI_LIUHAI,
    DIZHI_PO, DIZHI_SANXING, DIZHI_ZIXING, DIZHI_SANHE, DIZHI_SANHUI,
    NAYIN, NAYIN_WUXING,
    TIANYI_GUIREN, YIMA, TAOHUA, HONGLUAN, TIANXI, JINYU, WENCHANG,
    TIANDE, YUEDE, JIESHA, YANGREN, GUCHEN, GUASU,
    GULUAN_SHA, YINCHA_YANGCUO, WUHU_DUN,
)


# ── 工具函式 ──

def _sanhe_group(zhi: str) -> str | None:
    """找出地支所屬三合局（回傳 key string 如 '申子辰'）"""
    for key in ("申子辰", "寅午戌", "巳酉丑", "亥卯未"):
        if zhi in key:
            return key
    return None


def _sanhui_group(zhi: str) -> str | None:
    """找出地支所屬三會局"""
    for key in ("寅卯辰", "巳午未", "申酉戌", "亥子丑"):
        if zhi in key:
            return key
    return None


# ── 個盤擴充計算 ──

def calc_kongwang(day_pillar: str) -> list[str]:
    """從日柱算空亡（旬空）

    日柱所在的旬，最後兩個沒用到的地支就是空亡。
    例：甲戌旬（甲戌→癸未），地支用了戌亥子丑寅卯辰巳午未，空亡=申酉
    """
    tg_idx = GAN.index(day_pillar[0])
    dz_idx = ZHI.index(day_pillar[1])
    # 旬首天干序 = 0（甲），往回推到旬首
    start_dz = (dz_idx - tg_idx) % 12
    # 旬中用了 10 個地支（start_dz 起連續 10 個），剩下 2 個就是空亡
    used = {(start_dz + i) % 12 for i in range(10)}
    return [ZHI[i] for i in range(12) if i not in used]


def calc_nayin(pillar: str) -> dict:
    """回傳納音名稱和五行"""
    return {"納音": NAYIN.get(pillar, ""), "五行": NAYIN_WUXING.get(pillar, "")}


def calc_taiyuan(month_gan: str, month_zhi: str) -> str:
    """胎元：月干進一位、月支進三位"""
    tg = GAN[(GAN.index(month_gan) + 1) % 10]
    dz = ZHI[(ZHI.index(month_zhi) + 3) % 12]
    return tg + dz


def calc_minggong(year_gan: str, month_zhi: str, hour_zhi: str) -> str:
    """命宮：14 -（月支序 + 時支序），不足用 26 減。天干用五虎遁推。"""
    m = ZHI_ORDER[month_zhi]
    h = ZHI_ORDER[hour_zhi]
    total = m + h
    order = 14 - total if 14 - total >= 1 else 26 - total
    # order → 地支（1=寅, 2=卯, ...）
    zhi_list = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]
    dz = zhi_list[order - 1]
    # 天干：五虎遁，年干決定寅月天干，然後往後推
    yin_gan = WUHU_DUN[year_gan]
    yin_idx = GAN.index(yin_gan)
    dz_offset = ZHI.index(dz) - ZHI.index("寅")
    if dz_offset < 0:
        dz_offset += 12
    tg = GAN[(yin_idx + dz_offset) % 10]
    return tg + dz


def calc_shensha(day_gan: str, day_zhi: str, year_zhi: str, month_zhi: str) -> dict:
    """計算個盤神煞，回傳每個神煞的落點（地支或天干）"""
    result = {}

    # 天乙貴人（日干查）
    result["天乙貴人"] = TIANYI_GUIREN.get(day_gan, [])

    # 驛馬（日支三合局查）
    sg = _sanhe_group(day_zhi)
    if sg:
        result["驛馬"] = YIMA.get(sg, "")

    # 桃花-日支（日支三合局查）
    if sg:
        result["桃花_日支"] = TAOHUA.get(sg, "")

    # 桃花-年支（年支三合局查）
    yg = _sanhe_group(year_zhi)
    if yg:
        result["桃花_年支"] = TAOHUA.get(yg, "")

    # 紅鸞、天喜（年支查）
    result["紅鸞"] = HONGLUAN.get(year_zhi, "")
    result["天喜"] = TIANXI.get(year_zhi, "")

    # 金輿、文昌（日干查）
    result["金輿"] = JINYU.get(day_gan, "")
    result["文昌"] = WENCHANG.get(day_gan, "")

    # 天德、月德（月支查）
    result["天德"] = TIANDE.get(month_zhi, "")
    result["月德"] = YUEDE.get(month_zhi, "")

    # 劫煞（日支三合局查）
    if sg:
        result["劫煞"] = JIESHA.get(sg, "")

    # 羊刃（陽干查帝旺位）
    result["羊刃"] = YANGREN.get(day_gan, "")

    # 孤辰、寡宿（年支所屬三會局查... 實際上是三合局分組）
    # 傳統分組：寅卯辰、巳午未、申酉戌、亥子丑
    yhg = _sanhui_group(year_zhi)
    if yhg:
        result["孤辰"] = GUCHEN.get(yhg, "")
        result["寡宿"] = GUASU.get(yhg, "")

    return result


def calc_dayun(year_gan: str, month_gan: str, month_zhi: str, gender: str) -> list[dict]:
    """計算大運序列（10步）

    男命陽年順行、陰年逆行；女命反之。
    不含起運歲數（需要精確出生日期才能算）。
    """
    is_yang = GAN_YINYANG[year_gan] == "陽"
    is_male = gender == "男"
    # 順行：男陽 or 女陰；逆行：男陰 or 女陽
    forward = (is_male and is_yang) or (not is_male and not is_yang)

    mg_idx = GAN.index(month_gan)
    mz_idx = ZHI.index(month_zhi)
    step = 1 if forward else -1

    dayun = []
    for i in range(1, 11):
        tg = GAN[(mg_idx + step * i) % 10]
        dz = ZHI[(mz_idx + step * i) % 12]
        dayun.append({"序": i, "干支": tg + dz})
    return dayun


def enrich_bazi(bazi: dict, gender: str = "男") -> dict:
    """在 run_bazi() 的結果上擴充空亡、納音、胎元、命宮、神煞、大運"""
    pillars = bazi["四柱"]
    year_p = pillars["年柱"]
    month_p = pillars["月柱"]
    day_p = pillars["日柱"]
    hour_p = pillars["時柱"]

    day_pillar = day_p["干支"]
    year_pillar = year_p["干支"]

    bazi["空亡"] = calc_kongwang(day_pillar)
    bazi["納音"] = {
        "年柱": calc_nayin(year_pillar),
        "日柱": calc_nayin(day_pillar),
    }
    bazi["胎元"] = calc_taiyuan(month_p["天干"], month_p["地支"])
    bazi["命宮"] = calc_minggong(year_p["天干"], month_p["地支"], hour_p["地支"])
    bazi["神煞"] = calc_shensha(day_p["天干"], day_p["地支"], year_p["地支"], month_p["地支"])
    bazi["大運"] = calc_dayun(year_p["天干"], month_p["天干"], month_p["地支"], gender)

    return bazi


# ── 跨盤關係計算 ──

def _collect_stems_branches(bazi: dict) -> tuple[list[str], list[str]]:
    """從 bazi 結果收集四柱天干和地支"""
    gans = []
    zhis = []
    for label in ["年柱", "月柱", "日柱", "時柱"]:
        p = bazi["四柱"][label]
        gans.append(p["天干"])
        zhis.append(p["地支"])
    return gans, zhis


def calc_tiangan_he(gans_a: list[str], gans_b: list[str]) -> list[dict]:
    """跨盤天干五合"""
    labels = ["年", "月", "日", "時"]
    results = []
    for i, ga in enumerate(gans_a):
        for j, gb in enumerate(gans_b):
            pair = frozenset((ga, gb))
            if pair in TIANGAN_WUHE:
                results.append({
                    "A": f"{labels[i]}干{ga}",
                    "B": f"{labels[j]}干{gb}",
                    "合": f"{ga}{gb}合",
                    "化": TIANGAN_WUHE[pair],
                })
    return results


def calc_dizhi_liuhe(zhis_a: list[str], zhis_b: list[str]) -> list[dict]:
    """跨盤地支六合"""
    labels = ["年", "月", "日", "時"]
    results = []
    for i, za in enumerate(zhis_a):
        for j, zb in enumerate(zhis_b):
            pair = frozenset((za, zb))
            if pair in DIZHI_LIUHE:
                results.append({
                    "A": f"{labels[i]}支{za}",
                    "B": f"{labels[j]}支{zb}",
                    "合": f"{za}{zb}合",
                    "化": DIZHI_LIUHE[pair],
                })
    return results


def calc_dizhi_chong(zhis_a: list[str], zhis_b: list[str]) -> list[dict]:
    """跨盤地支六沖"""
    labels = ["年", "月", "日", "時"]
    results = []
    for i, za in enumerate(zhis_a):
        for j, zb in enumerate(zhis_b):
            if frozenset((za, zb)) in DIZHI_LIUCHONG:
                results.append({
                    "A": f"{labels[i]}支{za}",
                    "B": f"{labels[j]}支{zb}",
                    "沖": f"{za}{zb}沖",
                })
    return results


def calc_dizhi_hai(zhis_a: list[str], zhis_b: list[str]) -> list[dict]:
    """跨盤地支六害"""
    labels = ["年", "月", "日", "時"]
    results = []
    for i, za in enumerate(zhis_a):
        for j, zb in enumerate(zhis_b):
            if frozenset((za, zb)) in DIZHI_LIUHAI:
                results.append({
                    "A": f"{labels[i]}支{za}",
                    "B": f"{labels[j]}支{zb}",
                    "害": f"{za}{zb}害",
                })
    return results


def calc_dizhi_po(zhis_a: list[str], zhis_b: list[str]) -> list[dict]:
    """跨盤地支破"""
    labels = ["年", "月", "日", "時"]
    results = []
    for i, za in enumerate(zhis_a):
        for j, zb in enumerate(zhis_b):
            if frozenset((za, zb)) in DIZHI_PO:
                results.append({
                    "A": f"{labels[i]}支{za}",
                    "B": f"{labels[j]}支{zb}",
                    "破": f"{za}{zb}破",
                })
    return results


def calc_sanhe_sanhui(zhis_a: list[str], zhis_b: list[str]) -> dict:
    """跨盤三合局和三會方局（含盤內 + 跨盤湊成的局）"""
    all_zhis = zhis_a + zhis_b
    zhi_set = set(all_zhis)

    results = {"三合": [], "半合": [], "三會": []}

    # 三合
    for members, element in DIZHI_SANHE.items():
        present = members & zhi_set
        if len(present) == 3:
            # 區分盤內 vs 跨盤
            a_has = members & set(zhis_a)
            b_has = members & set(zhis_b)
            scope = "盤內A" if len(a_has) == 3 else "盤內B" if len(b_has) == 3 else "跨盤"
            results["三合"].append({"支": sorted(present, key=ZHI.index), "化": element, "範圍": scope})
        elif len(present) == 2:
            # 半合（跨盤才記）
            a_has = members & set(zhis_a)
            b_has = members & set(zhis_b)
            if a_has and b_has:
                results["半合"].append({"支": sorted(present, key=ZHI.index), "化": element, "範圍": "跨盤"})

    # 三會
    for members, element in DIZHI_SANHUI.items():
        present = members & zhi_set
        if len(present) == 3:
            a_has = members & set(zhis_a)
            b_has = members & set(zhis_b)
            scope = "盤內A" if len(a_has) == 3 else "盤內B" if len(b_has) == 3 else "跨盤"
            results["三會"].append({"支": sorted(present, key=ZHI.index), "化": element, "範圍": scope})

    return results


def calc_sanxing(zhis_a: list[str], zhis_b: list[str]) -> list[dict]:
    """跨盤三刑（含盤內 + 跨盤湊成的刑）"""
    all_zhis = zhis_a + zhis_b
    zhi_set = set(all_zhis)
    results = []

    for members, xtype in DIZHI_SANXING.items():
        if members <= zhi_set:
            a_has = members & set(zhis_a)
            b_has = members & set(zhis_b)
            scope = "盤內A" if a_has == members else "盤內B" if b_has == members else "跨盤"
            results.append({"支": sorted(members, key=ZHI.index), "類型": xtype, "範圍": scope})

    return results


def calc_anhe(zhis_a: list[str], zhis_b: list[str]) -> list[dict]:
    """跨盤暗合（藏干之間的天干五合）"""
    labels = ["年", "月", "日", "時"]
    results = []

    for i, za in enumerate(zhis_a):
        for j, zb in enumerate(zhis_b):
            cg_a = ZHI_CANGGAN[za]
            cg_b = ZHI_CANGGAN[zb]
            for ca in cg_a:
                for cb in cg_b:
                    pair = frozenset((ca, cb))
                    if pair in TIANGAN_WUHE:
                        results.append({
                            "A": f"{labels[i]}支{za}藏{ca}",
                            "B": f"{labels[j]}支{zb}藏{cb}",
                            "合": f"{ca}{cb}合",
                            "化": TIANGAN_WUHE[pair],
                        })
    return results


def calc_shensha_cross(shensha_a: dict, shensha_b: dict,
                       gans_a: list, zhis_a: list,
                       gans_b: list, zhis_b: list) -> dict:
    """跨盤神煞命中檢查：A 的神煞落點有沒有出現在 B 的盤中，反之亦然"""
    b_all = set(gans_b) | set(zhis_b)
    a_all = set(gans_a) | set(zhis_a)

    def check_hits(shensha: dict, target_set: set) -> dict:
        hits = {}
        for name, positions in shensha.items():
            if isinstance(positions, str):
                positions = [positions] if positions else []
            matched = [p for p in positions if p in target_set]
            if matched:
                hits[name] = matched
        return hits

    return {
        "A→B": check_hits(shensha_a, b_all),
        "B→A": check_hits(shensha_b, a_all),
    }


def calc_hunyin_xiongsha(day_pillar_a: str, day_pillar_b: str) -> dict:
    """婚姻凶煞檢查（孤鸞煞、陰差陽錯日）"""
    return {
        "A": {
            "孤鸞煞": day_pillar_a in GULUAN_SHA,
            "陰差陽錯日": day_pillar_a in YINCHA_YANGCUO,
        },
        "B": {
            "孤鸞煞": day_pillar_b in GULUAN_SHA,
            "陰差陽錯日": day_pillar_b in YINCHA_YANGCUO,
        },
    }


# ── 合盤主函式 ──

def run_bazi_compat(bazi_a: dict, bazi_b: dict,
                    gender_a: str = "男", gender_b: str = "男") -> dict:
    """合盤計算主函式

    接收兩個 run_bazi() 的結果，回傳完整的合盤結構化資料。
    """
    # 擴充個盤
    enrich_bazi(bazi_a, gender_a)
    enrich_bazi(bazi_b, gender_b)

    gans_a, zhis_a = _collect_stems_branches(bazi_a)
    gans_b, zhis_b = _collect_stems_branches(bazi_b)

    # 跨盤關係
    cross = {
        "天干合": calc_tiangan_he(gans_a, gans_b),
        "地支六合": calc_dizhi_liuhe(zhis_a, zhis_b),
        "地支六沖": calc_dizhi_chong(zhis_a, zhis_b),
        "地支六害": calc_dizhi_hai(zhis_a, zhis_b),
        "地支破": calc_dizhi_po(zhis_a, zhis_b),
        "三合三會": calc_sanhe_sanhui(zhis_a, zhis_b),
        "三刑": calc_sanxing(zhis_a, zhis_b),
        "暗合": calc_anhe(zhis_a, zhis_b),
    }

    # 神煞交叉
    cross["神煞交叉"] = calc_shensha_cross(
        bazi_a.get("神煞", {}), bazi_b.get("神煞", {}),
        gans_a, zhis_a, gans_b, zhis_b,
    )

    # 婚姻凶煞
    cross["婚姻凶煞"] = calc_hunyin_xiongsha(
        bazi_a["四柱"]["日柱"]["干支"],
        bazi_b["四柱"]["日柱"]["干支"],
    )

    return {
        "personA": bazi_a,
        "personB": bazi_b,
        "crossChart": cross,
    }
