import os
import json

try:
    from core import (
        run_qimen, run_liuren, run_taiyi, run_meihua,
        run_bazi, run_western_astro, run_vedic_astro,
        run_astro_synastry, run_astro_transit, run_vedic_transit,
        run_geomancy, run_qizheng, run_qizheng_transit,
        run_mayan_natal, run_mayan_fortune, run_mayan_transit,
        interpret as core_interpret,
    )
    from core.bazi import run_bazi_compat, bazi_from_pillars, run_bazi_fortune
    MODE = "direct"
except ImportError:
    MODE = "http"

API_BASE = os.getenv("BEBETTER_API_BASE", "https://bebetter.localtest.me/api")
VEDASTRO_API = "https://vedastro.azurewebsites.net/api/Calculate"


async def _geocode(address: str) -> tuple[float, float]:
    """用 Nominatim 把地址轉經緯度，失敗時拋出 ValueError"""
    import httpx
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": address, "format": "json", "limit": 1},
            headers={"User-Agent": "bebetter-cli/1.0"},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json()
    if not results:
        raise ValueError(f"找不到地址: {address}")
    return float(results[0]["lat"]), float(results[0]["lon"])


async def _post(path: str, payload: dict) -> str:
    import httpx
    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.post(
            f"{API_BASE}{path}", json=payload, timeout=60,
        )
        resp.raise_for_status()
        return resp.text


def _run_all_direct(year, month, day, hour, minute, lat, lng):
    """全系統排盤（direct mode 用）"""
    qimen = run_qimen(year, month, day, hour, minute)
    liuren = run_liuren(year, month, day, hour)
    taiyi = run_taiyi(year, month, day, hour, minute)
    meihua = run_meihua(year, month, day, hour, minute)
    bazi = run_bazi(year, month, day, hour)
    western = None
    vedic = None
    if lat is not None and lng is not None:
        western = run_western_astro(year, month, day, hour, minute, lat, lng)
        vedic = run_vedic_astro(year, month, day, hour, minute, lat, lng)
    return qimen, liuren, taiyi, meihua, bazi, western, vedic


async def _resolve_coords(lat, lng, address):
    """有地址但沒經緯度時，自動 geocode"""
    if address and lat is None and lng is None:
        lat, lng = await _geocode(address)
    return lat, lng


async def natal(year: int, month: int, day: int, hour: int, minute: int,
                lat: float = None, lng: float = None,
                address: str = None) -> str:
    """本命解讀:用出生時間排全部系統(奇門遁甲、大六壬、太乙神數、梅花易數、八字、占星),分析天生格局與性格。
輸入西曆出生年月日時分。提供經緯度(lat/lng)或地址(address)可加入占星分析。"""
    lat, lng = await _resolve_coords(lat, lng, address)

    if MODE == "direct":
        qimen, liuren, taiyi, meihua, bazi, western, vedic = _run_all_direct(
            year, month, day, hour, minute, lat, lng,
        )
        interpretation = core_interpret(
            qimen, liuren, taiyi, meihua, bazi, western, vedic,
            mode="natal",
        )
        result = {
            "mode": "natal",
            "qimen": qimen, "liuren": liuren, "taiyi": taiyi,
            "meihua": meihua, "bazi": bazi,
            "western_astro": western, "vedic_astro": vedic,
            "interpretation": interpretation,
        }
        return json.dumps(result, ensure_ascii=False, indent=2)

    # HTTP mode: 分別呼叫各系統端點再組合
    import asyncio
    base_payload = {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
    }
    loc_payload = {**base_payload}
    if lat is not None and lng is not None:
        loc_payload["lat"] = lat
        loc_payload["lng"] = lng

    tasks = {
        "bazi": _post("/bazi/natal", base_payload),
        "qimen": _post("/qimen/natal", base_payload),
        "liuren": _post("/liuren/natal", base_payload),
        "taiyi": _post("/taiyi/natal", base_payload),
        "meihua": _post("/meihua/natal", base_payload),
    }
    # 有座標才排占星盤
    if lat is not None and lng is not None:
        tasks["western_astro"] = _post("/astro/natal", loc_payload)
        tasks["vedic_astro"] = _post("/vedic/natal", loc_payload)

    keys = list(tasks.keys())
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    combined = {"mode": "natal"}
    for k, r in zip(keys, results):
        if isinstance(r, Exception):
            combined[k] = {"error": str(r)}
        else:
            try:
                combined[k] = json.loads(r)
            except (json.JSONDecodeError, TypeError):
                combined[k] = r
    return json.dumps(combined, ensure_ascii=False, indent=2)


