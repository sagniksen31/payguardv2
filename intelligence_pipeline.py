"""
intelligence_pipeline.py
════════════════════════
Layer 6 — Unified Orchestration Layer
PayGuard Predictive Intelligence Backend

Responsibilities:
  1. Load or generate historical logs
  2. Run feature engineering
  3. Train or load predictive model
  4. Score current incident batch
  5. Run root cause analysis
  6. Compute availability metrics
  7. Return structured output dict for UI

Contract:
  - No UI logic inside this module.
  - All outputs are plain Python dicts / DataFrames.
  - Caller (app.py / appc.py) is responsible for rendering.
  - Deterministic mode: seed=42.  Live mode: seed=None.
  - Each layer is independently invocable for testing.

Usage:
    from intelligence_pipeline import run_intelligence_pipeline, PipelineConfig

    config = PipelineConfig(n_days=60, seed=42, force_retrain=False)
    result = run_intelligence_pipeline(config)

    # result.keys():
    #   historical_logs       → pd.DataFrame (raw)
    #   engineered_features   → pd.DataFrame (features + labels)
    #   scored_batch          → pd.DataFrame (risk scores added)
    #   root_cause_summary    → dict (JSON-serialisable)
    #   availability_summary  → dict (JSON-serialisable)
    #   model_metrics         → dict
    #   pipeline_meta         → dict (timing, record counts, mode)
"""

from __future__ import annotations

import os
import time
import traceback
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

# ── Layer imports ─────────────────────────────────────────────────────────
from historical_log_generator import generate_historical_logs
from feature_engineering import engineer_features, get_ml_feature_columns
from predictive_engine import (
    train_model, load_model, score_batch, ensure_model_trained,
    MODEL_PATH,
)
from root_cause_engine import run_root_cause_analysis, root_cause_to_dict
from availability_engine import compute_availability_metrics, availability_to_dict

# ── Paths ─────────────────────────────────────────────────────────────────
DATA_DIR    = "data"
HISTORY_CSV = os.path.join(DATA_DIR, "historical_logs.csv")
FEATURES_CSV = os.path.join(DATA_DIR, "engineered_features.csv")


# ── Pipeline configuration ────────────────────────────────────────────────
@dataclass
class PipelineConfig:
    """
    All knobs to control pipeline execution.
    Pass one of these to run_intelligence_pipeline().
    """
    # Historical data
    n_days:          int  = 60
    seed:            Optional[int] = 42
    start_date:      Optional[str] = None
    reload_history:  bool = False   # True → regenerate history even if cached CSV exists

    # Model
    force_retrain:   bool = False   # True → always retrain (live mode)
    model_test_size: float = 0.20

    # Scoring batch
    score_n_recent:  Optional[int] = None  # None → score all; int → score last N rows

    # Root cause
    root_cause_window_days: Optional[int] = None  # None → full history

    # Availability
    availability_seed: Optional[int] = 42

    @property
    def deterministic(self) -> bool:
        return self.seed is not None


# ── Pipeline output type ──────────────────────────────────────────────────
@dataclass
class PipelineResult:
    historical_logs:      pd.DataFrame
    engineered_features:  pd.DataFrame
    scored_batch:         pd.DataFrame
    root_cause_summary:   dict
    availability_summary: dict
    model_metrics:        dict
    pipeline_meta:        dict
    errors:               list[str] = field(default_factory=list)


# ── Layer execution helpers ───────────────────────────────────────────────
def _timed(label: str, fn, *args, **kwargs):
    """Call fn(*args, **kwargs) and return (result, elapsed_seconds)."""
    t0 = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed = round(time.perf_counter() - t0, 3)
    print(f"[Pipeline] ✓ {label} completed in {elapsed}s")
    return result, elapsed


def _load_or_generate_history(config: PipelineConfig) -> pd.DataFrame:
    """Return historical log DataFrame, from cache or freshly generated."""
    if not config.reload_history and os.path.exists(HISTORY_CSV):
        print(f"[Pipeline] Loading cached historical logs from {HISTORY_CSV} \u2026")
        df = pd.read_csv(HISTORY_CSV, parse_dates=["timestamp", "date"])
        print(f"[Pipeline] Loaded {len(df):,} rows from cache.")
        return df

    print(f"[Pipeline] Generating {config.n_days}-day historical logs …")
    df = generate_historical_logs(
        n_days=config.n_days,
        seed=config.seed,
        start_date=config.start_date,
    )
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(HISTORY_CSV, index=False)
    print(f"[Pipeline] Historical logs cached to {HISTORY_CSV}")
    return df


