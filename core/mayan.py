"""
瑪雅曆排盤引擎。

包含 Long Count（長紀曆）、Tzolkin（卓爾金 260 天）、Haab（哈布 365 天）、
Lord of the Night（夜主九曜）、Year Bearer（年主）、以及 Harmonic 關係分析。

採用 GMT correlation 584283（Goodman–Martinez–Thompson），
瑪雅紀元 0.0.0.0.0 = Julian Day 584283 = 公元前 3114-08-11（西曆）
= 4 Ahau 8 Cumku，Lord G9。
"""

from datetime import date, timedelta

# ========== 常數表 ==========

# 20 個 Day Sign（日名），索引 0-19
# 格式：(Yucatec 名, 中文, 元素, 方位, 色, 關鍵字)
DAY_SIGNS = [
    ("Imix",      "鱷魚", "水", "東", "紅", "滋養、源頭、母性、生存本能"),
    ("Ik",        "風",   "風", "北", "白", "溝通、呼吸、靈感、訊息"),
    ("Akbal",     "夜",   "夜", "西", "藍", "內省、夢境、直覺、神秘"),
    ("Kan",       "種子", "火", "南", "黃", "成長、潛能、發芽、意圖"),
    ("Chicchan",  "蛇",   "火", "東", "紅", "生命力、本能、蛻變、熱情"),
    ("Cimi",      "死",   "水", "北", "白", "轉化、放下、結束、重生"),
    ("Manik",     "鹿",   "風", "西", "藍", "完成、工具、療癒、平衡"),
    ("Lamat",     "星",   "土", "南", "黃", "豐盛、藝術、優雅、金星"),
    ("Muluc",     "月",   "水", "東", "紅", "情緒、水、淨化、記憶"),
    ("Oc",        "狗",   "火", "北", "白", "忠誠、陪伴、愛、引導"),
    ("Chuen",     "猴",   "風", "西", "藍", "創造、遊戲、藝術家、織布"),
    ("Eb",        "路",   "土", "南", "黃", "人生道路、謙卑、服務、旅程"),
    ("Ben",       "蘆葦", "火", "東", "紅", "探索、支柱、成長、權威"),
    ("Ix",        "美洲豹", "土", "北", "白", "魔法、薩滿、秘密、心"),
    ("Men",       "鷹",   "風", "西", "藍", "願景、高度、遠見、心智"),
    ("Cib",       "戰士", "水", "南", "黃", "智慧、反思、戰士、祖先"),
    ("Caban",     "地震", "火", "東", "紅", "動能、同步、進化、大地"),
    ("Etznab",    "燧石", "水", "北", "白", "鏡子、真實、切割、反映"),
    ("Cauac",     "風暴", "火", "西", "藍", "淨化、雷雨、自我生成、能量"),
    ("Ahau",      "太陽", "火", "南", "黃", "光、開悟、無條件的愛、圓滿"),
]

# 13 個 Tone（調性），索引 0-12（對應 1-13）
# 格式：(中文名, 能量動詞, 問題, 關鍵字)
TONES = [
    ("磁性", "吸引", "我的目的是什麼？",     "統一、意圖、起步、定位"),
    ("月亮", "穩定", "我的挑戰是什麼？",     "兩極、極性、挑戰、清理"),
    ("電力", "激活", "我如何最佳服務？",     "行動、連結、服務、鍵結"),
    ("自我存在", "定義", "我的形式是什麼？", "形式、測量、定義、結構"),
    ("超頻", "賦能", "我如何賦予自己力量？", "放射、輻射、命令、中心"),
    ("韻律", "組織", "我如何擴展快樂？",     "平衡、平等、組織、回應"),
    ("共振", "啟發", "我如何啟發他人？",     "神秘、協調、頻率、管道"),
    ("銀河", "和諧", "我是否如我所信而活？", "正直、榜樣、和諧、建模"),
    ("太陽", "實現", "我如何實現目的？",     "意圖、脈動、實現、頂點"),
    ("行星", "完美", "我如何完善所為？",     "顯化、生產、完美、對齊"),
    ("光譜", "釋放", "我如何釋放放下？",     "解散、釋放、解放、解放"),
    ("水晶", "奉獻", "我如何奉獻？",         "合作、普遍化、合作、圓桌"),
    ("宇宙", "超越", "我如何擴展存在？",     "臨在、忍耐、超越、飛行"),
]

