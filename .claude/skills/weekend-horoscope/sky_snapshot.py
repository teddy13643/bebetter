#!/usr/bin/env python3
"""
週末天象快照計算器
給定日期，回傳該週末（週六＋週日）的行星位置、月亮換座、月亮相位、月相、空亡時段。

所有時間都以 Asia/Taipei (UTC+8) 的 naive datetime 表示。
"""

import sys
import json
from datetime import datetime, timedelta

import swisseph as swe

TZ_OFFSET_HOURS = 8  # Asia/Taipei

SIGNS = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir',
         'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis']

SIGN_ZH = {
    'Ari': '牡羊', 'Tau': '金牛', 'Gem': '雙子', 'Can': '巨蟹',
    'Leo': '獅子', 'Vir': '處女', 'Lib': '天秤', 'Sco': '天蠍',
    'Sag': '射手', 'Cap': '摩羯', 'Aqu': '水瓶', 'Pis': '雙魚'
}

SIGN_EMOJI = {
    'Ari': '♈', 'Tau': '♉', 'Gem': '♊', 'Can': '♋',
    'Leo': '♌', 'Vir': '♍', 'Lib': '♎', 'Sco': '♏',
    'Sag': '♐', 'Cap': '♑', 'Aqu': '♒', 'Pis': '♓'
}

PLANET_ZH = {
    'Sun': '太陽', 'Moon': '月亮', 'Mercury': '水星', 'Venus': '金星',
    'Mars': '火星', 'Jupiter': '木星', 'Saturn': '土星',
    'Uranus': '天王星', 'Neptune': '海王星', 'Pluto': '冥王星'
}

PLANETS_SWE = {
    'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY, 'Venus': swe.VENUS,
    'Mars': swe.MARS, 'Jupiter': swe.JUPITER, 'Saturn': swe.SATURN,
    'Uranus': swe.URANUS, 'Neptune': swe.NEPTUNE, 'Pluto': swe.PLUTO,
}

HOUSE_THEMES = {
    1: '自我、外在狀態',
    2: '花錢、享受、美食',
    3: '聊天、出門走走、學東西',
    4: '待在家、整理空間、家人',
    5: '約會、玩樂、創作',
    6: '運動、整理、做正事',
    7: '約人、一對一互動',
    8: '深度對話、理財、親密',
    9: '旅行、看書、探索新地方',
    10: '想工作規劃、社群經營',
    11: '朋友聚會、參加活動',
    12: '獨處、休息、充電'
}

# 相位定義：(角度, 外行星容許度, 月亮容許度)
# 月亮移動快，傳統占星月亮 orb 比外行星寬
ASPECTS = {
    '合相': {'angle': 0,   'orb_moon': 8, 'orb_default': 6},
    '六分': {'angle': 60,  'orb_moon': 4, 'orb_default': 3},
    '四分': {'angle': 90,  'orb_moon': 7, 'orb_default': 5},
    '三分': {'angle': 120, 'orb_moon': 7, 'orb_default': 5},
    '對分': {'angle': 180, 'orb_moon': 8, 'orb_default': 6},
}

ASPECT_NATURE = {
    '合相': '強化',
    '六分': '和諧',
    '四分': '張力',
    '三分': '順流',
    '對分': '拉扯',
}

# 星座守護星（傳統）— 用於月亮相位、相位主導性等運算
SIGN_RULER = {
    'Ari': 'Mars', 'Tau': 'Venus', 'Gem': 'Mercury', 'Can': 'Moon',
    'Leo': 'Sun', 'Vir': 'Mercury', 'Lib': 'Venus', 'Sco': 'Mars',
    'Sag': 'Jupiter', 'Cap': 'Saturn', 'Aqu': 'Saturn', 'Pis': 'Jupiter'
}

# 現代共同守護：Pluto/Uranus/Neptune 對應的星座，補強現代占星共識
MODERN_CORULER_SIGNS = {
    'Pluto': 'Sco',
    'Uranus': 'Aqu',
    'Neptune': 'Pis',
}

