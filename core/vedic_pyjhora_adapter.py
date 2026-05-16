"""PyJHora ↔ 現有 JSON 格式 adapter

把 PyJHora（Jagannatha Hora Python port）的數字 ID / 程序式輸出，
轉成本專案既有的中文 JSON 結構，讓 sub-agent / guide.md / frameworks 完全不用改。

設計原則：
- PyJHora 只負責「算盤」（行星位置 / dasha / yoga / varga / shadbala）
- 中文化、dignity、nakshatra 子物件沿用既有 vedic_constants / vedic_transit 邏輯
- 整宮制（Whole Sign）宮位自己從 sign 距離算，不用 PyJHora 的 Sripati bhava
"""

import os
import sys
import contextlib
from datetime import datetime
from zoneinfo import ZoneInfo

from core.vedic_constants import (
    SIGNS, PLANET_NAMES_ZH, SIGN_NAMES_ZH, DASHA_YEARS,
)


def tz_offset_hours(tz_str: str, year: int, month: int, day: int) -> float:
    """tz 名稱 → 出生當天的 UTC offset（小時，含當時的 DST 規則）。

    PyJHora 要 numeric offset；用出生日期算才能正確處理歷史時區
    （例：台灣 1945-1980 有夏令時，1980 後無，1991 出生 = +8）。
    """
    try:
        dt = datetime(year, month, day, 12, 0, tzinfo=ZoneInfo(tz_str))
        return dt.utcoffset().total_seconds() / 3600.0
    except Exception:
        return 8.0  # 退而求其次：台灣時區

# PyJHora planet id → 專案行星名（'L' = Lagna 上升）
_PID_TO_NAME = {
    0: "Sun", 1: "Moon", 2: "Mars", 3: "Mercury", 4: "Jupiter",
    5: "Venus", 6: "Saturn", 7: "Rahu", 8: "Ketu",
}

# 整宮制宮位序數 → 既有格式的 ordinal key
_HOUSE_ORDINAL = [
    "First_House", "Second_House", "Third_House", "Fourth_House",
    "Fifth_House", "Sixth_House", "Seventh_House", "Eighth_House",
    "Ninth_House", "Tenth_House", "Eleventh_House", "Twelfth_House",
]


@contextlib.contextmanager
def _silence_jhora():
    """PyJHora import 時會往 stdout 印 'xxx / added to system path'，吃掉避免污染 JSON。"""
    old = sys.stdout
    with open(os.devnull, "w") as devnull:
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old


def _jd_place(year, month, day, hour, minute, lat, lng, tz_offset):
    """建 PyJHora 的 julian day + Place，設 Lahiri ayanamsa。"""
    from jhora.panchanga import drik
    from jhora import utils

    drik.set_ayanamsa_mode("LAHIRI")
    dob = drik.Date(year, month, day)
    tob = (hour, minute, 0)
    place = drik.Place("loc", float(lat), float(lng), float(tz_offset))
    jd = utils.julian_day_number(dob, tob)
    return jd, place, dob, tob


def compute_rasi(year, month, day, hour, minute, lat, lng, tz_offset=8.0):
    """算 D1 本命盤原始資料（行星位置 + 逆行 + jd/place），給其他 builder 重用。

    回傳 dict：
      planet_positions: PyJHora 原始 [[pid,(sign,deg)],...]（含 'L' Lagna）
      retro: set，逆行的 planet id
      jd / place / dob / tob: PyJHora 物件，給 dasha / varga 等模組重用
    """
    with _silence_jhora():
        from jhora.horoscope.chart import charts
        from jhora.panchanga import drik

        jd, place, dob, tob = _jd_place(
            year, month, day, hour, minute, lat, lng, tz_offset
        )
        pp = charts.rasi_chart(jd, place)
        retro = set(drik.planets_in_retrograde(jd, place))

    return {
        "planet_positions": pp,
        "retro": retro,
        "jd": jd,
        "place": place,
        "dob": dob,
        "tob": tob,
    }


def build_planets_and_houses(rasi: dict) -> dict:
    """PyJHora rasi → 既有「行星」+「宮位」格式（整宮制 + nakshatra + dignity）。

    輸出對齊 _extract_planets_and_houses 的結構：
      行星[Name] = {星座, 度數, 絕對經度, 宮位, 逆行, 力量, nakshatra}
      宮位[第N宮] = {星座, 度數}，第1宮另含 ASC_實際度數 / ASC_絕對經度 / nakshatra
    """
    from core.vedic_transit import calc_nakshatra, _planet_dignity

    pp = rasi["planet_positions"]
    retro = rasi["retro"]

    # 先抓上升星座 index（整宮制的基準）
    asc_sign_idx = None
    asc_deg = None
    for pid, (sign_idx, deg) in pp:
        if pid == "L":
            asc_sign_idx = sign_idx
            asc_deg = deg
            break
    if asc_sign_idx is None:
        raise ValueError("PyJHora rasi_chart 缺 Lagna(L)")

    planets = {}
    for pid, (sign_idx, deg) in pp:
        if pid == "L":
            continue
        name = _PID_TO_NAME.get(pid)
        if name is None:
            continue
        abs_lon = round(sign_idx * 30 + deg, 2)
        sign = SIGNS[sign_idx]
        house_num = (sign_idx - asc_sign_idx) % 12  # 0-based
        planets[name] = {
            "星座": sign,
            "度數": round(deg, 2),
            "絕對經度": abs_lon,
            "宮位": _HOUSE_ORDINAL[house_num],
            "逆行": pid in retro,
            "力量": _planet_dignity(name, sign),
            "nakshatra": calc_nakshatra(abs_lon),
        }

    # 整宮制：第 N 宮 = 從 ASC 星座起算第 N 個星座，宮頭度數一律 0
    houses = {}
    for i in range(12):
        sign_idx = (asc_sign_idx + i) % 12
        houses[f"第{i + 1}宮"] = {"星座": SIGNS[sign_idx], "度數": 0.0}
    asc_abs = round(asc_sign_idx * 30 + asc_deg, 2)
    houses["第1宮"]["ASC_實際度數"] = round(asc_deg, 2)
    houses["第1宮"]["ASC_絕對經度"] = asc_abs
    houses["第1宮"]["nakshatra"] = calc_nakshatra(asc_abs)

    return {"行星": planets, "宮位": houses, "_asc_sign_idx": asc_sign_idx}