async def horary(year: int, month: int, day: int, hour: int, minute: int,
                 question: str = None,
                 lat: float = None, lng: float = None,
                 address: str = None) -> str:
    """問事解讀:用當下時間排全部系統(奇門遁甲、大六壬、太乙神數、梅花易數、八字、占星),分析事件走向與建議。
輸入西曆年月日時分。question=想問的問題。提供經緯度(lat/lng)或地址(address)可加入占星分析。"""
    lat, lng = await _resolve_coords(lat, lng, address)

    if MODE == "direct":
        qimen, liuren, taiyi, meihua, bazi, western, vedic = _run_all_direct(
            year, month, day, hour, minute, lat, lng,
        )
        interpretation = core_interpret(
            qimen, liuren, taiyi, meihua, bazi, western, vedic,
            mode="horary", question=question,
        )
        result = {
            "mode": "horary", "question": question,
            "qimen": qimen, "liuren": liuren, "taiyi": taiyi,
            "meihua": meihua, "bazi": bazi,
            "western_astro": western, "vedic_astro": vedic,
            "interpretation": interpretation,
        }
        return json.dumps(result, ensure_ascii=False, indent=2)

    # HTTP mode: 分別呼叫各系統端點再組合
    import asyncio
    base_payload = {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
    }
    if question:
        base_payload["question"] = question
    loc_payload = {**base_payload}
    if lat is not None and lng is not None:
        loc_payload["lat"] = lat
        loc_payload["lng"] = lng

    tasks = {
        "bazi": _post("/bazi/natal", base_payload),
        "qimen": _post("/qimen/horary", base_payload),
        "liuren": _post("/liuren/horary", base_payload),
        "taiyi": _post("/taiyi/horary", base_payload),
        "meihua": _post("/meihua/horary", base_payload),
    }
    if lat is not None and lng is not None:
        tasks["western_astro"] = _post("/astro/natal", loc_payload)
        tasks["vedic_astro"] = _post("/vedic/natal", loc_payload)

    keys = list(tasks.keys())
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    combined = {"mode": "horary", "question": question}
    for k, r in zip(keys, results):
        if isinstance(r, Exception):
            combined[k] = {"error": str(r)}
        else:
            try:
                combined[k] = json.loads(r)
            except (json.JSONDecodeError, TypeError):
                combined[k] = r
    return json.dumps(combined, ensure_ascii=False, indent=2)


async def bazi_compat(
    pillars_a: str, pillars_b: str,
    gender_a: str = "男", gender_b: str = "男",
    birth_date_a: str = "", birth_date_b: str = "",
) -> str:
    """八字合盤計算:輸入兩人四柱(如'庚午己丑癸未癸丑'),回傳個盤擴充(空亡/納音/胎元/命宮/神煞/大運)+跨盤關係(天干合/六合/六沖/六害/破/三合/三會/三刑/暗合/神煞交叉)。
gender_a/gender_b='男'或'女',影響大運順逆。
birth_date_a/birth_date_b='1990-07-15'格式,有值時計算起運歲並在大運附帶年齡區間。"""

    def _parse_date(s: str) -> tuple[int, int, int] | None:
        if not s:
            return None
        parts = s.split("-")
        return (int(parts[0]), int(parts[1]), int(parts[2]))

    bd_a = _parse_date(birth_date_a)
    bd_b = _parse_date(birth_date_b)

    if MODE == "direct":
        bazi_a = bazi_from_pillars(pillars_a)
        bazi_b = bazi_from_pillars(pillars_b)

        result = run_bazi_compat(bazi_a, bazi_b, gender_a, gender_b,
                                birth_date_a=bd_a, birth_date_b=bd_b)
        return json.dumps(result, ensure_ascii=False, indent=2)

    payload = {
        "pillars_a": pillars_a, "pillars_b": pillars_b,
        "gender_a": gender_a, "gender_b": gender_b,
        "birth_date_a": birth_date_a, "birth_date_b": birth_date_b,
    }
    return await _post("/bazi/compat", payload)


