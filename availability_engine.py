"""
availability_engine.py
══════════════════════
Layer 5 — Availability & Impact Engine
PayGuard Predictive Intelligence Backend

Responsibilities:
  - Compute per-ATM availability: 1 − (downtime / total_operational_minutes)
  - Compare three resolution strategies:
      A. Reactive    — incident detected AFTER failure (current baseline)
      B. Automated   — auto-resolution for eligible incidents
      C. Proactive   — predicted and pre-empted before escalation
  - Compute:
      downtime_prevented_minutes   (per strategy vs reactive baseline)
      escalation_avoided_count     (per strategy)
      availability_improvement_pct (vs reactive baseline)
  - Output structured metrics for dashboard availability and trend panels.

Resolution time assumptions (conservative empirical model):
  Reactive manual:     90–240 minutes mean
  Automated:           5–15 minutes mean (eligible issues only)
  Proactive (pre-empt): 20–45 minutes planned intervention

Availability = uptime / total_window_minutes
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass, asdict
from typing import Optional


# ── Resolution time parameters ────────────────────────────────────────────
# Each tuple: (mean_minutes, std_minutes)
RESOLUTION_PARAMS = {
    "reactive_manual":   (150.0, 45.0),
    "reactive_auto":     ( 30.0, 12.0),
    "automated":         ( 10.0,  4.0),
    "proactive":         ( 30.0, 10.0),
}

# Issues eligible for automated resolution
AUTOMATABLE_ISSUES = {"network_failure", "auth_timeout", "card_declined", "software_crash"}

# Issues where proactive intervention is meaningful (drift/escalation risk driven)
PROACTABLE_ISSUES  = {"network_failure", "hardware_fault", "auth_timeout", "software_crash", "cash_out"}

# Proactive intervention pre-emption success rate (given HIGH risk label)
PROACTIVE_SUCCESS_RATE = 0.72


# ── Data structures ───────────────────────────────────────────────────────
@dataclass
class ATMAvailabilityRecord:
    atm_id:                     str
    location:                   str
    total_incidents:            int
    total_downtime_reactive:    float   # minutes
    total_downtime_automated:   float
    total_downtime_proactive:   float
    availability_reactive:      float   # 0–1
    availability_automated:     float
    availability_proactive:     float
    improvement_auto_vs_reactive:   float   # pct points
    improvement_proactive_vs_reactive: float
    escalation_avoided_auto:    int
    escalation_avoided_proactive: int
    downtime_prevented_auto:    float   # minutes
    downtime_prevented_proactive: float


@dataclass
class FleetAvailabilitySummary:
    analysis_window_minutes:    float
    total_incidents:            int
    total_escalations_reactive: int
    total_escalations_automated: int
    total_escalations_proactive: int
    escalations_avoided_automated:  int
    escalations_avoided_proactive:  int

    fleet_availability_reactive:  float
    fleet_availability_automated: float
    fleet_availability_proactive: float

    fleet_improvement_auto_pct:      float
    fleet_improvement_proactive_pct: float

    total_downtime_prevented_auto_min:      float
    total_downtime_prevented_proactive_min: float

    per_atm: list[ATMAvailabilityRecord]

    # Trend: daily availability per strategy
    daily_trends: dict   # { "dates": [...], "reactive": [...], "automated": [...], "proactive": [...] }


# ── Helpers ───────────────────────────────────────────────────────────────
def _clamp_avail(v):
    """Clamp to [0, 1]. Accepts scalar, numpy array, or pandas Series."""
    clipped = np.clip(v, 0.0, 1.0)
    # Return same type as input so callers can use the result in DataFrame columns
    if isinstance(v, pd.Series):
        return pd.Series(clipped, index=v.index)
    return float(clipped)


def _compute_resolution_time(
    issue_type: str, escalated: bool, resolution_mode: str,
    actual_downtime: float, rng: np.random.Generator,
) -> dict[str, float]:
    """
    Return estimated resolution times for all three strategies for a single incident.
    """
    # ── Reactive ──
    if escalated:
        mu, sigma = RESOLUTION_PARAMS["reactive_manual"]
    else:
        mu, sigma = RESOLUTION_PARAMS["reactive_auto"]
    reactive_time = float(max(actual_downtime, abs(rng.normal(mu, sigma))))

    # ── Automated ──
    if issue_type in AUTOMATABLE_ISSUES and not escalated:
        mu_a, sigma_a = RESOLUTION_PARAMS["automated"]
        automated_time = float(max(1.0, abs(rng.normal(mu_a, sigma_a))))
    else:
        # Not automatable → same as reactive
        automated_time = reactive_time

    # ── Proactive ──
    if issue_type in PROACTABLE_ISSUES:
        # Proactive intervention succeeds with PROACTIVE_SUCCESS_RATE
        if rng.random() < PROACTIVE_SUCCESS_RATE:
            mu_p, sigma_p = RESOLUTION_PARAMS["proactive"]
            proactive_time = float(max(5.0, abs(rng.normal(mu_p, sigma_p))))
            # If proactive succeeds, escalation is avoided
            proactive_escalated = False
        else:
            proactive_time = reactive_time
            proactive_escalated = escalated
    else:
        proactive_time = reactive_time
        proactive_escalated = escalated

    return {
        "reactive_min":          reactive_time,
        "automated_min":         automated_time,
        "proactive_min":         proactive_time,
        "proactive_escalated":   proactive_escalated,
        "auto_avoided_escalation": (escalated and automated_time < reactive_time * 0.5),
    }


# ── Per-ATM availability computation ─────────────────────────────────────
def _compute_atm_availability(
    df_atm: pd.DataFrame,
    window_minutes: float,
    rng: np.random.Generator,
) -> ATMAvailabilityRecord:
    atm_id   = str(df_atm["atm_id"].iloc[0])
    location = str(df_atm["location"].iloc[0])
    n        = len(df_atm)

    r_times = []
    a_times = []
    p_times = []
    esc_avoided_auto     = 0
    esc_avoided_proactive = 0

    for _, row in df_atm.iterrows():
        result = _compute_resolution_time(
            issue_type=str(row["issue_type"]),
            escalated=bool(row["escalated"]),
            resolution_mode=str(row.get("resolution_mode", "MANUAL_REQUIRED")),
            actual_downtime=float(row["downtime_minutes"]),
            rng=rng,
        )
        r_times.append(result["reactive_min"])
        a_times.append(result["automated_min"])
        p_times.append(result["proactive_min"])

        if result["auto_avoided_escalation"]:
            esc_avoided_auto += 1
        if not result["proactive_escalated"] and bool(row["escalated"]):
            esc_avoided_proactive += 1

    total_reactive   = sum(r_times)
    total_automated  = sum(a_times)
    total_proactive  = sum(p_times)

    avail_r = _clamp_avail(1.0 - total_reactive  / window_minutes)
    avail_a = _clamp_avail(1.0 - total_automated / window_minutes)
    avail_p = _clamp_avail(1.0 - total_proactive / window_minutes)

    return ATMAvailabilityRecord(
        atm_id=atm_id,
        location=location,
        total_incidents=n,
        total_downtime_reactive=round(total_reactive,  2),
        total_downtime_automated=round(total_automated,2),
        total_downtime_proactive=round(total_proactive,2),
        availability_reactive=round(avail_r, 6),
        availability_automated=round(avail_a, 6),
        availability_proactive=round(avail_p, 6),
        improvement_auto_vs_reactive=round((avail_a - avail_r) * 100, 4),
        improvement_proactive_vs_reactive=round((avail_p - avail_r) * 100, 4),
        escalation_avoided_auto=esc_avoided_auto,
        escalation_avoided_proactive=esc_avoided_proactive,
        downtime_prevented_auto=round(total_reactive - total_automated, 2),
        downtime_prevented_proactive=round(total_reactive - total_proactive, 2),
    )


# ── Daily trend computation ───────────────────────────────────────────────
def _compute_daily_trends(
    df: pd.DataFrame, per_atm: list[ATMAvailabilityRecord]
) -> dict:
    """
    Build daily availability trend data across all strategies.
    Uses per-incident downtime approximations.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["timestamp"]).dt.date

    # Minutes in a day for the entire fleet
    n_atms     = df["atm_id"].nunique()
    day_minutes = 1440.0 * n_atms

    daily = df.groupby("date")["downtime_minutes"].agg(
        reactive="sum",
    ).reset_index()

    # Automated: automatable issues get 80% reduction
    auto_factor = df.copy()
    auto_factor["adj_downtime"] = np.where(
        auto_factor["issue_type"].isin(AUTOMATABLE_ISSUES),
        auto_factor["downtime_minutes"] * 0.20,
        auto_factor["downtime_minutes"],
    )
    daily_auto = auto_factor.groupby("date")["adj_downtime"].sum().reset_index()
    daily_auto.columns = ["date", "automated"]

    # Proactive: proactable issues get PROACTIVE_SUCCESS_RATE * 70% reduction
    pro_factor = df.copy()
    pro_factor["adj_downtime"] = np.where(
        pro_factor["issue_type"].isin(PROACTABLE_ISSUES),
        pro_factor["downtime_minutes"] * (1.0 - PROACTIVE_SUCCESS_RATE * 0.70),
        pro_factor["downtime_minutes"],
    )
    daily_pro = pro_factor.groupby("date")["adj_downtime"].sum().reset_index()
    daily_pro.columns = ["date", "proactive"]

    merged = daily.merge(daily_auto, on="date").merge(daily_pro, on="date")
    merged["avail_reactive"]  = _clamp_avail(1.0 - merged["reactive"]  / day_minutes)
    merged["avail_automated"] = _clamp_avail(1.0 - merged["automated"] / day_minutes)
    merged["avail_proactive"] = _clamp_avail(1.0 - merged["proactive"] / day_minutes)

    return {
        "dates":      merged["date"].astype(str).tolist(),
        "reactive":   merged["avail_reactive"].round(6).tolist(),
        "automated":  merged["avail_automated"].round(6).tolist(),
        "proactive":  merged["avail_proactive"].round(6).tolist(),
    }


