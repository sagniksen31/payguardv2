from typing import Literal

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    mode: Literal["stable", "live"] = "stable"
    n_days: int = Field(default=60, ge=1, le=3650)
    n_per_atm: int = Field(default=20, ge=1, le=100)
    force_retrain: bool = False


class PredictRequest(BaseModel):
    atm_id: str = Field(min_length=1)
    location: str = Field(min_length=1)
    transaction_volume: int = Field(ge=0)
    avg_amount: float = Field(ge=0)
    downtime_minutes: float = Field(ge=0)
    complaint_count: int = Field(ge=0)
    error_code: str = Field(min_length=1)


class FeedbackRequest(BaseModel):
    atm_id: str
    predicted_issue: str
    actual_issue: str
    action_helpful: Literal["yes", "no", "partial"]
    notes: str = ""
    resolution_time_minutes: int = Field(ge=0)
