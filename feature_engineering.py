"""
feature_engineering.py
=======================
Layer 2 - Feature Engineering Engine  (v2.3 - Ensemble upgrade)
PayGuard Predictive Intelligence Backend

Changes from v2.2
=================
NEW FEATURES (all computed post-concat, all registered in get_ml_feature_columns):

  escalation_momentum  = escalation_freq_3h - escalation_freq_6h
      Positive  -> escalation rate is accelerating into the recent 3h window;
                   a developing failure cluster is in progress right now.
      Negative  -> pressure is easing; 6h window carries older events not
                   being repeated recently.
      Near-zero -> uniform escalation rate across the 6h horizon.

  failure_pressure     = 0.4 * total_downtime_6h
                       + 0.4 * mean_complaints_6h
                       + 0.2 * drift_signal
      Composite multi-dimensional stress scalar named per the v2.3 spec.
      Identical formula to pressure_index (v2.2); the v2.2 name is retained
      in the DataFrame and feature manifest for backward compat with any
      pickled model artifacts that reference it.

CARRIED FORWARD UNCHANGED FROM v2.2
  drift_velocity, drift_acceleration  (groupby+shift per ATM)
  pressure_index                      (kept for artifact backward compat)
  All rolling (3h/6h/12h), lag, interaction, cyclical, encoding features
  engineer_features() public interface and execution order
  _add_escalation_target (O(n log n) reverse-roll, no per-row loop)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WINDOWS        = [3, 6, 12]   # rolling window sizes in hours
TARGET_HORIZON = 3            # predict escalation in next N hours


# ---------------------------------------------------------------------------
# Per-ATM rolling feature builder
# ---------------------------------------------------------------------------
def _rolling_features_for_atm(df_atm: pd.DataFrame) -> pd.DataFrame:
    """
    All time-series rolling features for a single ATM.

    Uses a timestamp index so window widths are wall-clock hours, not row
    counts.  Critical for the dense hourly grid (1,440 rows/ATM/60 days).
    """
    df = df_atm.copy().sort_values("timestamp").reset_index(drop=True)

    # Per-row delta signals
    df["complaint_delta"] = df["complaint_count"].diff().fillna(0)
    df["downtime_growth_pct"] = (
        df["downtime_minutes"]
        .pct_change()
        .replace([np.inf, -np.inf], 0)
        .fillna(0) * 100
    )
    df["txn_drop_pct"] = (
        (-df["transaction_volume"].pct_change())
        .replace([np.inf, -np.inf], 0)
        .fillna(0) * 100
    ).clip(lower=0)

    # Switch to timestamp index for time-based rolling
    df = df.set_index("timestamp")

    for w in WINDOWS:
        win = f"{w}h"
        df[f"failure_freq_{w}h"]            = df["downtime_minutes"].rolling(win, min_periods=1).count()
        df[f"escalation_freq_{w}h"]         = df["escalated"].rolling(win, min_periods=1).sum()
        df[f"rolling_complaint_delta_{w}h"] = df["complaint_delta"].rolling(win, min_periods=1).mean()
        df[f"rolling_downtime_growth_{w}h"] = df["downtime_growth_pct"].rolling(win, min_periods=1).mean()
        df[f"rolling_txn_drop_{w}h"]        = df["txn_drop_pct"].rolling(win, min_periods=1).mean()
        df[f"total_downtime_{w}h"]          = df["downtime_minutes"].rolling(win, min_periods=1).sum()
        df[f"mean_complaints_{w}h"]         = df["complaint_count"].rolling(win, min_periods=1).mean()
        df[f"cascade_density_{w}h"]         = df["is_cascade"].rolling(win, min_periods=1).mean()

    df = df.reset_index()  # restore timestamp as column

    # Lag features
    for lag in [1, 2]:
        df[f"lag_{lag}_downtime"]   = df["downtime_minutes"].shift(lag).fillna(0)
        df[f"lag_{lag}_complaints"] = df["complaint_count"].shift(lag).fillna(0)
        df[f"lag_{lag}_escalated"]  = df["escalated"].shift(lag).fillna(0)
        df[f"lag_{lag}_txn_volume"] = df["transaction_volume"].shift(lag).fillna(0)

    # Interaction features
    df["drift_x_age"]          = df["drift_signal"] * df["atm_age_years"]
    df["drift_x_downtime"]     = df["drift_signal"] * df["downtime_minutes"]
    df["complaint_x_downtime"] = df["complaint_count"] * np.log1p(df["downtime_minutes"])
    df["cluster_pressure"]     = df["in_cluster"].astype(float) * df["escalation_freq_3h"]

    return df


# ---------------------------------------------------------------------------
# Drift dynamics  (v2.2, carried forward unchanged)
# ---------------------------------------------------------------------------
def _add_drift_dynamics(df: pd.DataFrame) -> pd.DataFrame:
    """
    drift_velocity     = drift_signal[t] - drift_signal[t-1]
    drift_acceleration = drift_velocity[t] - drift_velocity[t-1]

    Computed via groupby("atm_id") + shift so no values leak across ATM
    boundaries after the cross-ATM concat.  NaN at first row per ATM -> 0.
    """
    df = df.sort_values(["atm_id", "timestamp"]).reset_index(drop=True)
    grp = df.groupby("atm_id", sort=False)

    df["drift_velocity"] = (
        df["drift_signal"] - grp["drift_signal"].shift(1)
    ).fillna(0.0)

    df["drift_acceleration"] = (
        df["drift_velocity"] - grp["drift_velocity"].shift(1)
    ).fillna(0.0)

    return df


# ---------------------------------------------------------------------------
# Pressure index  (v2.2 name, retained for artifact backward compat)
# ---------------------------------------------------------------------------
def _add_pressure_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    pressure_index = 0.4 * total_downtime_6h
                   + 0.4 * mean_complaints_6h
                   + 0.2 * drift_signal

    Retained verbatim from v2.2.  Models pickled under v2.2 that list
    'pressure_index' in their feature_cols will still score correctly.
    """
    df["pressure_index"] = (
        0.4 * df["total_downtime_6h"].fillna(0)
        + 0.4 * df["mean_complaints_6h"].fillna(0)
        + 0.2 * df["drift_signal"].fillna(0)
    )
    return df


