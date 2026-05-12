"""
historical_log_generator.py
═══════════════════════════
Layer 1 — Historical Data Engine
PayGuard Predictive Intelligence Backend  v2.1

Architecture change from v2.0:
  v2.0 → sparse: only emitted rows when an incident occurred (~3,355 rows for 12 ATMs)
  v2.1 → dense:  EVERY ATM gets EXACTLY ONE row per hour regardless of incident status.
                 Target: 60 × 24 × 100 = 144,000 base rows (guaranteed).
                 Incident hours get full failure fields populated.
                 Normal/degraded hours get healthy operational baselines.
                 Cascade incidents are appended as EXTRA rows on top of the base grid.

Row schema:
  Identity      : timestamp, date, hour, day_of_week
  ATM metadata  : atm_id, location, region, atm_age_years, atm_type, install_year
  Operational   : operational_status  (NORMAL | DEGRADED | INCIDENT | CASCADE)
                  transaction_volume, avg_amount, drift_signal
  Incident      : issue_type, error_code, downtime_minutes, complaint_count,
                  escalated, resolution_mode, resolution_minutes
  Flags         : is_cascade, cascade_parent, in_cluster

operational_status:
  NORMAL    — ATM healthy, no failure this hour
  DEGRADED  — No failure but drift_signal > 40 (health warning zone)
  INCIDENT  — Primary failure event this hour
  CASCADE   — Secondary failure triggered by a primary in the same ATM-hour

100 ATMs are procedurally generated across 8 regions, 4 ATM types,
and a realistic age distribution (1–12 years).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

# ── Constants ─────────────────────────────────────────────────────────────
N_ATMS = 100
N_DAYS = 60
SEED   = 42

REGIONS = ["North", "South", "East", "West", "Central", "Northeast", "Northwest", "Coastal"]

REGION_LOCATIONS: dict[str, list[str]] = {
    "North":     ["Delhi CP", "Delhi Airport", "Noida Hub", "Gurgaon Mall", "Chandigarh Sq",
                  "Amritsar Gate", "Ludhiana Market", "Agra Fort", "Meerut Bazaar", "Jaipur Pink"],
    "South":     ["Chennai Mall", "Chennai Station", "Bangalore Tech", "Bangalore Station",
                  "Hyderabad Hub", "Kochi Port", "Coimbatore Mill", "Mysore Palace",
                  "Vizag Beach", "Madurai Temple"],
    "East":      ["Kolkata Port", "Kolkata Station", "Bhubaneswar Sq", "Patna Market",
                  "Ranchi Hub", "Guwahati Gate", "Siliguri Mall", "Cuttack Road",
                  "Dhanbad Mine", "Jamshedpur Steel"],
    "West":      ["Mumbai Central", "Mumbai Airport", "Pune Market", "Pune Station",
                  "Ahmedabad Bazaar", "Surat Diamond", "Vadodara Gate", "Nashik Vine",
                  "Aurangabad Fort", "Nagpur Orange"],
    "Central":   ["Bhopal Lake", "Indore Market", "Raipur Steel", "Jabalpur Marble",
                  "Gwalior Fort", "Ujjain Temple", "Satna Hub", "Bilaspur Coal",
                  "Rewa Road", "Korba Plant"],
    "Northeast": ["Guwahati River", "Shillong Hills", "Imphal Valley", "Agartala Gate",
                  "Aizawl Peak", "Kohima Village", "Itanagar Base", "Dibrugarh Tea",
                  "Jorhat Fields", "Silchar Bridge"],
    "Northwest": ["Jaipur City", "Jodhpur Blue", "Udaipur Lake", "Ajmer Dargah",
                  "Kota Student", "Bikaner Fort", "Alwar Tiger", "Bharatpur Bird",
                  "Pali Road", "Sikar Market"],
    "Coastal":   ["Kochi Harbour", "Goa Beach", "Vizag Port", "Mangalore Dock",
                  "Pondicherry Sea", "Calicut Spice", "Trivandrum Capital", "Bhatkal Coast",
                  "Kakinada Oil", "Paradip Ship"],
}

ATM_TYPES = ["Standard", "Premium", "Mini", "Drive-Through"]

ISSUE_TYPES = [
    "network_failure",
    "card_declined",
    "hardware_fault",
    "cash_out",
    "auth_timeout",
    "software_crash",
]

# Skewed base probabilities (sum to 1.0)
BASE_ISSUE_PROBS = {
    "card_declined":   0.30,
    "network_failure": 0.25,
    "auth_timeout":    0.18,
    "cash_out":        0.13,
    "software_crash":  0.09,
    "hardware_fault":  0.05,
}

ERROR_CODE_MAP = {
    "network_failure":  ["E001", "E002", "E003", "E004"],
    "card_declined":    ["E010", "E011", "E012", "E013"],
    "hardware_fault":   ["E020", "E021", "E022", "E023"],
    "cash_out":         ["E030", "E031", "E032"],
    "auth_timeout":     ["E040", "E041", "E042", "E043"],
    "software_crash":   ["E050", "E051", "E052"],
}

# Hourly transaction volume multiplier (index = hour 0-23)
HOUR_VOLUME_PROFILE = np.array([
    0.10, 0.07, 0.05, 0.04, 0.04, 0.06,   # 00-05 night
    0.12, 0.25, 0.40, 0.60, 0.75, 0.80,   # 06-11 morning
    0.85, 0.82, 0.78, 0.80, 0.90, 0.95,   # 12-17 midday
    1.00, 0.95, 0.85, 0.70, 0.50, 0.25,   # 18-23 evening
])

CASCADE_SEEDS: dict[str, list[tuple[str, float]]] = {
    "network_failure": [("auth_timeout", 0.40), ("software_crash", 0.20)],
    "software_crash":  [("auth_timeout", 0.30), ("network_failure", 0.15)],
    "hardware_fault":  [("cash_out", 0.25),     ("software_crash", 0.10)],
    "auth_timeout":    [("card_declined", 0.35)],
}

AUTOMATABLE_ISSUES = {"network_failure", "auth_timeout", "card_declined", "software_crash"}


# ── ATM Fleet generation (100 ATMs) ──────────────────────────────────────
def _build_atm_fleet(n_atms: int, rng: np.random.Generator) -> list[dict]:
    """
    Procedurally generate n_atms ATMs with realistic diversity across
    8 regions, 4 ATM types, and ages 1-12 years (beta-distributed, peak ~4).
    """
    fleet: list[dict] = []
    region_list = list(REGION_LOCATIONS.keys())

    # Region assignment weights (proportional to population density)
    region_weights = np.array([15, 15, 10, 15, 10, 8, 12, 15], dtype=float)
    region_weights /= region_weights.sum()

    # ATM type weights: Standard most common, Drive-Through rare
    atm_type_weights = np.array([0.45, 0.20, 0.25, 0.10], dtype=float)

    # Track per-region usage count to append suffixes for uniqueness
    region_loc_counters: dict[str, int] = {r: 0 for r in region_list}

    for i in range(n_atms):
        region   = str(rng.choice(region_list, p=region_weights))
        loc_pool = REGION_LOCATIONS[region]

        # Cycle through location pool; add numeric suffix on second pass+
        loc_idx  = region_loc_counters[region] % len(loc_pool)
        suffix   = f" {region_loc_counters[region] // len(loc_pool) + 1}" \
                   if region_loc_counters[region] >= len(loc_pool) else ""
        location = loc_pool[loc_idx] + suffix
        region_loc_counters[region] += 1

        # Age: beta(2.5, 4.0) × 12 → peak ~4 years, range 1-12
        age_years = max(1, int(round(float(rng.beta(2.5, 4.0)) * 12)))
        atm_type  = str(rng.choice(ATM_TYPES, p=atm_type_weights))

        fleet.append({
            "atm_id":        f"ATM-{1000 + i + 1:04d}",
            "location":      location,
            "region":        region,
            "atm_age_years": age_years,
            "atm_type":      atm_type,
            "install_year":  datetime.now().year - age_years,
        })

    return fleet


# ── Probability modifiers ─────────────────────────────────────────────────
def _age_multiplier(age: int) -> float:
    """Older ATMs fail more. Quadratic, capped at 3x."""
    return min(1.0 + (age / 10.0) ** 2, 3.0)


def _hour_failure_multiplier(hour: int) -> float:
    """Peak-hour stress raises failure probability."""
    if hour in {9, 10, 11, 17, 18, 19}: return 1.45
    if hour in {0, 1, 2, 3, 4}:         return 0.60
    return 1.0


def _day_of_week_multiplier(dow: int) -> float:
    """Friday/Saturday are higher-traffic, higher-failure days."""
    return [0.90, 0.92, 0.95, 0.98, 1.20, 1.30, 1.10][dow]


def _drift_multiplier(drift: float) -> float:
    """Health degradation exponentially amplifies failure probability."""
    return 1.0 + 3.5 * (drift ** 2)


def _type_failure_multiplier(atm_type: str) -> float:
    """Premium ATMs are more reliable; Mini ATMs fail more."""
    return {"Standard": 1.00, "Premium": 0.75, "Mini": 1.20, "Drive-Through": 1.10}[atm_type]


# ── Drift schedule (per ATM, hourly over full window) ─────────────────────
def _build_drift_schedule(n_days: int, rng: np.random.Generator) -> np.ndarray:
    """
    Hourly health-drift array.  Cycles: healthy → gradual ramp → peak → instant reset.
    Values in [0.0, 1.0] where 1.0 = imminent failure.
    """
    total_hours = n_days * 24
    drift = np.zeros(total_hours)
    h = 0
    while h < total_hours:
        healthy_hours = int(rng.uniform(72, 336))   # 3-14 days healthy
        h += healthy_hours
        if h >= total_hours:
            break
        ramp_hours = int(rng.uniform(12, 96))
        peak_drift = float(rng.uniform(0.45, 1.0))
        for i in range(min(ramp_hours, total_hours - h)):
            drift[h + i] = peak_drift * (i / ramp_hours)
        h += ramp_hours
        plateau_hours = int(rng.uniform(6, 48))
        for i in range(min(plateau_hours, total_hours - h)):
            drift[h + i] = peak_drift
        h += plateau_hours
        # Instant maintenance reset — drift returns to 0
    return np.clip(drift, 0.0, 1.0)


# ── Cluster schedule (systemic events across fleet) ───────────────────────
def _build_cluster_schedule(n_days: int, rng: np.random.Generator) -> set[int]:
    """
    Set of hour-indices where a systemic cluster event is active
    (e.g. ISP outage, power grid issue, data-centre incident).
    8-20 cluster windows for a 100-ATM fleet.
    """
    total_hours = n_days * 24
    cluster_hours: set[int] = set()
    n_clusters = int(rng.integers(8, 20))
    for _ in range(n_clusters):
        start    = int(rng.integers(0, total_hours - 12))
        duration = int(rng.integers(2, 18))
        for h in range(start, min(start + duration, total_hours)):
            cluster_hours.add(h)
    return cluster_hours


# ── Row builders ──────────────────────────────────────────────────────────
def _normal_row(
    atm: dict, ts: datetime, drift_level: float, rng: np.random.Generator
) -> dict:
    """One row for a healthy/degraded ATM-hour (no failure event)."""
    hour        = ts.hour
    age         = atm["atm_age_years"]
    vol_cap     = max(50, 400 - age * 20)
    txn_vol     = max(1, int(
        HOUR_VOLUME_PROFILE[hour] * vol_cap
        * rng.uniform(0.88, 1.12)
        * (1.0 - drift_level * 0.15)
    ))
    avg_amt     = round(float(rng.uniform(400, 7000)) * (1.0 + 0.15 * (hour in {9,10,18,19})), 2)
    status      = "DEGRADED" if drift_level > 0.40 else "NORMAL"

    return {
        "timestamp":          ts.isoformat(),
        "date":               ts.date().isoformat(),
        "hour":               hour,
        "day_of_week":        ts.weekday(),
        "atm_id":             atm["atm_id"],
        "location":           atm["location"],
        "region":             atm["region"],
        "atm_age_years":      age,
        "atm_type":           atm["atm_type"],
        "operational_status": status,
        "transaction_volume": txn_vol,
        "avg_amount":         avg_amt,
        "drift_signal":       round(drift_level * 100, 2),
        "issue_type":         "",
        "error_code":         "",
        "downtime_minutes":   0,
        "complaint_count":    0,
        "escalated":          0,
        "resolution_mode":    "NONE",
        "resolution_minutes": 0,
        "is_cascade":         0,
        "cascade_parent":     "",
        "in_cluster":         0,
    }


def _incident_row(
    atm: dict,
    ts: datetime,
    issue_type: str,
    drift_level: float,
    in_cluster: bool,
    is_cascade: bool,
    cascade_parent: str,
    rng: np.random.Generator,
) -> dict:
    """One row for a failure event (INCIDENT or CASCADE)."""
    hour    = ts.hour
    age     = atm["atm_age_years"]
    vol_cap = max(50, 400 - age * 20)
    txn_vol = max(1, int(
        HOUR_VOLUME_PROFILE[hour] * vol_cap
        * rng.uniform(0.70, 1.05)
        * (1.0 - drift_level * 0.35)
    ))
    avg_amt = round(float(rng.uniform(500, 8000)) * (1.0 + 0.2 * (hour in {9,10,18,19})), 2)

    base_dt = {
        "network_failure": int(rng.integers(10,  90)),
        "card_declined":   int(rng.integers(0,   15)),
        "hardware_fault":  int(rng.integers(60, 480)),
        "cash_out":        int(rng.integers(30, 300)),
        "auth_timeout":    int(rng.integers(5,   60)),
        "software_crash":  int(rng.integers(20, 120)),
    }[issue_type]
    downtime = int(base_dt * (1.0 + drift_level * 1.5))

    base_cc = {
        "network_failure": int(rng.integers(3,  25)),
        "card_declined":   int(rng.integers(5,  35)),
        "hardware_fault":  int(rng.integers(10, 50)),
        "cash_out":        int(rng.integers(15, 70)),
        "auth_timeout":    int(rng.integers(2,  18)),
        "software_crash":  int(rng.integers(4,  30)),
    }[issue_type]
    complaints = int(base_cc * (1.8 if in_cluster else 1.0) * (1.0 + drift_level))

    escalated = (
        downtime > 120
        or complaints > 40
        or (in_cluster and rng.random() < 0.65)
        or drift_level > 0.7
    )

    if issue_type in AUTOMATABLE_ISSUES and not escalated and rng.random() < 0.55:
        res_mode = "AUTO_RESOLVED"
        res_min  = int(rng.uniform(1, 12))
    elif escalated:
        res_mode = "MANUAL_REQUIRED"
        res_min  = int(rng.uniform(60, 240))
    else:
        res_mode = "AUTO_ATTEMPTED"
        res_min  = int(rng.uniform(15, 60))

    return {
        "timestamp":          ts.isoformat(),
        "date":               ts.date().isoformat(),
        "hour":               hour,
        "day_of_week":        ts.weekday(),
        "atm_id":             atm["atm_id"],
        "location":           atm["location"],
        "region":             atm["region"],
        "atm_age_years":      age,
        "atm_type":           atm["atm_type"],
        "operational_status": "CASCADE" if is_cascade else "INCIDENT",
        "transaction_volume": txn_vol,
        "avg_amount":         avg_amt,
        "drift_signal":       round(drift_level * 100, 2),
        "issue_type":         issue_type,
        "error_code":         str(rng.choice(ERROR_CODE_MAP[issue_type])),
        "downtime_minutes":   downtime,
        "complaint_count":    complaints,
        "escalated":          int(escalated),
        "resolution_mode":    res_mode,
        "resolution_minutes": res_min,
        "is_cascade":         int(is_cascade),
        "cascade_parent":     cascade_parent,
        "in_cluster":         int(in_cluster),
    }


# ── Main generator ────────────────────────────────────────────────────────
def generate_historical_logs(
    n_days:     int           = N_DAYS,
    n_atms:     int           = N_ATMS,
    seed:       Optional[int] = SEED,
    start_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    Generate a dense historical log DataFrame.

    Every ATM-hour produces exactly one base row (NORMAL, DEGRADED, or INCIDENT).
    If an incident triggers cascade failures those are appended as extra rows
    with operational_status = CASCADE.

    Expected row counts (default 60d × 100 ATMs):
        base_rows    = 60 × 24 × 100 = 144,000   (guaranteed)
        cascade_rows ≈ 5-15% of INCIDENT rows     (additive)
        total        ≈ 144,000 – 148,000+

    Args:
        n_days     : Days to simulate (default 60).
        n_atms     : Number of ATMs to simulate (default 100).
        seed       : RNG seed. 42 = deterministic, None = live.
        start_date : ISO date string, e.g. "2024-01-01".
                     Defaults to (today - n_days).

    Returns:
        pd.DataFrame sorted by (atm_id, timestamp).
    """
    rng = np.random.default_rng(seed)

    # ── Date range ─────────────────────────────────────────────────────────
    if start_date is None:
        start_dt = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        start_dt = start_dt - timedelta(days=n_days)
    else:
        start_dt = datetime.fromisoformat(start_date)

    total_hours = n_days * 24

    # ── Fleet ──────────────────────────────────────────────────────────────
    fleet = _build_atm_fleet(n_atms, rng)
    print(
        f"[HistoricalLogGenerator] Fleet    : {len(fleet)} ATMs | "
        f"{n_days} days | "
        f"target base rows: {len(fleet) * total_hours:,}"
    )

    # ── Drift schedules (one per ATM, shape: total_hours) ──────────────────
    drift_schedules: dict[str, np.ndarray] = {
        atm["atm_id"]: _build_drift_schedule(n_days, rng)
        for atm in fleet
    }

    # ── Issue probability vectors (per ATM, shaped by age) ─────────────────
    hw_idx = ISSUE_TYPES.index("hardware_fault")
    issue_prob_vectors: dict[str, np.ndarray] = {}
    for atm in fleet:
        p = np.array([BASE_ISSUE_PROBS[i] for i in ISSUE_TYPES], dtype=float)
        p[hw_idx] *= _age_multiplier(atm["atm_age_years"])
        p /= p.sum()
        issue_prob_vectors[atm["atm_id"]] = p

    # ── Cluster schedule ───────────────────────────────────────────────────
    cluster_schedule: set[int] = _build_cluster_schedule(n_days, rng)

    # ── Main loop ─────────────────────────────────────────────────────────
    base_rows:    list[dict] = []   # exactly one per (ATM, hour)
    cascade_rows: list[dict] = []   # extra rows for cascade incidents

    for hour_idx in range(total_hours):
        ts         = start_dt + timedelta(hours=hour_idx)
        dow        = ts.weekday()
        hour       = ts.hour
        in_cluster = hour_idx in cluster_schedule

        # Pre-compute hour-level multipliers (shared across all ATMs this tick)
        h_mult  = _hour_failure_multiplier(hour)
        d_mult  = _day_of_week_multiplier(dow)
        cl_mult = 1.6 if in_cluster else 1.0

        for atm in fleet:
            atm_id      = atm["atm_id"]
            drift_level = float(drift_schedules[atm_id][hour_idx])

            # ── Incident probability for this ATM-hour ─────────────────────
            p_fail = min(
                0.08
                * _age_multiplier(atm["atm_age_years"])
                * h_mult
                * d_mult
                * _drift_multiplier(drift_level)
                * _type_failure_multiplier(atm["atm_type"])
                * cl_mult,
                0.95,
            )

            if rng.random() > p_fail:
                # ── Normal / Degraded row ──────────────────────────────────
                base_rows.append(_normal_row(atm, ts, drift_level, rng))
            else:
                # ── Incident row ───────────────────────────────────────────
                issue = str(rng.choice(ISSUE_TYPES, p=issue_prob_vectors[atm_id]))
                base_rows.append(_incident_row(
                    atm=atm, ts=ts, issue_type=issue,
                    drift_level=drift_level, in_cluster=in_cluster,
                    is_cascade=False, cascade_parent="", rng=rng,
                ))

                # ── Cascade rows (extra rows, do NOT replace base row) ─────
                for child_issue, prob in CASCADE_SEEDS.get(issue, []):
                    if rng.random() < prob:
                        cascade_rows.append(_incident_row(
                            atm=atm, ts=ts, issue_type=child_issue,
                            drift_level=drift_level, in_cluster=in_cluster,
                            is_cascade=True, cascade_parent=issue, rng=rng,
                        ))

    # ── Assemble ──────────────────────────────────────────────────────────
    df = pd.DataFrame(base_rows + cascade_rows)

    # ── Type normalisation ────────────────────────────────────────────────
    df["timestamp"]  = pd.to_datetime(df["timestamp"])
    df["date"]       = pd.to_datetime(df["date"])
    for col in ["escalated", "is_cascade", "in_cluster",
                "downtime_minutes", "complaint_count", "resolution_minutes",
                "transaction_volume"]:
        df[col] = df[col].astype(int)
    df["drift_signal"] = df["drift_signal"].astype(float)
    df["avg_amount"]   = df["avg_amount"].astype(float)

    df = df.sort_values(["atm_id", "timestamp"]).reset_index(drop=True)

    # ── Summary ───────────────────────────────────────────────────────────
    status_counts = df["operational_status"].value_counts()
    print(
        f"[HistoricalLogGenerator] Results:\n"
        f"  Total rows              : {len(df):,}\n"
        f"  Base rows               : {len(base_rows):,}  "
        f"(target {len(fleet) * total_hours:,})\n"
        f"  Cascade rows (extra)    : {len(cascade_rows):,}\n"
        f"  NORMAL                  : {status_counts.get('NORMAL', 0):,}\n"
        f"  DEGRADED (drift>40)     : {status_counts.get('DEGRADED', 0):,}\n"
        f"  INCIDENT                : {status_counts.get('INCIDENT', 0):,}\n"
        f"  CASCADE                 : {status_counts.get('CASCADE', 0):,}\n"
        f"  Escalation rate         : {df['escalated'].mean():.2%}\n"
        f"  Unique ATMs             : {df['atm_id'].nunique()}\n"
        f"  Regions covered         : {df['region'].nunique()}"
    )
    return df


