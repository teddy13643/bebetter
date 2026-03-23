import os
import json

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("bebetter")

try:
    from core import (
        run_qimen, run_liuren, run_taiyi, run_meihua,
        run_bazi, run_western_astro, run_vedic_astro,
        interpret as core_interpret,
    )
    from core.bazi import run_bazi_compat, bazi_from_pillars
    MODE = "direct"
except ImportError:
    MODE = "http"

API_BASE = os.getenv("BEBETTER_API_BASE", "https://bebetter.localtest.me/api")


async def _geocode(address: str) -> tuple[float, float]:
    """用 Nominatim 把地址轉經緯度，失敗時拋出 ValueError"""
    import httpx
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": address, "format": "json", "limit": 1},
            headers={"User-Agent": "bebetter-mcp/1.0"},
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


@mcp.tool()
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

    payload = {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute, "skip_interpret": True,
    }
    if lat is not None and lng is not None:
        payload["lat"] = lat
        payload["lng"] = lng
    return await _post("/natal", payload)


@mcp.tool()
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

    payload = {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute, "skip_interpret": True,
    }
    if question:
        payload["question"] = question
    if lat is not None and lng is not None:
        payload["lat"] = lat
        payload["lng"] = lng
    return await _post("/horary", payload)


@mcp.tool()
async def bazi_compat(
    pillars_a: str, pillars_b: str,
    gender_a: str = "男", gender_b: str = "男",
) -> str:
    """八字合盤計算:輸入兩人四柱(如'庚午己丑癸未癸丑'),回傳個盤擴充(空亡/納音/胎元/命宮/神煞/大運)+跨盤關係(天干合/六合/六沖/六害/破/三合/三會/三刑/暗合/神煞交叉)。
gender_a/gender_b='男'或'女',影響大運順逆。"""

    if MODE == "direct":
        bazi_a = bazi_from_pillars(pillars_a)
        bazi_b = bazi_from_pillars(pillars_b)

        result = run_bazi_compat(bazi_a, bazi_b, gender_a, gender_b)
        return json.dumps(result, ensure_ascii=False, indent=2)

    payload = {
        "pillars_a": pillars_a, "pillars_b": pillars_b,
        "gender_a": gender_a, "gender_b": gender_b,
    }
    return await _post("/bazi-compat", payload)


if __name__ == "__main__":
    mcp.run()
