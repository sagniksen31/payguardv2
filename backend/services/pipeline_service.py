import logging
import time
import hashlib
from dataclasses import asdict, is_dataclass
from threading import Lock
from typing import Any

import pandas as pd

from backend.core.automation_engine import compute_automation_metrics
from backend.core.automation_engine import automate_dataframe
from backend.core.intelligence_pipeline import (
    PipelineConfig,
    PipelineResult,
    get_fleet_kpis,
    run_intelligence_pipeline,
)


logger = logging.getLogger(__name__)

_pipeline_cache: dict[tuple[Any, ...], dict[str, Any]] = {}
_cache_lock = Lock()


def _jsonify(value: Any) -> Any:
    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")
    if isinstance(value, pd.Series):
        return value.to_dict()
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return {k: _jsonify(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonify(v) for v in value]
    return value


def _cache_key(mode: str, n_days: int, n_per_atm: int, force_retrain: bool) -> tuple[Any, ...]:
    return (mode, n_days, n_per_atm, force_retrain)


def _risk_rank(label: str) -> int:
    mapping = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
    return mapping.get(str(label).upper(), 0)


def _mode(series: pd.Series, default: Any = "") -> Any:
    if series is None or series.empty:
        return default
    vc = series.value_counts(dropna=True)
    if vc.empty:
        return default
    return vc.index[0]


def _prepare_incident_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only meaningful incident rows for UI-facing aggregation/export.
    This mirrors the Streamlit flow where empty issue rows are excluded.
    """
    if df is None or df.empty:
        return df
    out = df.copy()
    if "issue_type" not in out.columns:
        return out
    issue = out["issue_type"].astype(str).str.strip()
    mask = (issue != "") & (issue.str.upper() != "UNKNOWN")
    return out.loc[mask].copy()


def _derive_risk_label_from_score(score: float) -> str:
    if score >= 65:
        return "HIGH"
    if score >= 35:
        return "MEDIUM"
    return "LOW"


def _limit_per_atm(scored_batch: pd.DataFrame, n_per_atm: int) -> pd.DataFrame:
    if scored_batch is None or scored_batch.empty:
        return scored_batch
    if "timestamp" in scored_batch.columns:
        return scored_batch.sort_values("timestamp").groupby("atm_id", as_index=False, group_keys=False).tail(n_per_atm)
    return scored_batch.groupby("atm_id", as_index=False, group_keys=False).tail(n_per_atm)


def _derive_per_atm_summary(scored_batch: pd.DataFrame) -> list[dict[str, Any]]:
    if scored_batch is None or scored_batch.empty:
        return []

    rows: list[dict[str, Any]] = []
    for atm_id, g in scored_batch.groupby("atm_id"):
        risk_score = float(g["pre_failure_risk_score"].fillna(0).max()) if "pre_failure_risk_score" in g.columns else 0.0
        risk_label = _derive_risk_label_from_score(risk_score)
        tx_sum = float(g["transaction_volume"].fillna(0).sum()) if "transaction_volume" in g.columns else 0.0
        avg_amount = float(g["avg_amount"].fillna(0).mean()) if "avg_amount" in g.columns else 0.0
        primary_issue = _mode(g["issue_type"], "UNKNOWN") if "issue_type" in g.columns else "UNKNOWN"
        if primary_issue in ("", None):
            primary_issue = "UNKNOWN"
        rows.append({
            "atm_id": str(atm_id),
            "location": str(g["location"].iloc[0]) if "location" in g.columns and not g.empty else "Unknown",
            "risk": risk_label,
            "risk_score": round(risk_score, 2),
            "issue_type": str(primary_issue),
            "downtime_minutes": round(float(g["downtime_minutes"].fillna(0).mean()), 2) if "downtime_minutes" in g.columns else 0.0,
            "complaint_count": round(float(g["complaint_count"].fillna(0).mean()), 2) if "complaint_count" in g.columns else 0.0,
            "drift_signal": round(float(g["drift_signal"].fillna(0).max()), 2) if "drift_signal" in g.columns else 0.0,
            "in_cluster": int(g["in_cluster"].fillna(0).max()) if "in_cluster" in g.columns else 0,
            "is_cascade": int(g["is_cascade"].fillna(0).max()) if "is_cascade" in g.columns else 0,
            "transaction_volume": round(tx_sum, 2),
            "avg_amount": round(avg_amount, 2),
            "exposure": round(tx_sum * avg_amount, 2),
        })

    rows.sort(key=lambda x: float(x["risk_score"]), reverse=True)
    return rows


def _build_response(result: PipelineResult, n_per_atm: int, seed: int | None) -> dict[str, Any]:
    scored_batch = _limit_per_atm(result.scored_batch, n_per_atm)
    if scored_batch is not None:
        scored_batch = scored_batch.copy()
        if "issue_type" in scored_batch.columns:
            scored_batch["issue_type"] = scored_batch["issue_type"].replace("", pd.NA)
        if "error_code" in scored_batch.columns:
            scored_batch["error_code"] = scored_batch["error_code"].replace("", pd.NA)
        scored_batch.fillna(
            {
                "issue_type": "UNKNOWN",
                "error_code": "UNKNOWN",
            },
            inplace=True,
        )
        if "complaint_count" in scored_batch.columns:
            scored_batch["complaint_count"] = scored_batch["complaint_count"].fillna(0).round().astype(int)
        scored_batch = automate_dataframe(scored_batch)
    automation_metrics: dict[str, Any] = {}
    if "resolution_mode" in scored_batch.columns:
        automation_metrics = compute_automation_metrics(scored_batch)
    else:
        risk_counts = scored_batch["risk_label"].value_counts().to_dict() if "risk_label" in scored_batch.columns else {}
        automation_metrics = {
            "total_incidents": int(len(scored_batch)),
            "risk_distribution": risk_counts,
            "note": "Automation metrics unavailable in this pipeline output.",
        }
    per_atm_summary: list[dict[str, Any]] = []
    scored_batch_sample_json: list[dict[str, Any]] = []
    if scored_batch is not None:
        incident_rows = _prepare_incident_rows(scored_batch)
        per_atm_summary = _derive_per_atm_summary(incident_rows if incident_rows is not None else scored_batch)
        source_for_sample = incident_rows if incident_rows is not None and not incident_rows.empty else scored_batch
        scored_batch_sample_json = source_for_sample.sample(
            n=min(len(source_for_sample), 500),
            random_state=seed,
        ).to_dict(orient="records")

    return {
        "meta": _jsonify(result.pipeline_meta),
        "kpis": _jsonify(get_fleet_kpis(result)),
        "availability": _jsonify(result.availability_summary),
        "root_cause": _jsonify(result.root_cause_summary),
        "automation_metrics": _jsonify(automation_metrics),
        "per_atm_summary": per_atm_summary,
        "scored_batch_sample": scored_batch_sample_json,
    }


def run_pipeline_analysis(
    mode: str,
    n_days: int,
    n_per_atm: int,
    force_retrain: bool,
) -> dict[str, Any]:
    key = _cache_key(mode, n_days, n_per_atm, force_retrain)
    should_use_cache = mode == "stable" and not force_retrain
    with _cache_lock:
        if should_use_cache and key in _pipeline_cache:
            logger.info("Returning cached pipeline result for key=%s", key)
            return _pipeline_cache[key]

    if mode == "stable":
        seed_src = f"{mode}:{n_days}:{n_per_atm}:{int(force_retrain)}"
        seed = int(hashlib.sha256(seed_src.encode("utf-8")).hexdigest()[:8], 16) % 100000
    elif mode == "live":
        seed = None
    else:
        seed = None

    logger.info("Analyze request resolved mode=%s seed=%s n_days=%s n_per_atm=%s", mode, seed, n_days, n_per_atm)
    config = PipelineConfig(
        n_days=n_days,
        seed=seed,
        force_retrain=force_retrain,
        score_n_recent=None,
        reload_history=False,
        availability_seed=seed,
    )
    logger.info("Running intelligence pipeline with mode=%s, n_days=%s", mode, n_days)
    result = run_intelligence_pipeline(config)
    payload = _build_response(result, n_per_atm=n_per_atm, seed=seed)

    with _cache_lock:
        if should_use_cache:
            _pipeline_cache[key] = payload
    return payload