# 19 個 Haab 月（18 個月 + Wayeb），索引 0-18
# Wayeb 是 5 天的不祥時期
HAAB_MONTHS = [
    ("Pop",     "墊子"),
    ("Uo",      "青蛙"),
    ("Zip",     "紅雲"),
    ("Zotz",    "蝙蝠"),
    ("Tzec",    "死亡"),
    ("Xul",     "狗"),
    ("Yaxkin",  "新太陽"),
    ("Mol",     "水"),
    ("Chen",    "井"),
    ("Yax",     "綠"),
    ("Zac",     "白"),
    ("Ceh",     "紅"),
    ("Mac",     "合"),
    ("Kankin",  "黃日"),
    ("Muan",    "貓頭鷹"),
    ("Pax",     "鼓"),
    ("Kayab",   "歌龜"),
    ("Cumku",   "穀倉"),
    ("Wayeb",   "無名日"),  # 只有 5 天（0-4）
]

# 9 個 Lord of the Night（夜主），索引 0-8（對應 G1-G9）
LORDS_OF_NIGHT = [
    ("G1", "大地夜主", "根基、穩定"),
    ("G2", "玉米夜主", "滋養、豐饒"),
    ("G3", "雨水夜主", "流動、淨化"),
    ("G4", "玉石夜主", "價值、珍貴"),
    ("G5", "戰爭夜主", "衝突、決斷"),
    ("G6", "死亡夜主", "轉化、結束"),
    ("G7", "鏡子夜主", "真實、反映"),
    ("G8", "祖靈夜主", "智慧、傳承"),
    ("G9", "光夜主",   "覺醒、圓滿"),
]

# GMT correlation 常數
GMT_CORRELATION = 584283  # JDN for Maya epoch 0.0.0.0.0

# Tikal 年主系統：只有 4 個可能的 Year Bearer 日名
TIKAL_YEAR_BEARERS = {1, 6, 11, 16}  # Ik, Manik, Eb, Caban


# ========== 基礎轉換 ==========

