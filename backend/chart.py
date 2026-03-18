import os
import sys

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# kinqimen 有相對 import 問題，需要把它的目錄加到 sys.path
import sxtwl  # noqa: F401 - kinqimen 依賴，確保先載入

import site
kinqimen_dir = os.path.join(site.getsitepackages()[0], "kinqimen")
if kinqimen_dir not in sys.path:
    sys.path.insert(0, kinqimen_dir)

from kinqimen import kinqimen  # noqa: E402

router = APIRouter()


class ChartRequest(BaseModel):
    year: int
    month: int
    day: int
    hour: int
    minute: int


class ChartResponse(BaseModel):
    chart: dict
    interpretation: str | None = None


@router.post("/chart")
def create_chart(req: ChartRequest) -> ChartResponse:
    """排盤：輸入出生時間，回傳奇門遁甲盤"""
    try:
        result = kinqimen.Qimen(
            req.year, req.month, req.day, req.hour, req.minute
        ).pan(1)  # 拆補法
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"排盤失敗: {e}")

    return ChartResponse(chart=result)


@router.post("/chart/interpret")
def interpret_chart(req: ChartRequest) -> ChartResponse:
    """排盤 + AI 解讀"""
    try:
        result = kinqimen.Qimen(
            req.year, req.month, req.day, req.hour, req.minute
        ).pan(1)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"排盤失敗: {e}")

    interpretation = _interpret(result)
    return ChartResponse(chart=result, interpretation=interpretation)


def _interpret(chart: dict) -> str:
    """用 LLM 解讀奇門遁甲盤"""
    from openai import OpenAI
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        return "未設定 LLM_API_KEY，無法產生 AI 解讀"

    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
    )

    prompt = f"""你是一位精通奇門遁甲的命理師，擅長用白話文解讀命盤，幫助人成為更好的自己。

以下是一張奇門遁甲本命盤（JSON 格式）：

{chart}

請根據這張盤，分析此人的：
1. 核心天賦與性格特質
2. 最適合的發展方向（事業、學習）
3. 需要注意的盲點或陷阱
4. 具體的「如何 be better」建議

要求：
- 用繁體中文
- 白話文，不用術語堆砌
- 每個建議要具體可行，不要空泛
- 語氣溫暖但直接，像一個有智慧的朋友在跟你聊天"""

    model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=2000,
    )

    return response.choices[0].message.content
