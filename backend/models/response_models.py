from typing import Any, Literal

from pydantic import BaseModel


class AnalyzeResponse(BaseModel):
    meta: dict[str, Any]
    kpis: dict[str, Any]
    availability: dict[str, Any]
    root_cause: dict[str, Any]
    automation_metrics: dict[str, Any]
    per_atm_summary: list[dict[str, Any]]
    scored_batch_sample: list[dict[str, Any]]


class PredictResponse(BaseModel):
    atm_id: str
    risk_score: float
    risk_label: Literal["LOW", "MEDIUM", "HIGH"]
    issue_type: str
    escalation_probability: float | None = None
    downtime_minutes: float | None = None
    drift_signal: float | None = None
    failure_pressure: float | None = None
    predicted_issue: str


class FeedbackResponse(BaseModel):
    success: bool
    message: str


class FeedbackSummaryResponse(BaseModel):
    total: int
    correct: int
    accuracy: float | None