async def bazi_fortune(
    pillars: str, gender: str = "男", birth_date: str = "",
    target_year: int = None, forecast_years: int = 10,
) -> str:
    """八字大運流年分析:輸入個人四柱(如'庚午己丑癸未癸丑'),回傳個盤擴充+大運總覽+逐年流年分析(流年十神/與命盤交互/與大運交互/喜忌判定/神煞觸發)+關鍵年份摘要。
pillars=八字字串(6或8字)。gender='男'或'女',影響大運順逆。birth_date='1990-07-15'格式,有值時計算起運歲。target_year=分析起始年(預設今年)。forecast_years=向後預測年數(預設10)。"""

    def _parse_date(s: str) -> tuple[int, int, int] | None:
        if not s:
            return None
        parts = s.split("-")
        return (int(parts[0]), int(parts[1]), int(parts[2]))

    bd = _parse_date(birth_date)

    if MODE == "direct":
        result = run_bazi_fortune(
            pillars, gender, bd, target_year, forecast_years,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)

    payload = {
        "pillars": pillars,
        "gender": gender,
        "birth_date": birth_date,
    }
    if target_year is not None:
        payload["target_year"] = target_year
    payload["forecast_years"] = forecast_years
    return await _post("/bazi/fortune", payload)


async def astro_compat(
    name_a: str, year_a: int, month_a: int, day_a: int,
    hour_a: int, minute_a: int,
    name_b: str, year_b: int, month_b: int, day_b: int,
    hour_b: int, minute_b: int,
    lat_a: float = None, lng_a: float = None, address_a: str = None,
    lat_b: float = None, lng_b: float = None, address_b: str = None,
    tz_a: str = "Asia/Taipei", tz_b: str = "Asia/Taipei",
) -> str:
    """西洋占星合盤:輸入兩人出生資料,回傳 Synastry(跨盤相位+宮位疊合) + Composite(中點組合盤)。
經緯度(lat/lng)或地址(address)必須提供,占星需要出生地座標。"""
    lat_a, lng_a = await _resolve_coords(lat_a, lng_a, address_a)
    lat_b, lng_b = await _resolve_coords(lat_b, lng_b, address_b)

    if lat_a is None or lng_a is None:
        return "錯誤: 必須提供 A 的經緯度或地址"
    if lat_b is None or lng_b is None:
        return "錯誤: 必須提供 B 的經緯度或地址"

    if MODE == "direct":
        result = run_astro_synastry(
            name_a, year_a, month_a, day_a, hour_a, minute_a, lat_a, lng_a,
            name_b, year_b, month_b, day_b, hour_b, minute_b, lat_b, lng_b,
            tz_a, tz_b,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)

    payload = {
        "name_a": name_a, "year_a": year_a, "month_a": month_a, "day_a": day_a,
        "hour_a": hour_a, "minute_a": minute_a, "lat_a": lat_a, "lng_a": lng_a,
        "tz_a": tz_a,
        "name_b": name_b, "year_b": year_b, "month_b": month_b, "day_b": day_b,
        "hour_b": hour_b, "minute_b": minute_b, "lat_b": lat_b, "lng_b": lng_b,
        "tz_b": tz_b,
    }
    return await _post("/astro/compat", payload)


async def astro_transit(
    year: int, month: int, day: int, hour: int, minute: int,
    lat: float = None, lng: float = None, address: str = None,
    tz: str = "Asia/Taipei",
    target_year: int = None, forecast_years: int = 1,
) -> str:
    """西洋占星流年預測:輸入出生資料,回傳太陽回歸盤+外行星行運(木土天海冥與本命行星的相位、入相/精確/出相日期)+次限推運(推運月亮/太陽)+小限法(年度激活宮位與宮主星)+逆行衝擊(水金火逆行觸發的本命相位)。
經緯度(lat/lng)或地址(address)必須提供。target_year=預測年份(預設今年)。forecast_years=預測年數(預設1,最多3)。"""
    lat, lng = await _resolve_coords(lat, lng, address)

    if lat is None or lng is None:
        return "錯誤: 必須提供經緯度或地址"

    if MODE == "direct":
        result = run_astro_transit(
            year, month, day, hour, minute, lat, lng, tz,
            target_year, forecast_years,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)

    payload = {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "lat": lat, "lng": lng, "tz_str": tz,
    }
    if target_year is not None:
        payload["target_year"] = target_year
    payload["forecast_years"] = forecast_years
    return await _post("/astro/transit", payload)