# ---------------------------------------------------------------------------
# NEW v2.3: Failure pressure  (canonical v2.3 name, same formula)
# ---------------------------------------------------------------------------
def _add_failure_pressure(df: pd.DataFrame) -> pd.DataFrame:
    """
    failure_pressure = 0.4 * total_downtime_6h
                     + 0.4 * mean_complaints_6h
                     + 0.2 * drift_signal

    Canonical v2.3 name for the composite stress index.

    Weight rationale:
      downtime and complaints each receive 0.4 -- both are direct observed
      operational-impact signals at different granularities (minutes vs count).
      drift receives 0.2 -- it is a synthetic health-trajectory signal already
      partially captured by drift_velocity and drift_x_downtime; downweighting
      prevents double-counting.

    The 6h window balances sensitivity to sudden spikes (3h too narrow) against
    noise dilution from distant events (12h too wide).

    Even ATMs with zero recent incidents receive a non-zero failure_pressure
    when drift_signal is elevated, improving recall for slow degraders that
    would otherwise be invisible to incident-only feature sets.
    """
    df["failure_pressure"] = (
        0.4 * df["total_downtime_6h"].fillna(0)
        + 0.4 * df["mean_complaints_6h"].fillna(0)
        + 0.2 * df["drift_signal"].fillna(0)
    )
    return df


# ---------------------------------------------------------------------------
# NEW v2.3: Escalation momentum
# ---------------------------------------------------------------------------
def _add_escalation_momentum(df: pd.DataFrame) -> pd.DataFrame:
    """
    escalation_momentum = escalation_freq_3h - escalation_freq_6h

    Captures whether the escalation rate is accelerating or decelerating
    relative to the 6h baseline.

    Positive  -> escalations are concentrating into the most recent 3h window;
                 a worsening condition is developing right now.
    Negative  -> escalation pressure is easing; the 6h window is retaining
                 older events that are not recurring.
    Near-zero -> escalation rate is uniform across the 6h horizon.

    Requires escalation_freq_3h and escalation_freq_6h, both produced
    by the WINDOWS loop in _rolling_features_for_atm.  Called post-concat
    so the full fleet DataFrame is available.
    """
    df["escalation_momentum"] = (
        df["escalation_freq_3h"].fillna(0)
        - df["escalation_freq_6h"].fillna(0)
    )
    return df


