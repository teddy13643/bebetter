"""八字合盤計算模組

提供個盤擴充（空亡、納音、胎元、命宮、神煞）和跨盤關係計算（天干合、地支合沖刑害破、暗合）。
所有函式都是確定性查表，不涉及 LLM。
"""

from datetime import date, timedelta

import sxtwl

from core.constants import (
    GAN, ZHI, GAN_WUXING, GAN_YINYANG, ZHI_CANGGAN, ZHI_ORDER,
    WUXING_SHENG, WUXING_KE,
    TIANGAN_WUHE, DIZHI_LIUHE, DIZHI_LIUCHONG, DIZHI_LIUHAI,
    DIZHI_PO, DIZHI_SANXING, DIZHI_ZIXING, DIZHI_SANHE, DIZHI_SANHUI,
    NAYIN, NAYIN_WUXING,
    TIANYI_GUIREN, YIMA, TAOHUA, HONGLUAN, TIANXI, JINYU, WENCHANG,
    TIANDE, YUEDE, JIESHA, YANGREN, GUCHEN, GUASU,
    GULUAN_SHA, YINCHA_YANGCUO, WUHU_DUN,
    JIE, JIEQI,
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


def _is_forward(year_gan: str, gender: str) -> bool:
    """順行：男陽 or 女陰；逆行：男陰 or 女陽"""
    is_yang = GAN_YINYANG[year_gan] == "陽"
    is_male = gender == "男"
    return (is_male and is_yang) or (not is_male and not is_yang)


def calc_onset_age(year: int, month: int, day: int,
                   year_gan: str, gender: str) -> dict:
    """計算起運歲

    從出生日數到下一個（順排）或上一個（逆排）節的天數，
    每 3 天 = 1 歲，餘 1 天 = 4 個月。
    """
    forward = _is_forward(year_gan, gender)
    birth = date(year, month, day)
    direction = 1 if forward else -1

    # 從出生隔天起搜，出生當天不算
    for i in range(1, 60):
        check_date = birth + timedelta(days=direction * i)
        d = sxtwl.fromSolar(check_date.year, check_date.month, check_date.day)
        if d.hasJieQi():
            jq_idx = d.getJieQi()
            if jq_idx < len(JIEQI) and JIEQI[jq_idx] in JIE:
                onset_age = i // 3
                remainder_months = (i % 3) * 4
                return {
                    "起運歲": onset_age,
                    "餘月": remainder_months,
                    "起運年份": year + onset_age,
                }

    raise ValueError("60天內找不到節")


def calc_dayun(year_gan: str, month_gan: str, month_zhi: str, gender: str,
               onset_age: int | None = None, birth_year: int | None = None) -> list[dict]:
    """計算大運序列（10步）

    男命陽年順行、陰年逆行；女命反之。
    有 onset_age 時每步附帶年齡區間和年份區間。
    """
    forward = _is_forward(year_gan, gender)

    mg_idx = GAN.index(month_gan)
    mz_idx = ZHI.index(month_zhi)
    step = 1 if forward else -1

    dayun = []
    for i in range(1, 11):
        tg = GAN[(mg_idx + step * i) % 10]
        dz = ZHI[(mz_idx + step * i) % 12]
        entry = {"序": i, "干支": tg + dz}
        if onset_age is not None:
            age_start = onset_age + (i - 1) * 10
            age_end = age_start + 9
            entry["年齡"] = f"{age_start}-{age_end}"
            if birth_year is not None:
                entry["年份"] = f"{birth_year + age_start}-{birth_year + age_end}"
        dayun.append(entry)
    return dayun


# ── 月令旺衰（日主在月支的狀態）──
# 月支 → 該月旺的五行（得令）
_MONTH_WUXING = {
    "寅": "木", "卯": "木", "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水", "子": "水", "丑": "土",
}

# 十二長生表：五行在各地支的狀態
# 分陽干/陰干兩套（陰干逆行），此處用簡化版：只看主氣
_CHANGSHENG_YANG = {
    "木": {"亥": "長生", "子": "沐浴", "丑": "冠帶", "寅": "臨官", "卯": "帝旺",
           "辰": "衰", "巳": "病", "午": "死", "未": "墓", "申": "絕", "酉": "胎", "戌": "養"},
    "火": {"寅": "長生", "卯": "沐浴", "辰": "冠帶", "巳": "臨官", "午": "帝旺",
           "未": "衰", "申": "病", "酉": "死", "戌": "墓", "亥": "絕", "子": "胎", "丑": "養"},
    "土": {"寅": "長生", "卯": "沐浴", "辰": "冠帶", "巳": "臨官", "午": "帝旺",
           "未": "衰", "申": "病", "酉": "死", "戌": "墓", "亥": "絕", "子": "胎", "丑": "養"},
    "金": {"巳": "長生", "午": "沐浴", "未": "冠帶", "申": "臨官", "酉": "帝旺",
           "戌": "衰", "亥": "病", "子": "死", "丑": "墓", "寅": "絕", "卯": "胎", "辰": "養"},
    "水": {"申": "長生", "酉": "沐浴", "戌": "冠帶", "亥": "臨官", "子": "帝旺",
           "丑": "衰", "寅": "病", "卯": "死", "辰": "墓", "巳": "絕", "午": "胎", "未": "養"},
}

# 旺相的狀態（得地）
_STRONG_STATES = {"長生", "沐浴", "冠帶", "臨官", "帝旺", "養"}

# 調候用神表：(日主五行, 月支) → [調候用神五行]
# 基本原則：冬天生的需要火暖、夏天生的需要水潤、其他季節視情況
_TIAOJOU = {
    ("木", "子"): ["火"], ("木", "丑"): ["火"], ("木", "亥"): ["火"],
    ("木", "午"): ["水"], ("木", "未"): ["水"], ("木", "巳"): ["水"],
    ("木", "申"): ["水", "火"], ("木", "酉"): ["水", "火"],
    ("火", "子"): ["木"], ("火", "丑"): ["木"], ("火", "亥"): ["木"],
    ("火", "午"): ["水"], ("火", "未"): ["水", "金"], ("火", "巳"): ["水"],
    ("火", "申"): ["木"], ("火", "酉"): ["木"],
    ("土", "子"): ["火"], ("土", "丑"): ["火"], ("土", "亥"): ["火"],
    ("土", "午"): ["水"], ("土", "未"): ["水"], ("土", "巳"): ["水"],
    ("土", "寅"): ["火"], ("土", "卯"): ["火"],
    ("土", "申"): ["火"], ("土", "酉"): ["火"],
    ("金", "子"): ["火", "土"], ("金", "丑"): ["火", "土"], ("金", "亥"): ["火", "土"],
    ("金", "午"): ["水"], ("金", "未"): ["水"], ("金", "巳"): ["水"],
    ("金", "寅"): ["土"], ("金", "卯"): ["土"],
    ("水", "子"): ["火", "土"], ("水", "丑"): ["火"], ("水", "亥"): ["火", "土"],
    ("水", "午"): ["金", "水"], ("水", "未"): ["金", "水"], ("水", "巳"): ["金", "水"],
    ("水", "寅"): ["火"], ("水", "卯"): ["火"],
    ("水", "申"): ["火"], ("水", "酉"): ["火"],
}

# 暗合感情含義
_ANHE_MEANING = {
    frozenset(("甲", "己")): {"合": "甲己合", "化": "土", "感情": "義氣、無條件挺對方"},
    frozenset(("乙", "庚")): {"合": "乙庚合", "化": "金", "感情": "安全感、心理依靠"},
    frozenset(("丙", "辛")): {"合": "丙辛合", "化": "水", "感情": "同類感、懂我"},
    frozenset(("丁", "壬")): {"合": "丁壬合", "化": "木", "感情": "激發表達、想法多"},
    frozenset(("戊", "癸")): {"合": "戊癸合", "化": "火", "感情": "吸引力、慾望"},
}


def calc_yongshen(bazi: dict) -> dict:
    """用神分析：日主強弱量化 + 調候用神 + 喜忌判定

    回傳結構：
    {
        "日主強弱": { "得令", "得地", "得生", "得助", "分數", "判定" },
        "調候用神": [...],
        "喜用神": [...],
        "忌神": [...],
    }
    """
    dm = bazi["日主"]
    dm_wx = bazi["日主五行"]
    pillars = bazi["四柱"]
    month_zhi = pillars["月柱"]["地支"]

    # 收集所有地支
    all_zhi = [pillars[k]["地支"] for k in ["年柱", "月柱", "日柱"] if k in pillars]
    if "時柱" in pillars:
        all_zhi.append(pillars["時柱"]["地支"])

    # 收集所有天干（排除日主自己）
    other_gan = [pillars[k]["天干"] for k in ["年柱", "月柱"] if k in pillars]
    if "時柱" in pillars:
        other_gan.append(pillars["時柱"]["天干"])

    # 1. 得令：月令五行是否生助日主
    month_wx = _MONTH_WUXING[month_zhi]
    deling = month_wx == dm_wx or WUXING_SHENG[month_wx] == dm_wx

    # 2. 得地：日主五行在各地支的十二長生狀態
    dedi_count = 0
    for zhi in all_zhi:
        state = _CHANGSHENG_YANG.get(dm_wx, {}).get(zhi, "")
        if state in _STRONG_STATES:
            dedi_count += 1

    # 3. 得生：其他天干/藏干中，生日主的五行數量
    sheng_wx = [wx for wx, target in WUXING_SHENG.items() if target == dm_wx]
    desheng_count = sum(1 for g in other_gan if GAN_WUXING[g] in sheng_wx)
    # 藏干主氣也算
    for zhi in all_zhi:
        main_cg = ZHI_CANGGAN[zhi][0]
        if GAN_WUXING[main_cg] in sheng_wx:
            desheng_count += 1

    # 4. 得助：同五行的天干/藏干數量
    dezhu_count = sum(1 for g in other_gan if GAN_WUXING[g] == dm_wx)
    for zhi in all_zhi:
        main_cg = ZHI_CANGGAN[zhi][0]
        if GAN_WUXING[main_cg] == dm_wx:
            dezhu_count += 1

    # 量化分數：得令 40 分、得地每個 10 分、得生每個 8 分、得助每個 8 分
    score = (40 if deling else 0) + dedi_count * 10 + desheng_count * 8 + dezhu_count * 8
    if score >= 50:
        strength = "偏強"
    elif score >= 30:
        strength = "中和"
    else:
        strength = "偏弱"

    # 調候用神
    tiaojou_key = (dm_wx, month_zhi)
    tiaojou = _TIAOJOU.get(tiaojou_key, [])

    # 喜忌判定：偏強抑洩、偏弱生扶
    if score >= 50:
        # 日主強，喜：剋我者(官殺)、我生者(食傷)、我剋者(財)
        xi = [WUXING_KE[dm_wx], WUXING_SHENG[dm_wx]]
        # 加入財星（日主所剋的五行的生助者）
        cai_wx = [wx for wx in ["金", "木", "水", "火", "土"] if WUXING_KE[dm_wx] == wx]
        xi.extend(cai_wx)
        xi = list(dict.fromkeys(xi))
        ji = [dm_wx] + [wx for wx, t in WUXING_SHENG.items() if t == dm_wx]
    else:
        # 日主弱，喜：生我者(印)、同我者(比劫)
        xi = [dm_wx] + [wx for wx, t in WUXING_SHENG.items() if t == dm_wx]
        xi = list(dict.fromkeys(xi))
        ji = [WUXING_KE[dm_wx], WUXING_SHENG[dm_wx]]

    ji = list(dict.fromkeys(ji))

    return {
        "日主強弱": {
            "得令": deling,
            "得地": dedi_count,
            "得生": desheng_count,
            "得助": dezhu_count,
            "分數": score,
            "判定": strength,
        },
        "調候用神": tiaojou,
        "喜用神": xi,
        "忌神": ji,
    }


# ── 取格（格局）──
# 子平法：以月令藏干透干定格。Phase 1 做八正格 + 建祿/月劫；
# 外格（從／化／專旺）只標「疑似」不自動斷定，因外格誤判率高、需配合全局氣勢人工複核。

_SHISHEN_TO_GE = {
    "正官": "正官格", "七殺": "七殺格",
    "正財": "正財格", "偏財": "偏財格",
    "正印": "正印格", "偏印": "偏印格",
    "食神": "食神格", "傷官": "傷官格",
}

# 每格的相神（成格所喜）與破神（破格所忌）。
# 判定只看十神有沒有出現在原局，屬「結構傾向」；細部成敗仍需配合刑沖、
# 虛實、有無解救，故相破並見時回「待細推」而非鐵口斷成敗。
_GE_CHENGBAI = {
    "正官格": {"相": ["正財", "偏財", "正印"], "破": ["傷官"]},
    "七殺格": {"相": ["食神", "正印", "偏印"], "破": ["正財", "偏財"]},
    "正財格": {"相": ["正官", "七殺", "食神", "傷官"], "破": ["劫財", "比肩"]},
    "偏財格": {"相": ["正官", "七殺", "食神", "傷官"], "破": ["劫財", "比肩"]},
    "正印格": {"相": ["正官", "七殺"], "破": ["正財", "偏財"]},
    "偏印格": {"相": ["正財", "偏財", "正官", "七殺"], "破": []},
    "食神格": {"相": ["正財", "偏財"], "破": ["偏印"]},
    "傷官格": {"相": ["正財", "偏財", "正印"], "破": ["正官"]},
    "建祿格": {"相": ["正官", "七殺", "正財", "偏財"], "破": []},
    "月劫格": {"相": ["正官", "七殺", "正財", "偏財"], "破": []},
}


def calc_geju(bazi: dict) -> dict:
    """取格（格局）：以月令藏干透干定格，附成敗初步判定

    必須在 calc_yongshen 之後呼叫——疑似外格的判定要讀已算好的日主強弱分數。

    回傳：
    {
        "格局": "正官格",
        "取格依據": "月令亥本氣壬透月干",
        "成敗": "成格" | "破格" | "待細推",
        "說明": "結構傾向的一句話",
        "疑似外格": "疑似從弱…需人工複核" | None,
    }
    """
    dm = bazi["日主"]
    dm_wx = bazi["日主五行"]
    pillars = bazi["四柱"]
    month_zhi = pillars["月柱"]["地支"]

    # 局中其他天干（排除日主本身），與其對應的柱位，平行兩個 list
    pos_keys = [k for k in ["年柱", "月柱", "時柱"] if k in pillars]
    other_gan = [pillars[k]["天干"] for k in pos_keys]
    pos_label = {"年柱": "年", "月柱": "月", "時柱": "時"}

    cang = ZHI_CANGGAN[month_zhi]  # 月令藏干，本氣在 [0]

    # 本氣→中氣→餘氣，找第一個透天干者定格；全不透則取月令本氣
    ge_gan = None
    jiju = f"月令{month_zhi}藏干皆不透，取本氣{cang[0]}"
    for idx, cg in enumerate(cang):
        if cg in other_gan:
            ge_gan = cg
            tier = ("本氣", "中氣", "餘氣")[idx] if idx < 3 else "藏干"
            where = pos_label[pos_keys[other_gan.index(cg)]]
            jiju = f"月令{month_zhi}{tier}{cg}透{where}干"
            break
    if ge_gan is None:
        ge_gan = cang[0]

    ss = _calc_shishen(dm, ge_gan)

    # 月令為比劫 → 建祿（臨官）／月劫（帝旺，即陽刃）；其餘對八正格
    if ss in ("比肩", "劫財"):
        state = _CHANGSHENG_YANG.get(dm_wx, {}).get(month_zhi, "")
        ge = "月劫格" if state == "帝旺" else "建祿格"
        jiju = f"月令{month_zhi}為日主{('帝旺' if ge == '月劫格' else '臨官')}（{ss}）"
    else:
        ge = _SHISHEN_TO_GE.get(ss)

    if ge is None:
        return {
            "格局": "未定格",
            "取格依據": f"月令{month_zhi}定格十神為{ss}，未對應標準格",
            "成敗": "待細推",
            "說明": "結構特殊，建議人工複核",
            "疑似外格": None,
        }

    # 成敗：原局十神（天干 + 各地支本氣）有沒有相神／破神
    local_ss = {_calc_shishen(dm, g) for g in other_gan}
    for k in ["年柱", "月柱", "日柱", "時柱"]:
        if k in pillars:
            local_ss.add(_calc_shishen(dm, ZHI_CANGGAN[pillars[k]["地支"]][0]))

    rule = _GE_CHENGBAI.get(ge, {"相": [], "破": []})
    xiang_hit = [x for x in rule["相"] if x in local_ss]
    po_hit = [p for p in rule["破"] if p in local_ss]

    if po_hit and not xiang_hit:
        chengbai = "破格"
        note = f"局見{'/'.join(po_hit)}破格、無相神救應（結構傾向）"
    elif xiang_hit and not po_hit:
        chengbai = "成格"
        note = f"局見相神{'/'.join(xiang_hit)}護衛（結構傾向）"
    elif xiang_hit and po_hit:
        chengbai = "待細推"
        note = f"相神{'/'.join(xiang_hit)}與破神{'/'.join(po_hit)}並見，成敗需配合刑沖虛實細推"
    else:
        chengbai = "待細推"
        note = "無明顯相神或破神，屬普通格局"

    # Phase 1：外格只標疑似不自動斷，用既有日主強弱分數當訊號
    suspect = None
    score = bazi.get("用神分析", {}).get("日主強弱", {}).get("分數")
    if score is not None:
        if score >= 70 and ss in ("比肩", "劫財"):
            suspect = "疑似專旺／從旺格，需配合全局氣勢人工複核"
        elif score <= 12:
            suspect = "疑似從弱（從財／從殺／從兒）格，需配合全局氣勢人工複核"

    return {
        "格局": ge,
        "取格依據": jiju,
        "成敗": chengbai,
        "說明": note,
        "疑似外格": suspect,
    }


def calc_anhe_meaning(anhe_results: list) -> dict:
    """對暗合結果附加感情含義

    接收 calc_anhe() 的回傳，補上五合類型和感情意義。
    回傳：{ "暗合詳情": [...], "命中數": N, "缺少": [...] }
    """
    all_types = set(_ANHE_MEANING.keys())
    hit_types = set()
    details = []

    for item in anhe_results:
        # calc_anhe 回傳的 "合" 格式是 "己甲合"，取前兩字就是兩個天干
        he_str = item.get("合", "")
        if len(he_str) >= 2:
            key = frozenset((he_str[0], he_str[1]))
        else:
            key = frozenset()
        if key in _ANHE_MEANING:
            hit_types.add(key)
            info = _ANHE_MEANING[key]
            details.append({**item, "感情": info["感情"]})
        else:
            details.append(item)

    missing = []
    for key in all_types:
        if key not in hit_types:
            info = _ANHE_MEANING[key]
            missing.append({"合": info["合"], "化": info["化"], "感情": info["感情"]})

    return {
        "暗合詳情": details,
        "命中數": len(hit_types),
        "總數": len(all_types),
        "缺少": missing,
    }


def enrich_bazi(bazi: dict, gender: str = "男",
                birth_date: tuple[int, int, int] | None = None) -> dict:
    """在 run_bazi() 的結果上擴充空亡、納音、胎元、命宮、神煞、大運

    birth_date: (year, month, day)，有值時計算起運歲並附帶年齡區間。
    """
    pillars = bazi["四柱"]
    year_p = pillars["年柱"]
    month_p = pillars["月柱"]
    day_p = pillars["日柱"]
    hour_p = pillars.get("時柱")

    day_pillar = day_p["干支"]
    year_pillar = year_p["干支"]

    bazi["空亡"] = calc_kongwang(day_pillar)
    bazi["納音"] = {
        "年柱": calc_nayin(year_pillar),
        "日柱": calc_nayin(day_pillar),
    }
    bazi["胎元"] = calc_taiyuan(month_p["天干"], month_p["地支"])
    if hour_p:
        bazi["命宮"] = calc_minggong(year_p["天干"], month_p["地支"], hour_p["地支"])
    else:
        bazi["命宮"] = None
    bazi["神煞"] = calc_shensha(day_p["天干"], day_p["地支"], year_p["地支"], month_p["地支"])

    # 大運：有生日時計算起運歲並附帶年齡區間
    onset_age = None
    birth_year = None
    if birth_date:
        onset_info = calc_onset_age(*birth_date, year_p["天干"], gender)
        bazi["起運"] = onset_info
        onset_age = onset_info["起運歲"]
        birth_year = birth_date[0]
    bazi["大運"] = calc_dayun(
        year_p["天干"], month_p["天干"], month_p["地支"], gender,
        onset_age=onset_age, birth_year=birth_year,
    )
    bazi["用神分析"] = calc_yongshen(bazi)
    bazi["格局"] = calc_geju(bazi)

    return bazi


# ── 跨盤關係計算 ──

def _collect_stems_branches(bazi: dict) -> tuple[list[str], list[str]]:
    """從 bazi 結果收集天干和地支，缺時柱時只收三柱"""
    gans = []
    zhis = []
    for label in ["年柱", "月柱", "日柱", "時柱"]:
        p = bazi["四柱"].get(label)
        if p is None:
            continue
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


# ── 模組級十神計算（供合盤進階分析復用）──

def _calc_shishen(day_master: str, target_gan: str) -> str:
    """計算 target_gan 相對於 day_master 的十神"""
    if target_gan == day_master:
        return "比肩"
    dm_wx = GAN_WUXING[day_master]
    tg_wx = GAN_WUXING[target_gan]
    same_pol = GAN_YINYANG[day_master] == GAN_YINYANG[target_gan]
    if dm_wx == tg_wx:
        return "比肩" if same_pol else "劫財"
    if WUXING_SHENG[dm_wx] == tg_wx:
        return "食神" if same_pol else "傷官"
    if WUXING_SHENG[tg_wx] == dm_wx:
        return "偏印" if same_pol else "正印"
    if WUXING_KE[dm_wx] == tg_wx:
        return "偏財" if same_pol else "正財"
    if WUXING_KE[tg_wx] == dm_wx:
        return "七殺" if same_pol else "正官"
    return ""


# ── 合盤進階分析 ──

_SAME_SEX_BOARD = {
    "比肩": "你就是我——安靜的心動",
    "劫財": "你是我但不一樣——有刺激",
}


def calc_day_master_relation(dm_a: str, dm_b: str, same_sex: bool = True) -> dict:
    """日主關係 + 感情星判定"""
    rel = _calc_shishen(dm_a, dm_b)
    result = {"甲看乙": rel, "乙看甲": _calc_shishen(dm_b, dm_a)}
    if same_sex:
        result["感情星"] = rel in _SAME_SEX_BOARD
        result["底板"] = _SAME_SEX_BOARD.get(rel, "")
    return result


def _wx_judge(wx: str, yongshen: dict) -> str:
    """判斷某五行對某人是喜/忌/中性"""
    if wx in yongshen.get("喜用神", []):
        return "喜"
    if wx in yongshen.get("忌神", []):
        return "忌"
    return "中性"


def calc_combination_pnl(cross: dict, ys_a: dict, ys_b: dict) -> list[dict]:
    """合化損益：每組合局化出的五行對甲乙各自是喜/忌"""
    results = []

    for item in cross.get("天干合", []):
        if item.get("化"):
            results.append({
                "類型": "天干合", "組合": item["合"], "化": item["化"],
                "強度": "天干合",
                "甲": _wx_judge(item["化"], ys_a),
                "乙": _wx_judge(item["化"], ys_b),
            })

    sh = cross.get("三合三會", {})
    for kind, strength in [("三會", "方局"), ("三合", "三合"), ("半合", "半合")]:
        for item in sh.get(kind, []):
            if item.get("化"):
                results.append({
                    "類型": kind, "組合": "".join(item["支"]) + kind + item["化"],
                    "化": item["化"], "強度": strength,
                    "甲": _wx_judge(item["化"], ys_a),
                    "乙": _wx_judge(item["化"], ys_b),
                })

    for item in cross.get("地支六合", []):
        if item.get("化"):
            results.append({
                "類型": "六合", "組合": item.get("合", ""), "化": item["化"],
                "強度": "六合",
                "甲": _wx_judge(item["化"], ys_a),
                "乙": _wx_judge(item["化"], ys_b),
            })

    return results


def calc_tiaohuo_complement(ys_a: dict, ys_b: dict,
                            wx_a: dict, wx_b: dict,
                            combination_pnl: list) -> dict:
    """調候互補：甲的調候用神在乙盤有無 + 合局化出是否補到"""
    def _check(needed: list, provider_wx: dict, pnl: list, label: str) -> dict:
        if not needed:
            return {"需要": [], "滿足": True, "來源": []}
        sources = []
        for wx in needed:
            if provider_wx.get(wx, 0) >= 1.0:
                sources.append(f"{label}本盤{wx}={provider_wx[wx]}")
            for item in pnl:
                if item["化"] == wx:
                    sources.append(f"{item['組合']}化{wx}")
        return {"需要": needed, "滿足": len(sources) > 0, "來源": sources}

    return {
        "甲的調候": _check(ys_a.get("調候用神", []), wx_b, combination_pnl, "乙"),
        "乙的調候": _check(ys_b.get("調候用神", []), wx_a, combination_pnl, "甲"),
    }


def calc_yongshen_interaction(ys_a: dict, ys_b: dict,
                              wx_a: dict, wx_b: dict) -> dict:
    """用神交互：自帶型/消耗型/割肉 + 倒垃圾管道"""
    xi_a, ji_a = set(ys_a.get("喜用神", [])), set(ys_a.get("忌神", []))
    xi_b, ji_b = set(ys_b.get("喜用神", [])), set(ys_b.get("忌神", []))

    def _supply(needed: set, p_wx: dict, p_xi: set, p_ji: set) -> list:
        out = []
        for wx in needed:
            amt = p_wx.get(wx, 0)
            if amt < 0.5:
                continue
            if wx in p_ji:
                cost = "倒垃圾"
            elif wx in p_xi:
                cost = "割肉"
            else:
                cost = "自帶"
            out.append({"五行": wx, "量": round(amt, 1), "成本": cost})
        return out

    dump_a2b = [wx for wx in ji_a if wx in xi_b]
    dump_b2a = [wx for wx in ji_b if wx in xi_a]

    return {
        "甲→乙": _supply(xi_b, wx_a, xi_a, ji_a),
        "乙→甲": _supply(xi_a, wx_b, xi_b, ji_b),
        "倒垃圾管道": {"甲→乙": dump_a2b, "乙→甲": dump_b2a},
        "共同喜用": list(xi_a & xi_b),
    }


def _detect_internal_conflicts(zhis: list) -> list[dict]:
    """偵測單盤內的六沖和爭合"""
    from collections import Counter
    conflicts = []

    # 六沖
    labels = ["年支", "月支", "日支", "時支"]
    for i in range(len(zhis)):
        for j in range(i + 1, len(zhis)):
            if frozenset((zhis[i], zhis[j])) in DIZHI_LIUCHONG:
                conflicts.append({
                    "類型": "六沖", "支": [zhis[i], zhis[j]],
                    "位置": [labels[i], labels[j]],
                })

    # 爭合：同地支 > 1 個，且六合對象也在盤內
    zhi_counts = Counter(zhis)
    for zhi, count in zhi_counts.items():
        if count <= 1:
            continue
        for pair, hua in DIZHI_LIUHE.items():
            if zhi in pair:
                target = [z for z in pair if z != zhi][0]
                if target in zhis:
                    conflicts.append({
                        "類型": "爭合", "搶合方": zhi, "搶合數": count,
                        "目標": target, "合化": hua,
                    })

    return conflicts


def calc_internal_conflicts(bazi_a: dict, bazi_b: dict, cross: dict) -> dict:
    """盤內矛盾偵測 + 跨盤合局是否解開"""
    def _get_zhis(bazi):
        return [bazi["四柱"][k]["地支"]
                for k in ["年柱", "月柱", "日柱", "時柱"]
                if k in bazi["四柱"]]

    zhis_a = _get_zhis(bazi_a)
    zhis_b = _get_zhis(bazi_b)
    conflicts_a = _detect_internal_conflicts(zhis_a)
    conflicts_b = _detect_internal_conflicts(zhis_b)

    # 跨盤合局涉及的地支（被拉走的候選）
    cross_pulled = set()
    sh = cross.get("三合三會", {})
    for item in sh.get("三會", []) + sh.get("三合", []) + sh.get("半合", []):
        cross_pulled.update(item.get("支", []))

    # 標記每個矛盾是否被跨盤合局解開
    for c in conflicts_a:
        if c["類型"] == "六沖":
            c["跨盤解開"] = any(z in cross_pulled for z in c["支"])
        elif c["類型"] == "爭合":
            c["跨盤解開"] = c["搶合方"] in cross_pulled
    for c in conflicts_b:
        if c["類型"] == "六沖":
            c["跨盤解開"] = any(z in cross_pulled for z in c["支"])
        elif c["類型"] == "爭合":
            c["跨盤解開"] = c["搶合方"] in cross_pulled

    return {"甲盤內矛盾": conflicts_a, "乙盤內矛盾": conflicts_b}


def calc_kongwang_cross(bazi_a: dict, bazi_b: dict) -> dict:
    """甲乙空亡落在對方哪些地支（含宮位標記）"""
    labels = ["年支", "月支", "日支", "時支"]
    kw_a = set(bazi_a.get("空亡", []))
    kw_b = set(bazi_b.get("空亡", []))

    def _hits(kw: set, target_bazi: dict) -> list[dict]:
        hits = []
        for i, key in enumerate(["年柱", "月柱", "日柱", "時柱"]):
            p = target_bazi["四柱"].get(key)
            if p and p["地支"] in kw:
                hits.append({"地支": p["地支"], "宮位": labels[i]})
        return hits

    return {
        "甲空亡落乙": _hits(kw_a, bazi_b),
        "乙空亡落甲": _hits(kw_b, bazi_a),
    }


def calc_wuxing_complement(wx_a: dict, wx_b: dict) -> dict:
    """五行共缺與互補"""
    weak_threshold = 1.0
    strong_threshold = 2.0
    weak_a = {wx for wx, v in wx_a.items() if v < weak_threshold}
    weak_b = {wx for wx, v in wx_b.items() if v < weak_threshold}

    return {
        "共缺": sorted(weak_a & weak_b),
        "甲缺乙補": sorted(wx for wx in weak_a if wx_b.get(wx, 0) >= strong_threshold),
        "乙缺甲補": sorted(wx for wx in weak_b if wx_a.get(wx, 0) >= strong_threshold),
    }


def calc_nayin_complement(bazi_a: dict, bazi_b: dict) -> list[dict]:
    """納音五行互補關係"""
    ny_a = bazi_a.get("納音", {})
    ny_b = bazi_b.get("納音", {})
    relations = []
    for la, na in ny_a.items():
        for lb, nb in ny_b.items():
            wa = na.get("五行", "")
            wb = nb.get("五行", "")
            if not wa or not wb:
                continue
            if wa == wb:
                rel = "同五行"
            elif WUXING_SHENG.get(wa) == wb:
                rel = f"{wa}生{wb}"
            elif WUXING_SHENG.get(wb) == wa:
                rel = f"{wb}生{wa}"
            elif WUXING_KE.get(wa) == wb:
                rel = f"{wa}剋{wb}"
            elif WUXING_KE.get(wb) == wa:
                rel = f"{wb}剋{wa}"
            else:
                continue
            relations.append({
                "甲": f"{la}{na['納音']}({wa})",
                "乙": f"{lb}{nb['納音']}({wb})",
                "關係": rel,
            })
    return relations


def _year_ganzhi(year: int) -> str:
    """西曆年 → 干支"""
    return GAN[(year - 4) % 10] + ZHI[(year - 4) % 12]


def _get_dayun_window(bazi: dict, current_year: int, count: int = 3) -> list[dict]:
    """取當前 + 後 count-1 步大運"""
    found = False
    window = []
    for dy in bazi.get("大運", []):
        if not found and "年份" in dy:
            start, end = dy["年份"].split("-")
            if int(start) <= current_year <= int(end):
                found = True
        if found:
            window.append(dy)
            if len(window) >= count:
                break
    return window


def _check_dayun_vs_chart(dayun_gz: str, other_bazi: dict) -> list[str]:
    """大運干支 vs 對方四柱的合/沖/三會/三合"""
    dg, dz = dayun_gz[0], dayun_gz[1]
    other_zhis = [other_bazi["四柱"][k]["地支"]
                  for k in ["年柱", "月柱", "日柱", "時柱"]
                  if k in other_bazi["四柱"]]
    other_gans = [other_bazi["四柱"][k]["天干"]
                  for k in ["年柱", "月柱", "日柱", "時柱"]
                  if k in other_bazi["四柱"]]
    hits = []

    for og in other_gans:
        pair = frozenset((dg, og))
        if pair in TIANGAN_WUHE:
            hits.append(f"{dg}{og}合化{TIANGAN_WUHE[pair]}")

    for oz in other_zhis:
        pair = frozenset((dz, oz))
        if pair in DIZHI_LIUHE:
            hits.append(f"{dz}{oz}六合化{DIZHI_LIUHE[pair]}")
        if pair in DIZHI_LIUCHONG:
            hits.append(f"{dz}{oz}六沖")

    # 三會：大運地支 + 對方兩個地支湊齊
    for members, element in DIZHI_SANHUI.items():
        if dz in members and len(members & set(other_zhis)) >= 2:
            hits.append(f"{''.join(sorted(members, key=ZHI.index))}三會{element}")

    # 三合
    for members, element in DIZHI_SANHE.items():
        if dz in members and len(members & set(other_zhis)) >= 2:
            hits.append(f"{''.join(sorted(members, key=ZHI.index))}三合{element}")

    return hits


def calc_dayun_interaction(bazi_a: dict, bazi_b: dict,
                           current_year: int) -> dict:
    """當前 + 下兩步大運的跨盤交互"""
    ys_a = bazi_a.get("用神分析", {})
    ys_b = bazi_b.get("用神分析", {})

    def _annotate(window, other_bazi, self_ys, other_ys, direction):
        out = []
        for dy in window:
            gz = dy["干支"]
            interactions = _check_dayun_vs_chart(gz, other_bazi)
            # 大運地支主氣五行是否為忌神
            dz_main_wx = GAN_WUXING[ZHI_CANGGAN[gz[1]][0]]
            entry = {**dy, f"對{direction}盤交互": interactions}
            if dz_main_wx in other_ys.get("忌神", []):
                entry[f"對{direction}忌神"] = True
            if dz_main_wx in self_ys.get("忌神", []):
                entry["對自己忌神"] = True
            out.append(entry)
        return out

    return {
        "甲大運": _annotate(
            _get_dayun_window(bazi_a, current_year),
            bazi_b, ys_a, ys_b, "乙"),
        "乙大運": _annotate(
            _get_dayun_window(bazi_b, current_year),
            bazi_a, ys_b, ys_a, "甲"),
    }


def calc_critical_years(bazi_a: dict, bazi_b: dict,
                        start_year: int, count: int = 10) -> list[dict]:
    """未來 N 年的流年觸發事件"""
    dm_a = bazi_a["四柱"]["日柱"]["干支"]
    dm_b = bazi_b["四柱"]["日柱"]["干支"]
    ys_a = bazi_a.get("用神分析", {})
    ys_b = bazi_b.get("用神分析", {})

    zhis_a = [bazi_a["四柱"][k]["地支"]
              for k in ["年柱", "月柱", "日柱", "時柱"]
              if k in bazi_a["四柱"]]
    zhis_b = [bazi_b["四柱"][k]["地支"]
              for k in ["年柱", "月柱", "日柱", "時柱"]
              if k in bazi_b["四柱"]]
    all_zhis = zhis_a + zhis_b

    results = []
    for y in range(start_year, start_year + count):
        gz = _year_ganzhi(y)
        yg, yz = gz[0], gz[1]
        events = []

        # 沖日柱
        if frozenset((yz, dm_a[1])) in DIZHI_LIUCHONG:
            events.append("沖甲日支")
        if frozenset((yz, dm_b[1])) in DIZHI_LIUCHONG:
            events.append("沖乙日支")

        # 合日主天干
        pair_a = frozenset((yg, dm_a[0]))
        if pair_a in TIANGAN_WUHE:
            events.append(f"合甲日主化{TIANGAN_WUHE[pair_a]}")
        pair_b = frozenset((yg, dm_b[0]))
        if pair_b in TIANGAN_WUHE:
            events.append(f"合乙日主化{TIANGAN_WUHE[pair_b]}")

        # 引發三會/三合
        for members, element in DIZHI_SANHUI.items():
            if yz in members and len(members & set(all_zhis)) >= 2:
                events.append(f"引發三會{element}")
        for members, element in DIZHI_SANHE.items():
            if yz in members and len(members & set(all_zhis)) >= 2:
                events.append(f"引發三合{element}")

        # 忌神加重
        yz_wx = GAN_WUXING[ZHI_CANGGAN[yz][0]]
        if yz_wx in ys_a.get("忌神", []) and yz_wx in ys_b.get("忌神", []):
            events.append(f"雙方忌神{yz_wx}")
        elif yz_wx in ys_a.get("忌神", []):
            events.append(f"甲忌神{yz_wx}")
        elif yz_wx in ys_b.get("忌神", []):
            events.append(f"乙忌神{yz_wx}")

        # 補共缺
        weak_both = {wx for wx in ["金", "木", "水", "火", "土"]
                     if bazi_a["五行分布"].get(wx, 0) < 1.0
                     and bazi_b["五行分布"].get(wx, 0) < 1.0}
        if yz_wx in weak_both:
            events.append(f"補共缺{yz_wx}")

        if events:
            results.append({"年份": y, "干支": gz, "事件": events})

    return results


def calc_compat_scores(cross: dict) -> dict:
    """合盤各維度分數 + 建議評級"""
    scores = {}

    # 調候
    th = cross.get("調候互補", {})
    a_ok = th.get("甲的調候", {}).get("滿足", False)
    b_ok = th.get("乙的調候", {}).get("滿足", False)
    scores["調候"] = {"雙向": a_ok and b_ok, "甲滿足": a_ok, "乙滿足": b_ok}

    # 用神
    ys = cross.get("用神交互", {})
    dump_a2b = ys.get("倒垃圾管道", {}).get("甲→乙", [])
    dump_b2a = ys.get("倒垃圾管道", {}).get("乙→甲", [])
    scores["用神"] = {
        "有倒垃圾": bool(dump_a2b or dump_b2a),
        "共同喜用": ys.get("共同喜用", []),
    }

    # 盤內矛盾化解
    ic = cross.get("盤內矛盾", {})
    a_resolved = any(c.get("跨盤解開") for c in ic.get("甲盤內矛盾", []))
    b_resolved = any(c.get("跨盤解開") for c in ic.get("乙盤內矛盾", []))
    scores["矛盾化解"] = {
        "甲解開": a_resolved, "乙解開": b_resolved,
        "雙向": a_resolved and b_resolved,
    }

    # 合化淨值（方局忌神懲罰加重）
    pnl = cross.get("合化損益", [])
    xi = sum(1 for p in pnl if p.get("甲") == "喜" and p.get("乙") == "喜")
    ji_raw = [p for p in pnl if p.get("甲") == "忌" or p.get("乙") == "忌"]
    ji_weighted = sum(2 if p.get("強度") == "方局" else 1 for p in ji_raw)
    scores["合化淨值"] = {"喜": xi, "忌": len(ji_raw), "忌加權": ji_weighted, "淨": xi - ji_weighted}

    # 暗合
    ah = cross.get("暗合含義", {})
    scores["暗合"] = {"命中": ah.get("命中數", 0), "總數": ah.get("總數", 5)}

    # 沖剋
    scores["沖剋"] = {
        "六沖": len(cross.get("地支六沖", [])),
        "六害": len(cross.get("地支六害", [])),
    }

    # 感情星
    scores["感情星"] = cross.get("日主關係", {}).get("感情星", False)

    # 加權計分
    total = 0
    if scores["調候"]["雙向"]:
        total += 3
    elif scores["調候"]["甲滿足"] or scores["調候"]["乙滿足"]:
        total += 1
    if scores["矛盾化解"]["雙向"]:
        total += 3
    elif scores["矛盾化解"]["甲解開"] or scores["矛盾化解"]["乙解開"]:
        total += 1
    total += scores["合化淨值"]["淨"]
    total += scores["暗合"]["命中"]
    total -= scores["沖剋"]["六沖"] * 2
    total -= scores["沖剋"]["六害"]
    if scores["感情星"]:
        total += 1
    if scores["用神"]["有倒垃圾"]:
        total += 1

    # S 需要幾乎完美（調候雙向 + 矛盾化解 + 暗合高 + 無忌神方局）
    if total >= 12:
        grade = "S"
    elif total >= 8:
        grade = "A+"
    elif total >= 5:
        grade = "A"
    elif total >= 2:
        grade = "B"
    elif total >= -1:
        grade = "C"
    else:
        grade = "D"

    scores["總分"] = total
    scores["建議評級"] = grade
    return scores


def calc_palace_correspondence(bazi_a: dict, bazi_b: dict) -> list[dict]:
    """宮位對應：逐柱比對天干地支關係"""
    labels = ["年柱", "月柱", "日柱", "時柱"]
    meanings = {"年柱": "家庭背景", "月柱": "社會事業",
                "日柱": "自我伴侶", "時柱": "私下未來"}
    results = []
    for label in labels:
        pa = bazi_a["四柱"].get(label)
        pb = bazi_b["四柱"].get(label)
        if not pa or not pb:
            continue

        # 天干
        tg_rel = ""
        tg_pair = frozenset((pa["天干"], pb["天干"]))
        if tg_pair in TIANGAN_WUHE:
            tg_rel = f"{pa['天干']}{pb['天干']}合化{TIANGAN_WUHE[tg_pair]}"
        elif pa["天干"] == pb["天干"]:
            tg_rel = "同干"

        # 地支
        dz_rel = ""
        dz_pair = frozenset((pa["地支"], pb["地支"]))
        if dz_pair in DIZHI_LIUHE:
            dz_rel = f"六合化{DIZHI_LIUHE[dz_pair]}"
        elif dz_pair in DIZHI_LIUCHONG:
            dz_rel = "六沖"
        elif dz_pair in DIZHI_LIUHAI:
            dz_rel = "六害"
        elif pa["地支"] == pb["地支"]:
            dz_rel = "同支"

        results.append({
            "宮位": label, "含義": meanings[label],
            "甲": pa["干支"], "乙": pb["干支"],
            "天干": tg_rel, "地支": dz_rel,
        })
    return results


# ── 四柱字串 → run_bazi() 相容 dict ──

def bazi_from_pillars(pillars_str: str) -> dict:
    """從八字字串構造 run_bazi() 相容的 dict。

    接受 6 字（三柱，缺時柱）或 8 字（四柱完整）。
    缺時柱時四柱 dict 不含 "時柱" key，下游據此判斷。
    """
    length = len(pillars_str)
    if length not in (6, 8):
        raise ValueError(f"需要 6 或 8 個字，收到 {length} 個字")
    pairs = [(pillars_str[i], pillars_str[i + 1]) for i in range(0, length, 2)]
    day_master = pairs[2][0]

    def shishen(tg):
        if tg == day_master:
            return "比肩"
        dm_wx = GAN_WUXING[day_master]
        tg_wx = GAN_WUXING[tg]
        same_pol = GAN_YINYANG[day_master] == GAN_YINYANG[tg]
        if dm_wx == tg_wx:
            return "比肩" if same_pol else "劫財"
        if WUXING_SHENG[dm_wx] == tg_wx:
            return "食神" if same_pol else "傷官"
        if WUXING_SHENG[tg_wx] == dm_wx:
            return "偏印" if same_pol else "正印"
        if WUXING_KE[dm_wx] == tg_wx:
            return "偏財" if same_pol else "正財"
        if WUXING_KE[tg_wx] == dm_wx:
            return "七殺" if same_pol else "正官"
        return ""

    all_labels = ["年柱", "月柱", "日柱", "時柱"]
    result_pillars = {}
    wuxing = {"金": 0, "木": 0, "水": 0, "火": 0, "土": 0}
    for i, (g, z) in enumerate(pairs):
        cg = ZHI_CANGGAN[z]
        result_pillars[all_labels[i]] = {
            "天干": g, "地支": z, "干支": g + z,
            "十神": shishen(g) if i != 2 else "日主",
            "藏干": [{"天干": c, "十神": shishen(c)} for c in cg],
        }
        wuxing[GAN_WUXING[g]] += 1
        for j, c in enumerate(cg):
            wuxing[GAN_WUXING[c]] += 0.7 if j == 0 else 0.3

    return {
        "四柱": result_pillars,
        "日主": day_master,
        "日主五行": GAN_WUXING[day_master],
        "日主陰陽": GAN_YINYANG[day_master],
        "五行分布": {k: round(v, 1) for k, v in wuxing.items()},
    }


# ── 合盤主函式 ──

def _calc_shishen(day_master: str, target_gan: str) -> str:
    """日主視角的十神關係"""
    if target_gan == day_master:
        return "比肩"
    dm_wx = GAN_WUXING[day_master]
    tg_wx = GAN_WUXING[target_gan]
    same_pol = GAN_YINYANG[day_master] == GAN_YINYANG[target_gan]
    if dm_wx == tg_wx:
        return "比肩" if same_pol else "劫財"
    if WUXING_SHENG[dm_wx] == tg_wx:
        return "食神" if same_pol else "傷官"
    if WUXING_SHENG[tg_wx] == dm_wx:
        return "偏印" if same_pol else "正印"
    if WUXING_KE[dm_wx] == tg_wx:
        return "偏財" if same_pol else "正財"
    if WUXING_KE[tg_wx] == dm_wx:
        return "七殺" if same_pol else "正官"
    return ""


def _calc_liunian_bindayun(bazi: dict, year: int,
                           dayun_gz: str | None) -> dict:
    """單年流年分析：流年干支 × 命盤 × 大運的交互

    回傳結構包含流年十神、與命盤的合沖刑害、與大運的交互、喜忌判定。
    """
    gz = _year_ganzhi(year)
    yg, yz = gz[0], gz[1]
    dm = bazi["日主"]
    ys = bazi.get("用神分析", {})
    xi_list = ys.get("喜用神", [])
    ji_list = ys.get("忌神", [])

    # 流年天干十神
    ln_shishen = _calc_shishen(dm, yg)

    # 流年天干五行、地支主氣五行
    yg_wx = GAN_WUXING[yg]
    yz_main_cg = ZHI_CANGGAN[yz][0]
    yz_wx = GAN_WUXING[yz_main_cg]
    yz_shishen = _calc_shishen(dm, yz_main_cg)

    # 納音
    ln_nayin = calc_nayin(gz)

    # ── 流年 vs 命盤四柱 ──
    chart_zhis = [bazi["四柱"][k]["地支"]
                  for k in ["年柱", "月柱", "日柱", "時柱"]
                  if k in bazi["四柱"]]
    chart_gans = [bazi["四柱"][k]["天干"]
                  for k in ["年柱", "月柱", "日柱", "時柱"]
                  if k in bazi["四柱"]]
    labels = ["年", "月", "日", "時"]

    vs_chart = []

    # 天干合
    for i, cg in enumerate(chart_gans):
        pair = frozenset((yg, cg))
        if pair in TIANGAN_WUHE:
            vs_chart.append(f"流年{yg}合{labels[i]}干{cg}化{TIANGAN_WUHE[pair]}")

    # 地支六合、六沖、六害、破
    for i, cz in enumerate(chart_zhis):
        pair = frozenset((yz, cz))
        if pair in DIZHI_LIUHE:
            vs_chart.append(f"流年{yz}合{labels[i]}支{cz}化{DIZHI_LIUHE[pair]}")
        if pair in DIZHI_LIUCHONG:
            vs_chart.append(f"流年{yz}沖{labels[i]}支{cz}")
        if pair in DIZHI_LIUHAI:
            vs_chart.append(f"流年{yz}害{labels[i]}支{cz}")
        if pair in DIZHI_PO:
            vs_chart.append(f"流年{yz}破{labels[i]}支{cz}")

    # 三合、三會（流年地支 + 命盤兩個地支湊齊）
    for members, element in DIZHI_SANHE.items():
        if yz in members and len(members & set(chart_zhis)) >= 2:
            vs_chart.append(f"流年{yz}引發三合{element}局")
    for members, element in DIZHI_SANHUI.items():
        if yz in members and len(members & set(chart_zhis)) >= 2:
            vs_chart.append(f"流年{yz}引發三會{element}局")

    # 三刑（流年地支 + 命盤地支）
    all_zhis_with_ln = chart_zhis + [yz]
    zhi_set = set(all_zhis_with_ln)
    for members, xing_type in DIZHI_SANXING.items():
        if yz in members and members.issubset(zhi_set):
            vs_chart.append(f"流年{yz}引發{xing_type}刑")

    # ── 流年 vs 大運 ──
    vs_dayun = []
    dayun_shishen = ""
    if dayun_gz:
        dg, dz = dayun_gz[0], dayun_gz[1]
        dayun_shishen = _calc_shishen(dm, dg)

        # 天干合
        tg_pair = frozenset((yg, dg))
        if tg_pair in TIANGAN_WUHE:
            vs_dayun.append(f"流年{yg}合大運{dg}化{TIANGAN_WUHE[tg_pair]}")

        # 地支合沖害破
        dz_pair = frozenset((yz, dz))
        if dz_pair in DIZHI_LIUHE:
            vs_dayun.append(f"流年{yz}合大運{dz}化{DIZHI_LIUHE[dz_pair]}")
        if dz_pair in DIZHI_LIUCHONG:
            vs_dayun.append(f"流年{yz}沖大運{dz}")
        if dz_pair in DIZHI_LIUHAI:
            vs_dayun.append(f"流年{yz}害大運{dz}")

        # 大運地支 + 流年地支 + 命盤地支 → 三合三會
        combined = set(chart_zhis + [yz, dz])
        for members, element in DIZHI_SANHE.items():
            if yz in members and dz in members and members.issubset(combined):
                vs_dayun.append(f"流年{yz}+大運{dz}湊三合{element}局")
        for members, element in DIZHI_SANHUI.items():
            if yz in members and dz in members and members.issubset(combined):
                vs_dayun.append(f"流年{yz}+大運{dz}湊三會{element}局")

    # ── 喜忌判定 ──
    # 天干五行和地支主氣五行分別判斷
    xi_count = (1 if yg_wx in xi_list else 0) + (1 if yz_wx in xi_list else 0)
    ji_count = (1 if yg_wx in ji_list else 0) + (1 if yz_wx in ji_list else 0)
    if xi_count >= 2:
        verdict = "大吉"
    elif xi_count > ji_count:
        verdict = "偏吉"
    elif ji_count >= 2:
        verdict = "凶"
    elif ji_count > xi_count:
        verdict = "偏凶"
    else:
        verdict = "平"

    # 神煞觸發（流年地支是否落在命盤神煞位）
    shensha_hits = []
    chart_shensha = bazi.get("神煞", {})
    for name, positions in chart_shensha.items():
        if isinstance(positions, list):
            if yz in positions:
                shensha_hits.append(name)
        elif isinstance(positions, str) and yz == positions:
            shensha_hits.append(name)

    result = {
        "年份": year,
        "干支": gz,
        "納音": ln_nayin,
        "天干十神": ln_shishen,
        "地支藏干十神": yz_shishen,
        "天干五行": yg_wx,
        "地支主氣五行": yz_wx,
        "喜忌": verdict,
        "與命盤交互": vs_chart,
    }
    if dayun_gz:
        result["所在大運"] = dayun_gz
        result["大運十神"] = dayun_shishen
        result["與大運交互"] = vs_dayun
    if shensha_hits:
        result["觸發神煞"] = shensha_hits

    return result


def _find_current_dayun(bazi: dict, year: int) -> dict | None:
    """找出指定年份所在的大運，回傳大運 dict 或 None"""
    for dy in bazi.get("大運", []):
        if "年份" not in dy:
            continue
        start, end = dy["年份"].split("-")
        if int(start) <= year <= int(end):
            return dy
    return None


def run_bazi_fortune(pillars_str: str, gender: str = "男",
                     birth_date: tuple[int, int, int] | None = None,
                     target_year: int | None = None,
                     forecast_years: int = 10) -> dict:
    """個人八字大運流年分析

    從四柱字串出發，計算個盤擴充 + 定位當前大運 + 逐年流年分析。
    target_year: 分析起始年份（預設今年）。
    forecast_years: 向後預測年數（預設 10）。
    """
    from datetime import date as _date

    if target_year is None:
        target_year = _date.today().year

    bazi = bazi_from_pillars(pillars_str)
    enrich_bazi(bazi, gender, birth_date=birth_date)

    # 逐年分析
    liunian = []
    key_years = []
    for y in range(target_year, target_year + forecast_years):
        # 定位該年所在的大運
        dy = _find_current_dayun(bazi, y)
        dayun_gz = dy["干支"] if dy else None

        analysis = _calc_liunian_bindayun(bazi, y, dayun_gz)
        liunian.append(analysis)

        # 標記關鍵年份（有合沖刑 or 凶 or 大吉 or 觸發神煞）
        is_key = (
            analysis["喜忌"] in ("大吉", "凶")
            or analysis.get("觸發神煞")
            or any("沖" in e for e in analysis["與命盤交互"])
            or any("刑" in e for e in analysis["與命盤交互"])
        )
        if is_key:
            key_years.append({
                "年份": y,
                "干支": analysis["干支"],
                "喜忌": analysis["喜忌"],
                "重點": _summarize_key_year(analysis),
            })

    # 當前大運
    current_dy = _find_current_dayun(bazi, target_year)

    # 整理個盤摘要（不需要完整重複四柱細節，只留重點）
    return {
        "個盤": {
            "四柱": bazi["四柱"],
            "日主": bazi["日主"],
            "日主五行": bazi["日主五行"],
            "五行分布": bazi["五行分布"],
            "空亡": bazi.get("空亡"),
            "納音": bazi.get("納音"),
            "胎元": bazi.get("胎元"),
            "命宮": bazi.get("命宮"),
            "神煞": bazi.get("神煞"),
            "用神分析": bazi.get("用神分析"),
            "格局": bazi.get("格局"),
        },
        "起運": bazi.get("起運"),
        "大運總覽": bazi.get("大運", []),
        "當前大運": current_dy,
        "流年分析": liunian,
        "關鍵年份": key_years,
    }


def _summarize_key_year(analysis: dict) -> str:
    """一句話摘要關鍵年份的重點事件"""
    parts = []
    if analysis["喜忌"] in ("大吉", "凶"):
        parts.append(analysis["喜忌"])
    for e in analysis["與命盤交互"]:
        if "沖" in e or "刑" in e:
            parts.append(e)
    if analysis.get("觸發神煞"):
        parts.append("觸發" + "、".join(analysis["觸發神煞"]))
    if analysis.get("與大運交互"):
        for e in analysis["與大運交互"]:
            if "沖" in e:
                parts.append(e)
    return "；".join(parts) if parts else ""


def run_bazi_compat(bazi_a: dict, bazi_b: dict,
                    gender_a: str = "男", gender_b: str = "男",
                    birth_date_a: tuple[int, int, int] | None = None,
                    birth_date_b: tuple[int, int, int] | None = None) -> dict:
    """合盤計算主函式

    接收兩個 run_bazi() 的結果，回傳完整的合盤結構化資料。
    birth_date_a/b: (year, month, day)，有值時計算起運歲。
    """
    # 擴充個盤
    enrich_bazi(bazi_a, gender_a, birth_date=birth_date_a)
    enrich_bazi(bazi_b, gender_b, birth_date=birth_date_b)

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

    # 暗合附加感情含義
    cross["暗合含義"] = calc_anhe_meaning(cross["暗合"])

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

    # ── 進階分析（減少 AI 推算量）──
    ys_a = bazi_a.get("用神分析", {})
    ys_b = bazi_b.get("用神分析", {})
    wx_a = bazi_a.get("五行分布", {})
    wx_b = bazi_b.get("五行分布", {})

    same_sex = (gender_a == gender_b)
    cross["日主關係"] = calc_day_master_relation(
        bazi_a["日主"], bazi_b["日主"], same_sex)

    pnl = calc_combination_pnl(cross, ys_a, ys_b)
    cross["合化損益"] = pnl

    cross["調候互補"] = calc_tiaohuo_complement(ys_a, ys_b, wx_a, wx_b, pnl)
    cross["用神交互"] = calc_yongshen_interaction(ys_a, ys_b, wx_a, wx_b)
    cross["盤內矛盾"] = calc_internal_conflicts(bazi_a, bazi_b, cross)
    cross["宮位對應"] = calc_palace_correspondence(bazi_a, bazi_b)

    # ── 新增：減少 AI 推算的確定性計算 ──
    cross["空亡交叉"] = calc_kongwang_cross(bazi_a, bazi_b)
    cross["五行互補"] = calc_wuxing_complement(wx_a, wx_b)
    cross["納音互補"] = calc_nayin_complement(bazi_a, bazi_b)
    cross["合盤評分"] = calc_compat_scores(cross)

    # 大運交互和流年需要年份資訊
    from datetime import date as _date
    current_year = _date.today().year
    cross["大運交互"] = calc_dayun_interaction(bazi_a, bazi_b, current_year)
    cross["流年觸發"] = calc_critical_years(bazi_a, bazi_b, current_year, count=10)

    return {
        "personA": bazi_a,
        "personB": bazi_b,
        "crossChart": cross,
    }
