import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core import (
    run_qimen, run_liuren, run_taiyi, run_meihua,
    run_bazi, run_western_astro, run_vedic_astro,
    bazi_from_pillars, run_bazi_compat,
    interpret as core_interpret,
)

router = APIRouter()
_executor = ThreadPoolExecutor(max_workers=3)


class NatalRequest(BaseModel):
    year: int
    month: int
    day: int
    hour: int
    minute: int
    lat: float | None = None
    lng: float | None = None
    skip_interpret: bool = False


class HoraryRequest(BaseModel):
    year: int
    month: int
    day: int
    hour: int
    minute: int
    lat: float | None = None
    lng: float | None = None
    question: str | None = None
    skip_interpret: bool = False


class BaziCompatRequest(BaseModel):
    pillars_a: str
    pillars_b: str
    gender_a: str = "男"
    gender_b: str = "男"


class DivinationResponse(BaseModel):
    mode: str
    question: str | None = None
    qimen: dict
    liuren: dict
    taiyi: dict
    meihua: dict
    bazi: dict
    western_astro: dict | None = None
    vedic_astro: dict | None = None
    interpretation: str | None = None


async def _run_all_systems(year, month, day, hour, minute, lat, lng):
    """全系統排盤，回傳 7 個盤的結果"""
    loop = asyncio.get_event_loop()

    # kinqimen 和 kintaiyi 共用裸 config module，不能並行跑
    qimen = run_qimen(year, month, day, hour, minute)
    taiyi = run_taiyi(year, month, day, hour, minute)

    parallel_tasks = [
        loop.run_in_executor(_executor, run_liuren, year, month, day, hour),
        loop.run_in_executor(_executor, run_meihua, year, month, day, hour, minute),
        loop.run_in_executor(_executor, run_bazi, year, month, day, hour),
    ]
    liuren, meihua, bazi = await asyncio.gather(*parallel_tasks)

    western_astro = None
    vedic_astro = None
    if lat is not None and lng is not None:
        w_task = loop.run_in_executor(
            _executor, run_western_astro,
            year, month, day, hour, minute, lat, lng,
        )
        v_task = loop.run_in_executor(
            _executor, run_vedic_astro,
            year, month, day, hour, minute, lat, lng,
        )
        western_astro, vedic_astro = await asyncio.gather(w_task, v_task)

    return qimen, liuren, taiyi, meihua, bazi, western_astro, vedic_astro


@router.post("/natal")
async def natal(req: NatalRequest) -> DivinationResponse:
    """本命解讀：用出生時間排全部系統，分析天生格局"""
    loop = asyncio.get_event_loop()
    try:
        qimen, liuren, taiyi, meihua, bazi, western, vedic = await _run_all_systems(
            req.year, req.month, req.day, req.hour, req.minute, req.lat, req.lng,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"排盤失敗: {e}")

    interpretation = None
    if not req.skip_interpret:
        interpretation = await loop.run_in_executor(
            _executor, core_interpret,
            qimen, liuren, taiyi, meihua, bazi, western, vedic,
            "natal", None,
        )

    return DivinationResponse(
        mode="natal",
        qimen=qimen, liuren=liuren, taiyi=taiyi, meihua=meihua,
        bazi=bazi, western_astro=western, vedic_astro=vedic,
        interpretation=interpretation,
    )


@router.post("/horary")
async def horary(req: HoraryRequest) -> DivinationResponse:
    """問事解讀：用當下時間排全部系統，分析事件走向"""
    loop = asyncio.get_event_loop()
    try:
        qimen, liuren, taiyi, meihua, bazi, western, vedic = await _run_all_systems(
            req.year, req.month, req.day, req.hour, req.minute, req.lat, req.lng,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"排盤失敗: {e}")

    interpretation = None
    if not req.skip_interpret:
        interpretation = await loop.run_in_executor(
            _executor, core_interpret,
            qimen, liuren, taiyi, meihua, bazi, western, vedic,
            "horary", req.question,
        )

    return DivinationResponse(
        mode="horary", question=req.question,
        qimen=qimen, liuren=liuren, taiyi=taiyi, meihua=meihua,
        bazi=bazi, western_astro=western, vedic_astro=vedic,
        interpretation=interpretation,
    )


@router.post("/bazi-compat")
async def bazi_compat(req: BaziCompatRequest):
    """八字合盤：從四柱字串計算個盤擴充 + 跨盤關係"""
    loop = asyncio.get_event_loop()
    try:
        bazi_a = bazi_from_pillars(req.pillars_a)
        bazi_b = bazi_from_pillars(req.pillars_b)
        result = await loop.run_in_executor(
            _executor, run_bazi_compat,
            bazi_a, bazi_b, req.gender_a, req.gender_b,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"合盤計算失敗: {e}")
    return result