def gregorian_to_jdn(year: int, month: int, day: int) -> int:
    """西曆轉 Julian Day Number。支援負年份（BCE）。"""
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def jdn_to_gregorian(jdn: int) -> tuple[int, int, int]:
    """JDN 轉西曆。"""
    a = jdn + 32044
    b = (4 * a + 3) // 146097
    c = a - (146097 * b) // 4
    d = (4 * c + 3) // 1461
    e = c - (1461 * d) // 4
    m = (5 * e + 2) // 153
    day = e - (153 * m + 2) // 5 + 1
    month = m + 3 - 12 * (m // 10)
    year = 100 * b + d - 4800 + m // 10
    return year, month, day


def days_since_epoch(year: int, month: int, day: int) -> int:
    """距離瑪雅紀元的天數。"""
    return gregorian_to_jdn(year, month, day) - GMT_CORRELATION


# ========== 曆法計算 ==========

def long_count(days: int) -> tuple[int, int, int, int, int]:
    """長紀曆：Baktun.Katun.Tun.Uinal.Kin"""
    baktun, r = divmod(days, 144000)
    katun, r = divmod(r, 7200)
    tun, r = divmod(r, 360)
    uinal, kin = divmod(r, 20)
    return baktun, katun, tun, uinal, kin


def tzolkin(days: int) -> tuple[int, int]:
    """卓爾金曆：回傳 (tone 1-13, sign_index 0-19)。
    基準點：0.0.0.0.0 = 4 Ahau（tone=4, sign=19）。"""
    tone = ((days + 3) % 13) + 1
    sign = (days + 19) % 20
    return tone, sign


def haab(days: int) -> tuple[int, int]:
    """哈布曆：回傳 (month_index 0-18, day_in_month)。
    基準點：0.0.0.0.0 = 8 Cumku（month=17, day=8，年內第 348 天）。
    Wayeb (month=18) 只有 5 天（day 0-4）。"""
    haab_day = (days + 348) % 365
    month = haab_day // 20
    day_in_month = haab_day % 20
    return month, day_in_month


def lord_of_night(days: int) -> int:
    """夜主九曜：回傳 1-9。基準點 0.0.0.0.0 = G9。"""
    return ((days + 8) % 9) + 1


def tzolkin_index(tone: int, sign: int) -> int:
    """Tzolkin 在 260 天中的序號（Kin 1-260）。"""
    # 找到滿足 (n % 13) + 1 == tone 且 n % 20 == sign 的 n，n 在 0-259
    for n in range(260):
        if (n % 13) + 1 == tone and n % 20 == sign:
            return n + 1
    return 0  # unreachable


# ========== 年主（Year Bearer） ==========

def haab_new_year_jdn(gregorian_year: int) -> int:
    """找出指定西曆年內，最接近 1 月的 Haab 新年（0 Pop）之 JDN。
    若該年沒有 0 Pop，回傳最接近的一個。"""
    # 從該年 1/1 起算，往後找第一個 haab_day == 0 的日子
    jan1 = gregorian_to_jdn(gregorian_year, 1, 1)
    ds = jan1 - GMT_CORRELATION
    offset = (365 - ((ds + 348) % 365)) % 365
    return jan1 + offset


def year_bearer(gregorian_year: int) -> tuple[int, int, int]:
    """指定西曆年的 Year Bearer。
    回傳 (tone, sign_index, new_year_jdn)。"""
    jdn = haab_new_year_jdn(gregorian_year)
    ds = jdn - GMT_CORRELATION
    tone, sign = tzolkin(ds)
    return tone, sign, jdn


# ========== Harmonic 關係 ==========

def harmonic_relation(sign_a: int, sign_b: int) -> str:
    """判斷兩個 Tzolkin 日名的 Harmonic 關係。
    - 相同：同一日名，能量共振
    - 挑戰 (Antipode)：相差 10，對立面帶來成長
    - 隱藏 (Occult)：相加等於 19，潛在天賦或秘密支持
    - 其他：中性"""
    if sign_a == sign_b:
        return "相同"
    if (sign_a + 10) % 20 == sign_b:
        return "挑戰"
    if sign_a + sign_b == 19:
        return "隱藏"
    return "中性"


def antipode_sign(sign: int) -> int:
    return (sign + 10) % 20


def occult_sign(sign: int) -> int:
    return 19 - sign


# ========== 格式化輸出 ==========

def format_day(days: int) -> dict:
    """把一個日子（距紀元天數）展開成完整 Maya 日期資訊。"""
    bk, kt, tn, un, kn = long_count(days)
    tone, sign = tzolkin(days)
    hm, hd = haab(days)
    lord = lord_of_night(days)
    kin = tzolkin_index(tone, sign)

    sign_info = DAY_SIGNS[sign]
    tone_info = TONES[tone - 1]
    month_info = HAAB_MONTHS[hm]
    lord_info = LORDS_OF_NIGHT[lord - 1]

    return {
        "long_count": f"{bk}.{kt}.{tn}.{un}.{kn}",
        "long_count_parts": {
            "baktun": bk, "katun": kt, "tun": tn, "uinal": un, "kin": kn
        },
        "tzolkin": {
            "kin": kin,
            "tone": tone,
            "tone_name": tone_info[0],
            "tone_action": tone_info[1],
            "tone_question": tone_info[2],
            "sign_index": sign,
            "sign_name": sign_info[0],
            "sign_cn": sign_info[1],
            "element": sign_info[2],
            "direction": sign_info[3],
            "color": sign_info[4],
            "keywords": sign_info[5],
            "display": f"{tone} {sign_info[0]} ({sign_info[1]})",
        },
        "haab": {
            "month_index": hm,
            "month_name": month_info[0],
            "month_cn": month_info[1],
            "day": hd,
            "display": f"{hd} {month_info[0]}",
            "is_wayeb": hm == 18,
        },
        "lord_of_night": {
            "index": lord,
            "name": lord_info[0],
            "cn": lord_info[1],
            "meaning": lord_info[2],
        },
    }


# ========== 主要 API ==========

def run_mayan_natal(year: int, month: int, day: int) -> dict:
    """瑪雅曆本命盤。

    輸入：西曆年月日（不需時間與出生地）
    輸出：Long Count、Tzolkin、Haab、Lord of Night、Galactic Signature、
          Harmonic 家族、本命日名與調性的能量主題"""
    days = days_since_epoch(year, month, day)
    info = format_day(days)

    sign = info["tzolkin"]["sign_index"]
    tone = info["tzolkin"]["tone"]
    sign_info = DAY_SIGNS[sign]
    tone_info = TONES[tone - 1]

    # Harmonic 家族：挑戰 + 隱藏
    anti = antipode_sign(sign)
    occ = occult_sign(sign)

    # 本命所在的 Haab 年的 Year Bearer
    # 出生日落在當年 0 Pop 之前 → 還在前一個 Haab 年，bearer 取 year-1
    birth_jdn = gregorian_to_jdn(year, month, day)
    haab_year = year if birth_jdn >= haab_new_year_jdn(year) else year - 1
    yb_tone, yb_sign, _ = year_bearer(haab_year)
    yb_info = DAY_SIGNS[yb_sign]
    yb_relation = harmonic_relation(sign, yb_sign)
    yb_tikal = yb_sign in TIKAL_YEAR_BEARERS

    return {
        "birth": {"year": year, "month": month, "day": day},
        "long_count": info["long_count"],
        "long_count_parts": info["long_count_parts"],
        "tzolkin": info["tzolkin"],
        "haab": info["haab"],
        "lord_of_night": info["lord_of_night"],
        "galactic_signature": {
            "display": info["tzolkin"]["display"],
            "kin": info["tzolkin"]["kin"],
            "theme": f"{tone_info[1]}的{sign_info[1]}",
            "life_question": tone_info[2],
            "gift": sign_info[5],
            "tone_energy": tone_info[3],
        },
        "harmonic_family": {
            "self": {
                "sign_name": sign_info[0],
                "sign_cn": sign_info[1],
                "meaning": "你的本命能量",
            },
            "antipode": {
                "sign_name": DAY_SIGNS[anti][0],
                "sign_cn": DAY_SIGNS[anti][1],
                "meaning": "對立面，帶來成長的挑戰",
                "keywords": DAY_SIGNS[anti][5],
            },
            "occult": {
                "sign_name": DAY_SIGNS[occ][0],
                "sign_cn": DAY_SIGNS[occ][1],
                "meaning": "隱藏的天賦與秘密支持",
                "keywords": DAY_SIGNS[occ][5],
            },
        },
        "birth_year_bearer": {
            "tone": yb_tone,
            "sign_name": yb_info[0],
            "sign_cn": yb_info[1],
            "display": f"{yb_tone} {yb_info[0]} ({yb_info[1]})",
            "relation_to_natal": yb_relation,
            "is_tikal_bearer": yb_tikal,
            "meaning": "你出生那個 Haab 年的主宰日，為本命加上年度底色",
        },
    }


def run_mayan_fortune(
    year: int, month: int, day: int,
    target_year: int | None = None,
    forecast_years: int = 10,
) -> dict:
    """瑪雅曆大運 + 流年 + 流月。

    - 大運：52 年 Calendar Round 人生週期 + Katun 階段切分
    - 流年：從 target_year 起 N 年，每年 Year Bearer 與本命的 Harmonic 關係
    - 流月：當前所在的 Trecena（13 天）與 Haab Uinal（20 天）"""
    from datetime import date as _date
    today = _date.today()
    if target_year is None:
        # 預設取「當下所在的 Haab 年」，避免今天在 0 Pop 前時跳過進行中的年
        today_jdn = gregorian_to_jdn(today.year, today.month, today.day)
        target_year = today.year if today_jdn >= haab_new_year_jdn(today.year) else today.year - 1

    natal_days = days_since_epoch(year, month, day)
    natal_info = format_day(natal_days)
    natal_sign = natal_info["tzolkin"]["sign_index"]
    natal_tone = natal_info["tzolkin"]["tone"]

    # ===== 大運：52 年 Calendar Round =====
    # Calendar Round = 18980 天（260 × 73 = 365 × 52）
    round_length_days = 18980
    round_length_years = 52
    age_days = days_since_epoch(today.year, today.month, today.day) - natal_days
    current_round_position_days = age_days % round_length_days
    current_round_position_years = current_round_position_days / 365.25
    next_signature_return_jdn = gregorian_to_jdn(year, month, day) + round_length_days
    while next_signature_return_jdn < gregorian_to_jdn(today.year, today.month, today.day):
        next_signature_return_jdn += round_length_days
    nsr_y, nsr_m, nsr_d = jdn_to_gregorian(next_signature_return_jdn)

    # Katun 階段：每 ~19.7 年（7200 天）一個生命階段
    katun_days = 7200
    current_katun_stage = age_days // katun_days + 1
    current_katun_start_age = ((age_days // katun_days) * katun_days) / 365.25
    current_katun_end_age = (((age_days // katun_days) + 1) * katun_days) / 365.25

    katun_stages = []
    for i in range(5):  # 前 5 個 Katun 階段 ≈ 0-98 歲
        start_days = i * katun_days
        end_days = (i + 1) * katun_days
        stage_start_date = gregorian_to_jdn(year, month, day) + start_days
        sy, sm, sd = jdn_to_gregorian(stage_start_date)
        stage_days_point = natal_days + start_days
        stage_info = format_day(stage_days_point)
        katun_stages.append({
            "stage": i + 1,
            "age_range": f"{start_days/365.25:.1f}–{end_days/365.25:.1f}",
            "start_date": f"{sy}-{sm:02d}-{sd:02d}",
            "signature": stage_info["tzolkin"]["display"],
            "theme": DAY_SIGNS[stage_info["tzolkin"]["sign_index"]][5],
            "is_current": i + 1 == current_katun_stage,
        })

    # ===== 流年：每年 Year Bearer 與本命的互動 =====
    yearly = []
    for i in range(forecast_years):
        y = target_year + i
        yb_tone, yb_sign, yb_jdn = year_bearer(y)
        yb_y, yb_m, yb_d = jdn_to_gregorian(yb_jdn)
        relation = harmonic_relation(natal_sign, yb_sign)
        yb_info = DAY_SIGNS[yb_sign]
        yearly.append({
            "year": y,
            "new_year_date": f"{yb_y}-{yb_m:02d}-{yb_d:02d}",
            "bearer": f"{yb_tone} {yb_info[0]} ({yb_info[1]})",
            "bearer_sign": yb_info[0],
            "bearer_cn": yb_info[1],
            "bearer_tone": yb_tone,
            "relation_to_natal": relation,
            "theme": yb_info[5],
            "tone_energy": TONES[yb_tone - 1][3],
            "year_question": TONES[yb_tone - 1][2],
            "is_tikal_bearer": yb_sign in TIKAL_YEAR_BEARERS,
        })

    # ===== 流月：當前 Trecena + Haab Uinal =====
    today_days = days_since_epoch(today.year, today.month, today.day)
    today_info = format_day(today_days)
    today_tone, today_sign = tzolkin(today_days)

    # Trecena 起始日：回推到 tone=1 的那一天
    trecena_offset = today_tone - 1
    trecena_start_days = today_days - trecena_offset
    ts_y, ts_m, ts_d = jdn_to_gregorian(trecena_start_days + GMT_CORRELATION)
    trecena_start_info = format_day(trecena_start_days)
    trecena_end_days = trecena_start_days + 12
    te_y, te_m, te_d = jdn_to_gregorian(trecena_end_days + GMT_CORRELATION)
    trecena_sign_idx = trecena_start_info["tzolkin"]["sign_index"]

    # Haab Uinal：當前所在的 20 天月份
    haab_month_idx, haab_day_in_month = haab(today_days)
    haab_month_info = HAAB_MONTHS[haab_month_idx]
    haab_month_start_days = today_days - haab_day_in_month
    hs_y, hs_m, hs_d = jdn_to_gregorian(haab_month_start_days + GMT_CORRELATION)

    return {
        "natal": {
            "birth": {"year": year, "month": month, "day": day},
            "signature": natal_info["tzolkin"]["display"],
            "kin": natal_info["tzolkin"]["kin"],
        },
        "calendar_round": {
            "length_years": round_length_years,
            "current_position_years": round(current_round_position_years, 1),
            "progress_percent": round(current_round_position_days / round_length_days * 100, 1),
            "next_signature_return": f"{nsr_y}-{nsr_m:02d}-{nsr_d:02d}",
            "meaning": "52 年 Calendar Round 是瑪雅的大運週期，Signature 重現代表新週期起點",
        },
        "katun_stages": {
            "current_stage": current_katun_stage,
            "current_age_range": f"{current_katun_start_age:.1f}–{current_katun_end_age:.1f}",
            "stages": katun_stages,
            "meaning": "個人生命週期，每 ~19.7 年（7200 天）一段，以該段起點的 Kin 為能量基調。非 Long Count 的 cosmic Katun。",
        },
        "yearly": yearly,
        "current_trecena": {
            "start_date": f"{ts_y}-{ts_m:02d}-{ts_d:02d}",
            "end_date": f"{te_y}-{te_m:02d}-{te_d:02d}",
            "lead_sign": DAY_SIGNS[trecena_sign_idx][0],
            "lead_sign_cn": DAY_SIGNS[trecena_sign_idx][1],
            "theme": DAY_SIGNS[trecena_sign_idx][5],
            "today_tone": today_tone,
            "today_position": f"第 {today_tone}/13 天",
            "meaning": "Trecena 是 13 天的能量波，以 tone 1 的日名為主題",
        },
        "current_haab_month": {
            "month_name": haab_month_info[0],
            "month_cn": haab_month_info[1],
            "start_date": f"{hs_y}-{hs_m:02d}-{hs_d:02d}",
            "day_in_month": haab_day_in_month,
            "is_wayeb": haab_month_idx == 18,
            "meaning": "Haab 月份是 20 天（Wayeb 為 5 天），代表該月的社會/季節基調",
        },
    }


def run_mayan_transit(
    year: int, month: int, day: int,
    target_date: str | None = None,
) -> dict:
    """瑪雅曆當下能量：指定日期的 Kin + 當日與本命的 Harmonic 關係。

    target_date 格式 YYYY-MM-DD，預設今天。"""
    if target_date:
        parts = target_date.split("-")
        ty, tm, td = int(parts[0]), int(parts[1]), int(parts[2])
    else:
        today = date.today()
        ty, tm, td = today.year, today.month, today.day

    natal_days = days_since_epoch(year, month, day)
    natal_info = format_day(natal_days)
    natal_sign = natal_info["tzolkin"]["sign_index"]

    target_days = days_since_epoch(ty, tm, td)
    target_info = format_day(target_days)
    target_sign = target_info["tzolkin"]["sign_index"]

    relation = harmonic_relation(natal_sign, target_sign)
    age_days = target_days - natal_days

    return {
        "natal": {
            "birth": {"year": year, "month": month, "day": day},
            "signature": natal_info["tzolkin"]["display"],
        },
        "target_date": f"{ty}-{tm:02d}-{td:02d}",
        "age_days": age_days,
        "day_info": target_info,
        "relation_to_natal": relation,
        "relation_meaning": {
            "相同": "能量共振日，你本質的頻率在放大",
            "挑戰": "對立面啟動，適合面對盲點、突破慣性",
            "隱藏": "隱性支持日，直覺與潛意識能量在運作",
            "中性": "日常能量，以當日 Kin 的主題為主",
        }.get(relation, ""),
    }