# 月相分界（以 Moon-Sun 黃經差為準，0° = 新月，180° = 滿月）
MOON_PHASES = [
    (22.5,  '新月',   '🌑', '重啟、許願、定新方向'),
    (67.5,  '眉月',   '🌒', '醞釀、輕推、探索'),
    (112.5, '上弦月', '🌓', '行動、突破、做決定'),
    (157.5, '盈凸月', '🌔', '調整、修正、持續推進'),
    (202.5, '滿月',   '🌕', '情緒放大、高光時刻、關鍵揭曉'),
    (247.5, '虧凸月', '🌖', '分享、回顧、感謝'),
    (292.5, '下弦月', '🌗', '放手、斷捨離、整理'),
    (337.5, '殘月',   '🌘', '休息、沉澱、結束循環'),
]


def _jd(dt_local):
    """把 Asia/Taipei naive datetime 轉 UT julian day"""
    dt_utc = dt_local - timedelta(hours=TZ_OFFSET_HOURS)
    hour_fraction = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hour_fraction)


def planet_state(dt_local, planet_name):
    """回傳行星 (黃經度, 速度 deg/day)"""
    pid = PLANETS_SWE[planet_name]
    pos, _ = swe.calc_ut(_jd(dt_local), pid)
    return pos[0], pos[3]  # longitude, speed


def sign_index(lon):
    """黃經度轉星座 index (0 = Ari)"""
    return int(lon / 30) % 12


def extract_planets(dt_local):
    """取得某時刻所有行星狀態"""
    planets = {}
    for name in PLANETS_SWE:
        lon, speed = planet_state(dt_local, name)
        idx = sign_index(lon)
        planets[name] = {
            'sign': SIGNS[idx],
            'sign_zh': SIGN_ZH[SIGNS[idx]],
            'emoji': SIGN_EMOJI[SIGNS[idx]],
            'degree': round(lon % 30, 2),
            'abs_pos': round(lon, 2),
            'retrograde': speed < 0,
            'speed': round(speed, 4),
        }
    return planets


def angular_diff(a, b):
    """兩個黃經的最短角距 (0~180)"""
    d = abs(a - b) % 360
    return 360 - d if d > 180 else d


def calc_aspect(pos1, pos2, involves_moon=False):
    """計算兩個絕對黃經之間的相位"""
    diff = angular_diff(pos1, pos2)
    for name, spec in ASPECTS.items():
        orb_limit = spec['orb_moon'] if involves_moon else spec['orb_default']
        orb = abs(diff - spec['angle'])
        if orb <= orb_limit:
            return {
                'aspect': name,
                'nature': ASPECT_NATURE[name],
                'orb': round(orb, 2),
            }
    return None


def collect_moon_aspects_over_day(day_start, day_end, step_hours=3):
    """在一天內多個時間點取樣月亮相位，聚合成該天出現過的相位（取每個 planet-aspect 最緊 orb）"""
    step = timedelta(hours=step_hours)
    t = day_start
    # key: (planet, aspect_name) -> {'orb': min_orb, 'nature': ..., 'planet_zh': ...}
    best = {}
    while t <= day_end:
        moon_lon, _ = planet_state(t, 'Moon')
        for name in PLANETS_SWE:
            if name == 'Moon':
                continue
            p_lon, _ = planet_state(t, name)
            asp = calc_aspect(moon_lon, p_lon, involves_moon=True)
            if asp:
                key = (name, asp['aspect'])
                if key not in best or asp['orb'] < best[key]['orb']:
                    best[key] = {
                        'planet': name,
                        'planet_zh': PLANET_ZH[name],
                        'aspect': asp['aspect'],
                        'nature': asp['nature'],
                        'orb': asp['orb'],
                    }
        t += step
    aspects = sorted(best.values(), key=lambda x: x['orb'])
    return aspects


