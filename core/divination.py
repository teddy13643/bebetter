import os
import sys
import site

from core.utils import sanitize, solar_to_ganzhi


def run_qimen(year: int, month: int, day: int, hour: int, minute: int) -> dict:
    """奇門遁甲排盤"""
    _pkg = os.path.join(site.getsitepackages()[0], "kinqimen")
    if _pkg not in sys.path:
        sys.path.insert(0, _pkg)
    import kinqimen
    return kinqimen.Qimen(year, month, day, hour, minute).pan(1)


def run_liuren(year: int, month: int, day: int, hour: int) -> dict:
    """大六壬排盤"""
    from kinliuren import kinliuren as mod
    jieqi, lunar_month, day_gz, hour_gz = solar_to_ganzhi(year, month, day, hour)
    return mod.Liuren(jieqi, lunar_month, day_gz, hour_gz).result(0)


def run_taiyi(year: int, month: int, day: int, hour: int, minute: int) -> dict:
    """太乙神數排盤"""
    _pkg = os.path.join(site.getsitepackages()[0], "kintaiyi")
    # kintaiyi 和 kinqimen 都有裸 config.py，清掉避免衝突
    for mod_name in list(sys.modules.keys()):
        if mod_name in ("config", "taiyidict"):
            del sys.modules[mod_name]
    if _pkg not in sys.path:
        sys.path.insert(0, _pkg)
    import kintaiyi
    result = kintaiyi.Taiyi(year, month, day, hour, minute).pan(3, 1)
    return sanitize(result)


