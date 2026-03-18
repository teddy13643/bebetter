from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chart import router as chart_router

app = FastAPI(title="BeBetter API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chart_router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