def get_interplanetary_aspects(planets):
    """行星間主要相位（不含月亮）"""
    names = [n for n in planets if n != 'Moon']
    aspects = []
    for i, n1 in enumerate(names):
        for n2 in names[i + 1:]:
            asp = calc_aspect(planets[n1]['abs_pos'], planets[n2]['abs_pos'], involves_moon=False)
            if asp:
                aspects.append({
                    'planet1': n1, 'planet1_zh': PLANET_ZH[n1],
                    'planet2': n2, 'planet2_zh': PLANET_ZH[n2],
                    **asp
                })
    aspects.sort(key=lambda x: x['orb'])
    return aspects


def house_from_sign(planet_sign, rising_sign):
    return ((SIGNS.index(planet_sign) - SIGNS.index(rising_sign)) % 12) + 1


def find_next_saturday(today):
    days_until_sat = (5 - today.weekday()) % 7
    if days_until_sat == 0:
        return today
    return today + timedelta(days=days_until_sat)


def find_moon_sign_change(start_dt, end_dt):
    """二分搜尋月亮在 [start, end] 之間的換座時刻。沒換座回 None"""
    start_lon, _ = planet_state(start_dt, 'Moon')
    end_lon, _ = planet_state(end_dt, 'Moon')
    start_sign = sign_index(start_lon)
    end_sign = sign_index(end_lon)
    if start_sign == end_sign:
        return None
    lo, hi = start_dt, end_dt
    while (hi - lo).total_seconds() > 60:
        mid = lo + (hi - lo) / 2
        mid_lon, _ = planet_state(mid, 'Moon')
        if sign_index(mid_lon) == start_sign:
            lo = mid
        else:
            hi = mid
    return {
        'time': hi.strftime('%Y-%m-%d %H:%M'),
        'from_sign': SIGNS[start_sign],
        'from_sign_zh': SIGN_ZH[SIGNS[start_sign]],
        'to_sign': SIGNS[end_sign],
        'to_sign_zh': SIGN_ZH[SIGNS[end_sign]],
    }


def find_sun_ingress(weekend_start, weekend_end):
    """太陽在週末窗口內換座（節氣轉換），回傳精確時刻。沒換則 None。"""
    sun_start, _ = planet_state(weekend_start, 'Sun')
    sun_end, _ = planet_state(weekend_end, 'Sun')
    start_sign = sign_index(sun_start)
    end_sign = sign_index(sun_end)
    if start_sign == end_sign:
        return None
    lo, hi = weekend_start, weekend_end
    while (hi - lo).total_seconds() > 60:
        mid = lo + (hi - lo) / 2
        mid_lon, _ = planet_state(mid, 'Sun')
        if sign_index(mid_lon) == start_sign:
            lo = mid
        else:
            hi = mid
    return {
        'time': hi.strftime('%Y-%m-%d %H:%M'),
        'from_sign': SIGNS[start_sign],
        'from_sign_zh': SIGN_ZH[SIGNS[start_sign]],
        'to_sign': SIGNS[end_sign],
        'to_sign_zh': SIGN_ZH[SIGNS[end_sign]],
    }


def find_planet_stations(weekend_start, weekend_end, extend_days=3):
    """
    偵測行星停滯（速度由正轉負或反向）。
    掃描週末 ±extend_days，proximity 標記事件落點：
      within = 週末當下、before = 週末前、after = 週末後。
    停滯前後幾天，那顆行星的議題仍持續發酵，所以擴大窗口。
    """
    scan_start = weekend_start - timedelta(days=extend_days)
    scan_end = weekend_end + timedelta(days=extend_days)
    stations = []
    targets = ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
    for planet in targets:
        _, speed_start = planet_state(scan_start, planet)
        _, speed_end = planet_state(scan_end, planet)
        if speed_start * speed_end >= 0:
            continue
        lo, hi = scan_start, scan_end
        while (hi - lo).total_seconds() > 60:
            mid = lo + (hi - lo) / 2
            _, speed_mid = planet_state(mid, planet)
            if speed_mid * speed_start > 0:
                lo = mid
            else:
                hi = mid
        direction = 'retrograde' if speed_start > 0 else 'direct'
        if weekend_start <= hi <= weekend_end:
            proximity = 'within'
        elif hi < weekend_start:
            proximity = 'before'
        else:
            proximity = 'after'
        is_inner = planet in ('Mercury', 'Venus', 'Mars')
        stations.append({
            'planet': planet,
            'planet_zh': PLANET_ZH[planet],
            'time': hi.strftime('%Y-%m-%d %H:%M'),
            'direction': direction,
            'direction_zh': '轉逆行' if direction == 'retrograde' else '轉順行',
            'proximity': proximity,
            'days_from_weekend_start': round((hi - weekend_start).total_seconds() / 86400.0, 1),
            'tier': 'inner' if is_inner else 'outer',
        })
    return stations