# ── Main pipeline ─────────────────────────────────────────────────────────
def run_intelligence_pipeline(
    config: Optional[PipelineConfig] = None,
) -> PipelineResult:
    """
    Execute the full predictive intelligence pipeline.

    Args:
        config : PipelineConfig instance.  Defaults to PipelineConfig() (deterministic, 60 days).

    Returns:
        PipelineResult with all layer outputs.
    """
    if config is None:
        config = PipelineConfig()

    pipeline_start = time.perf_counter()
    errors: list[str] = []
    timings: dict[str, float] = {}

    print("=" * 65)
    print("  PayGuard Intelligence Pipeline — Starting")
    print(f"  Mode: {'DETERMINISTIC (seed=42)' if config.deterministic else 'LIVE (no seed)'}")
    print(f"  History: {config.n_days} days | Force retrain: {config.force_retrain}")
    print("=" * 65)

    # ── Layer 1: Historical Data ──────────────────────────────────────────
    try:
        df_history, timings["layer1_history"] = _timed(
            "Layer 1 — Historical Log Generation",
            _load_or_generate_history, config
        )
    except Exception as e:
        errors.append(f"Layer1: {e}")
        traceback.print_exc()
        raise RuntimeError(f"Layer 1 failed: {e}") from e

    # ── Layer 2: Feature Engineering ─────────────────────────────────────
    try:
        df_features, timings["layer2_features"] = _timed(
            "Layer 2 — Feature Engineering",
            engineer_features, df_history, True
        )
    except Exception as e:
        errors.append(f"Layer2: {e}")
        traceback.print_exc()
        raise RuntimeError(f"Layer 2 failed: {e}") from e

    # ── Layer 3: Predictive Model ─────────────────────────────────────────
    try:
        if config.force_retrain or not os.path.exists(MODEL_PATH):
            model_artifact, timings["layer3_model"] = _timed(
                "Layer 3 — Model Training",
                train_model, df_features,
                "will_escalate_next_3h",
                config.seed,
                config.model_test_size,
                True,
            )
        else:
            model_artifact = load_model()
            timings["layer3_model"] = 0.0
            print("[Pipeline] ✓ Layer 3 — Model loaded from disk (skipped training).")

        model_metrics = model_artifact["metrics"] if model_artifact else {}
    except Exception as e:
        errors.append(f"Layer3: {e}")
        traceback.print_exc()
        model_artifact = None
        model_metrics  = {}
        print(f"[Pipeline] ⚠ Layer 3 failed ({e}) — scoring will be skipped.")

    # ── Layer 3b: Score current batch ─────────────────────────────────────
    try:
        if model_artifact is not None:
            score_df = (
                df_features.tail(config.score_n_recent)
                if config.score_n_recent
                else df_features
            )
            df_scored, timings["layer3_scoring"] = _timed(
                "Layer 3 — Risk Scoring",
                score_batch, score_df, model_artifact
            )
        else:
            df_scored = df_features.copy()
            df_scored["escalation_probability"] = float("nan")
            df_scored["pre_failure_risk_score"]  = float("nan")
            df_scored["risk_label"]              = "UNKNOWN"
            timings["layer3_scoring"] = 0.0
    except Exception as e:
        errors.append(f"Layer3_scoring: {e}")
        traceback.print_exc()
        df_scored = df_features.copy()
        timings["layer3_scoring"] = 0.0

    # ── Layer 4: Root Cause Analysis ──────────────────────────────────────
    try:
        rc_summary_obj, timings["layer4_rootcause"] = _timed(
            "Layer 4 — Root Cause Analysis",
            run_root_cause_analysis,
            df_history,
            config.root_cause_window_days,
        )
        rc_summary_dict = root_cause_to_dict(rc_summary_obj)
    except Exception as e:
        errors.append(f"Layer4: {e}")
        traceback.print_exc()
        rc_summary_dict = {"error": str(e)}
        timings["layer4_rootcause"] = 0.0

    # ── Layer 5: Availability & Impact ────────────────────────────────────
    try:
        avail_summary_obj, timings["layer5_availability"] = _timed(
            "Layer 5 — Availability & Impact Metrics",
            compute_availability_metrics,
            df_history,
            config.availability_seed,
        )
        avail_summary_dict = availability_to_dict(avail_summary_obj)
    except Exception as e:
        errors.append(f"Layer5: {e}")
        traceback.print_exc()
        avail_summary_dict = {"error": str(e)}
        timings["layer5_availability"] = 0.0

    # ── Pipeline metadata ─────────────────────────────────────────────────
    total_elapsed = round(time.perf_counter() - pipeline_start, 3)

    pipeline_meta = {
        "mode":                "deterministic" if config.deterministic else "live",
        "seed":                config.seed,
        "n_days":              config.n_days,
        "total_records":       len(df_history),
        "engineered_records":  len(df_features),
        "scored_records":      len(df_scored),
        "total_elapsed_sec":   total_elapsed,
        "layer_timings_sec":   timings,
        "errors":              errors,
        "model_path":          MODEL_PATH,
        "feature_count":       len(get_ml_feature_columns()),
    }

    print("=" * 65)
    print(f"  Pipeline COMPLETE in {total_elapsed}s | "
          f"{len(errors)} error(s)")
    if errors:
        print(f"  Errors: {errors}")
    print("=" * 65)

    return PipelineResult(
        historical_logs=df_history,
        engineered_features=df_features,
        scored_batch=df_scored,
        root_cause_summary=rc_summary_dict,
        availability_summary=avail_summary_dict,
        model_metrics=model_metrics,
        pipeline_meta=pipeline_meta,
        errors=errors,
    )


