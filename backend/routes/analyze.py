import logging

from fastapi import APIRouter, HTTPException

from backend.models.request_models import AnalyzeRequest
from backend.models.response_models import AnalyzeResponse
from backend.services.pipeline_service import run_pipeline_analysis


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    try:
        payload = run_pipeline_analysis(
            mode=request.mode,
            n_days=request.n_days,
            n_per_atm=request.n_per_atm,
            force_retrain=request.force_retrain,
        )
        return AnalyzeResponse(**payload)
    except Exception as exc:
        logger.exception("Analyze endpoint failed")
        raise HTTPException(status_code=500, detail=f"Analyze failed: {exc}") from exc
