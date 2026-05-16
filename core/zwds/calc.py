"""紫微斗數排盤 — CLI wrapper for py-iztro"""
import sys
import json

from py_iztro import Astro

# iztro time_index: 0=早子, 1=丑, 2=寅, ... 12=晚子
# 24小時制轉 time_index（每 2 小時一個時辰）
def hour_to_index(hour):
    if hour == 23:
        return 12
    return hour // 2


# 天干四化表：天干 → (化祿, 化權, 化科, 化忌)
STEM_MUTAGEN = {
    "甲": ("廉貞", "破軍", "武曲", "太陽"),
    "乙": ("天機", "天梁", "紫微", "太陰"),
    "丙": ("天同", "天機", "文昌", "廉貞"),
    "丁": ("太陰", "天同", "天機", "巨門"),
    "戊": ("貪狼", "太陰", "右弼", "天機"),
    "己": ("武曲", "貪狼", "天梁", "文曲"),
    "庚": ("太陽", "武曲", "太陰", "天同"),
    "辛": ("巨門", "太陽", "文曲", "文昌"),
    "壬": ("天梁", "紫微", "左輔", "武曲"),
    "癸": ("破軍", "巨門", "太陰", "貪狼"),
}

MUTAGEN_NAMES = ("化祿", "化權", "化科", "化忌")


def find_star_palace(palaces, star_name):
    """找出某顆星在哪個宮，搜主星和輔星"""
    for p in palaces:
        for s in p.major_stars:
            if s.name == star_name:
                return p.name
        for s in p.minor_stars:
            if s.name == star_name:
                return p.name
    return None


def calc_flying_stars(palaces, palace_names):
    """計算指定宮位的飛星四化路徑

    palace_names: 要分析的宮位名稱列表（如 ["命宮", "財帛", "官祿", "夫妻"]）
    回傳: { "命宮": [{"mutagen": "化祿", "star": "廉貞", "to_palace": "官祿"}, ...], ... }
    """
    result = {}
    for pname in palace_names:
        palace = next((p for p in palaces if p.name == pname), None)
        if not palace:
            continue
        stem = palace.heavenly_stem
        if stem not in STEM_MUTAGEN:
            continue
        stars = STEM_MUTAGEN[stem]
        flights = []
        for i, star_name in enumerate(stars):
            to_palace = find_star_palace(palaces, star_name)
            flights.append({
                "mutagen": MUTAGEN_NAMES[i],
                "star": star_name,
                "to_palace": to_palace,
            })
        result[pname] = flights
    return result


HEAVENLY_STEMS = "甲乙丙丁戊己庚辛壬癸"
EARTHLY_BRANCHES = "子丑寅卯辰巳午未申酉戌亥"


def year_to_stem_branch(year):
    """西曆年 → (天干, 地支)"""
    return HEAVENLY_STEMS[(year - 4) % 10], EARTHLY_BRANCHES[(year - 4) % 12]


def calc_taisui(palaces, other_year):
    """太歲入卦：對方生年地支落入我盤的哪個宮，再用對方天干飛四化

    回傳: {
        "other_stem": "甲", "other_branch": "午",
        "landing_palace": { 宮位資訊 + 主星 },
        "flying_stars": [四化飛到哪]
    }
    """
    stem, branch = year_to_stem_branch(other_year)

    # 找對方地支對應的宮位
    landing = next((p for p in palaces if p.earthly_branch == branch), None)
    if not landing:
        return None

    landing_info = {
        "name": landing.name,
        "major_stars": [s.name for s in landing.major_stars],
        "minor_stars": [s.name for s in landing.minor_stars],
    }

    # 用對方天干飛四化到我盤上
    flights = []
    if stem in STEM_MUTAGEN:
        for i, star_name in enumerate(STEM_MUTAGEN[stem]):
            to_palace = find_star_palace(palaces, star_name)
            flights.append({
                "mutagen": MUTAGEN_NAMES[i],
                "star": star_name,
                "to_palace": to_palace,
            })

    return {
        "other_stem": stem,
        "other_branch": branch,
        "landing_palace": landing_info,
        "flying_stars": flights,
    }


