#!/usr/bin/env python3
"""
週間財金星象快照
給定週一日期，回傳該週（週一到週五）的市場節奏相關天象。

所有時間都以 Asia/Taipei (UTC+8) 的 naive datetime 表示。
"""

import sys
import json
from datetime import datetime, timedelta

import swisseph as swe

TZ_OFFSET_HOURS = 8

SIGNS = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir',
         'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis']

SIGN_ZH = {
    'Ari': '牡羊', 'Tau': '金牛', 'Gem': '雙子', 'Can': '巨蟹',
    'Leo': '獅子', 'Vir': '處女', 'Lib': '天秤', 'Sco': '天蠍',
    'Sag': '射手', 'Cap': '摩羯', 'Aqu': '水瓶', 'Pis': '雙魚'
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

# 行星市場意義（給 Claude 寫文案時對照用）
PLANET_MARKET_MEANING = {
    'Sun': '整體盤面基調、主線題材',
    'Moon': '散戶情緒、短線波動',
    'Mercury': '科技、通訊、交易、資訊、AI',
    'Venus': '消費、零售、精品、娛樂',
    'Mars': '能源、軍工、高波動、衝動',
    'Jupiter': '金融、航運、成長股、樂觀擴張',
    'Saturn': '基建、房產、保守、紀律',
    'Uranus': '加密、科技突破、意外、創新',
    'Neptune': '醫藥、油氣、夢想題材、炒作',
    'Pluto': '核能、礦產、重組、權力題材',
}

# 相位定義：外行星 orb 較窄、個人行星稍寬
ASPECTS = {
    '合相': {'angle': 0, 'orb_outer': 6, 'orb_personal': 8},
    '六分': {'angle': 60, 'orb_outer': 3, 'orb_personal': 4},
    '四分': {'angle': 90, 'orb_outer': 5, 'orb_personal': 7},
    '三分': {'angle': 120, 'orb_outer': 5, 'orb_personal': 7},
    '對分': {'angle': 180, 'orb_outer': 6, 'orb_personal': 8},
}

ASPECT_NATURE = {
    '合相': '強化', '六分': '和諧', '四分': '張力',
    '三分': '順流', '對分': '拉扯',
}

PERSONAL_PLANETS = {'Sun', 'Mercury', 'Venus', 'Mars'}

# 月相（Moon-Sun 黃經差為準）
MOON_PHASES = [
    (22.5, '新月', '🌑', '重啟、新題材啟動、試水溫'),
    (67.5, '眉月', '🌒', '醞釀、觀察、輕推'),
    (112.5, '上弦月', '🌓', '行動、拍板、突破'),
    (157.5, '盈凸月', '🌔', '調整、優化、持續推進'),
    (202.5, '滿月', '🌕', '情緒放大、攤牌、關鍵揭曉'),
    (247.5, '虧凸月', '🌖', '分享、回顧、獲利了結'),
    (292.5, '下弦月', '🌗', '放手、汰弱、整理'),
    (337.5, '殘月', '🌘', '休息、沉澱、結束循環'),
]


def _jd(dt_local):
    """Asia/Taipei naive datetime → UT julian day"""
    dt_utc = dt_local - timedelta(hours=TZ_OFFSET_HOURS)
    hour_fraction = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hour_fraction)


def planet_state(dt_local, planet_name):
    """回傳 (黃經度, 速度 deg/day)"""
    pid = PLANETS_SWE[planet_name]
    pos, _ = swe.calc_ut(_jd(dt_local), pid)
    return pos[0], pos[3]


def sign_index(lon):
    return int(lon / 30) % 12


def extract_planets(dt_local):
    """取得某時刻所有行星狀態（含市場意義）"""
    planets = {}
    for name in PLANETS_SWE:
        lon, speed = planet_state(dt_local, name)
        idx = sign_index(lon)
        planets[name] = {
            'name_zh': PLANET_ZH[name],
            'sign': SIGNS[idx],
            'sign_zh': SIGN_ZH[SIGNS[idx]],
            'degree': round(lon % 30, 2),
            'abs_pos': round(lon, 2),
            'retrograde': speed < 0,
            'speed': round(speed, 4),
            'market_meaning': PLANET_MARKET_MEANING[name],
        }
    return planets


def angular_diff(a, b):
    d = abs(a - b) % 360
    return 360 - d if d > 180 else d


def calc_aspect(pos1, pos2, is_personal=False):
    diff = angular_diff(pos1, pos2)
    for name, spec in ASPECTS.items():
        orb_limit = spec['orb_personal'] if is_personal else spec['orb_outer']
        orb = abs(diff - spec['angle'])
        if orb <= orb_limit:
            return {
                'aspect': name,
                'nature': ASPECT_NATURE[name],
                'orb': round(orb, 2),
            }
    return None