async def vedic_transit(
    year: int, month: int, day: int, hour: int, minute: int,
    lat: float = None, lng: float = None, address: str = None,
    tz: str = "Asia/Taipei",
    target_year: int = None, forecast_years: int = 1,
    profile_key: str = None, target_date: str = None,
) -> str:
    """印度占星流年預測。經緯度(lat/lng)或地址(address)必須提供。
target_year=預測年份(預設今年)。forecast_years=預測年數(預設1,最多3)。
profile_key=快取檔肉眼識別字串(如 main / friend-alice)。
target_date=YYYY-MM-DD,給了就走流日模式,只算當天。"""
    lat, lng = await _resolve_coords(lat, lng, address)

    if lat is None or lng is None:
        return "錯誤: 必須提供經緯度或地址"

    if MODE == "direct":
        result = run_vedic_transit(
            year, month, day, hour, minute, lat, lng, tz,
            target_year, forecast_years,
            profile_key, target_date,
        )
        result["resolved_coords"] = {"lat": lat, "lng": lng}
        return json.dumps(result, ensure_ascii=False, indent=2)

    payload = {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "lat": lat, "lng": lng, "tz_str": tz,
    }
    if target_year is not None:
        payload["target_year"] = target_year
    payload["forecast_years"] = forecast_years
    if profile_key:
        payload["profile_key"] = profile_key
    if target_date:
        payload["target_date"] = target_date
    return await _post("/vedic/transit", payload)


async def astro_natal(
    year: int, month: int, day: int, hour: int, minute: int,
    lat: float = None, lng: float = None, address: str = None,
) -> str:
    """西洋占星本命盤:行星、相位、宮位。經緯度或地址必須提供。"""
    lat, lng = await _resolve_coords(lat, lng, address)
    if lat is None or lng is None:
        return "錯誤: 必須提供經緯度或地址"

    if MODE == "direct":
        result = run_western_astro(year, month, day, hour, minute, lat, lng)
        result["resolved_coords"] = {"lat": lat, "lng": lng}
        return json.dumps(result, ensure_ascii=False, indent=2)

    payload = {"year": year, "month": month, "day": day,
               "hour": hour, "minute": minute, "lat": lat, "lng": lng}
    return await _post("/astro/natal", payload)


async def vedic_natal(
    year: int, month: int, day: int, hour: int, minute: int,
    lat: float = None, lng: float = None, address: str = None,
) -> str:
    """印度占星本命盤:行星、宮位、Nakshatra。經緯度或地址必須提供。"""
    lat, lng = await _resolve_coords(lat, lng, address)
    if lat is None or lng is None:
        return "錯誤: 必須提供經緯度或地址"

    if MODE == "direct":
        result = run_vedic_astro(year, month, day, hour, minute, lat, lng)
        result["resolved_coords"] = {"lat": lat, "lng": lng}
        return json.dumps(result, ensure_ascii=False, indent=2)

    payload = {"year": year, "month": month, "day": day,
               "hour": hour, "minute": minute, "lat": lat, "lng": lng}
    return await _post("/vedic/natal", payload)


async def vedic_reference() -> str:
    """印度占星完整對照表 — 行星 / 星座 / nakshatra / dasha / varga / karaka / yoga / gochar 一次回齊"""
    if MODE == "direct":
        from core.vedic_reference import get_full_reference
        return json.dumps(get_full_reference(), ensure_ascii=False, indent=2)
    import httpx
    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.get(f"{API_BASE}/vedic/reference", timeout=30)
        resp.raise_for_status()
        return resp.text


async def mayan_natal(year: int, month: int, day: int) -> str:
    """瑪雅曆本命:Long Count + Tzolkin + Haab + Lord of Night + Galactic Signature"""
    if MODE == "direct":
        result = run_mayan_natal(year, month, day)
        return json.dumps(result, ensure_ascii=False, indent=2)
    return await _post("/mayan/natal", {"year": year, "month": month, "day": day})


