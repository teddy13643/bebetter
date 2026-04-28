"""印度占星分盤（Varga Charts）計算模組

從 Kerykeion AstrologicalSubject 的恆星黃道行星經度，
依 BPHS（Brihat Parashara Hora Shastra）規則計算 17 張分盤
（D-2/3/4/6/7/8/9/10/12/16/20/24/27/30/40/45/60）。

D-6（疾病、敵對）和 D-8（壽命、意外）不在 BPHS 原典 Shodashvarga 16 張中，
屬於擴展派（PVR Narasimha Rao / Sanjay Rath）採用的補充分盤，主要用於健康、
慢性病、突發災禍等主題。
"""

from math import floor

from kerykeion import AstrologicalSubject

from core.vedic_constants import (
    SIGNS, SIGN_NAMES_ZH, SIGN_ELEMENTS, NAVAMSA_ELEMENT_START, VARGA_INFO,
    EXALTATION, DEBILITATION, OWN_SIGNS,
)

# 要計算的行星（含羅睺計都）
_PLANET_ATTRS = [
    "sun", "moon", "mercury", "venus", "mars",
    "jupiter", "saturn",
]
_NODE_ATTRS = [
    ("true_north_lunar_node", "Rahu"),
    ("true_south_lunar_node", "Ketu"),
]


def _sign_idx(abs_pos: float) -> int:
    """絕對經度 → 星座 index（0=Ari, 11=Pis）"""
    return int(abs_pos / 30) % 12


def _degree_in_sign(abs_pos: float) -> float:
    """絕對經度 → 星座內度數（0-30）"""
    return abs_pos % 30


def _format_sign(idx: int) -> dict:
    sign = SIGNS[idx % 12]
    return {"星座": sign, "星座_zh": SIGN_NAMES_ZH[sign]}


def _planet_dignity(planet_name: str, sign: str) -> str | None:
    """判斷行星在該星座的力量狀態"""
    if EXALTATION.get(planet_name) == sign:
        return "高揚"
    if DEBILITATION.get(planet_name) == sign:
        return "落陷"
    if sign in OWN_SIGNS.get(planet_name, []):
        return "廟旺"
    return None


# --- D-2 Hora ---
def _calc_d2(abs_pos: float, sign_idx: int) -> int:
    """奇數星座：前 15° → Leo(4), 後 15° → Cancer(3)
    偶數星座：前 15° → Cancer(3), 後 15° → Leo(4)"""
    deg = _degree_in_sign(abs_pos)
    is_odd = (sign_idx % 2 == 0)  # 0=Ari(奇), 1=Tau(偶)
    if is_odd:
        return 4 if deg < 15 else 3  # Leo / Cancer
    else:
        return 3 if deg < 15 else 4  # Cancer / Leo


# --- D-3 Drekkana ---
def _calc_d3(abs_pos: float, sign_idx: int) -> int:
    """每 10° 一段：第 1 段 = 自身，第 2 段 = +4（第 5 座），第 3 段 = +8（第 9 座）"""
    deg = _degree_in_sign(abs_pos)
    part = min(int(deg / 10), 2)
    offsets = [0, 4, 8]
    return (sign_idx + offsets[part]) % 12


# --- D-4 Chaturthamsa ---
def _calc_d4(abs_pos: float, sign_idx: int) -> int:
    """每 7°30' 一段（30/4）。第 1/2/3/4 段對應從本宮起算的 1/4/7/10 宮（Kendras）"""
    deg = _degree_in_sign(abs_pos)
    part = min(int(deg / 7.5), 3)
    offsets = [0, 3, 6, 9]
    return (sign_idx + offsets[part]) % 12


# --- D-6 Shashtamsa ---
def _calc_d6(abs_pos: float, sign_idx: int) -> int:
    """每 5° 一段（30/6）。
    奇數座從自身開始數，偶數座從第 7 座開始數"""
    deg = _degree_in_sign(abs_pos)
    part = min(int(deg / 5), 5)
    is_odd = (sign_idx % 2 == 0)
    start = sign_idx if is_odd else (sign_idx + 6) % 12
    return (start + part) % 12


# --- D-7 Saptamsa ---
def _calc_d7(abs_pos: float, sign_idx: int) -> int:
    """每 4°17'8.57" 一段（30/7）。
    奇數座從自身開始數，偶數座從第 7 座開始數"""
    deg = _degree_in_sign(abs_pos)
    part = min(int(deg / (30 / 7)), 6)
    is_odd = (sign_idx % 2 == 0)
    start = sign_idx if is_odd else (sign_idx + 6) % 12
    return (start + part) % 12