def get_current_aspects(planets):
    """行星間相位（不含月亮，月亮太快）"""
    names = [n for n in planets if n != 'Moon']
    aspects = []
    for i, n1 in enumerate(names):
        for n2 in names[i + 1:]:
            is_personal = n1 in PERSONAL_PLANETS or n2 in PERSONAL_PLANETS
            asp = calc_aspect(planets[n1]['abs_pos'], planets[n2]['abs_pos'], is_personal)
            if asp:
                aspects.append({
                    'planet1': n1,
                    'planet1_zh': PLANET_ZH[n1],
                    'planet2': n2,
                    'planet2_zh': PLANET_ZH[n2],
                    'meaning1': PLANET_MARKET_MEANING[n1],
                    'meaning2': PLANET_MARKET_MEANING[n2],
                    **asp,
                })
    aspects.sort(key=lambda x: x['orb'])
    return aspects


def find_sign_changes(start_dt, end_dt):
    """本週內行星換座（不含月亮）"""
    changes = []
    for name in PLANETS_SWE:
        if name == 'Moon':
            continue
        start_lon, _ = planet_state(start_dt, name)
        end_lon, _ = planet_state(end_dt, name)
        start_sign = sign_index(start_lon)
        end_sign = sign_index(end_lon)
        if start_sign == end_sign:
            continue
        lo, hi = start_dt, end_dt
        while (hi - lo).total_seconds() > 3600:
            mid = lo + (hi - lo) / 2
            mid_lon, _ = planet_state(mid, name)
            if sign_index(mid_lon) == start_sign:
                lo = mid
            else:
                hi = mid
        changes.append({
            'planet': name,
            'planet_zh': PLANET_ZH[name],
            'time': hi.strftime('%Y-%m-%d %H:%M'),
            'from_sign': SIGN_ZH[SIGNS[start_sign]],
            'to_sign': SIGN_ZH[SIGNS[end_sign]],
            'market_meaning': PLANET_MARKET_MEANING[name],
        })
    return changes


def find_retrograde_stations(start_dt, end_dt):
    """本週內行星逆行轉向事件"""
    stations = []
    for name in PLANETS_SWE:
        if name == 'Moon':
            continue
        _, start_speed = planet_state(start_dt, name)
        _, end_speed = planet_state(end_dt, name)
        start_retro = start_speed < 0
        end_retro = end_speed < 0
        if start_retro == end_retro:
            continue
        lo, hi = start_dt, end_dt
        while (hi - lo).total_seconds() > 3600:
            mid = lo + (hi - lo) / 2
            _, mid_speed = planet_state(mid, name)
            if (mid_speed < 0) == start_retro:
                lo = mid
            else:
                hi = mid
        stations.append({
            'planet': name,
            'planet_zh': PLANET_ZH[name],
            'time': hi.strftime('%Y-%m-%d %H:%M'),
            'direction': '順轉逆（逆行開始）' if end_retro else '逆轉順（逆行結束）',
            'market_meaning': PLANET_MARKET_MEANING[name],
        })
    return stations


def get_moon_phase(dt_local):
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
    return {
        'phase': '殘月',
        'emoji': '🌘',
        'meaning': '休息、沉澱、結束循環',
        'sun_moon_angle': round(diff, 2),
    }


def find_next_monday(today):
    days_until_mon = (0 - today.weekday()) % 7
    if days_until_mon == 0:
        days_until_mon = 7
    return today + timedelta(days=days_until_mon)


def main():
    try:
        if len(sys.argv) > 1:
            target = datetime.strptime(sys.argv[1], '%Y-%m-%d')
        else:
            target = find_next_monday(datetime.now())
    except ValueError as e:
        print(json.dumps({'error': f'日期格式錯誤，需要 YYYY-MM-DD: {e}'}, ensure_ascii=False))
        sys.exit(1)

    monday = target.replace(hour=0, minute=0, second=0, microsecond=0)
    friday = monday + timedelta(days=4, hours=23, minutes=59)
    wednesday_noon = monday + timedelta(days=2, hours=12)

    planets = extract_planets(wednesday_noon)
    moon_phase = get_moon_phase(wednesday_noon)
    current_aspects = get_current_aspects(planets)
    sign_changes = find_sign_changes(monday, friday)
    retrograde_stations = find_retrograde_stations(monday, friday)

    currently_retrograde = [
        {
            'planet': name,
            'planet_zh': PLANET_ZH[name],
            'sign_zh': data['sign_zh'],
            'market_meaning': PLANET_MARKET_MEANING[name],
        }
        for name, data in planets.items()
        if data['retrograde'] and name != 'Moon'
    ]

    result = {
        'week': {
            'monday': monday.strftime('%m/%d'),
            'friday': friday.strftime('%m/%d'),
            'monday_full': monday.strftime('%Y-%m-%d'),
            'friday_full': friday.strftime('%Y-%m-%d'),
        },
        'moon_phase': moon_phase,
        'planets': planets,
        'current_aspects': current_aspects,
        'sign_changes_this_week': sign_changes,
        'retrograde_stations_this_week': retrograde_stations,
        'currently_retrograde': currently_retrograde,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
