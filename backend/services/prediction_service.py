import logging
from threading import Lock
from typing import Any

from backend.core.predictive_engine import load_model, score_single


logger = logging.getLogger(__name__)

_model_artifact: dict[str, Any] | None = None
_model_lock = Lock()


def _get_model() -> dict[str, Any]:
    global _model_artifact
    with _model_lock:
        if _model_artifact is None:
            logger.info("Loading model artifact into global cache")
            artifact = load_model()
            if artifact is None:
                raise RuntimeError("No trained model found. Run /analyze first to train/load a model.")
            _model_artifact = artifact
        return _model_artifact


def predict_single(
    atm_id: str,
    location: str,
    transaction_volume: int,
    avg_amount: float,
    downtime_minutes: float,
    complaint_count: int,
    error_code: str,
) -> dict[str, Any]:
    artifact = _get_model()
    raw = score_single(
        atm_id=atm_id,
        issue_type=error_code,
        transaction_volume=float(transaction_volume),
        downtime_minutes=float(downtime_minutes),
        complaint_count=float(complaint_count),
        drift_signal=1.0 if complaint_count > 0 else 0.0,
        atm_age_years=5.0,
        artifact=artifact,
    )
    return {
        "atm_id": atm_id,
        "risk_score": float(raw["risk_score"]),
        "risk_label": raw["risk_label"],
        "issue_type": error_code,
        "escalation_probability": float(raw.get("escalation_probability", 0.0)),
        "downtime_minutes": float(downtime_minutes),
        "drift_signal": float(raw.get("drift_signal", 0.0)),
        "failure_pressure": float(raw.get("failure_pressure", 0.0)),
        "predicted_issue": error_code,
    }