def find_eclipses(weekend_start, weekend_end):
    """
    偵測週末期間的日月蝕：
      日蝕 = 精確新月（Sun-Moon 角差 ≈ 0）+ 月亮距月交點 < 18°
      月蝕 = 精確滿月（Sun-Moon 角差 ≈ 180）+ 月亮距月交點 < 12°
    使用 MEAN_NODE，不需要 ephe 檔。
    """
    step = timedelta(minutes=15)
    t = weekend_start
    best_new = (None, 999.0, 0.0)   # time, dist to 0, moon_lon
    best_full = (None, 999.0, 0.0)  # time, dist to 180, moon_lon
    while t <= weekend_end:
        sun_lon, _ = planet_state(t, 'Sun')
        moon_lon, _ = planet_state(t, 'Moon')
        diff = (moon_lon - sun_lon) % 360
        new_dist = min(diff, 360 - diff)
        full_dist = abs(diff - 180)
        if new_dist < best_new[1]:
            best_new = (t, new_dist, moon_lon)
        if full_dist < best_full[1]:
            best_full = (t, full_dist, moon_lon)
        t += step

    def _node_distance(dt_local, moon_lon):
        node_pos, _ = swe.calc_ut(_jd(dt_local), swe.MEAN_NODE)
        node_lon = node_pos[0]
        d1 = angular_diff(moon_lon, node_lon)
        d2 = angular_diff(moon_lon, (node_lon + 180) % 360)
        return min(d1, d2)

    eclipses = []
    if best_new[0] and best_new[1] < 1.0:
        nd = _node_distance(best_new[0], best_new[2])
        if nd < 18:
            eclipses.append({
                'type': 'solar',
                'type_zh': '日蝕',
                'time': best_new[0].strftime('%Y-%m-%d %H:%M'),
                'node_distance': round(nd, 1),
            })
    if best_full[0] and best_full[1] < 1.0:
        nd = _node_distance(best_full[0], best_full[2])
        if nd < 12:
            eclipses.append({
                'type': 'lunar',
                'type_zh': '月蝕',
                'time': best_full[0].strftime('%Y-%m-%d %H:%M'),
                'node_distance': round(nd, 1),
            })
    return eclipses


