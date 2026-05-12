import logging

from fastapi import FastAPI

from backend.routes.analyze import router as analyze_router
from backend.routes.feedback import router as feedback_router
from backend.routes.live_batch import router as live_batch_router
from backend.routes.predict import router as predict_router
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = FastAPI(
    title="PayGuard ATM Intelligence API",
    version="1.0.0",
    description="Production-ready FastAPI backend for ATM predictive intelligence.",
)

app.include_router(analyze_router, tags=["analyze"])
app.include_router(predict_router, tags=["predict"])
app.include_router(feedback_router, tags=["feedback"])
app.include_router(live_batch_router, tags=["live"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
