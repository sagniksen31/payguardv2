from typing import Any

from backend.core.feedback_store import get_accuracy_summary, save_feedback


def submit_feedback(
    atm_id: str,
    predicted_issue: str,
    actual_issue: str,
    action_helpful: str,
    notes: str,
    resolution_time_minutes: int,
) -> dict[str, Any]:
    save_feedback(
        atm_id=atm_id,
        predicted_issue=predicted_issue,
        technician_actual_issue=actual_issue,
        action_helpful=action_helpful,
        technician_notes=notes,
        resolution_time_minutes=resolution_time_minutes,
    )
    return {"success": True, "message": "Feedback saved successfully."}


def feedback_summary() -> dict[str, Any]:
    return get_accuracy_summary()