def compute_sign_event_hits(special_events, sat_planets):
    """
    把特殊事件展開到每個星座，列出哪幾個事件擊中該星座、為什麼。
    讓 12 星座貼文寫作時知道是否要把事件融進該則。
    """
    hits = {sign: [] for sign in SIGNS}

    # 太陽換座：離開的星座收尾、進入的星座開場
    si = special_events.get('sun_ingress')
    if si:
        hits[si['from_sign']].append({
            'event': 'sun_ingress',
            'note': '太陽離開你的星座，過去一個月的循環收尾',
        })
        hits[si['to_sign']].append({
            'event': 'sun_ingress',
            'note': '太陽進到你的星座，未來一個月你是主角',
        })

    # 行星停滯：所在星座（議題打在自己身上）+ 該行星守護的星座（守護星被觸發）
    for s in special_events.get('stations', []):
        planet = s['planet']
        planet_zh = s['planet_zh']
        direction_zh = s['direction_zh']
        current_sign = sat_planets[planet]['sign']
        ruled_signs = [sg for sg, ruler in SIGN_RULER.items() if ruler == planet]
        modern_sign = MODERN_CORULER_SIGNS.get(planet)
        if modern_sign and modern_sign not in ruled_signs:
            ruled_signs.append(modern_sign)
        hits[current_sign].append({
            'event': 'station',
            'planet': planet,
            'direction': s['direction'],
            'note': f"{planet_zh}就在你星座裡{direction_zh}，議題直接打在你身上",
        })
        for rs in ruled_signs:
            if rs == current_sign:
                continue
            hits[rs].append({
                'event': 'station',
                'planet': planet,
                'direction': s['direction'],
                'note': f"{planet_zh}是你的守護星，{direction_zh}你體感最強",
            })

    # 日月蝕：蝕點所在的星座 + 對宮（軸線兩端都會感受到）
    for e in special_events.get('eclipses', []):
        eclipse_time = datetime.strptime(e['time'], '%Y-%m-%d %H:%M')
        moon_lon, _ = planet_state(eclipse_time, 'Moon')
        sun_lon, _ = planet_state(eclipse_time, 'Sun')
        moon_sign = SIGNS[sign_index(moon_lon)]
        sun_sign = SIGNS[sign_index(sun_lon)]
        opp_moon = SIGNS[(sign_index(moon_lon) + 6) % 12]
        if e['type'] == 'solar':
            # 新月日蝕：日月同星座
            hits[moon_sign].append({
                'event': 'eclipse',
                'eclipse_type': 'solar',
                'note': '日蝕落在你的星座，重啟訊號被放大、新章節啟動',
            })
            hits[opp_moon].append({
                'event': 'eclipse',
                'eclipse_type': 'solar',
                'note': '日蝕在你對宮，關係/合作議題出現轉折',
            })
        else:
            # 滿月月蝕：日月對沖，軸線兩端都該寫
            hits[moon_sign].append({
                'event': 'eclipse',
                'eclipse_type': 'lunar',
                'note': '月蝕落在你的星座，情緒攤牌、藏不住的事浮上來',
            })
            hits[sun_sign].append({
                'event': 'eclipse',
                'eclipse_type': 'lunar',
                'note': '月蝕在你對宮，關係/伙伴議題逼你看清',
            })

    return hits


def scan_moon_exact_aspects(start_dt, end_dt, step_minutes=15):
    """
    掃描月亮與其他行星的精確相位時間點（orb local minimum）。
    回傳 [{time, planet, aspect, orb}, ...] 按時間排序。
    """
    MAJOR = [(0, '合相'), (60, '六分'), (90, '四分'), (120, '三分'), (180, '對分')]
    step = timedelta(minutes=step_minutes)

    # 每個 (planet, aspect) 保留最近三個取樣點 orb，判斷 local minimum
    history = {}
    exacts = []

    t = start_dt
    while t <= end_dt:
        moon_lon, _ = planet_state(t, 'Moon')
        for name in PLANETS_SWE:
            if name == 'Moon':
                continue
            p_lon, _ = planet_state(t, name)
            diff = angular_diff(moon_lon, p_lon)
            for ang, aname in MAJOR:
                orb = abs(diff - ang)
                if orb > 5:
                    # 離太遠不納入追蹤
                    history.pop((name, aname), None)
                    continue
                key = (name, aname)
                hist = history.get(key, [])
                hist.append((t, orb))
                if len(hist) > 3:
                    hist = hist[-3:]
                history[key] = hist
                if len(hist) == 3:
                    a, b, c = hist
                    if b[1] < a[1] and b[1] <= c[1] and b[1] < 1.0:
                        exacts.append({
                            'time': b[0],
                            'planet': name,
                            'planet_zh': PLANET_ZH[name],
                            'aspect': aname,
                            'orb': round(b[1], 3),
                        })
        t += step

    exacts.sort(key=lambda x: x['time'])
    return exacts