async def mayan_fortune(
    year: int, month: int, day: int,
    target_year: int = None, forecast_years: int = 10,
) -> str:
    """瑪雅曆運勢:52 年大運 + Katun + 流年 + 當前 Trecena/Haab"""
    if MODE == "direct":
        result = run_mayan_fortune(year, month, day, target_year, forecast_years)
        return json.dumps(result, ensure_ascii=False, indent=2)
    payload = {"year": year, "month": month, "day": day,
               "forecast_years": forecast_years}
    if target_year is not None:
        payload["target_year"] = target_year
    return await _post("/mayan/fortune", payload)


async def mayan_transit(
    year: int, month: int, day: int,
    target_date: str = None,
) -> str:
    """瑪雅曆當下能量:指定日期 Kin + 與本命的 Harmonic 關係。target_date=YYYY-MM-DD,預設今天。"""
    if MODE == "direct":
        result = run_mayan_transit(year, month, day, target_date)
        return json.dumps(result, ensure_ascii=False, indent=2)
    payload = {"year": year, "month": month, "day": day}
    if target_date:
        payload["target_date"] = target_date
    return await _post("/mayan/transit", payload)


def _tz_offset(tz_name: str, year: int, month: int, day: int,
               hour: int, minute: int) -> str:
    """時區名稱轉 offset 字串，如 'Asia/Taipei' → '+08:00'"""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    dt = datetime(year, month, day, hour, minute, tzinfo=ZoneInfo(tz_name))
    total = int(dt.utcoffset().total_seconds())
    sign = "+" if total >= 0 else "-"
    h, rem = divmod(abs(total), 3600)
    return f"{sign}{h:02d}:{rem // 60:02d}"


