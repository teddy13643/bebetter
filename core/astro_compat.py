"""西洋占星合盤模組

提供 Synastry（跨盤相位 + 宮位疊合）和 Composite（中點組合盤）計算。
輸入兩人出生資料，回傳結構化 dict 供 API / MCP tool 使用。
"""

from kerykeion import (
    AstrologicalSubject, AstrologicalSubjectFactory,
    ChartDataFactory, CompositeSubjectFactory,
)
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS

# 在預設基礎上開啟四大小行星，否則 ceres/pallas/juno/vesta 會是 None
_BEBETTER_ACTIVE_POINTS = DEFAULT_ACTIVE_POINTS + ["Ceres", "Pallas", "Juno", "Vesta"]


def _build_subject(name: str, year: int, month: int, day: int,
                   hour: int, minute: int, lat: float, lng: float,
                   tz_str: str = "Asia/Taipei"):
    """建立 AstrologicalSubjectModel（含小行星）"""
    return AstrologicalSubjectFactory.from_birth_data(
        name=name, year=year, month=month, day=day,
        hour=hour, minute=minute, lat=lat, lng=lng,
        tz_str=tz_str, zodiac_type="Tropical", online=False,
        active_points=_BEBETTER_ACTIVE_POINTS,
    )


def _format_planet(p: dict) -> dict:
    """把 kerykeion planet dict 格式化成中文 key"""
    return {
        "星座": p["sign"],
        "度數": round(p["position"], 2),
        "逆行": p.get("retrograde", False),
    }


_PLANET_ATTRS = [
    "sun", "moon", "mercury", "venus", "mars",
    "jupiter", "saturn", "uranus", "neptune", "pluto",
]
_EXTRA_POINT_ATTRS = [
    "true_north_lunar_node", "true_south_lunar_node",
    "mean_lilith",
    "chiron", "ceres", "pallas", "juno", "vesta",
]
_HOUSE_ORDINALS = [
    "first", "second", "third", "fourth", "fifth", "sixth",
    "seventh", "eighth", "ninth", "tenth", "eleventh", "twelfth",
]


def _format_natal(subject_model) -> dict:
    """從 AstrologicalSubjectModel 提取行星 + 宮位，對齊現有 _run_astro() 格式"""
    d = subject_model.model_dump()

    planets = {}
    for attr in _PLANET_ATTRS:
        p = d[attr]
        planets[p["name"]] = {
            "星座": p["sign"],
            "度數": round(p["position"], 2),
            "宮位": p["house"],
            "逆行": p.get("retrograde", False),
        }

    extra_points = {}
    for attr in _EXTRA_POINT_ATTRS:
        p = d.get(attr)
        if p is not None:
            extra_points[p["name"]] = {
                "星座": p["sign"],
                "度數": round(p["position"], 2),
                "宮位": p["house"],
                "逆行": p.get("retrograde", False),
            }

    houses = {}
    for i, ordinal in enumerate(_HOUSE_ORDINALS):
        h = d[f"{ordinal}_house"]
        houses[f"第{i + 1}宮"] = {
            "星座": h["sign"],
            "度數": round(h["position"], 2),
        }

    return {"行星": planets, "其他星體": extra_points, "宮位": houses}


def _format_aspect(a: dict) -> dict:
    return {
        "行星A": f"{a['p1_owner']} {a['p1_name']}",
        "行星B": f"{a['p2_owner']} {a['p2_name']}",
        "相位": a["aspect"],
        "容許度": round(a["orbit"], 2),
        "精確度": a["aspect_degrees"],
    }


def _format_composite_aspect(a: dict) -> dict:
    return {
        "行星A": a["p1_name"],
        "行星B": a["p2_name"],
        "相位": a["aspect"],
        "容許度": round(a["orbit"], 2),
    }


def _format_house_comparison(hc: dict) -> dict:
    """格式化宮位疊合：A 的行星落 B 的幾宮、反之亦然"""
    result = {}
    for key, label in [
        ("first_points_in_second_houses", "A落B宮"),
        ("second_points_in_first_houses", "B落A宮"),
    ]:
        items = hc.get(key, [])
        result[label] = [
            {
                "行星": item["point_name"],
                "原本宮位": item["point_owner_house_name"],
                "落入對方宮位": item["projected_house_name"],
            }
            for item in items
        ]
    return result



def run_astro_synastry(
    name_a: str, year_a: int, month_a: int, day_a: int,
    hour_a: int, minute_a: int, lat_a: float, lng_a: float,
    name_b: str, year_b: int, month_b: int, day_b: int,
    hour_b: int, minute_b: int, lat_b: float, lng_b: float,
    tz_a: str = "Asia/Taipei", tz_b: str = "Asia/Taipei",
) -> dict:
    """西洋占星合盤：Synastry + Composite

    回傳結構：
    {
        "個盤": { "A": {...}, "B": {...} },
        "synastry": { "跨盤相位", "宮位疊合" },
        "composite": { "行星", "宮位", "盤內相位" },
    }
    """
    model_a = _build_subject(name_a, year_a, month_a, day_a, hour_a, minute_a, lat_a, lng_a, tz_a)
    model_b = _build_subject(name_b, year_b, month_b, day_b, hour_b, minute_b, lat_b, lng_b, tz_b)

    # Synastry：跨盤相位 + 宮位疊合
    syn_data = ChartDataFactory.create_synastry_chart_data(
        model_a, model_b,
    )
    syn = syn_data.model_dump()

    # Composite：中點組合盤
    comp_factory = CompositeSubjectFactory(model_a, model_b)
    comp_model = comp_factory.get_midpoint_composite_subject_model()
    comp_data = ChartDataFactory.create_composite_chart_data(comp_model)
    comp = comp_data.model_dump()

    # 組合盤行星 + 宮位（model 結構是 flat attributes，跟 AstrologicalSubjectModel 一樣）
    comp_subject = comp.get("subject", {})
    comp_planets = {}
    for attr in _PLANET_ATTRS:
        p = comp_subject.get(attr, {})
        if p:
            comp_planets[p["name"]] = {
                "星座": p["sign"],
                "度數": round(p["position"], 2),
                "逆行": p.get("retrograde", False),
            }
    comp_extra = {}
    for attr in _EXTRA_POINT_ATTRS:
        p = comp_subject.get(attr, {})
        if p:
            comp_extra[p["name"]] = {
                "星座": p["sign"],
                "度數": round(p["position"], 2),
                "逆行": p.get("retrograde", False),
            }
    comp_houses = {}
    for i, ordinal in enumerate(_HOUSE_ORDINALS):
        h = comp_subject.get(f"{ordinal}_house", {})
        if h:
            comp_houses[f"第{i + 1}宮"] = {
                "星座": h["sign"],
                "度數": round(h["position"], 2),
            }

    return {
        "個盤": {
            name_a: _format_natal(model_a),
            name_b: _format_natal(model_b),
        },
        "synastry": {
            "跨盤相位": [_format_aspect(a) for a in syn.get("aspects", [])],
            "宮位疊合": _format_house_comparison(syn.get("house_comparison", {})),
        },
        "composite": {
            "行星": comp_planets,
            "其他星體": comp_extra,
            "宮位": comp_houses,
            "盤內相位": [_format_composite_aspect(a) for a in comp.get("aspects", [])],
        },
    }