# ── Convenience helpers for app.py ────────────────────────────────────────
def get_high_risk_incidents(result: PipelineResult, top_n: int = 20) -> pd.DataFrame:
    """Return top N HIGH-risk incidents sorted by risk score descending."""
    df = result.scored_batch
    high = df[df["risk_label"] == "HIGH"].copy()
    return high.sort_values("pre_failure_risk_score", ascending=False).head(top_n)


def get_proactive_alert_atms(result: PipelineResult) -> pd.DataFrame:
    """
    Return ATMs that should receive proactive alerts RIGHT NOW:
    HIGH risk in the scored batch.
    Deduplicated to one row per ATM (highest score).
    """
    df = result.scored_batch
    high = df[df["risk_label"] == "HIGH"].copy()
    if high.empty:
        return pd.DataFrame()
    return (
        high.sort_values("pre_failure_risk_score", ascending=False)
        .drop_duplicates(subset=["atm_id"], keep="first")
        .reset_index(drop=True)
    )


def get_availability_comparison_table(result: PipelineResult) -> pd.DataFrame:
    """Return a clean DataFrame comparing availability across all three strategies."""
    avail = result.availability_summary
    per_atm = avail.get("per_atm", [])
    if not per_atm:
        return pd.DataFrame()
    rows = []
    for rec in per_atm:
        rows.append({
            "ATM ID":           rec["atm_id"],
            "Location":         rec["location"],
            "Incidents":        rec["total_incidents"],
            "Avail (Reactive)": f"{rec['availability_reactive']:.4%}",
            "Avail (Automated)":f"{rec['availability_automated']:.4%}",
            "Avail (Proactive)":f"{rec['availability_proactive']:.4%}",
            "Improvement (Pro)":(
                f"+{rec['improvement_proactive_vs_reactive']:.3f}pp"
            ),
            "Downtime Prevented (min)": int(rec["downtime_prevented_proactive"]),
        })
    return pd.DataFrame(rows)


def get_root_cause_repeat_atms(result: PipelineResult) -> pd.DataFrame:
    """Return repeat ATM patterns as a flat DataFrame."""
    patterns = result.root_cause_summary.get("repeat_atm_patterns", [])
    if not patterns:
        return pd.DataFrame()
    return pd.DataFrame(patterns)


def get_fleet_kpis(result: PipelineResult) -> dict:
    """
    Return a concise KPI dict for the top-of-dashboard summary panel.
    Safe to call even if sub-layers partially failed.
    """
    meta  = result.pipeline_meta
    avail = result.availability_summary
    rc    = result.root_cause_summary

    return {
        "total_incidents":             meta.get("total_records", 0),
        "total_escalations":           rc.get("total_escalations", 0),
        "overall_escalation_rate":     rc.get("overall_escalation_rate", 0),
        "fleet_availability_reactive": avail.get("fleet_availability_reactive", 0),
        "fleet_availability_proactive":avail.get("fleet_availability_proactive", 0),
        "fleet_improvement_pct":       avail.get("fleet_improvement_proactive_pct", 0),
        "escalations_avoided_proactive": avail.get("escalations_avoided_proactive", 0),
        "downtime_prevented_min":      avail.get("total_downtime_prevented_proactive_min", 0),
        "top_risk_atms":               rc.get("top_risk_atm_ids", []),
        "n_systemic_clusters":         len([
            c for c in rc.get("issue_clusters", []) if c.get("is_systemic")
        ]),
        "pipeline_elapsed_sec":        meta.get("total_elapsed_sec", 0),
    }


# ── CLI entrypoint ────────────────────────────────────────────────────────
if __name__ == "__main__":
    config = PipelineConfig(
        n_days=60,
        seed=42,
        force_retrain=False,
        reload_history=False,
        score_n_recent=500,
    )
    result = run_intelligence_pipeline(config)

    print("\n── Fleet KPIs ──────────────────────────────────────────────")
    kpis = get_fleet_kpis(result)
    for k, v in kpis.items():
        print(f"  {k:<40} {v}")

    print("\n── Top HIGH Risk Incidents ─────────────────────────────────")
    top_risk = get_high_risk_incidents(result, top_n=5)
    if not top_risk.empty:
        print(top_risk[["atm_id", "location", "issue_type",
                         "pre_failure_risk_score", "risk_label"]].to_string(index=False))

    print("\n── Availability Comparison (first 5 ATMs) ──────────────────")
    avail_table = get_availability_comparison_table(result)
    print(avail_table.head(5).to_string(index=False))
