"""
BeBetter API — 命理排盤引擎。
每個命理系統獨立一組 endpoint，按「系統/功能」分類。

10 組系統、21 個 endpoint：
  /bazi     — 八字（natal, fortune, compat）
  /qimen    — 奇門遁甲（natal, horary）
  /liuren   — 大六壬（natal, horary）
  /taiyi    — 太乙神數（natal, horary）
  /meihua   — 梅花易數（natal, horary）
  /astro    — 西洋占星（natal, transit, compat）
  /vedic    — 印度占星（natal, transit）
  /geomancy — 地占術（horary）
  /qizheng  — 七政四餘（natal）
  /mayan    — 瑪雅曆（natal, fortune, transit）
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)


def _wrap_calc_error(label: str, exc: Exception) -> HTTPException:
    """命理計算失敗：完整 trace 進 log，對外只給使用者能行動的訊息。

    ValueError 通常是參數驗證（如「找不到地址」），照原訊息回；
    其他 exception 收斂為「請檢查生辰參數」，避免吐 stack trace。
    """
    if isinstance(exc, ValueError):
        return HTTPException(400, detail=f"{label}：{exc}")
    logger.exception("%s: %s", label, exc)
    return HTTPException(400, detail=f"{label}，請檢查生辰參數是否正確（年月日時分 + 出生地）")

from core import (
    run_qimen, run_liuren, run_taiyi, run_meihua,
    run_bazi, run_western_astro, run_vedic_astro,
    bazi_from_pillars, run_bazi_compat, run_bazi_fortune,
    run_astro_synastry, run_astro_transit, run_vedic_transit,
    run_geomancy, run_qizheng,
    run_mayan_natal, run_mayan_fortune, run_mayan_transit,
)

router = APIRouter()
_executor = ThreadPoolExecutor(max_workers=3)


# ===== Request Models =====

class BirthTimeRequest(BaseModel):
    """通用生辰：年月日時分"""
    year: int
    month: int
    day: int
    hour: int
    minute: int = 0


class LocationRequest(BirthTimeRequest):
    """生辰 + 出生地（占星系需要經緯度）"""
    lat: float | None = None
    lng: float | None = None
    address: str | None = None


class TransitRequest(LocationRequest):
    """占星流年：生辰 + 出生地 + 預測區間。

    target_date 給了就走流日模式（只算當天），target_year / forecast_years 會被忽略。
    """
    tz_str: str = "Asia/Taipei"
    target_year: int | None = None
    forecast_years: int = 1
    target_date: str | None = None  # 'YYYY-MM-DD'，給了就走流日模式
    include_natal_summary: bool = True
    profile_key: str | None = None  # 主對話傳人類可讀識別（如 main / friend-alice），會出現在快取檔名


class BaziFortuneRequest(BaseModel):
    """八字流年：四柱 + 性別 + 出生日期"""
    pillars: str
    gender: str = "男"
    birth_date: str = ""
    target_year: int | None = None
    forecast_years: int = 10


class BaziCompatRequest(BaseModel):
    """八字合盤：兩人四柱"""
    pillars_a: str
    pillars_b: str
    gender_a: str = "男"
    gender_b: str = "男"
    birth_date_a: str = ""
    birth_date_b: str = ""


class GeomancyRequest(BaseModel):
    """地占問事：問題 + 可選種子或手動 Mother"""
    question: str = ""
    seed: str | None = None
    manual_mothers: list[list[int]] | None = None


class QizhengRequest(LocationRequest):
    """七政四餘：生辰 + 出生地 + 時區"""
    tz_str: str = "Asia/Taipei"


class MayanDateRequest(BaseModel):
    """瑪雅曆本命：年月日（不需時間與出生地）"""
    year: int
    month: int
    day: int


class MayanFortuneRequest(MayanDateRequest):
    """瑪雅曆大運流年：本命日期 + 預測區間"""
    target_year: int | None = None
    forecast_years: int = 10


class MayanTransitRequest(MayanDateRequest):
    """瑪雅曆當下能量：本命日期 + 目標日期"""
    target_date: str | None = None


class AstroCompatRequest(BaseModel):
    """西洋占星合盤：兩人出生資料"""
    name_a: str
    year_a: int
    month_a: int
    day_a: int
    hour_a: int
    minute_a: int
    lat_a: float | None = None
    lng_a: float | None = None
    address_a: str | None = None
    tz_a: str = "Asia/Taipei"
    name_b: str
    year_b: int
    month_b: int
    day_b: int
    hour_b: int
    minute_b: int
    lat_b: float | None = None
    lng_b: float | None = None
    address_b: str | None = None
    tz_b: str = "Asia/Taipei"


# ===== 共用工具 =====

_geocode_cache: dict[str, tuple[float, float]] = {}


async def _geocode(address: str) -> tuple[float, float]:
    """地址轉經緯度。同地址結果常駐記憶體，避免重複打 nominatim 撞 rate limit。"""
    key = address.strip().lower()
    if key in _geocode_cache:
        return _geocode_cache[key]
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": address, "format": "json", "limit": 1},
            headers={"User-Agent": "bebetter-api/1.0"},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json()
    if not results:
        raise ValueError(f"找不到地址: {address}")
    coords = (float(results[0]["lat"]), float(results[0]["lon"]))
    _geocode_cache[key] = coords
    return coords


async def _resolve_coords(lat, lng, address):
    """有地址但沒經緯度時自動 geocode"""
    if address and lat is None and lng is None:
        lat, lng = await _geocode(address)
    return lat, lng


def _parse_date(s: str) -> tuple[int, int, int] | None:
    if not s:
        return None
    parts = s.split("-")
    return (int(parts[0]), int(parts[1]), int(parts[2]))


# ===== 八字 =====

bazi_router = APIRouter(prefix="/bazi", tags=["八字"])


@bazi_router.post("/natal")
async def bazi_natal(req: BirthTimeRequest):
    """八字本命：四柱、十神、藏干、五行分布"""
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            _executor, run_bazi, req.year, req.month, req.day, req.hour,
        )
    except Exception as e:
        raise _wrap_calc_error('八字排盤失敗', e)
    return result


@bazi_router.post("/fortune")
async def bazi_fortune(req: BaziFortuneRequest):
    """八字流年：大運 + 逐年分析"""
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            _executor, run_bazi_fortune,
            req.pillars, req.gender, _parse_date(req.birth_date),
            req.target_year, req.forecast_years,
        )
    except Exception as e:
        raise _wrap_calc_error('八字流年計算失敗', e)
    return result


@bazi_router.post("/compat")
async def bazi_compat(req: BaziCompatRequest):
    """八字合盤：個盤擴充 + 跨盤關係"""
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            _executor, run_bazi_compat,
            bazi_from_pillars(req.pillars_a), bazi_from_pillars(req.pillars_b),
            req.gender_a, req.gender_b,
            _parse_date(req.birth_date_a), _parse_date(req.birth_date_b),
        )
    except Exception as e:
        raise _wrap_calc_error('八字合盤計算失敗', e)
    return result


# ===== 奇門遁甲 =====
# run_qimen 和 run_taiyi 共用 config module，不能放進 executor 並行

qimen_router = APIRouter(prefix="/qimen", tags=["奇門遁甲"])


@qimen_router.post("/natal")
async def qimen_natal(req: BirthTimeRequest):
    """奇門遁甲本命盤"""
    try:
        return run_qimen(req.year, req.month, req.day, req.hour, req.minute)
    except Exception as e:
        raise _wrap_calc_error('奇門排盤失敗', e)


@qimen_router.post("/horary")
async def qimen_horary(req: BirthTimeRequest):
    """奇門遁甲問事盤"""
    try:
        return run_qimen(req.year, req.month, req.day, req.hour, req.minute)
    except Exception as e:
        raise _wrap_calc_error('奇門排盤失敗', e)


# ===== 大六壬 =====

liuren_router = APIRouter(prefix="/liuren", tags=["大六壬"])


@liuren_router.post("/natal")
async def liuren_natal(req: BirthTimeRequest):
    """大六壬本命盤"""
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            _executor, run_liuren, req.year, req.month, req.day, req.hour,
        )
    except Exception as e:
        raise _wrap_calc_error('六壬排盤失敗', e)
    return result


@liuren_router.post("/horary")
async def liuren_horary(req: BirthTimeRequest):
    """大六壬問事盤"""
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            _executor, run_liuren, req.year, req.month, req.day, req.hour,
        )
    except Exception as e:
        raise _wrap_calc_error('六壬排盤失敗', e)
    return result


# ===== 太乙神數 =====
# run_taiyi 和 run_qimen 共用 config module，不能放進 executor 並行

taiyi_router = APIRouter(prefix="/taiyi", tags=["太乙神數"])


@taiyi_router.post("/natal")
async def taiyi_natal(req: BirthTimeRequest):
    """太乙神數本命盤"""
    try:
        return run_taiyi(req.year, req.month, req.day, req.hour, req.minute)
    except Exception as e:
        raise _wrap_calc_error('太乙排盤失敗', e)


@taiyi_router.post("/horary")
async def taiyi_horary(req: BirthTimeRequest):
    """太乙神數問事盤"""
    try:
        return run_taiyi(req.year, req.month, req.day, req.hour, req.minute)
    except Exception as e:
        raise _wrap_calc_error('太乙排盤失敗', e)


# ===== 梅花易數 =====

meihua_router = APIRouter(prefix="/meihua", tags=["梅花易數"])


@meihua_router.post("/natal")
async def meihua_natal(req: BirthTimeRequest):
    """梅花易數本命卦"""
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            _executor, run_meihua,
            req.year, req.month, req.day, req.hour, req.minute,
        )
    except Exception as e:
        raise _wrap_calc_error('梅花排卦失敗', e)
    return result


@meihua_router.post("/horary")
async def meihua_horary(req: BirthTimeRequest):
    """梅花易數問事卦"""
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            _executor, run_meihua,
            req.year, req.month, req.day, req.hour, req.minute,
        )
    except Exception as e:
        raise _wrap_calc_error('梅花排卦失敗', e)
    return result


# ===== 地占術 =====

geomancy_router = APIRouter(prefix="/geomancy", tags=["地占術"])


@geomancy_router.post("/horary")
async def geomancy_horary(req: GeomancyRequest):
    """地占問事：用隨機種子或手動輸入產生 Shield Chart，解讀問題走向"""
    try:
        result = run_geomancy(
            question=req.question,
            seed=req.seed,
            manual_mothers=req.manual_mothers,
        )
    except Exception as e:
        raise _wrap_calc_error('地占排盤失敗', e)
    return result


# ===== 西洋占星 =====

astro_router = APIRouter(prefix="/astro", tags=["西洋占星"])


@astro_router.post("/natal")
async def astro_natal(req: LocationRequest):
    """西洋占星本命盤：行星、相位、宮位"""
    loop = asyncio.get_event_loop()
    try:
        lat, lng = await _resolve_coords(req.lat, req.lng, req.address)
        if lat is None or lng is None:
            raise ValueError("必須提供經緯度或地址")
        result = await loop.run_in_executor(
            _executor, run_western_astro,
            req.year, req.month, req.day, req.hour, req.minute, lat, lng,
        )
    except Exception as e:
        raise _wrap_calc_error('占星排盤失敗', e)
    return result


@astro_router.post("/transit")
async def astro_transit_ep(req: TransitRequest):
    """西洋占星流年：行運 + 太陽回歸 + 次限推運 + 逆行衝擊"""
    loop = asyncio.get_event_loop()
    try:
        lat, lng = await _resolve_coords(req.lat, req.lng, req.address)
        if lat is None or lng is None:
            raise ValueError("必須提供經緯度或地址")
        result = await loop.run_in_executor(
            _executor, run_astro_transit,
            req.year, req.month, req.day, req.hour, req.minute,
            lat, lng, req.tz_str, req.target_year, req.forecast_years,
        )
    except Exception as e:
        raise _wrap_calc_error('占星流年計算失敗', e)
    if not req.include_natal_summary:
        result.pop("本命盤摘要", None)
    return result


@astro_router.post("/compat")
async def astro_compat(req: AstroCompatRequest):
    """西洋占星合盤：Synastry + Composite"""
    loop = asyncio.get_event_loop()
    try:
        lat_a, lng_a = await _resolve_coords(req.lat_a, req.lng_a, req.address_a)
        lat_b, lng_b = await _resolve_coords(req.lat_b, req.lng_b, req.address_b)
        if lat_a is None or lng_a is None:
            raise ValueError("必須提供 A 的經緯度或地址")
        if lat_b is None or lng_b is None:
            raise ValueError("必須提供 B 的經緯度或地址")
        result = await loop.run_in_executor(
            _executor, run_astro_synastry,
            req.name_a, req.year_a, req.month_a, req.day_a,
            req.hour_a, req.minute_a, lat_a, lng_a,
            req.name_b, req.year_b, req.month_b, req.day_b,
            req.hour_b, req.minute_b, lat_b, lng_b,
            req.tz_a, req.tz_b,
        )
    except Exception as e:
        raise _wrap_calc_error('占星合盤計算失敗', e)
    return result


# ===== 印度占星 =====

vedic_router = APIRouter(prefix="/vedic", tags=["印度占星"])


@vedic_router.get("/reference")
async def vedic_reference():
    """印度占星完整對照表 — 行星 / 星座 / dignity / nakshatra / dasha / varga / karaka / devata / yoga / gochar 一次回齊"""
    from core.vedic_reference import get_full_reference
    return get_full_reference()


@vedic_router.post("/natal")
async def vedic_natal(req: LocationRequest):
    """印度占星本命盤：行星、宮位、Nakshatra"""
    loop = asyncio.get_event_loop()
    try:
        lat, lng = await _resolve_coords(req.lat, req.lng, req.address)
        if lat is None or lng is None:
            raise ValueError("必須提供經緯度或地址")
        result = await loop.run_in_executor(
            _executor, run_vedic_astro,
            req.year, req.month, req.day, req.hour, req.minute, lat, lng,
        )
    except Exception as e:
        raise _wrap_calc_error('印度占星排盤失敗', e)
    return result


@vedic_router.post("/transit")
async def vedic_transit_ep(req: TransitRequest):
    """印度占星流年：完整本命盤 + Dasha 大限 + Gochar 行運 + Sade Sati"""
    loop = asyncio.get_event_loop()
    try:
        lat, lng = await _resolve_coords(req.lat, req.lng, req.address)
        if lat is None or lng is None:
            raise ValueError("必須提供經緯度或地址")
        result = await loop.run_in_executor(
            _executor, run_vedic_transit,
            req.year, req.month, req.day, req.hour, req.minute,
            lat, lng, req.tz_str, req.target_year, req.forecast_years,
            req.profile_key, req.target_date,
        )
    except Exception as e:
        raise _wrap_calc_error('印度占星計算失敗', e)
    if not req.include_natal_summary:
        result.pop("本命盤", None)
    # 回傳 resolved 經緯度，讓呼叫方可存下來避免重複 geocode
    result["resolved_coords"] = {"lat": lat, "lng": lng}
    return result


# ===== 七政四餘 =====

qizheng_router = APIRouter(prefix="/qizheng", tags=["七政四餘"])


@qizheng_router.post("/natal")
async def qizheng_natal(req: QizhengRequest):
    """七政四餘本命盤：十一曜位置、十二宮、相位、格局"""
    loop = asyncio.get_event_loop()
    try:
        lat, lng = await _resolve_coords(req.lat, req.lng, req.address)
        if lat is None or lng is None:
            raise ValueError("必須提供經緯度或地址")
        result = await loop.run_in_executor(
            _executor, run_qizheng,
            req.year, req.month, req.day, req.hour, req.minute,
            lat, lng, req.tz_str,
        )
    except Exception as e:
        raise _wrap_calc_error('七政四餘排盤失敗', e)
    return result


# ===== 瑪雅曆 =====

mayan_router = APIRouter(prefix="/mayan", tags=["瑪雅曆"])


@mayan_router.post("/natal")
async def mayan_natal(req: MayanDateRequest):
    """瑪雅曆本命盤：Long Count + Tzolkin + Haab + Lord of Night + Galactic Signature"""
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            _executor, run_mayan_natal, req.year, req.month, req.day,
        )
    except Exception as e:
        raise _wrap_calc_error('瑪雅曆排盤失敗', e)
    return result


@mayan_router.post("/fortune")
async def mayan_fortune(req: MayanFortuneRequest):
    """瑪雅曆運勢：52 年 Calendar Round 大運 + Katun 階段 + 流年 Year Bearer + 當前 Trecena/Haab 月"""
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            _executor, run_mayan_fortune,
            req.year, req.month, req.day, req.target_year, req.forecast_years,
        )
    except Exception as e:
        raise _wrap_calc_error('瑪雅曆運勢計算失敗', e)
    return result


@mayan_router.post("/transit")
async def mayan_transit_ep(req: MayanTransitRequest):
    """瑪雅曆當下能量：指定日期 Kin + 與本命的 Harmonic 關係"""
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            _executor, run_mayan_transit,
            req.year, req.month, req.day, req.target_date,
        )
    except Exception as e:
        raise _wrap_calc_error('瑪雅曆流日計算失敗', e)
    return result


# ===== 註冊所有 sub-router =====

for r in (bazi_router, qimen_router, liuren_router, taiyi_router,
          meihua_router, geomancy_router, astro_router, vedic_router,
          qizheng_router, mayan_router):
    router.include_router(r)
