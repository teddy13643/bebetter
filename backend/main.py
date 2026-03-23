from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from unified import router as unified_router

app = FastAPI(title="BeBetter API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(unified_router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
