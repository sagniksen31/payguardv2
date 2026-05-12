"""
automation_engine.py
Layer 5: Automated First-Level Remediation

Determines whether an incident can be auto-resolved without human intervention.
Simulates remote execution of remediation steps and returns structured results.

Design philosophy:
  - Only attempt automation on LOW-RISK, WELL-UNDERSTOOD issue patterns
  - Never auto-resolve escalated (high-impact / long-downtime) incidents
  - Every action is simulated but logged with realistic step-by-step detail
  - If automation fails (simulated), gracefully fall back to MANUAL_REQUIRED
  - Randomised success rates model real-world partial automation reliability

Resolution Modes:
  AUTO_RESOLVED    → System fixed it; no human needed
  AUTO_ATTEMPTED   → System tried but failed; routing to human with context
  MANUAL_REQUIRED  → Not eligible for automation; human assigned immediately
"""

import random
import time
import datetime

# ── Eligibility Thresholds ────────────────────────────────────────────────────
# Incidents exceeding these limits are too risky to auto-remediate
AUTO_MAX_IMPACT_SCORE   = 50_000    # ₹50K — low-risk ceiling
AUTO_MAX_DOWNTIME       = 60        # 60 min — short outages only
AUTO_MAX_COMPLAINTS     = 15        # few complaints = contained blast radius

# ── Per-Issue Automation Playbooks ────────────────────────────────────────────
# Each playbook defines:
#   steps        : ordered list of simulated actions with timing
#   success_rate : probability of full auto-resolution (0.0 – 1.0)
#   auto_sla_sec : expected wall-clock seconds for automation to complete (simulated)

PLAYBOOKS = {
    "network_failure": {
        "steps": [
            ("PING_CHECK",       "Pinging gateway 192.168.1.1 … response: 32ms",              0.4),
            ("INTERFACE_RESET",  "Sending remote reset signal to NIC eth0 …",                  0.8),
            ("DNS_FLUSH",        "Flushing DNS cache on ATM controller …",                     0.3),
            ("CONNECTIVITY_TEST","Re-testing outbound connectivity to payment processor …",    0.6),
            ("VERIFY",           "Confirming transaction heartbeat restored …",                 0.5),
        ],
        "success_rate": 0.72,   # 72% of network issues auto-clear with a reset
        "auto_sla_sec": 45,
    },
    "card_declined": {
        "steps": [
            ("GATEWAY_STATUS",   "Querying card processor gateway health endpoint …",          0.3),
            ("RETRY_BATCH",      "Triggering retry on last 5 declined transactions …",         0.5),
            ("RULE_CHECK",       "Verifying no new decline rules activated in last 1hr …",     0.4),
            ("SESSION_RESET",    "Resetting processor session token …",                        0.3),
            ("VERIFY",           "Re-running test transaction with dummy card …",               0.4),
        ],
        "success_rate": 0.65,   # Session/token issues auto-clear well; bank-side problems don't
        "auto_sla_sec": 30,
    },
    "auth_timeout": {
        "steps": [
            ("LATENCY_CHECK",    "Measuring round-trip to auth server: 2340ms (degraded) …",  0.3),
            ("TIMEOUT_EXTEND",   "Pushing config update: auth_timeout_ms = 8000 …",            0.5),
            ("RETRY_QUEUE",      "Draining and retrying 12 queued auth requests …",            0.6),
            ("CACHE_WARMUP",     "Pre-warming session token cache for this ATM …",             0.4),
            ("VERIFY",           "Auth latency now 310ms — threshold passed …",                0.5),
        ],
        "success_rate": 0.80,   # Config tweaks are highly automatable
        "auto_sla_sec": 25,
    },
    "cash_out": {
        "steps": [
            ("BALANCE_VERIFY",   "Pulling cassette sensor readings: 0 notes detected …",      0.3),
            ("ALERT_DISPATCH",   "Auto-creating cash replenishment ticket in ticketing system …", 0.4),
            ("BRANCH_NOTIFY",    "Sending SMS alert to branch manager (+91-XXXXXX) …",         0.3),
            ("PARTIAL_DISABLE",  "Disabling cash-withdrawal; keeping balance enquiry active …", 0.4),
        ],
        "success_rate": 0.45,   # Can't actually refill remotely — lower automation value
        "auto_sla_sec": 20,
    },
    "hardware_fault": {
        "steps": [
            ("DIAGNOSTICS",      "Running remote hardware diagnostic suite …",                 0.5),
            ("SOFT_RESET",       "Attempting soft reset of card reader module …",              0.6),
            ("ERROR_LOG_PULL",   "Pulling error logs from ATM firmware …",                     0.4),
            ("TICKET_CREATE",    "Auto-creating field dispatch ticket with diagnostic dump …", 0.3),
        ],
        "success_rate": 0.20,   # Physical faults rarely auto-resolve; but we can prep the tech
        "auto_sla_sec": 15,
    },
}