# --- D-8 Ashtamsa ---
def _calc_d8(abs_pos: float, sign_idx: int) -> int:
    """每 3°45' 一段（30/8）。Movable 從 Ari、Fixed 從 Leo、Dual 從 Sag 起算"""
    deg = _degree_in_sign(abs_pos)
    part = min(int(deg / 3.75), 7)
    start = {0: 0, 1: 4, 2: 8}[sign_idx % 3]
    return (start + part) % 12


# --- D-9 Navamsa ---
def _calc_d9(abs_pos: float) -> int:
    """每 3°20' 一段（30/9）。按星座元素決定起算點。
    等效於 floor(abs_pos / 3.3333) % 12"""
    return int(abs_pos / (30 / 9)) % 12


# --- D-10 Dasamsa ---
def _calc_d10(abs_pos: float, sign_idx: int) -> int:
    """每 3° 一段（30/10）。
    奇數座從自身開始，偶數座從第 9 座開始"""
    deg = _degree_in_sign(abs_pos)
    part = min(int(deg / 3), 9)
    is_odd = (sign_idx % 2 == 0)
    start = sign_idx if is_odd else (sign_idx + 8) % 12
    return (start + part) % 12


# --- D-12 Dwadasamsa ---
def _calc_d12(abs_pos: float, sign_idx: int) -> int:
    """每 2°30' 一段（30/12）。從自身星座開始數"""
    deg = _degree_in_sign(abs_pos)
    part = min(int(deg / 2.5), 11)
    return (sign_idx + part) % 12


# --- D-16 Shodasamsa ---
def _calc_d16(abs_pos: float, sign_idx: int) -> int:
    """每 1°52'30" 一段（30/16）。Movable 從 Ari、Fixed 從 Leo、Dual 從 Sag 起算"""
    deg = _degree_in_sign(abs_pos)
    part = min(int(deg / 1.875), 15)
    start = {0: 0, 1: 4, 2: 8}[sign_idx % 3]
    return (start + part) % 12


# --- D-27 Saptavimsamsa (Bhamsa) ---
_D27_ELEMENT_START = {"fire": 0, "earth": 3, "air": 6, "water": 9}

def _calc_d27(abs_pos: float, sign_idx: int) -> int:
    """每 1°6'40" 一段（30/27）。依星座元素決定起算（fire→Ari, earth→Can, air→Lib, water→Cap）"""
    deg = _degree_in_sign(abs_pos)
    part = min(int(deg / (30 / 27)), 26)
    element = SIGN_ELEMENTS[SIGNS[sign_idx]]
    start = _D27_ELEMENT_START[element]
    return (start + part) % 12


# --- D-40 Khavedamsa ---
def _calc_d40(abs_pos: float, sign_idx: int) -> int:
    """每 0°45' 一段（30/40）。奇座從 Ari、偶座從 Lib 起算"""
    deg = _degree_in_sign(abs_pos)
    part = min(int(deg / 0.75), 39)
    is_odd = (sign_idx % 2 == 0)
    start = 0 if is_odd else 6
    return (start + part) % 12


# --- D-45 Akshavedamsa ---
def _calc_d45(abs_pos: float, sign_idx: int) -> int:
    """每 0°40' 一段（30/45）。Movable 從 Ari、Fixed 從 Leo、Dual 從 Sag 起算"""
    deg = _degree_in_sign(abs_pos)
    part = min(int(deg / (30 / 45)), 44)
    start = {0: 0, 1: 4, 2: 8}[sign_idx % 3]
    return (start + part) % 12


# --- D-20 Vimsamsa ---
def _calc_d20(abs_pos: float, sign_idx: int) -> int:
    """每 1°30' 一段（30/20）。
    Movable 座從 Ari、Fixed 從 Sag、Dual 從 Leo 起算"""
    deg = _degree_in_sign(abs_pos)
    part = min(int(deg / 1.5), 19)
    start = {0: 0, 1: 8, 2: 4}[sign_idx % 3]
    return (start + part) % 12


# --- D-24 Chaturvimsamsa ---
def _calc_d24(abs_pos: float, sign_idx: int) -> int:
    """每 1°15' 一段（30/24）。
    奇座從 Leo、偶座從 Cancer 起算"""
    deg = _degree_in_sign(abs_pos)
    part = min(int(deg / 1.25), 23)
    is_odd = (sign_idx % 2 == 0)
    start = 4 if is_odd else 3
    return (start + part) % 12