# ---------------------------------------------------------------------------
# Target label: vectorised forward-looking escalation  (unchanged)
# ---------------------------------------------------------------------------
def _add_escalation_target(
    df_atm: pd.DataFrame,
    horizon_hours: int = TARGET_HORIZON,
) -> pd.DataFrame:
    """
    Binary label: will_escalate_next_{horizon}h.

    O(n log n) vectorised -- no per-row Python loop.
    Reverse-roll trick: reverse time axis, roll horizon_hours-wide window,
    reverse back.  Result at t = count of escalated=1 rows strictly in
    (t, t + horizon_hours].  Subtracts own flag so only future rows count.
    """
    df         = df_atm.copy().sort_values("timestamp").reset_index(drop=True)
    target_col = f"will_escalate_next_{horizon_hours}h"
    ts_series  = df.set_index("timestamp")["escalated"].astype(float)
    win        = f"{horizon_hours}h"

    forward_sum = (
        ts_series.iloc[::-1]
        .rolling(win, min_periods=1)
        .sum()
        .iloc[::-1]
        - ts_series
    ).clip(lower=0)

    df[target_col] = (forward_sum.values > 0).astype(int)
    return df


# ---------------------------------------------------------------------------
# Encoding helpers  (unchanged)
# ---------------------------------------------------------------------------
ISSUE_TYPES_ORDERED = [
    "network_failure", "card_declined", "hardware_fault",
    "cash_out", "auth_timeout", "software_crash",
]


def _encode_issue_type(df: pd.DataFrame) -> pd.DataFrame:
    for issue in ISSUE_TYPES_ORDERED:
        df[f"issue_{issue}"] = (df["issue_type"] == issue).astype(int)
    return df


def _encode_resolution_mode(df: pd.DataFrame) -> pd.DataFrame:
    mode_map = {"AUTO_RESOLVED": 0, "AUTO_ATTEMPTED": 1, "MANUAL_REQUIRED": 2, "NONE": 0}
    df["resolution_mode_enc"] = df["resolution_mode"].map(mode_map).fillna(1).astype(int)
    return df


def _add_cyclical_time(df: pd.DataFrame) -> pd.DataFrame:
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["dow_sin"]  = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"]  = np.cos(2 * np.pi * df["day_of_week"] / 7)
    return df


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------
def engineer_features(
    df_raw: pd.DataFrame,
    add_target: bool = True,
    target_horizon_hours: int = TARGET_HORIZON,
) -> pd.DataFrame:
    """
    Full feature engineering pipeline.

    Execution order (dependency-driven):
      1. Static encodings   -- issue one-hot, resolution ordinal, cyclical time
      2. Per-ATM loop       -- rolling + lag features (uses timestamp index)
      3. Per-ATM loop       -- escalation target label  [if add_target=True]
      4. Concat all ATMs
      5. Drift dynamics     -- groupby("atm_id") + shift, post-concat    [v2.2]
      6. Pressure index     -- vectorised, requires total_downtime_6h     [v2.2 compat]
      7. Failure pressure   -- same formula, canonical v2.3 name          [NEW v2.3]
      8. Escalation momentum-- requires escalation_freq_3h/6h (step 2)   [NEW v2.3]
      9. Fill NaN -> 0, sort by (atm_id, timestamp)

    Args:
        df_raw               : Raw log DataFrame from historical_log_generator.
        add_target           : Compute will_escalate_next_Nh label.
        target_horizon_hours : Prediction horizon in hours (default 3).

    Returns:
        Feature-enriched DataFrame.  All ML columns are numeric.
        Use get_ml_feature_columns() to select the model input slice.
    """
    df = df_raw.copy()

    # Step 1
    df = _encode_issue_type(df)
    df = _encode_resolution_mode(df)
    df = _add_cyclical_time(df)

    # Steps 2 + 3
    atm_groups = []
    for _atm_id, group in df.groupby("atm_id", sort=False):
        enriched = _rolling_features_for_atm(group)
        if add_target:
            enriched = _add_escalation_target(enriched, horizon_hours=target_horizon_hours)
        atm_groups.append(enriched)

    # Step 4
    df_feat = pd.concat(atm_groups, ignore_index=True)

    # Steps 5-8: all require the full fleet DataFrame (post-concat)
    df_feat = _add_drift_dynamics(df_feat)      # step 5  [v2.2]
    df_feat = _add_pressure_index(df_feat)      # step 6  [v2.2 compat]
    df_feat = _add_failure_pressure(df_feat)    # step 7  [v2.3 new]
    df_feat = _add_escalation_momentum(df_feat) # step 8  [v2.3 new]

    # Step 9
    numeric_cols = df_feat.select_dtypes(include=[np.number]).columns
    df_feat[numeric_cols] = df_feat[numeric_cols].fillna(0)
    df_feat = df_feat.sort_values(["atm_id", "timestamp"]).reset_index(drop=True)

    print(
        f"[FeatureEngineering] Engineered {len(df_feat):,} rows "
        f"x {len(df_feat.columns)} columns."
    )
    if add_target:
        target_col = f"will_escalate_next_{target_horizon_hours}h"
        print(
            f"[FeatureEngineering] Target '{target_col}' "
            f"positive rate: {df_feat[target_col].mean():.2%}"
        )

    return df_feat


