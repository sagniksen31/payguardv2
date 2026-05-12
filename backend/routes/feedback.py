import logging

from fastapi import APIRouter, HTTPException

from backend.models.request_models import FeedbackRequest
from backend.models.response_models import FeedbackResponse, FeedbackSummaryResponse
from backend.services.feedback_service import feedback_summary, submit_feedback


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
def feedback(request: FeedbackRequest) -> FeedbackResponse:
    try:
        payload = submit_feedback(
            atm_id=request.atm_id,
            predicted_issue=request.predicted_issue,
            actual_issue=request.actual_issue,
            action_helpful=request.action_helpful,
            notes=request.notes,
            resolution_time_minutes=request.resolution_time_minutes,
        )
        return FeedbackResponse(**payload)
    except Exception as exc:
        logger.exception("Feedback endpoint failed")
        raise HTTPException(status_code=500, detail=f"Feedback failed: {exc}") from exc


@router.get("/feedback/summary", response_model=FeedbackSummaryResponse)
def feedback_stats() -> FeedbackSummaryResponse:
    try:
        payload = feedback_summary()
        return FeedbackSummaryResponse(**payload)
    except Exception as exc:
        logger.exception("Feedback summary endpoint failed")
        raise HTTPException(status_code=500, detail=f"Feedback summary failed: {exc}") from exc