class _PlanetShim:
    """duck-type kerykeion 行星物件，讓 vedic_transit 內部 .sign/.position/... 零改動。"""

    __slots__ = ("name", "sign", "position", "abs_pos", "retrograde")

    def __init__(self, name, sign, position, abs_pos, retro):
        self.name = name
        self.sign = sign
        self.position = position
        self.abs_pos = abs_pos
        self.retrograde = retro


class _TransitSubject:
    """duck-type kerykeion AstrologicalSubject 的 transit 介面（只含 9 graha + 交點）。"""

    _ATTR = {
        "Sun": "sun", "Moon": "moon", "Mars": "mars", "Mercury": "mercury",
        "Jupiter": "jupiter", "Venus": "venus", "Saturn": "saturn",
    }

    def __init__(self, pp, retro):
        for pid, (sign_idx, deg) in pp:
            if pid == "L":
                continue
            name = _PID_TO_NAME.get(pid)
            if name is None:
                continue
            abs_lon = round(sign_idx * 30 + deg, 2)
            shim = _PlanetShim(
                name, SIGNS[sign_idx], round(deg, 2), abs_lon, pid in retro
            )
            if name == "Rahu":
                self.true_north_lunar_node = shim
            elif name == "Ketu":
                self.true_south_lunar_node = shim
            else:
                setattr(self, self._ATTR[name], shim)


def transit_subject(year, month, day, hour, minute, lat, lng, tz_offset=8.0):
    """某日某時的行運盤，回傳 duck-type subject（取代 kerykeion AstrologicalSubject）。"""
    rasi = compute_rasi(year, month, day, hour, minute, lat, lng, tz_offset)
    return _TransitSubject(rasi["planet_positions"], rasi["retro"])


def vimsottari_from_birth(year, month, day, hour, minute, lat, lng,
                          tz_offset=8.0) -> dict:
    """便捷封裝：出生資料 → 既有 dasha 格式（內部自己 compute_rasi）。"""
    rasi = compute_rasi(year, month, day, hour, minute, lat, lng, tz_offset)
    return build_vimsottari(rasi)


def build_vimsottari(rasi: dict) -> dict:
    """PyJHora vimsottari → 既有「dasha」格式。

    既有格式：{"mahadashas": [{lord, lord_zh, 年數, 起, 迄, antardashas:[{lord,lord_zh,起,迄,年數}]}]}
    PyJHora flat list：[[(md_pid, ad_pid), (Y,M,D,hour_dec), dur_years], ...]
    需把 flat (MD,AD) pair 重組成 MD 巢狀 AD。
    """
    with _silence_jhora():
        from jhora.horoscope.dhasa.graha import vimsottari
        flat = vimsottari.get_vimsottari_dhasa_bhukthi(rasi["jd"], rasi["place"])[1]

    def _fmt(date_tuple):
        y, m, d = date_tuple[0], date_tuple[1], date_tuple[2]
        return f"{y:04d}-{m:02d}-{d:02d}"

    mahadashas = []
    cur_md = None
    for (md_pid, ad_pid), date_t, dur in flat:
        md_name = _PID_TO_NAME[md_pid]
        ad_name = _PID_TO_NAME[ad_pid]
        start = _fmt(date_t)
        if cur_md is None or cur_md["_pid"] != md_pid:
            if cur_md is not None:
                mahadashas.append(cur_md)
            cur_md = {
                "_pid": md_pid,
                "lord": md_name,
                "lord_zh": PLANET_NAMES_ZH.get(md_name, md_name),
                "年數": DASHA_YEARS[md_name],
                "起": start,
                "迄": None,
                "antardashas": [],
            }
        cur_md["antardashas"].append({
            "lord": ad_name,
            "lord_zh": PLANET_NAMES_ZH.get(ad_name, ad_name),
            "起": start,
            "迄": None,
            "年數": round(dur, 2),
        })
    if cur_md is not None:
        mahadashas.append(cur_md)

    # 補「迄」：下一個 AD/MD 的「起」就是上一個的「迄」
    for mi, md in enumerate(mahadashas):
        ads = md["antardashas"]
        for ai in range(len(ads)):
            if ai + 1 < len(ads):
                ads[ai]["迄"] = ads[ai + 1]["起"]
            elif mi + 1 < len(mahadashas):
                ads[ai]["迄"] = mahadashas[mi + 1]["起"]
        md["起"] = ads[0]["起"]
        if mi + 1 < len(mahadashas):
            md["迄"] = mahadashas[mi + 1]["起"]
        else:
            md["迄"] = ads[-1]["迄"]
        del md["_pid"]

    return {"mahadashas": mahadashas}