# ── Public interface ──────────────────────────────────────────────────────
def compute_availability_metrics(
    df: pd.DataFrame,
    seed: Optional[int] = 42,
) -> FleetAvailabilitySummary:
    """
    Compute full fleet availability and impact metrics.

    Args:
        df   : Historical logs DataFrame (from historical_log_generator or pipeline).
        seed : RNG seed for resolution time sampling (42 = deterministic).

    Returns:
        FleetAvailabilitySummary with per-ATM and fleet-level metrics.
    """
    rng = np.random.default_rng(seed)

    # Total analysis window in minutes
    if len(df) == 0:
        raise ValueError("[AvailabilityEngine] Empty DataFrame provided.")

    t_min = pd.to_datetime(df["timestamp"]).min()
    t_max = pd.to_datetime(df["timestamp"]).max()
    n_atms = df["atm_id"].nunique()
    window_minutes = ((t_max - t_min).total_seconds() / 60.0) * n_atms
    window_minutes = max(window_minutes, 1.0)

    print(f"[AvailabilityEngine] Window: {(t_max - t_min).days + 1} days | "
          f"{n_atms} ATMs | {len(df):,} incidents")

    per_atm_records: list[ATMAvailabilityRecord] = []

    for atm_id, group in df.groupby("atm_id"):
        # Per-ATM window
        atm_window = max(
            ((group["timestamp"].max() - group["timestamp"].min()).total_seconds() / 60.0),
            1440.0,   # minimum 1 day
        )
        rec = _compute_atm_availability(group, atm_window, rng)
        per_atm_records.append(rec)

    # ── Fleet aggregation ─────────────────────────────────────────────────
    total_incidents    = len(df)
    total_esc_reactive = int(df["escalated"].sum())

    esc_auto_avoided = sum(r.escalation_avoided_auto     for r in per_atm_records)
    esc_pro_avoided  = sum(r.escalation_avoided_proactive for r in per_atm_records)

    total_dt_reactive  = sum(r.total_downtime_reactive  for r in per_atm_records)
    total_dt_automated = sum(r.total_downtime_automated for r in per_atm_records)
    total_dt_proactive = sum(r.total_downtime_proactive for r in per_atm_records)

    fleet_r = _clamp_avail(1.0 - total_dt_reactive  / window_minutes)
    fleet_a = _clamp_avail(1.0 - total_dt_automated / window_minutes)
    fleet_p = _clamp_avail(1.0 - total_dt_proactive / window_minutes)

    daily_trends = _compute_daily_trends(df, per_atm_records)

    summary = FleetAvailabilitySummary(
        analysis_window_minutes=round(window_minutes, 2),
        total_incidents=total_incidents,
        total_escalations_reactive=total_esc_reactive,
        total_escalations_automated=max(0, total_esc_reactive - esc_auto_avoided),
        total_escalations_proactive=max(0, total_esc_reactive - esc_pro_avoided),
        escalations_avoided_automated=esc_auto_avoided,
        escalations_avoided_proactive=esc_pro_avoided,
        fleet_availability_reactive=round(fleet_r, 6),
        fleet_availability_automated=round(fleet_a, 6),
        fleet_availability_proactive=round(fleet_p, 6),
        fleet_improvement_auto_pct=round((fleet_a - fleet_r) * 100, 4),
        fleet_improvement_proactive_pct=round((fleet_p - fleet_r) * 100, 4),
        total_downtime_prevented_auto_min=round(total_dt_reactive - total_dt_automated, 2),
        total_downtime_prevented_proactive_min=round(total_dt_reactive - total_dt_proactive, 2),
        per_atm=per_atm_records,
        daily_trends=daily_trends,
    )

    print(
        f"[AvailabilityEngine] Fleet availability — "
        f"Reactive: {fleet_r:.4%} | "
        f"Automated: {fleet_a:.4%} (+{(fleet_a-fleet_r)*100:.3f}pp) | "
        f"Proactive: {fleet_p:.4%} (+{(fleet_p-fleet_r)*100:.3f}pp)"
    )

    return summary


def availability_to_dict(summary: FleetAvailabilitySummary) -> dict:
    """Convert FleetAvailabilitySummary to JSON-serialisable dict."""
    return asdict(summary)


if __name__ == "__main__":
    from historical_log_generator import generate_historical_logs
    raw = generate_historical_logs(n_days=30, seed=42)
    avail = compute_availability_metrics(raw, seed=42)
    print(f"\nFleet Reactive Availability:  {avail.fleet_availability_reactive:.4%}")
    print(f"Fleet Automated Availability: {avail.fleet_availability_automated:.4%}")
    print(f"Fleet Proactive Availability: {avail.fleet_availability_proactive:.4%}")
    print(f"Escalations Avoided (Proactive): {avail.escalations_avoided_proactive}")
    print(f"Downtime Prevented (Proactive): {avail.total_downtime_prevented_proactive_min:,.0f} min")