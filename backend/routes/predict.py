import logging

from fastapi import APIRouter, HTTPException

from backend.models.request_models import PredictRequest
from backend.models.response_models import PredictResponse
from backend.services.prediction_service import predict_single


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    try:
        payload = predict_single(
            atm_id=request.atm_id,
            location=request.location,
            transaction_volume=request.transaction_volume,
            avg_amount=request.avg_amount,
            downtime_minutes=request.downtime_minutes,
            complaint_count=request.complaint_count,
            error_code=request.error_code,
        )
        return PredictResponse(**payload)
    except Exception as exc:
        logger.exception("Predict endpoint failed")
        raise HTTPException(status_code=500, detail=f"Predict failed: {exc}") from exc