FALLBACK_PLAYBOOK = {
    "steps": [
        ("LOG_INCIDENT",  "Logging incident to central incident management system …", 0.3),
        ("TICKET_CREATE", "Auto-creating support ticket with classification context …", 0.4),
    ],
    "success_rate": 0.10,
    "auto_sla_sec": 10,
}


# ── Core Functions ─────────────────────────────────────────────────────────────

def is_eligible_for_automation(
    impact_score: float,
    downtime_minutes: float,
    complaint_count: int,
    escalation_status: str,
) -> tuple[bool, str]:
    """
    Decide if an incident qualifies for automated remediation.

    Returns:
        (eligible: bool, reason: str)
    """
    if "ESCALATED" in str(escalation_status):
        return False, "Incident is escalated — requires human authority"

    if impact_score > AUTO_MAX_IMPACT_SCORE:
        return False, f"Impact ₹{impact_score:,.0f} exceeds auto-remediation ceiling ₹{AUTO_MAX_IMPACT_SCORE:,.0f}"

    if downtime_minutes > AUTO_MAX_DOWNTIME:
        return False, f"Downtime {downtime_minutes}min exceeds auto-remediation limit {AUTO_MAX_DOWNTIME}min"

    if complaint_count > AUTO_MAX_COMPLAINTS:
        return False, f"Complaint volume {complaint_count} exceeds safe automation threshold {AUTO_MAX_COMPLAINTS}"

    return True, "Eligible for automated first-level remediation"


def simulate_step(step_name: str, step_description: str, step_duration_sec: float) -> dict:
    """
    Simulate execution of a single remediation step.
    Returns a structured step result.
    """
    # In a real system this would call APIs, run scripts, etc.
    # Here we simulate with deterministic-ish logic + tiny sleep for realism
    time.sleep(min(step_duration_sec * 0.05, 0.05))  # capped at 50ms for demo speed

    return {
        "step":        step_name,
        "description": step_description,
        "status":      "COMPLETED",
        "timestamp":   datetime.datetime.now().strftime("%H:%M:%S"),
    }