def serialize_star(s):
    result = {"name": s.name}
    if hasattr(s, "brightness") and s.brightness:
        result["brightness"] = s.brightness
    if hasattr(s, "mutagen") and s.mutagen:
        result["mutagen"] = s.mutagen
    if hasattr(s, "type") and s.type:
        result["type"] = str(s.type)
    return result


def serialize_palace(p):
    major = [serialize_star(s) for s in p.major_stars]
    minor = [serialize_star(s) for s in p.minor_stars]

    result = {
        "name": p.name,
        "heavenly_stem": p.heavenly_stem,
        "earthly_branch": p.earthly_branch,
        "is_body_palace": p.is_body_palace,
        "major_stars": major,
        "minor_stars": minor,
    }

    if hasattr(p, "decadal") and p.decadal:
        d = p.decadal
        result["decadal"] = {
            "range": d.range if hasattr(d, "range") else None,
        }
    if hasattr(p, "ages") and p.ages:
        result["ages"] = list(p.ages)

    return result


def calc_natal(year, month, day, hour, gender):
    """本命盤"""
    date_str = f"{year}-{month}-{day}"
    time_idx = hour_to_index(hour)

    a = Astro().by_solar(date_str, time_idx, gender, language="zh-TW")

    palaces = [serialize_palace(p) for p in a.palaces]

    # 找命宮主星
    soul_palace = next((p for p in a.palaces if p.name == "命宮"), None)
    soul_majors = [s.name for s in soul_palace.major_stars] if soul_palace else []

    # 找身宮位置
    body_palace = next((p for p in a.palaces if p.is_body_palace), None)
    body_palace_name = body_palace.name if body_palace else ""

    # 本命四化（從命宮天干推）
    natal_mutagen = []
    if soul_palace:
        # 從 palaces 裡找有四化標記的星
        for p in a.palaces:
            for s in p.major_stars:
                if s.mutagen:
                    natal_mutagen.append({
                        "star": s.name,
                        "mutagen": s.mutagen,
                        "palace": p.name,
                    })

    # 飛星四化：命宮、財帛、官祿、夫妻
    flying = calc_flying_stars(a.palaces, ["命宮", "財帛", "官祿", "夫妻"])

    return {
        "mode": "natal",
        "soul_star": a.soul,
        "soul_palace_majors": soul_majors,
        "body_star": a.body,
        "body_palace": body_palace_name,
        "five_elements_class": a.five_elements_class,
        "chinese_date": a.chinese_date,
        "sign": a.sign if hasattr(a, "sign") else "",
        "zodiac": a.zodiac if hasattr(a, "zodiac") else "",
        "palaces": palaces,
        "natal_mutagen": natal_mutagen,
        "flying_stars": flying,
    }


def calc_horoscope(year, month, day, hour, gender,
                   target_year, target_month=None, target_day=None):
    """流年/流月/流日"""
    date_str = f"{year}-{month}-{day}"
    time_idx = hour_to_index(hour)

    a = Astro().by_solar(date_str, time_idx, gender, language="zh-TW")

    # 決定 horoscope 日期
    if target_day:
        h_date = f"{target_year}-{target_month}-{target_day}"
    elif target_month:
        h_date = f"{target_year}-{target_month}-15"
    else:
        h_date = f"{target_year}-6-15"

    h = a.horoscope(h_date)

    result = {
        "target_date": h_date,
    }

    # 大限
    if h.decadal:
        result["decadal"] = {
            "stem_branch": f"{h.decadal.heavenly_stem}{h.decadal.earthly_branch}",
            "mutagen": h.decadal.mutagen,
            "palace_names": h.decadal.palace_names,
        }

    # 流年
    if h.yearly:
        result["yearly"] = {
            "stem_branch": f"{h.yearly.heavenly_stem}{h.yearly.earthly_branch}",
            "mutagen": h.yearly.mutagen,
            "palace_names": h.yearly.palace_names,
        }

    # 流月
    if h.monthly:
        result["monthly"] = {
            "stem_branch": f"{h.monthly.heavenly_stem}{h.monthly.earthly_branch}",
            "mutagen": h.monthly.mutagen,
            "palace_names": h.monthly.palace_names,
        }

    # 流日
    if h.daily:
        result["daily"] = {
            "stem_branch": f"{h.daily.heavenly_stem}{h.daily.earthly_branch}",
            "mutagen": h.daily.mutagen,
            "palace_names": h.daily.palace_names,
        }

    return result