def run_meihua(year: int, month: int, day: int, hour: int, minute: int) -> dict:
    """梅花易數排盤（時間起卦法）"""
    import sxtwl
    from core.constants import (
        XIANTIAN, TRIGRAM_ELEMENT, TRIGRAM_NATURE, TRIGRAM_LINES,
        LINES_TRIGRAM, GUA_NAMES, WUXING_SHENG, WUXING_KE,
    )

    d = sxtwl.fromSolar(year, month, day)

    year_zhi = d.getYearGZ().dz + 1  # 子=1 ... 亥=12
    lunar_month = abs(d.getLunarMonth())
    lunar_day = d.getLunarDay()
    hour_zhi = ((hour + 1) // 2) % 12 + 1

    # 上卦、下卦、動爻
    upper_num = (year_zhi + lunar_month + lunar_day) % 8 or 8
    lower_num = (year_zhi + lunar_month + lunar_day + hour_zhi) % 8 or 8
    changing_line = (year_zhi + lunar_month + lunar_day + hour_zhi) % 6 or 6

    upper = XIANTIAN[upper_num]
    lower = XIANTIAN[lower_num]

    # 本卦六爻（下→上）
    lines = TRIGRAM_LINES[lower] + TRIGRAM_LINES[upper]

    # 互卦：2-4 爻為下，3-5 爻為上
    hu_lower = LINES_TRIGRAM[tuple(lines[1:4])]
    hu_upper = LINES_TRIGRAM[tuple(lines[2:5])]

    # 變卦：動爻變陰陽
    bian_lines = lines[:]
    bian_lines[changing_line - 1] = 1 - bian_lines[changing_line - 1]
    bian_lower = LINES_TRIGRAM[tuple(bian_lines[0:3])]
    bian_upper = LINES_TRIGRAM[tuple(bian_lines[3:6])]

    # 體用：動爻在下卦(1-3)則下卦為用、上卦為體，反之亦然
    if changing_line <= 3:
        ti, yong = upper, lower
    else:
        ti, yong = lower, upper

    ti_elem = TRIGRAM_ELEMENT[ti]
    yong_elem = TRIGRAM_ELEMENT[yong]

    # 五行生剋關係
    def wuxing_relation(a, b):
        """a 對 b 的關係"""
        if a == b:
            return "比和"
        if WUXING_SHENG[a] == b:
            return "生"
        if WUXING_KE[a] == b:
            return "剋"
        if WUXING_SHENG[b] == a:
            return "被生"
        return "被剋"

    ti_yong_relation = wuxing_relation(ti_elem, yong_elem)

    return {
        "起卦參數": {
            "農曆": f"{d.getLunarYear()}年{lunar_month}月{lunar_day}日",
            "年支數": year_zhi,
            "月數": lunar_month,
            "日數": lunar_day,
            "時支數": hour_zhi,
        },
        "本卦": {
            "卦名": GUA_NAMES[(upper, lower)],
            "上卦": f"{upper}（{TRIGRAM_NATURE[upper]}）",
            "下卦": f"{lower}（{TRIGRAM_NATURE[lower]}）",
            "動爻": changing_line,
        },
        "互卦": {
            "卦名": GUA_NAMES[(hu_upper, hu_lower)],
            "上卦": f"{hu_upper}（{TRIGRAM_NATURE[hu_upper]}）",
            "下卦": f"{hu_lower}（{TRIGRAM_NATURE[hu_lower]}）",
        },
        "變卦": {
            "卦名": GUA_NAMES[(bian_upper, bian_lower)],
            "上卦": f"{bian_upper}（{TRIGRAM_NATURE[bian_upper]}）",
            "下卦": f"{bian_lower}（{TRIGRAM_NATURE[bian_lower]}）",
        },
        "體用": {
            "體": f"{ti}（{TRIGRAM_NATURE[ti]}，{ti_elem}）",
            "用": f"{yong}（{TRIGRAM_NATURE[yong]}，{yong_elem}）",
            "關係": ti_yong_relation,
            "斷語": _meihua_verdict(ti_elem, ti_yong_relation),
        },
    }


def _meihua_verdict(ti_elem: str, relation: str) -> str:
    """體用關係的本命斷語"""
    verdicts = {
        "比和": "內外一致，性格穩定踏實，但缺乏爆發力",
        "生": "天生付出型，容易為別人操勞，要學會留能量給自己",
        "被生": "天生有貴人體質，環境總是幫你，資源會主動靠過來",
        "剋": "天生掌控力強，有主導權和領導力，適合帶隊",
        "被剋": "天生壓力體質，外在環境常給你考驗，但也磨出韌性",
    }
    return verdicts.get(relation, "")


def run_bazi(year: int, month: int, day: int, hour: int) -> dict:
    """八字排盤"""
    import sxtwl
    from core.constants import (
        GAN, ZHI, GAN_WUXING, GAN_YINYANG, ZHI_CANGGAN,
        WUXING_SHENG, WUXING_KE,
    )

    d = sxtwl.fromSolar(year, month, day)

    year_gz = d.getYearGZ()
    month_gz = d.getMonthGZ()
    day_gz = d.getDayGZ()
    hour_zhi_idx = ((hour + 1) // 2) % 12
    hour_tg_idx = (day_gz.tg * 2 + hour_zhi_idx) % 10

    pillars = [
        (GAN[year_gz.tg], ZHI[year_gz.dz]),
        (GAN[month_gz.tg], ZHI[month_gz.dz]),
        (GAN[day_gz.tg], ZHI[day_gz.dz]),
        (GAN[hour_tg_idx], ZHI[hour_zhi_idx]),
    ]

    day_master = pillars[2][0]

    def shishen(target_gan):
        """日主對某天干的十神關係"""
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

    labels = ["年柱", "月柱", "日柱", "時柱"]
    result_pillars = {}
    for i, (gan, zhi) in enumerate(pillars):
        canggan = ZHI_CANGGAN[zhi]
        result_pillars[labels[i]] = {
            "天干": gan,
            "地支": zhi,
            "干支": gan + zhi,
            "十神": shishen(gan) if i != 2 else "日主",
            "藏干": [{"天干": cg, "十神": shishen(cg)} for cg in canggan],
        }

    # 八字五行統計（天干算 1，藏干主氣算 0.7、餘氣算 0.3）
    wuxing_count = {"金": 0, "木": 0, "水": 0, "火": 0, "土": 0}
    for gan, zhi in pillars:
        wuxing_count[GAN_WUXING[gan]] += 1
        canggan = ZHI_CANGGAN[zhi]
        for j, cg in enumerate(canggan):
            wuxing_count[GAN_WUXING[cg]] += 0.7 if j == 0 else 0.3

    return {
        "四柱": result_pillars,
        "日主": day_master,
        "日主五行": GAN_WUXING[day_master],
        "日主陰陽": GAN_YINYANG[day_master],
        "五行分布": {k: round(v, 1) for k, v in wuxing_count.items()},
    }


def _run_astro(year: int, month: int, day: int, hour: int, minute: int,
               lat: float, lng: float, tz_str: str,
               zodiac_type: str, sidereal_mode: str = None) -> dict:
    """占星排盤共用邏輯"""
    from kerykeion import AstrologicalSubject

    kwargs = dict(
        name="Subject", year=year, month=month, day=day,
        hour=hour, minute=minute, lat=lat, lng=lng,
        tz_str=tz_str, zodiac_type=zodiac_type,
    )
    if sidereal_mode:
        kwargs["sidereal_mode"] = sidereal_mode

    subject = AstrologicalSubject(**kwargs)

    planet_attrs = [
        "sun", "moon", "mercury", "venus", "mars",
        "jupiter", "saturn", "uranus", "neptune", "pluto",
    ]
    planets = {}
    for attr in planet_attrs:
        p = getattr(subject, attr)
        planets[p.name] = {
            "星座": p.sign,
            "度數": round(p.position, 2),
            "宮位": p.house,
            "逆行": p.retrograde,
        }

    house_ordinals = [
        "first", "second", "third", "fourth", "fifth", "sixth",
        "seventh", "eighth", "ninth", "tenth", "eleventh", "twelfth",
    ]
    houses = {}
    for i, ordinal in enumerate(house_ordinals):
        h = getattr(subject, f"{ordinal}_house")
        houses[f"第{i + 1}宮"] = {
            "星座": h.sign,
            "度數": round(h.position, 2),
        }

    label = "回歸黃道 (Tropical)" if zodiac_type == "Tropic" else f"恆星黃道 (Sidereal - {sidereal_mode})"
    return {"制度": label, "行星": planets, "宮位": houses}


def run_western_astro(year: int, month: int, day: int, hour: int, minute: int,
                      lat: float, lng: float, tz_str: str = "Asia/Taipei") -> dict:
    """西洋占星排盤（回歸黃道）"""
    return _run_astro(year, month, day, hour, minute, lat, lng, tz_str, "Tropic")


def run_vedic_astro(year: int, month: int, day: int, hour: int, minute: int,
                    lat: float, lng: float, tz_str: str = "Asia/Taipei") -> dict:
    """印度占星排盤（恆星黃道 Lahiri）"""
    return _run_astro(year, month, day, hour, minute, lat, lng, tz_str, "Sidereal", "LAHIRI")