def run_automation(
    predicted_issue: str,
    impact_score: float,
    downtime_minutes: float,
    complaint_count: int,
    escalation_status: str,
    seed: int = None,
) -> dict:
    """
    Main automation entry point for a single incident.

    Returns a dict with:
        resolution_mode    : AUTO_RESOLVED | AUTO_ATTEMPTED | MANUAL_REQUIRED
        automation_log     : human-readable string of what happened
        steps_executed     : list of step result dicts
        auto_resolution_time_sec : simulated elapsed time
        eligibility_reason : why auto was or wasn't attempted
    """
    # Seed for reproducibility in batch runs (based on impact_score)
    rng = random.Random(seed if seed is not None else int(impact_score) % 9999)

    start_time = datetime.datetime.now()

    # ── Step 1: Eligibility Gate ──────────────────────────────────────────────
    eligible, reason = is_eligible_for_automation(
        impact_score, downtime_minutes, complaint_count, escalation_status
    )

    if not eligible:
        return {
            "resolution_mode":           "MANUAL_REQUIRED",
            "automation_log":            f"[SKIP] Auto-remediation bypassed. {reason}. Routed to human team.",
            "steps_executed":            [],
            "auto_resolution_time_sec":  0,
            "eligibility_reason":        reason,
        }

    # ── Step 2: Select Playbook ───────────────────────────────────────────────
    playbook = PLAYBOOKS.get(predicted_issue, FALLBACK_PLAYBOOK)
    steps_executed = []
    log_lines = [f"[START] Automation initiated at {start_time.strftime('%H:%M:%S')} for issue: {predicted_issue}"]

    # ── Step 3: Execute Steps ─────────────────────────────────────────────────
    for step_name, step_desc, step_dur in playbook["steps"]:
        result = simulate_step(step_name, step_desc, step_dur)
        steps_executed.append(result)
        log_lines.append(f"  [{result['timestamp']}] {step_name}: {step_desc}")

    # ── Step 4: Determine Outcome ─────────────────────────────────────────────
    success = rng.random() < playbook["success_rate"]
    elapsed = playbook["auto_sla_sec"]

    if success:
        resolution_mode = "AUTO_RESOLVED"
        log_lines.append(f"[SUCCESS] All steps completed. Incident auto-resolved in ~{elapsed}s.")
        log_lines.append(f"[CLOSED] No human intervention required.")
    else:
        resolution_mode = "AUTO_ATTEMPTED"
        log_lines.append(f"[PARTIAL] Automation steps executed but issue persists.")
        log_lines.append(f"[HANDOFF] Routing to human team with full diagnostic context attached.")

    return {
        "resolution_mode":           resolution_mode,
        "automation_log":            "\n".join(log_lines),
        "steps_executed":            steps_executed,
        "auto_resolution_time_sec":  elapsed if success else elapsed,
        "eligibility_reason":        reason,
    }


def automate_dataframe(
    df,
    ml_confidence_threshold: float = 0.60,
    deterministic: bool = True,
) -> "pd.DataFrame":
    """
    Apply automation layer to a full DataFrame.

    Adds columns:
        resolution_mode          : AUTO_RESOLVED | AUTO_ATTEMPTED | MANUAL_REQUIRED
        automation_log           : detailed step log string
        auto_resolution_time_sec : seconds taken (0 if MANUAL_REQUIRED)
        eligibility_reason       : human-readable string explaining gate decision

    Args:
        ml_confidence_threshold:
            Rows whose ml_confidence is below this are forced to MANUAL_REQUIRED
            before any other gate is evaluated.
        deterministic:
            True  (default) — Stable Demo Mode: each row seeded by its index,
                              so results are identical across runs.
            False           — Live Simulation Mode: seed=None → outcomes vary
                              each run, reflecting real-world randomness.
    """
    import pandas as pd

    results = []
    for idx, row in df.iterrows():

        # ── ML Confidence Gate (pre-eligibility) ─────────────────────────────
        confidence = float(row.get("ml_confidence", 1.0))
        if confidence < ml_confidence_threshold:
            results.append({
                "resolution_mode":           "MANUAL_REQUIRED",
                "automation_log": (
                    f"[SKIP] ML confidence {confidence:.2f} is below threshold "
                    f"{ml_confidence_threshold:.2f}. "
                    f"Prediction uncertain — routing to human for verification."
                ),
                "auto_resolution_time_sec":  0,
                "eligibility_reason": (
                    f"ML confidence {confidence:.2f} < threshold {ml_confidence_threshold:.2f}"
                ),
            })
            continue

        # ── Normal automation path ────────────────────────────────────────────
        # Stable Demo: seed = row index → fully reproducible per-incident outcome.
        # Live Sim:    seed = None     → random.Random() uses global state → varies.
        row_seed = idx if deterministic else None

        result = run_automation(
            predicted_issue   = row.get("predicted_issue", "unknown"),
            impact_score      = row.get("impact_score", 0),
            downtime_minutes  = row.get("downtime_minutes", 0),
            complaint_count   = row.get("complaint_count", 0),
            escalation_status = row.get("escalation_status", ""),
            seed              = row_seed,
        )
        results.append(result)

    results_df = pd.DataFrame(results, index=df.index)
    df = df.copy()
    df["resolution_mode"]           = results_df["resolution_mode"]
    df["automation_log"]            = results_df["automation_log"]
    df["auto_resolution_time_sec"]  = results_df["auto_resolution_time_sec"]
    df["eligibility_reason"]        = results_df["eligibility_reason"]
    return df


# ── Metrics ───────────────────────────────────────────────────────────────────