def find_void_of_course(weekend_start, weekend_end, sign_change):
    """
    找出週末期間的月亮空亡時段。

    定義：月亮在當前星座發生最後一個主相位之後，直到換座之間的時段。
    週末若有換座，可能有 0~2 段 VoC（換座前、換座後）。
    """
    exacts = scan_moon_exact_aspects(weekend_start, weekend_end)
    voc_periods = []

    if sign_change:
        change_time = datetime.strptime(sign_change['time'], '%Y-%m-%d %H:%M')
        # 換座前：從最後一個 exact aspect (換座前) 到 change_time
        before = [e for e in exacts if e['time'] < change_time]
        if before:
            last = before[-1]
            voc_start = last['time']
            # 只標記超過 30 分鐘的 VoC（太短沒意義）
            if (change_time - voc_start).total_seconds() > 1800:
                voc_periods.append({
                    'start': voc_start.strftime('%Y-%m-%d %H:%M'),
                    'end': change_time.strftime('%Y-%m-%d %H:%M'),
                    'last_aspect': f"{last['aspect']}{PLANET_ZH[last['planet']]}",
                })
        # 換座後：從 change_time 之後最後一個 exact 到 weekend_end；若之後沒 exact，整段都是 VoC
        after = [e for e in exacts if e['time'] > change_time]
        if after:
            last_after = after[-1]
            voc_start = last_after['time']
            if (weekend_end - voc_start).total_seconds() > 1800:
                voc_periods.append({
                    'start': voc_start.strftime('%Y-%m-%d %H:%M'),
                    'end': weekend_end.strftime('%Y-%m-%d %H:%M'),
                    'last_aspect': f"{last_after['aspect']}{PLANET_ZH[last_after['planet']]}",
                    'note': '直到週末結束',
                })
        else:
            # 換座後整個週末都沒精確相位
            voc_periods.append({
                'start': change_time.strftime('%Y-%m-%d %H:%M'),
                'end': weekend_end.strftime('%Y-%m-%d %H:%M'),
                'last_aspect': None,
                'note': '換座後到週末結束都沒精確相位',
            })
    else:
        # 沒換座：最後一個 exact 之後到週末結束
        if exacts:
            last = exacts[-1]
            voc_start = last['time']
            if (weekend_end - voc_start).total_seconds() > 1800:
                voc_periods.append({
                    'start': voc_start.strftime('%Y-%m-%d %H:%M'),
                    'end': weekend_end.strftime('%Y-%m-%d %H:%M'),
                    'last_aspect': f"{last['aspect']}{PLANET_ZH[last['planet']]}",
                    'note': '直到週末結束',
                })

    return voc_periods


def get_moon_phase(dt_local):
    """回傳月相資訊"""
    sun_lon, _ = planet_state(dt_local, 'Sun')
    moon_lon, _ = planet_state(dt_local, 'Moon')
    diff = (moon_lon - sun_lon) % 360
    for boundary, name, emoji, meaning in MOON_PHASES:
        if diff < boundary:
            return {
                'phase': name,
                'emoji': emoji,
                'meaning': meaning,
                'sun_moon_angle': round(diff, 2),
            }
    # diff >= 337.5
    return {
        'phase': '殘月',
        'emoji': '🌘',
        'meaning': '休息、沉澱、結束循環',
        'sun_moon_angle': round(diff, 2),
    }