# ── Fleet metadata accessor (used by downstream layers) ───────────────────
def get_fleet_metadata(n_atms: int = N_ATMS, seed: Optional[int] = SEED) -> pd.DataFrame:
    """Return ATM fleet metadata as a DataFrame (no log generation)."""
    rng = np.random.default_rng(seed)
    return pd.DataFrame(_build_atm_fleet(n_atms, rng))


if __name__ == "__main__":
    df = generate_historical_logs(n_days=60, n_atms=100, seed=42)

    base_expected = 60 * 24 * 100
    base_actual   = len(df[~df["operational_status"].isin(["CASCADE"])])
    print(f"\n── Validation ──────────────────────────────────────────────")
    print(f"  Expected base rows  : {base_expected:,}")
    print(f"  Actual base rows    : {base_actual:,}  "
          f"({'OK' if base_actual == base_expected else 'MISMATCH'})")
    print(f"  Cascade (extra) rows: {(df['is_cascade'] == 1).sum():,}")
    print(f"  Grand total         : {len(df):,}")

    print(f"\n── operational_status ──────────────────────────────────────")
    print(df["operational_status"].value_counts().to_string())

    print(f"\n── Issue distribution (failures only) ──────────────────────")
    print(df[df["issue_type"] != ""]["issue_type"].value_counts().to_string())

    print(f"\n── Region distribution ─────────────────────────────────────")
    print(df.drop_duplicates("atm_id")[["atm_id", "region", "atm_type", "atm_age_years"]]
          .groupby("region")["atm_id"].count().to_string())

    print(f"\n── Sample (5 normal + 5 incident rows) ─────────────────────")
    cols = ["timestamp", "atm_id", "operational_status",
            "issue_type", "downtime_minutes", "drift_signal", "escalated"]
    normal_sample   = df[df["operational_status"] == "NORMAL"].head(3)[cols]
    incident_sample = df[df["operational_status"] == "INCIDENT"].head(3)[cols]
    cascade_sample  = df[df["operational_status"] == "CASCADE"].head(3)[cols]
    print(pd.concat([normal_sample, incident_sample, cascade_sample]).to_string())