# Baseline minutes a human technician spends per incident on average
MANUAL_BASELINE_MINUTES = 120

def compute_automation_metrics(df) -> dict:
    """
    Compute automation performance metrics for dashboard display.

    Core metrics:
        total_incidents, auto_resolved_count, manual_required_count, auto_attempted_count
        auto_resolved_pct, manual_required_pct, auto_attempted_pct
        avg_auto_time_sec, manual_reduction_pct

    Advanced operational metrics (new):
        downtime_saved_minutes      : AUTO_RESOLVED count × MANUAL_BASELINE_MINUTES
        revenue_auto_contained      : sum of impact_score for AUTO_RESOLVED rows (₹)
        repeat_atm_count            : number of ATM IDs appearing more than once
        low_confidence_count        : rows flagged as uncertain by ML confidence gate
    """
    import pandas as pd

    total = len(df)
    if total == 0:
        return {}

    auto_resolved  = (df["resolution_mode"] == "AUTO_RESOLVED").sum()
    manual_req     = (df["resolution_mode"] == "MANUAL_REQUIRED").sum()
    auto_attempted = (df["resolution_mode"] == "AUTO_ATTEMPTED").sum()

    resolved_times = df.loc[
        df["resolution_mode"] == "AUTO_RESOLVED", "auto_resolution_time_sec"
    ]
    avg_auto_time = resolved_times.mean() if len(resolved_times) > 0 else 0

    # Manual reduction: before = 100% manual, after = MANUAL_REQUIRED + AUTO_ATTEMPTED
    humans_needed    = manual_req + auto_attempted
    manual_reduction = ((total - humans_needed) / total * 100) if total > 0 else 0

    # ── Advanced metrics ──────────────────────────────────────────────────────

    # 1. Estimated downtime saved: each AUTO_RESOLVED incident avoids a full
    #    manual diagnostic cycle (baseline = MANUAL_BASELINE_MINUTES per incident)
    downtime_saved = int(auto_resolved) * MANUAL_BASELINE_MINUTES

    # 2. Revenue auto-contained: sum of financial exposure for AUTO_RESOLVED rows
    if "impact_score" in df.columns:
        revenue_contained = df.loc[
            df["resolution_mode"] == "AUTO_RESOLVED", "impact_score"
        ].sum()
    else:
        revenue_contained = 0.0

    # 3. Repeat ATM detection: flag ATMs appearing more than once in this run
    if "atm_id" in df.columns:
        atm_counts    = df["atm_id"].value_counts()
        repeat_atms   = int((atm_counts > 1).sum())
        repeat_atm_ids = list(atm_counts[atm_counts > 1].index)
    else:
        repeat_atms    = 0
        repeat_atm_ids = []

    # 4. Low-confidence predictions forced to manual
    if "eligibility_reason" in df.columns:
        low_conf_count = df["eligibility_reason"].str.contains(
            "ML confidence", na=False
        ).sum()
    else:
        low_conf_count = 0

    return {
        # Core
        "total_incidents":         int(total),
        "auto_resolved_count":     int(auto_resolved),
        "manual_required_count":   int(manual_req),
        "auto_attempted_count":    int(auto_attempted),
        "auto_resolved_pct":       round(auto_resolved  / total * 100, 1),
        "manual_required_pct":     round(manual_req     / total * 100, 1),
        "auto_attempted_pct":      round(auto_attempted / total * 100, 1),
        "avg_auto_time_sec":       round(float(avg_auto_time), 1),
        "manual_reduction_pct":    round(manual_reduction, 1),
        # Advanced
        "downtime_saved_minutes":  downtime_saved,
        "revenue_auto_contained":  round(float(revenue_contained), 2),
        "repeat_atm_count":        repeat_atms,
        "repeat_atm_ids":          repeat_atm_ids,
        "low_confidence_count":    int(low_conf_count),
    }


if __name__ == "__main__":
    # Smoke test
    test = run_automation(
        predicted_issue="network_failure",
        impact_score=18_000,
        downtime_minutes=25,
        complaint_count=8,
        escalation_status="✅ Normal — Monitor",
        seed=42,
    )
    print(f"Mode: {test['resolution_mode']}")
    print(test["automation_log"])