# ---------------------------------------------------------------------------
# Feature column manifest
# ---------------------------------------------------------------------------
def get_ml_feature_columns(target_horizon_hours: int = TARGET_HORIZON) -> list[str]:
    """
    Ordered list of all ML feature columns for train_model() and score_batch().

    Excludes: atm_id, timestamp, date, location, region, atm_type,
              operational_status, issue_type (raw string), error_code,
              resolution_mode (raw string), cascade_parent, target label.

    v2.2 additions: drift_velocity, drift_acceleration, pressure_index  (+3)
    v2.3 additions: failure_pressure, escalation_momentum               (+2)
    Total: 79 features
    """
    base_features = [
        # ATM identity / static metadata
        "hour", "day_of_week", "atm_age_years",
        # Operational signals
        "transaction_volume", "avg_amount", "downtime_minutes",
        "complaint_count", "drift_signal",
        # Event flags
        "is_cascade", "in_cluster",
        # Per-row derived signals
        "complaint_delta", "downtime_growth_pct", "txn_drop_pct",
        # Cyclical time encoding
        "hour_sin", "hour_cos", "dow_sin", "dow_cos",
        # Resolution mode
        "resolution_mode_enc",
        # Interaction features
        "drift_x_age", "drift_x_downtime", "complaint_x_downtime",
        "cluster_pressure",
        # v2.2 temporal drift dynamics
        "drift_velocity",       # d(drift)/dt per ATM
        "drift_acceleration",   # d2(drift)/dt2 per ATM
        # v2.2 composite stress (retained for artifact backward compat)
        "pressure_index",
        # v2.3 NEW
        "failure_pressure",     # canonical v2.3 name; same formula as pressure_index
        "escalation_momentum",  # escalation_freq_3h - escalation_freq_6h
    ]

    rolling_features = []
    for w in WINDOWS:
        rolling_features += [
            f"failure_freq_{w}h",
            f"escalation_freq_{w}h",
            f"rolling_complaint_delta_{w}h",
            f"rolling_downtime_growth_{w}h",
            f"rolling_txn_drop_{w}h",
            f"total_downtime_{w}h",
            f"mean_complaints_{w}h",
            f"cascade_density_{w}h",
        ]

    lag_features = [
        f"lag_{lag}_{field}"
        for lag in [1, 2]
        for field in ["downtime", "complaints", "escalated", "txn_volume"]
    ]

    issue_features = [f"issue_{i}" for i in ISSUE_TYPES_ORDERED]

    return base_features + rolling_features + lag_features + issue_features


if __name__ == "__main__":
    from historical_log_generator import generate_historical_logs

    raw  = generate_historical_logs(n_days=7, n_atms=100, seed=42)
    feat = engineer_features(raw, add_target=True)
    cols = get_ml_feature_columns()

    print(f"\nTotal ML features    : {len(cols)}")
    new_v23 = ["failure_pressure", "escalation_momentum"]
    for c in new_v23:
        present = c in feat.columns
        print(f"  {c}: present={present}  "
              + (f"mean={feat[c].mean():.4f}  std={feat[c].std():.4f}" if present else ""))

    print("\nSample -- ATM-1001 first 8 rows:")
    print(feat[feat["atm_id"] == "ATM-1001"].head(8)[[
        "timestamp", "drift_signal", "drift_velocity", "drift_acceleration",
        "escalation_momentum", "failure_pressure",
    ]].to_string(index=False))