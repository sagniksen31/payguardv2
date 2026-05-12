"""
feedback_store.py
Layer 5: Technician feedback loop.

Stores corrections / ratings to a local CSV.
Can be used later to audit predictions or retrain the model.
"""

import os
import csv
import datetime
import pandas as pd

FEEDBACK_PATH = "data/feedback.csv"

COLUMNS = [
    "timestamp",
    "atm_id",
    "predicted_issue",
    "technician_actual_issue",
    "prediction_correct",
    "action_helpful",        # yes / no / partial
    "technician_notes",
    "resolution_time_minutes",
]


def _ensure_file():
    """Create feedback CSV with headers if it doesn't exist."""
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(FEEDBACK_PATH):
        with open(FEEDBACK_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            writer.writeheader()


def save_feedback(
    atm_id: str,
    predicted_issue: str,
    technician_actual_issue: str,
    action_helpful: str = "yes",
    technician_notes: str = "",
    resolution_time_minutes: int = 0,
) -> None:
    """Append a technician feedback record."""
    _ensure_file()
    prediction_correct = "yes" if predicted_issue == technician_actual_issue else "no"
    record = {
        "timestamp":                 datetime.datetime.now().isoformat(),
        "atm_id":                    atm_id,
        "predicted_issue":           predicted_issue,
        "technician_actual_issue":   technician_actual_issue,
        "prediction_correct":        prediction_correct,
        "action_helpful":            action_helpful,
        "technician_notes":          technician_notes,
        "resolution_time_minutes":   resolution_time_minutes,
    }
    with open(FEEDBACK_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writerow(record)
    print(f"Feedback saved for {atm_id}")


def load_feedback() -> pd.DataFrame:
    """Load all feedback records as a DataFrame."""
    _ensure_file()
    df = pd.read_csv(FEEDBACK_PATH)
    if df.empty:
        return pd.DataFrame(columns=COLUMNS)
    return df


def get_accuracy_summary() -> dict:
    """Compute simple accuracy stats from feedback."""
    df = load_feedback()
    if df.empty:
        return {"total": 0, "correct": 0, "accuracy": None}
    total   = len(df)
    correct = (df["prediction_correct"] == "yes").sum()
    return {
        "total":    total,
        "correct":  int(correct),
        "accuracy": round(correct / total * 100, 1),
    }