def calc_yearly_overview(year, month, day, hour, gender, target_year):
    """流年 12 個月總覽"""
    results = []
    for m in range(1, 13):
        h = calc_horoscope(year, month, day, hour, gender, target_year, m, 15)
        h["period"] = f"{target_year}-{m:02d}"
        results.append(h)
    return results


if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage:")
        print("  本命: python calc.py YEAR MONTH DAY HOUR GENDER")
        print("  流日: python calc.py YEAR MONTH DAY HOUR GENDER transit TYEAR TMONTH TDAY")
        print("  流月: python calc.py YEAR MONTH DAY HOUR GENDER monthly TYEAR TMONTH")
        print("  流年: python calc.py YEAR MONTH DAY HOUR GENDER yearly TYEAR")
        print("  太歲入卦: python calc.py YEAR MONTH DAY HOUR GENDER taisui OTHER_YEAR")
        print()
        print("  HOUR = 24小時制 (0-23)")
        print("  GENDER = 男 or 女")
        print("  OTHER_YEAR = 對方出生年（西曆）")
        sys.exit(1)

    year = int(sys.argv[1])
    month = int(sys.argv[2])
    day = int(sys.argv[3])
    hour = int(sys.argv[4])
    gender = sys.argv[5]

    mode = sys.argv[6] if len(sys.argv) > 6 else "natal"

    if mode == "natal":
        # 本命盤
        natal = calc_natal(year, month, day, hour, gender)
        print(json.dumps(natal, ensure_ascii=False, indent=2))

    elif mode == "transit":
        # 流日：本命 + 指定日期的 horoscope
        ty, tm, td = int(sys.argv[7]), int(sys.argv[8]), int(sys.argv[9])
        natal = calc_natal(year, month, day, hour, gender)
        horoscope = calc_horoscope(year, month, day, hour, gender, ty, tm, td)
        print(json.dumps({"natal": natal, "horoscope": horoscope}, ensure_ascii=False, indent=2))

    elif mode == "monthly":
        # 流月：本命 + 指定月份
        ty, tm = int(sys.argv[7]), int(sys.argv[8])
        natal = calc_natal(year, month, day, hour, gender)
        horoscope = calc_horoscope(year, month, day, hour, gender, ty, tm)
        print(json.dumps({"natal": natal, "horoscope": horoscope}, ensure_ascii=False, indent=2))

    elif mode == "yearly":
        # 流年：本命 + 12 個月總覽
        ty = int(sys.argv[7])
        natal = calc_natal(year, month, day, hour, gender)
        overview = calc_yearly_overview(year, month, day, hour, gender, ty)
        print(json.dumps({"natal": natal, "yearly_overview": overview}, ensure_ascii=False, indent=2))

    elif mode == "taisui":
        # 太歲入卦：本命 + 對方生年入卦分析
        other_year = int(sys.argv[7])
        natal = calc_natal(year, month, day, hour, gender)
        a = Astro().by_solar(f"{year}-{month}-{day}", hour_to_index(hour), gender, language="zh-TW")
        taisui = calc_taisui(a.palaces, other_year)
        print(json.dumps({"natal": natal, "taisui": taisui}, ensure_ascii=False, indent=2))

    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)