async def vedic_compat(
    name_a: str, year_a: int, month_a: int, day_a: int,
    hour_a: int, minute_a: int,
    name_b: str, year_b: int, month_b: int, day_b: int,
    hour_b: int, minute_b: int,
    lat_a: float = None, lng_a: float = None, address_a: str = None,
    lat_b: float = None, lng_b: float = None, address_b: str = None,
    tz_a: str = "Asia/Taipei", tz_b: str = "Asia/Taipei",
) -> str:
    """印度占星婚配(Kuta Matching):輸入兩人出生資料,回傳 Ashtakoot 八項 Kuta 計分(36分制)+31項深度預測(Dosha/壽命/婚姻穩定/性格)+兩人 Vedic 本命盤。
經緯度(lat/lng)或地址(address)必須提供。name_a/name_b=兩人姓名或代號。"""
    lat_a, lng_a = await _resolve_coords(lat_a, lng_a, address_a)
    lat_b, lng_b = await _resolve_coords(lat_b, lng_b, address_b)

    if lat_a is None or lng_a is None:
        return "錯誤: 必須提供 A 的經緯度或地址"
    if lat_b is None or lng_b is None:
        return "錯誤: 必須提供 B 的經緯度或地址"

    import asyncio

    off_a = _tz_offset(tz_a, year_a, month_a, day_a, hour_a, minute_a)
    off_b = _tz_offset(tz_b, year_b, month_b, day_b, hour_b, minute_b)

    # VedAstro Kuta 計分 + 深度預測
    async def _kuta():
        import httpx
        payload = {
            "maleBirthTime": {
                "StdTime": f"{hour_a:02d}:{minute_a:02d} {day_a:02d}/{month_a:02d}/{year_a} {off_a}",
                "Location": {"Name": address_a or name_a,
                             "Longitude": lng_a, "Latitude": lat_a},
            },
            "femaleBirthTime": {
                "StdTime": f"{hour_b:02d}:{minute_b:02d} {day_b:02d}/{month_b:02d}/{year_b} {off_b}",
                "Location": {"Name": address_b or name_b,
                             "Longitude": lng_b, "Latitude": lat_b},
            },
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{VEDASTRO_API}/MatchReport", json=payload, timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("Status") == "Fail":
                return {"error": data.get("Payload", "VedAstro API error")}
            return data.get("Payload")

    # 兩人 Vedic 本命盤（從自有系統取）
    async def _vedic_chart(year, month, day, hour, minute, lat, lng):
        if MODE == "direct" and lat is not None and lng is not None:
            return run_vedic_astro(year, month, day, hour, minute, lat, lng)
        payload = {"year": year, "month": month, "day": day,
                   "hour": hour, "minute": minute, "lat": lat, "lng": lng}
        result = await _post("/vedic/natal", payload)
        try:
            return json.loads(result)
        except (json.JSONDecodeError, TypeError):
            return result

    results = await asyncio.gather(
        _kuta(),
        _vedic_chart(year_a, month_a, day_a, hour_a, minute_a, lat_a, lng_a),
        _vedic_chart(year_b, month_b, day_b, hour_b, minute_b, lat_b, lng_b),
        return_exceptions=True,
    )

    def _safe(r):
        return {"error": str(r)} if isinstance(r, Exception) else r

    combined = {
        "kuta_report": _safe(results[0]),
        "chart_a": {"name": name_a, "vedic_astro": _safe(results[1])},
        "chart_b": {"name": name_b, "vedic_astro": _safe(results[2])},
    }
    return json.dumps(combined, ensure_ascii=False, indent=2)


async def geomancy(
    question: str = "",
    seed: str = None,
    manual_mothers: list[list[int]] = None,
) -> str:
    """地占問事(Geomancy):用隨機種子或手動輸入產生 Shield Chart(15 figures),排入12宮位,解讀問題走向。
不需要出生時間,問一個具體問題即可起盤。question=想問的問題。seed=隨機種子(預設用當前時間)。
manual_mothers=手動輸入4個Mother figure,每個為[1或2,1或2,1或2,1或2](1=單點,2=雙點)。"""

    if MODE == "direct":
        result = run_geomancy(
            question=question,
            seed=seed,
            manual_mothers=manual_mothers,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)

    payload = {"question": question}
    if seed is not None:
        payload["seed"] = seed
    if manual_mothers is not None:
        payload["manual_mothers"] = manual_mothers
    return await _post("/geomancy/horary", payload)


async def qizheng(
    year: int, month: int, day: int, hour: int, minute: int,
    lat: float = None, lng: float = None, address: str = None,
    tz: str = "Asia/Taipei",
) -> str:
    """七政四餘本命盤:用出生時間排十一曜(日月金木水火土+羅睺計都紫氣月孛),分析恆星黃道位置、十二宮、廟旺落陷、二十八宿、相位和格局。
經緯度(lat/lng)或地址(address)必須提供,七政四餘需要出生地計算命宮。tz=時區(預設Asia/Taipei)。"""
    lat, lng = await _resolve_coords(lat, lng, address)

    if lat is None or lng is None:
        return "錯誤: 必須提供經緯度或地址"

    if MODE == "direct":
        result = run_qizheng(year, month, day, hour, minute, lat, lng, tz)
        return json.dumps(result, ensure_ascii=False, indent=2)

    payload = {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "lat": lat, "lng": lng, "tz_str": tz,
    }
    return await _post("/qizheng/natal", payload)


async def qizheng_transit(
    year: int, month: int, day: int, hour: int, minute: int,
    target_year: int,
    target_month: int = None,
    lat: float = None, lng: float = None, address: str = None,
    tz: str = "Asia/Taipei",
) -> str:
    """七政四餘流運盤:用本命資料+目標年(月選填),排大限(果老年限表)+小限(逐年走宮)+流年(流運十一曜過本命宮+相位)+流月(如指定月份)。
回傳當前大限宮主強弱、小限宮、流年流運星曜激活本命宮位與相位、太歲地支入宮。
經緯度(lat/lng)或地址(address)必須提供。target_year=目標年。target_month=目標月(選填,有給才算流月)。tz=時區(預設Asia/Taipei)。"""
    lat, lng = await _resolve_coords(lat, lng, address)

    if lat is None or lng is None:
        return "錯誤: 必須提供經緯度或地址"

    if MODE == "direct":
        result = run_qizheng_transit(
            year, month, day, hour, minute, lat, lng,
            target_year, target_month, tz,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)

    payload = {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "lat": lat, "lng": lng, "tz_str": tz,
        "target_year": target_year,
    }
    if target_month is not None:
        payload["target_month"] = target_month
    return await _post("/qizheng/transit", payload)