# --- D-30 Trimsamsa ---
# 非均分：奇座/偶座度數區間和對應行星不同，結果為該行星守護星座
# (上界, 結果星座 idx)
_D30_ODD_RANGES = [
    (5,  0),   # 0-5°: Mars → Ari
    (10, 10),  # 5-10°: Saturn → Aqu
    (18, 8),   # 10-18°: Jupiter → Sag
    (25, 2),   # 18-25°: Mercury → Gem
    (30, 6),   # 25-30°: Venus → Lib
]
_D30_EVEN_RANGES = [
    (5,  1),   # 0-5°: Venus → Tau
    (12, 5),   # 5-12°: Mercury → Vir
    (20, 11),  # 12-20°: Jupiter → Pis
    (25, 9),   # 20-25°: Saturn → Cap
    (30, 7),   # 25-30°: Mars → Sco
]

def _calc_d30(abs_pos: float, sign_idx: int) -> int:
    """非均分：奇座按 Mars/Sat/Jup/Mer/Ven 切（5/5/8/7/5°），
    偶座按 Ven/Mer/Jup/Sat/Mars 切（5/7/8/5/5°），結果為該行星守護星座"""
    deg = _degree_in_sign(abs_pos)
    is_odd = (sign_idx % 2 == 0)
    ranges = _D30_ODD_RANGES if is_odd else _D30_EVEN_RANGES
    for upper, sign in ranges:
        if deg < upper:
            return sign
    return ranges[-1][1]


# --- D-60 Shastiamsa ---
def _calc_d60(abs_pos: float, sign_idx: int) -> int:
    """每 0.5° 一段（30/60）。第 N 段（N=1..60）從本宮偏移 (N-1) mod 12 個星座。
    出生時間需精確到分鐘以內，誤差 2 分鐘整張盤就不一樣"""
    deg = _degree_in_sign(abs_pos)
    part = min(int(deg * 2), 59)
    return (sign_idx + part) % 12


# 計算函式對照表
_VARGA_FUNCS = {
    "D2":  _calc_d2,
    "D3":  _calc_d3,
    "D4":  _calc_d4,
    "D6":  _calc_d6,
    "D7":  _calc_d7,
    "D8":  _calc_d8,
    "D9":  _calc_d9,
    "D10": _calc_d10,
    "D12": _calc_d12,
    "D16": _calc_d16,
    "D20": _calc_d20,
    "D24": _calc_d24,
    "D27": _calc_d27,
    "D30": _calc_d30,
    "D40": _calc_d40,
    "D45": _calc_d45,
    "D60": _calc_d60,
}

# D-9 和 D-12 不需要 sign_idx 參數（公式只用 abs_pos）
_NO_SIGN_IDX = {"D9"}


def _calc_single_varga(varga_key: str, planets_data: list[tuple[str, float]]) -> dict:
    """計算單張分盤的所有行星位置"""
    info = VARGA_INFO[varga_key]
    func = _VARGA_FUNCS[varga_key]
    needs_sign = varga_key not in _NO_SIGN_IDX

    result_planets = {}
    for name, abs_pos in planets_data:
        sidx = _sign_idx(abs_pos)
        if needs_sign:
            varga_sign_idx = func(abs_pos, sidx)
        else:
            varga_sign_idx = func(abs_pos)

        sign = SIGNS[varga_sign_idx % 12]
        entry = {
            "星座": sign,
            "星座_zh": SIGN_NAMES_ZH[sign],
        }
        dignity = _planet_dignity(name, sign)
        if dignity:
            entry["力量"] = dignity
        result_planets[name] = entry

    return {
        "類型": f"D-{varga_key[1:]}",
        "名稱": info["name"],
        "中文": info["zh"],
        "用途": info["用途"],
        "行星": result_planets,
    }


def calc_varga_charts(subject: AstrologicalSubject) -> dict:
    """從 Kerykeion subject 計算 17 張分盤
    （D-2/3/4/6/7/8/9/10/12/16/20/24/27/30/40/45/60）

    回傳格式：{"D2": {...}, "D3": {...}, ...}
    """
    # 收集所有行星的 (name, abs_pos)
    planets_data = []
    for attr in _PLANET_ATTRS:
        p = getattr(subject, attr)
        planets_data.append((p.name, p.abs_pos))

    for attr, name in _NODE_ATTRS:
        node = getattr(subject, attr, None)
        if node:
            planets_data.append((name, node.abs_pos))

    return {
        key: _calc_single_varga(key, planets_data)
        for key in _VARGA_FUNCS
    }
