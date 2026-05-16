"""Jaimini Chara Dasha（星座為主的大運系統）

跟 Vimshottari（行星為主、固定週期）邏輯完全不同：
- 起點是上升星座，不是月亮 nakshatra
- 推進單位是星座，不是行星
- 每個星座的年數動態決定（1-12 年），總和隨盤面浮動

用途：跟 Vimshottari 交叉驗證 — 兩套都觸發某宮位 = 高機率事件。

規則來源：Parashari-Jaimini（KN Rao 傳承）。
- Lagna 在奇數星座（Ari/Gem/Leo/Lib/Sag/Aqu）→ 順行
- Lagna 在偶數星座 → 逆行
- 各星座年數 = 從該星座順著 dasha 方向算到其 lord 所在星座的步數 - 1
  - lord 在自己的星座 → 12 年
- Aqu/Sco 的 Rahu/Ketu 共主規則未實作（採傳統 7 行星 rulership）
"""

from datetime import datetime, timedelta

from core.vedic_constants import SIGNS, SIGN_NAMES_ZH, SIGN_LORDS, SIDEREAL_YEAR_DAYS

# 奇數星座（Ari/Gem/Leo/Lib/Sag/Aqu）→ 順行；偶數 → 逆行
ODD_SIGN_INDICES = {0, 2, 4, 6, 8, 10}


def _sign_idx(sign: str) -> int:
    return SIGNS.index(sign)


def _count_signs(from_idx: int, to_idx: int, forward: bool) -> int:
    """從 from 算到 to 是第幾個星座（from 自己 = 1）

    forward=True 順時針 / False 逆時針
    """
    if forward:
        return ((to_idx - from_idx) % 12) + 1
    else:
        return ((from_idx - to_idx) % 12) + 1


def _years_for_sign(sign_idx: int, lord_sign_idx: int, forward: bool) -> int:
    """計算某星座的 Chara Dasha 年數。

    年數 = 從該星座算到其 lord 所在星座的步數 - 1
    特例：lord 在自己的星座（步數 = 1） → 12 年
    """
    count = _count_signs(sign_idx, lord_sign_idx, forward)
    if count == 1:
        return 12
    return count - 1


def calc_chara_dasha(planet_signs: dict, asc_sign: str,
                     birth_dt: datetime) -> dict:
    """計算 12 個 Chara Dasha Mahadasha + 每個的 Antardasha。

    planet_signs: {"Sun": "Sag", "Moon": "Sco", ...}
    asc_sign: 上升星座縮寫
    """
    asc_idx = _sign_idx(asc_sign)
    forward = asc_idx in ODD_SIGN_INDICES

    # 12 個星座按 dasha 方向排序，從上升開始
    sequence = []
    for i in range(12):
        if forward:
            sequence.append((asc_idx + i) % 12)
        else:
            sequence.append((asc_idx - i) % 12)

    mahadashas = []
    cursor = birth_dt

    for sidx in sequence:
        sign = SIGNS[sidx]
        lord = SIGN_LORDS[sign]
        lord_planet = planet_signs.get(lord)
        if lord_planet is None:
            continue
        lord_sidx = _sign_idx(lord_planet)
        years = _years_for_sign(sidx, lord_sidx, forward)
        days = years * SIDEREAL_YEAR_DAYS
        end = cursor + timedelta(days=days)

        antardashas = _calc_antardashas(
            sidx, planet_signs, forward, cursor, end,
        )

        mahadashas.append({
            "星座": sign,
            "星座_zh": SIGN_NAMES_ZH[sign],
            "lord": lord,
            "年數": years,
            "起": cursor.strftime("%Y-%m-%d"),
            "迄": end.strftime("%Y-%m-%d"),
            "antardashas": antardashas,
        })
        cursor = end

    return {
        "起算": "上升星座",
        "方向": "順行" if forward else "逆行",
        "mahadashas": mahadashas,
        "總年數": sum(m["年數"] for m in mahadashas),
    }


def _calc_antardashas(maha_sign_idx: int, planet_signs: dict, forward: bool,
                       maha_start: datetime, maha_end: datetime) -> list[dict]:
    """Antardasha：從 Mahadasha 星座開始，同方向走 12 個星座，
    每個子期間比例 = 該子星座的 Chara Dasha 年數 / 120
    """
    maha_seconds = (maha_end - maha_start).total_seconds()
    sub_sequence = []
    for i in range(12):
        if forward:
            sub_sequence.append((maha_sign_idx + i) % 12)
        else:
            sub_sequence.append((maha_sign_idx - i) % 12)

    sub_years_list = []
    for sidx in sub_sequence:
        sign = SIGNS[sidx]
        lord = SIGN_LORDS[sign]
        lord_sidx = _sign_idx(planet_signs[lord])
        sub_years_list.append(_years_for_sign(sidx, lord_sidx, forward))

    total_sub_years = sum(sub_years_list)

    antardashas = []
    cursor = maha_start
    for sidx, sub_years in zip(sub_sequence, sub_years_list):
        sub_seconds = maha_seconds * sub_years / total_sub_years
        end = cursor + timedelta(seconds=sub_seconds)
        sign = SIGNS[sidx]
        antardashas.append({
            "星座": sign,
            "星座_zh": SIGN_NAMES_ZH[sign],
            "lord": SIGN_LORDS[sign],
            "起": cursor.strftime("%Y-%m-%d"),
            "迄": end.strftime("%Y-%m-%d"),
        })
        cursor = end
    return antardashas


def find_current_chara_dasha(dasha_data: dict, target_dt: datetime) -> dict:
    """找出目標日期所在的 Chara Mahadasha + Antardasha。"""
    target_str = target_dt.strftime("%Y-%m-%d")

    for maha in dasha_data["mahadashas"]:
        if maha["起"] <= target_str <= maha["迄"]:
            current_antar = None
            for antar in maha["antardashas"]:
                if antar["起"] <= target_str <= antar["迄"]:
                    current_antar = antar
                    break
            return {
                "mahadasha": {
                    "星座": maha["星座"],
                    "星座_zh": maha["星座_zh"],
                    "lord": maha["lord"],
                    "起": maha["起"],
                    "迄": maha["迄"],
                },
                "antardasha": current_antar,
            }
    return {"mahadasha": None, "antardasha": None}