def main():
    # 解析日期參數
    try:
        if len(sys.argv) > 1:
            target = datetime.strptime(sys.argv[1], '%Y-%m-%d')
        else:
            target = find_next_saturday(datetime.now())
    except ValueError as e:
        print(json.dumps({'error': f'日期格式錯誤，需要 YYYY-MM-DD: {e}'}, ensure_ascii=False))
        sys.exit(1)

    # 週末範圍：週六 00:00 ~ 週日 23:59
    saturday = target.replace(hour=0, minute=0, second=0, microsecond=0)
    sunday = saturday + timedelta(days=1)
    weekend_start = saturday
    weekend_end = sunday.replace(hour=23, minute=59)

    # 行星快照（取週六中午作代表）
    sat_noon = saturday.replace(hour=12)
    sun_noon = sunday.replace(hour=12)
    sat_planets = extract_planets(sat_noon)
    sun_planets = extract_planets(sun_noon)

    # 月亮換座時間（精確到分鐘）
    sign_change = find_moon_sign_change(weekend_start, weekend_end)
    moon_changes = sign_change is not None

    # 月亮相位：每天分別多時間點掃描聚合
    sat_moon_aspects = collect_moon_aspects_over_day(
        saturday, saturday.replace(hour=23, minute=59), step_hours=3
    )
    sun_moon_aspects = collect_moon_aspects_over_day(
        sunday, sunday.replace(hour=23, minute=59), step_hours=3
    )

    # 空亡時段（月亮精確相位後到換座的放空期）
    voc_periods = find_void_of_course(weekend_start, weekend_end, sign_change)

    # 月相（週六中午為準，用來定調週末基調）
    moon_phase = get_moon_phase(sat_noon)

    # 行星間相位
    interplanetary = get_interplanetary_aspects(sat_planets)

    # 特殊事件：太陽換座、行星停滯、日月蝕
    special_events = {
        'sun_ingress': find_sun_ingress(weekend_start, weekend_end),
        'stations': find_planet_stations(weekend_start, weekend_end),
        'eclipses': find_eclipses(weekend_start, weekend_end),
    }

    # 把特殊事件展開到 12 星座（守護星、所在星座、對宮）
    sign_event_hits = compute_sign_event_hits(special_events, sat_planets)

    # 每個星座的月亮宮位
    moon_houses = {}
    for sign in SIGNS:
        sat_house = house_from_sign(sat_planets['Moon']['sign'], sign)
        sun_house = house_from_sign(sun_planets['Moon']['sign'], sign)
        moon_houses[sign] = {
            'sign_zh': SIGN_ZH[sign],
            'emoji': SIGN_EMOJI[sign],
            'ruler': SIGN_RULER[sign],
            'ruler_zh': PLANET_ZH[SIGN_RULER[sign]],
            'saturday_house': sat_house,
            'saturday_theme': HOUSE_THEMES[sat_house],
            'sunday_house': sun_house,
            'sunday_theme': HOUSE_THEMES[sun_house],
            'ruler_aspected_sat': next(
                (a for a in sat_moon_aspects if a['planet'] == SIGN_RULER[sign]), None
            ),
            'ruler_aspected_sun': next(
                (a for a in sun_moon_aspects if a['planet'] == SIGN_RULER[sign]), None
            ),
            'event_hits': sign_event_hits[sign],
        }

    # 哪些星座有行星過境
    sign_transits = {}
    for sign in SIGNS:
        transiting = [
            {'planet': name, 'planet_zh': PLANET_ZH[name], 'retrograde': data['retrograde']}
            for name, data in sat_planets.items()
            if data['sign'] == sign and name != 'Moon'
        ]
        if transiting:
            sign_transits[sign] = transiting

    result = {
        'weekend': {
            'saturday': saturday.strftime('%m/%d'),
            'sunday': sunday.strftime('%m/%d'),
            'saturday_full': saturday.strftime('%Y-%m-%d'),
            'sunday_full': sunday.strftime('%Y-%m-%d'),
        },
        'moon': {
            'saturday': {
                'sign': sat_planets['Moon']['sign'],
                'sign_zh': sat_planets['Moon']['sign_zh'],
                'emoji': sat_planets['Moon']['emoji'],
                'degree': sat_planets['Moon']['degree'],
            },
            'sunday': {
                'sign': sun_planets['Moon']['sign'],
                'sign_zh': sun_planets['Moon']['sign_zh'],
                'emoji': sun_planets['Moon']['emoji'],
                'degree': sun_planets['Moon']['degree'],
            },
            'changes_sign': moon_changes,
            'sign_change': sign_change,
        },
        'moon_phase': moon_phase,
        'void_of_course': voc_periods,
        'planets': sat_planets,
        'moon_aspects': {
            'saturday': sat_moon_aspects,
            'sunday': sun_moon_aspects,
        },
        'interplanetary_aspects': interplanetary,
        'moon_houses_per_sign': moon_houses,
        'sign_transits': sign_transits,
        'special_events': special_events,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
