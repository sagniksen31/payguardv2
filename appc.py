"""
appc2.py — PayGuard Intelligence Operations Centre v2.2
Stable · Low Risk Tab · Automation Tab · Data Source Options
"""

import os
import datetime
import hashlib
import numpy as np
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="PayGuard Intelligence Centre",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,300;0,400;0,500&family=DM+Sans:wght@300;400;500;600;700&display=swap');

:root {
  --bg-base:#080808; --bg-surface:#101010; --bg-card:#121212; --bg-elevated:#1a1a1a;
  --border:#282828; --border-gold:#40361a;
  --gold:#d4af37; --gold-light:#f7e092; --gold-dark:#8c7e5a;
  --gold-dim:rgba(212,175,55,0.10); --gold-border:rgba(212,175,55,0.22);
  --text-primary:#f0e6d2; --text-secondary:#8c7e5a; --text-muted:#544726;
  --danger:#ff4d4d; --danger-bg:rgba(255,77,77,0.08); --danger-border:rgba(255,77,77,0.22);
  --warning:#f59e0b; --warning-bg:rgba(245,158,11,0.08); --warning-border:rgba(245,158,11,0.22);
  --success:#22c55e; --success-bg:rgba(34,197,94,0.08); --success-border:rgba(34,197,94,0.22);
  --font-mono:'DM Mono','Courier New',monospace;
  --font-sans:'DM Sans',system-ui,sans-serif;
  --radius-sm:5px; --radius-md:10px; --radius-lg:14px;
  --shadow:0 4px 12px rgba(0,0,0,0.85);
}
html, body { font-family:var(--font-sans)!important; background-color:var(--bg-base)!important; color:var(--text-primary)!important; }
footer { visibility:hidden; }
.main .block-container { padding:1rem 2rem 3rem 2rem!important; max-width:1600px!important; }
h3 { color:var(--gold-dark)!important; font-family:var(--font-mono)!important; font-size:0.72rem!important;
     text-transform:uppercase; letter-spacing:1.5px; margin-top:1.6rem!important; margin-bottom:0.5rem!important; }
p { font-size:0.84rem; color:var(--text-secondary); }
hr { border-color:var(--border)!important; margin:0.9rem 0!important; }
[data-testid="stSidebar"] { background-color:var(--bg-surface)!important; border-right:1px solid var(--border)!important; }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label { color:var(--text-secondary)!important; font-size:0.78rem!important; }
[data-testid="stSlider"]>div>div>div { background:var(--gold)!important; }
.stButton>button { font-family:var(--font-mono)!important; font-size:0.72rem!important; font-weight:500!important;
  text-transform:uppercase; letter-spacing:0.07em; border-radius:20px!important;
  border:1px solid var(--border)!important; background:var(--bg-elevated)!important; color:var(--gold)!important; }
.stButton>button:hover { border-color:var(--gold)!important; background:var(--gold-dim)!important; color:var(--gold-light)!important; }
.stButton>button[kind="primary"] { background:var(--gold)!important; border-color:var(--gold)!important; color:#080808!important; font-weight:700!important; }
.stTextInput>div>div>input,.stNumberInput>div>div>input,.stSelectbox>div>div,.stTextArea>div>textarea {
  font-family:var(--font-mono)!important; font-size:0.8rem!important; background:var(--bg-elevated)!important;
  border:1px solid var(--border)!important; border-radius:var(--radius-sm)!important; color:var(--text-primary)!important; }
.stSelectbox>div>div>div { color:var(--text-primary)!important; }
[data-testid="stTabs"] { border-bottom:1px solid var(--border); }
button[data-baseweb="tab"] { font-family:var(--font-mono)!important; font-size:0.68rem!important;
  text-transform:uppercase; letter-spacing:0.09em; color:var(--text-secondary)!important;
  background:transparent!important; border:none!important; padding:0.65rem 1rem!important; }
button[data-baseweb="tab"][aria-selected="true"] { color:var(--gold)!important; border-bottom:2px solid var(--gold)!important; }
[data-testid="metric-container"] { background:var(--bg-card)!important; border:1px solid var(--border)!important;
  border-radius:var(--radius-md)!important; padding:1rem 1.2rem!important; box-shadow:var(--shadow)!important;
  position:relative; overflow:hidden; }
[data-testid="metric-container"]::before { content:''; position:absolute; top:0; left:0;
  width:36px; height:2px; background:var(--gold); opacity:0.7; }
[data-testid="metric-container"] label { font-family:var(--font-mono)!important; font-size:0.6rem!important;
  text-transform:uppercase; letter-spacing:0.1em; color:var(--gold-dark)!important; }
[data-testid="stMetricValue"] { font-family:var(--font-mono)!important; font-size:1.4rem!important; font-weight:500!important; color:var(--text-primary)!important; }
[data-testid="stMetricDelta"] { font-family:var(--font-mono)!important; font-size:0.63rem!important; }
[data-testid="stDataFrame"] { border:1px solid var(--border)!important; border-radius:var(--radius-md)!important; overflow:hidden; box-shadow:var(--shadow); }
[data-testid="stDataFrame"] th { background:var(--bg-elevated)!important; color:var(--gold-dark)!important;
  text-transform:uppercase; font-family:var(--font-mono)!important; font-size:0.6rem!important; border-bottom:1px solid var(--border)!important; }
[data-testid="stDataFrame"] td { font-family:var(--font-mono)!important; font-size:0.75rem!important; border-color:var(--border)!important; }
[data-testid="stExpander"] { background:var(--bg-card)!important; border:1px solid var(--border)!important;
  border-radius:var(--radius-md)!important; margin-bottom:5px!important; overflow:hidden; box-shadow:var(--shadow); }
[data-testid="stExpander"] summary { font-family:var(--font-mono)!important; font-size:0.75rem!important; color:var(--gold-dark)!important; padding:0.55rem 0.85rem!important; }
[data-testid="stExpanderDetails"] { background:var(--bg-elevated)!important; border-top:1px solid var(--border)!important; padding:0.9rem!important; }
.stCaption,[data-testid="stCaptionContainer"] { font-family:var(--font-mono)!important; font-size:0.65rem!important; color:var(--text-secondary)!important; }
[data-testid="stRadio"] label { font-family:var(--font-mono)!important; font-size:0.75rem!important; color:var(--text-secondary)!important; }
[data-testid="stSpinner"]>div { border-top-color:var(--gold)!important; }
.dash-card { background:var(--bg-card); border-radius:var(--radius-lg); padding:15px; border:1px solid var(--border); box-shadow:var(--shadow); }
.gd-card { background:var(--bg-card); border-radius:var(--radius-md); padding:14px 16px; border:1px solid var(--border);
  box-shadow:var(--shadow); position:relative; overflow:hidden; transition:border-color 0.15s ease; }
.gd-card:hover { border-color:var(--border-gold); }
.gd-card::before { content:''; position:absolute; top:0; left:0; width:36px; height:2px; background:var(--gold); opacity:0.7; }
.gd-label { color:var(--gold-dark); font-size:12px; font-weight:500; }
.gd-value { font-size:28px; font-weight:600; margin-top:7px; line-height:1.15; font-family:var(--font-mono); }
.gd-icon { border-radius:8px; padding:6px; display:flex; align-items:center; justify-content:center; }
.pg-section-label { display:flex; align-items:center; gap:0.5rem; font-family:var(--font-mono);
  font-size:0.62rem; font-weight:500; text-transform:uppercase; letter-spacing:0.13em; color:var(--gold-dark);
  border-bottom:1px solid var(--border); padding-bottom:0.4rem; margin:1.5rem 0 0.9rem 0; }
.pg-section-label::before { content:''; display:block; width:3px; height:11px; background:var(--gold); border-radius:2px; flex-shrink:0; }
.pg-mode-header { display:flex; align-items:center; gap:0.7rem; padding:0.7rem 1rem;
  border-radius:var(--radius-md); margin:0.75rem 0; font-family:var(--font-mono); font-size:0.75rem; }
.pg-mode-header.red   { background:var(--danger-bg);  border:1px solid var(--danger-border);  color:var(--danger); }
.pg-mode-header.amber { background:var(--warning-bg); border:1px solid var(--warning-border); color:var(--warning); }
.pg-mode-header.green { background:var(--success-bg); border:1px solid var(--success-border); color:var(--success); }
.pg-mode-count { font-size:1.0rem; font-weight:500; margin-left:auto; }
.pg-mode-impact { font-size:0.67rem; opacity:0.72; }
.pg-detail-grid { display:grid; grid-template-columns:1fr 1fr; gap:0.45rem 1.25rem; margin-bottom:0.65rem; }
.pg-detail-row { font-family:var(--font-mono); font-size:0.73rem; display:flex; gap:0.4rem; align-items:baseline; }
.pg-detail-key { color:var(--gold-dark); font-size:0.6rem; text-transform:uppercase; letter-spacing:0.07em; white-space:nowrap; flex-shrink:0; }
.pg-detail-val { color:var(--text-primary); }
.risk-pill { font-family:var(--font-mono); font-size:0.63rem; padding:1px 7px; border-radius:3px; display:inline-block; font-weight:600; }
.risk-high   { color:#ff4d4d; background:rgba(255,77,77,0.12);  border:1px solid rgba(255,77,77,0.3); }
.risk-medium { color:#f59e0b; background:rgba(245,158,11,0.12); border:1px solid rgba(245,158,11,0.3); }
.risk-low    { color:#22c55e; background:rgba(34,197,94,0.12);  border:1px solid rgba(34,197,94,0.3); }
.pg-action-box { background:var(--bg-elevated); border:1px solid var(--border); border-left:3px solid var(--gold);
  border-radius:var(--radius-sm); padding:0.55rem 0.8rem; font-family:var(--font-mono); font-size:0.72rem;
  color:var(--text-primary); line-height:1.5; margin-top:0.5rem; }
.pg-sb-section { font-family:var(--font-mono); font-size:0.6rem; text-transform:uppercase; letter-spacing:1.5px;
  color:var(--gold-dark); font-weight:600; margin:0.9rem 0 0.45rem 0; }
.pg-sidebar-stat { display:flex; justify-content:space-between; align-items:center;
  padding:4px 0; border-bottom:1px solid var(--border); font-family:var(--font-mono); font-size:0.68rem; }
.pg-sidebar-stat-key { color:var(--gold-dark); }
.pg-sidebar-stat-val { color:var(--text-primary); font-weight:500; }
.pg-empty-state { text-align:center; padding:3rem 1rem; font-family:var(--font-mono); font-size:0.75rem;
  color:var(--gold-dark); border:1px dashed var(--border-gold); border-radius:var(--radius-md);
  line-height:1.8; background:rgba(20,20,20,0.6); }
.pg-empty-icon { font-size:2rem; display:block; margin-bottom:0.5rem; }
.pg-form-card { background:var(--bg-elevated); border:1px solid var(--border-gold);
  border-radius:var(--radius-md); padding:1rem 1.1rem; margin-bottom:0.5rem; }
.pg-form-label { font-family:var(--font-mono); font-size:0.6rem; text-transform:uppercase;
  letter-spacing:0.1em; color:var(--gold-dark); margin-bottom:2px; }
.pg-form-value { font-family:var(--font-mono); font-size:0.82rem; color:var(--text-primary); margin-bottom:0.55rem; }
.pg-alert-banner { background:rgba(255,77,77,0.07); border:1px solid rgba(255,77,77,0.25);
  border-left:3px solid #ff4d4d; border-radius:var(--radius-md); padding:0.65rem 1rem;
  font-family:var(--font-mono); font-size:0.73rem; color:#ff8080; margin-bottom:0.5rem; }
.avail-bar-wrap { background:var(--border); border-radius:3px; height:6px; overflow:hidden; margin-top:4px; }
.avail-bar-fill { height:100%; border-radius:3px; background:var(--gold); }
.pg-ctx-hist { background:rgba(212,175,55,0.05); border:1px solid rgba(212,175,55,0.18);
  border-left:3px solid #d4af37; border-radius:var(--radius-md); padding:0.45rem 0.9rem;
  font-family:var(--font-mono); font-size:0.67rem; color:var(--gold-dark); margin-bottom:0.6rem; }
.pg-ctx-rt { background:rgba(34,197,94,0.05); border:1px solid rgba(34,197,94,0.18);
  border-left:3px solid #22c55e; border-radius:var(--radius-md); padding:0.45rem 0.9rem;
  font-family:var(--font-mono); font-size:0.67rem; color:#22c55e; margin-bottom:0.6rem; }
.pg-pred-card { background:var(--bg-card); border:1px solid var(--border-gold);
  border-radius:var(--radius-lg); padding:1.5rem 1.8rem; margin-top:1rem; }
.pg-pred-score { font-size:3.5rem; font-weight:700; font-family:var(--font-mono); line-height:1; }
.pg-idle-panel { background:var(--bg-card); border:1px solid var(--border-gold);
  border-radius:var(--radius-lg); padding:2.5rem 2rem; margin:1rem 0 2rem 0; font-family:var(--font-mono); }
.pg-launch-section { background:var(--bg-elevated); border:1px solid var(--border);
  border-radius:var(--radius-md); padding:1.2rem 1.4rem; }
.pg-input-panel { background:var(--bg-elevated); border:1px solid var(--border-gold);
  border-radius:var(--radius-md); padding:1.2rem 1.4rem; margin-bottom:1rem; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
from intelligence_pipeline import (
    run_intelligence_pipeline, PipelineConfig,
    get_availability_comparison_table, get_root_cause_repeat_atms,
    get_fleet_kpis, PipelineResult,
)
from predictive_engine import score_single, score_batch, load_model
from feature_engineering import engineer_features


@st.cache_resource
def get_model():
    """Load model once and cache for the lifetime of the Streamlit session."""
    return load_model()


from feedback_store import save_feedback, load_feedback, get_accuracy_summary
from automation_engine import compute_automation_metrics

STABLE_DEMO = "Stable Demo Mode"
LIVE_SIM    = "Live Simulation Mode"

_MAX_DF_ROWS    = 200
_MAX_EXPANDERS  = 30
_MAX_CHART_ROWS = 5000
_TAIL_PER_ATM   = 20
_MAX_LOG_ROWS   = 50

REQUIRED_CSV_COLUMNS = [
    "atm_id", "location", "hour_of_day", "transaction_volume",
    "avg_amount", "downtime_minutes", "complaint_count", "error_code",
]


# ─────────────────────────────────────────────────────────────────────────────
#  PIPELINE EXECUTION
# ─────────────────────────────────────────────────────────────────────────────
def _clean_numeric(df):
    """Force numeric columns to proper dtypes to prevent pandas TypeError."""
    int_cols = ["hour", "day_of_week", "atm_age_years", "transaction_volume",
                "downtime_minutes", "complaint_count", "escalated",
                "resolution_minutes", "is_cascade", "in_cluster"]
    float_cols = ["avg_amount", "drift_signal"]
    for c in int_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    for c in float_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    return df


def execute_pipeline(
    mode: str, n_days: int, score_n: int, force_retrain: bool, n_per_atm: int = 20
) -> PipelineResult:
    # ── Delete corrupted CSV cache if dtype is wrong ───────────────────────
    _cache = os.path.join("data", "historical_logs.csv")
    if os.path.exists(_cache):
        try:
            _probe = pd.read_csv(_cache, nrows=5, low_memory=False)
            if "hour" in _probe.columns and _probe["hour"].dtype == object:
                os.remove(_cache)
                print("[PayGuard] Removed corrupted CSV cache")
        except Exception:
            os.remove(_cache)

    # ── PROBLEM 1 FIX: Param-sensitive deterministic seed ─────────────────
    # Python's built-in hash() is randomised per-process (PYTHONHASHSEED).
    # Use hashlib for a stable, reproducible seed across all runs.
    # Same params → same seed → same output (Stable Demo)
    # Different params → different seed → different output
    if mode == STABLE_DEMO:
        _param_str = f"{n_days}:{n_per_atm}"
        _seed = int(hashlib.md5(_param_str.encode()).hexdigest(), 16) % 100_000
    else:
        _seed = None  # true randomness in Live Simulation

    config = PipelineConfig(
        n_days=n_days,
        seed=_seed,
        reload_history=(mode == LIVE_SIM),
        force_retrain=force_retrain,
        score_n_recent=score_n,
    )
    result = run_intelligence_pipeline(config)
    # Fix dtypes on result dataframes
    if result.historical_logs is not None:
        result.historical_logs = _clean_numeric(result.historical_logs)
    if result.scored_batch is not None:
        result.scored_batch = _clean_numeric(result.scored_batch)
    return result


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def section_label(icon: str, text: str) -> None:
    st.markdown(f'<div class="pg-section-label">{icon}&nbsp; {text}</div>', unsafe_allow_html=True)

def risk_pill_html(label: str) -> str:
    cls = {"HIGH":"risk-high","MEDIUM":"risk-medium","LOW":"risk-low"}.get(label,"risk-low")
    return f'<span class="risk-pill {cls}">{label}</span>'

def score_bar_html(score: float) -> str:
    c = "#ff4d4d" if score >= 65 else ("#f59e0b" if score >= 35 else "#22c55e")
    s = min(max(score, 0), 100)
    return (f'<div style="font-family:var(--font-mono);font-size:0.7rem;color:{c}">{s:.0f}'
            f'<div class="avail-bar-wrap" style="width:80px;display:inline-block;vertical-align:middle;margin-left:6px">'
            f'<div class="avail-bar-fill" style="width:{s:.0f}%;background:{c}"></div></div></div>')

def _svg(color, path):
    return (f'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{path}</svg>')

_G="#d4af37"; _GL="#f7e092"; _GD="#8c7e5a"; _R="#ff4d4d"; _B="#60a5fa"

ICONS = dict(
    warning=_svg(_R,'<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line>'),
    shield=_svg(_R,'<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>'),
    check=_svg(_G,'<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline>'),
    refresh=_svg(_GD,'<polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>'),
    timer=_svg(_G,'<circle cx="12" cy="13" r="8"></circle><polyline points="12 9 12 13 14 15"></polyline><line x1="12" y1="2" x2="12" y2="4"></line><line x1="8" y1="2" x2="16" y2="2"></line>'),
    star=_svg(_GL,'<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>'),
    flag=_svg(_GD,'<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"></path><line x1="4" y1="22" x2="4" y2="15"></line>'),
    trend_up=_svg(_B,'<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline>'),
    brain=_svg(_G,'<path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-1.66z"></path><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-1.66z"></path>'),
    chain=_svg(_GD,'<line x1="10" y1="13" x2="14" y2="9"></line><path d="M3 8l4-4 4 4-4 4z"></path><path d="M13 16l4-4 4 4-4 4z"></path>'),
    bolt=_svg(_G,'<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>'),
    robot=_svg(_GL,'<rect x="3" y="11" width="18" height="10" rx="2"></rect><circle cx="12" cy="5" r="2"></circle><path d="M12 7v4"></path><line x1="8" y1="16" x2="8" y2="16"></line><line x1="16" y1="16" x2="16" y2="16"></line>'),
)

def metric_card(title, value, color, icon_key):
    svg = ICONS.get(icon_key, "")
    return (f'<div class="gd-card"><div style="display:flex;justify-content:space-between;align-items:flex-start;">'
            f'<div><div class="gd-label">{title}</div><div class="gd-value" style="color:{color};">{value}</div></div>'
            f'<div class="gd-icon" style="background:{color}15;border:1px solid {color}33;">{svg}</div>'
            f'</div></div>')


# ─────────────────────────────────────────────────────────────────────────────
#  PER-ATM AGGREGATION
# ─────────────────────────────────────────────────────────────────────────────
def aggregate_atm_risk(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    def modal(s):
        vc = s.value_counts()
        return vc.index[0] if len(vc) else ""

    agg = df.groupby("atm_id").agg(
        location               =("location",               "first"),
        issue_type             =("issue_type",             modal),
        pre_failure_risk_score =("pre_failure_risk_score", "max"),
        escalation_probability =("escalation_probability", "max"),
        drift_signal           =("drift_signal",           "max"),
        downtime_minutes       =("downtime_minutes",       "mean"),
        complaint_count        =("complaint_count",        "mean"),
        atm_age_years          =("atm_age_years",          "first"),
        in_cluster             =("in_cluster",             "max"),
        is_cascade             =("is_cascade",             "max"),
        resolution_mode        =("resolution_mode",        modal),
        incident_count         =("atm_id",                 "count"),
    ).reset_index()

    agg["risk_label"] = np.where(
        agg["pre_failure_risk_score"] >= 65, "HIGH",
        np.where(agg["pre_failure_risk_score"] >= 35, "MEDIUM", "LOW")
    )
    return agg.sort_values("pre_failure_risk_score", ascending=False).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
#  INCIDENT CARD
# ─────────────────────────────────────────────────────────────────────────────
def render_incident_card(row: pd.Series) -> None:
    rs = row.get("pre_failure_risk_score", 0)
    rl = row.get("risk_label", "LOW")
    title = (f"{row.get('atm_id','—')}  ·  {row.get('location','—')}  ·  "
             f"{str(row.get('issue_type','—')).replace('_',' ').title()}  ·  Risk {rs:.0f}  ·  {rl}")
    with st.expander(title, expanded=False):
        lc, rc_col = st.columns(2)
        with lc:
            st.markdown(f"""<div class="pg-detail-grid">
              <div class="pg-detail-row"><span class="pg-detail-key">Issue</span><span class="pg-detail-val">{str(row.get('issue_type','—')).replace('_',' ').title()}</span></div>
              <div class="pg-detail-row"><span class="pg-detail-key">Avg Downtime</span><span class="pg-detail-val">{float(row.get('downtime_minutes',0)):.0f} min</span></div>
              <div class="pg-detail-row"><span class="pg-detail-key">Avg Complaints</span><span class="pg-detail-val">{float(row.get('complaint_count',0)):.0f}</span></div>
              <div class="pg-detail-row"><span class="pg-detail-key">Drift Signal</span><span class="pg-detail-val">{float(row.get('drift_signal',0)):.1f}/100</span></div>
              <div class="pg-detail-row"><span class="pg-detail-key">ATM Age</span><span class="pg-detail-val">{row.get('atm_age_years','—')} yrs</span></div>
              <div class="pg-detail-row"><span class="pg-detail-key">Incidents (sample)</span><span class="pg-detail-val">{int(row.get('incident_count',1))}</span></div>
            </div>""", unsafe_allow_html=True)
        with rc_col:
            ep = float(row.get("escalation_probability", 0))
            st.markdown(f"""<div class="pg-detail-grid">
              <div class="pg-detail-row"><span class="pg-detail-key">Risk Score</span><span class="pg-detail-val">{score_bar_html(rs)}</span></div>
              <div class="pg-detail-row"><span class="pg-detail-key">Risk Label</span><span class="pg-detail-val">{risk_pill_html(rl)}</span></div>
              <div class="pg-detail-row"><span class="pg-detail-key">Esc. Prob</span><span class="pg-detail-val">{ep:.1%}</span></div>
              <div class="pg-detail-row"><span class="pg-detail-key">In Cluster</span><span class="pg-detail-val">{'Yes' if row.get('in_cluster',0) else 'No'}</span></div>
              <div class="pg-detail-row"><span class="pg-detail-key">Resolution</span><span class="pg-detail-val" style="font-size:0.68rem">{row.get('resolution_mode','—')}</span></div>
            </div>""", unsafe_allow_html=True)

        # ── TASK 3: Decision Explanation ──────────────────────────────────
        st.markdown(
            "<div style='border-top:1px solid var(--border);margin-top:0.6rem;padding-top:0.55rem;'"
            "><span style='font-family:var(--font-mono);font-size:0.6rem;text-transform:uppercase;"
            "letter-spacing:0.1em;color:var(--gold-dark);font-weight:600;'>Why this decision?</span></div>",
            unsafe_allow_html=True
        )
        _conf_line = ""
        _conf_val  = row.get("ml_confidence", row.get("confidence", None))
        if _conf_val is not None:
            try:
                _conf_line = f"\n- 🤖 **ML Confidence:** {float(_conf_val):.1%}"
            except (TypeError, ValueError):
                pass
        _impact_proxy = float(row.get("pre_failure_risk_score", 0)) * 1000
        st.markdown(
            f"- ⏱ **Downtime:** {float(row.get('downtime_minutes', 0)):.0f} min\n"
            f"- 📣 **Complaints:** {float(row.get('complaint_count', 0)):.0f}\n"
            f"- 💸 **Impact Score:** ₹{_impact_proxy:,.0f} exposure proxy"
            + _conf_line
        )


def render_risk_panel(atm_df: pd.DataFrame, risk_level: str, color: str, icon: str, title: str) -> None:
    subset = atm_df[atm_df["risk_label"] == risk_level] if "risk_label" in atm_df.columns else pd.DataFrame()
    count  = len(subset)
    avg_dt = float(subset["downtime_minutes"].mean()) if count else 0
    avg_sc = float(subset["pre_failure_risk_score"].mean()) if count else 0
    st.markdown(f'<div class="pg-mode-header {color}"><span style="font-size:1.05rem">{icon}</span>'
                f'<span style="font-weight:500">{title}</span><span class="pg-mode-count">{count} ATMs</span>'
                f'<span class="pg-mode-impact">avg risk {avg_sc:.0f} · avg downtime {avg_dt:.0f} min</span></div>',
                unsafe_allow_html=True)
    if count == 0:
        st.markdown('<div class="pg-empty-state" style="padding:1.5rem"><span class="pg-empty-icon" style="font-size:1.2rem">✓</span>No ATMs in this risk category.</div>', unsafe_allow_html=True)
        return
    mk1, mk2, mk3, mk4 = st.columns(4)
    mk1.metric("ATMs", count)
    mk2.metric("Avg Risk Score", f"{avg_sc:.1f}")
    mk3.metric("Avg Downtime", f"{avg_dt:.0f} min")
    top_issue = subset["issue_type"].value_counts().idxmax().replace("_"," ").title() if count and "issue_type" in subset.columns else "—"
    mk4.metric("Top Issue", top_issue)
    render_n = subset.head(_MAX_EXPANDERS)
    st.markdown(f'<div style="font-family:var(--font-mono);font-size:0.64rem;color:var(--gold-dark);margin:0.5rem 0 0.35rem 0;">Showing {len(render_n)} of {count} ATM(s)</div>', unsafe_allow_html=True)
    for _, row in render_n.iterrows():
        render_incident_card(row)


# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="margin-bottom:18px;"><span style="color:#d4af37;font-weight:400;font-size:20px;">Pay</span>'
                '<span style="color:#f0e6d2;font-weight:700;font-size:20px;">Guard</span><br>'
                '<span style="color:#8c7e5a;font-size:10px;letter-spacing:1.5px;font-weight:600;text-transform:uppercase;">'
                'INTELLIGENCE CENTRE · V2.2</span></div>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sb-section">⚙ CONFIGURATION</div>', unsafe_allow_html=True)

    sb_mode    = st.radio("Execution Mode", [STABLE_DEMO, LIVE_SIM], index=0, key="sb_mode")
    sb_days    = st.slider("History Window (days)", 7, 90, 60, key="sb_days")
    sb_n_per_atm = st.slider("N incidents per ATM", 5, 50, 20, step=5, key="sb_n_per_atm")
    sb_retrain = st.checkbox("Force Model Retrain", value=False, key="sb_retrain",
                              help="Retrain from scratch (~2 min). Leave unchecked to reuse saved model.")

    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sb-section">◈ SYSTEM TELEMETRY</div>', unsafe_allow_html=True)

    def _sb_stat(k, v):
        st.markdown(f'<div class="pg-sidebar-stat"><span class="pg-sidebar-stat-key">{k}</span>'
                    f'<span class="pg-sidebar-stat-val">{v}</span></div>', unsafe_allow_html=True)

    if "pipeline_result" in st.session_state:
        meta = st.session_state["pipeline_result"].pipeline_meta
        _sb_stat("Total records",  f"{meta.get('total_records',0):,}")
        _sb_stat("Scored records", f"{meta.get('scored_records',0):,}")
        _sb_stat("Elapsed",        f"{meta.get('total_elapsed_sec',0):.1f}s")
        _sb_stat("Features",       str(meta.get('feature_count',0)))
    else:
        _sb_stat("Status", "Awaiting run")

    acc = get_accuracy_summary()
    _sb_stat("Feedback records", f"{acc['total']:,}")
    if acc["total"] > 0:
        _sb_stat("Technician accuracy", f"{acc['accuracy']}%")

    st.markdown('<hr>', unsafe_allow_html=True)
    sb_run = st.button("▶  Run Pipeline", use_container_width=True, type="primary", key="sb_run_btn")
    if st.button("🔄  Clear & Reset", use_container_width=True, key="sb_reset_btn"):
        for k in ["pipeline_result","pipeline_error","pipeline_traceback","lp_result","raw_df"]:
            st.session_state.pop(k, None)
        st.rerun()

    st.markdown('<div style="font-family:var(--font-mono);font-size:0.55rem;color:#544726;line-height:1.8;padding:0.2rem 0;">'
                'XGBoost · LightGBM · CatBoost ensemble<br>Root Cause Mining · Drift Detection<br>Fully Offline</div>',
                unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────────────────────────────────────
now_str = datetime.datetime.now().strftime("%d %b %Y  %H:%M")
st.markdown(f"""
<div style="background:#121212;border:1px solid #282828;border-radius:14px;padding:18px 22px;
     display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;
     box-shadow:0 4px 12px rgba(0,0,0,0.85);position:relative;overflow:hidden;">
  <div style="position:absolute;top:0;left:0;right:0;height:1px;
       background:linear-gradient(90deg,transparent,#d4af37 35%,rgba(212,175,55,0.3) 65%,transparent);opacity:0.5;"></div>
  <div>
    <div style="margin-bottom:4px;">
      <span style="color:#d4af37;font-weight:400;font-size:22px;">Pay</span>
      <span style="color:#f0e6d2;font-weight:700;font-size:22px;">Guard</span>
      <span style="color:#8c7e5a;font-weight:400;font-size:18px;"> INTELLIGENCE</span>
    </div>
    <div style="color:#8c7e5a;font-size:11px;font-weight:600;letter-spacing:1px;">PREDICTIVE ATM INCIDENT INTELLIGENCE PLATFORM · v2.2</div>
  </div>
  <div style="text-align:right;">
    <div style="color:#8c7e5a;font-size:12px;margin-bottom:7px;"><span style="color:#d4af37;font-size:9px;">●</span> LIVE &nbsp;·&nbsp; {now_str}</div>
    <div style="background:#1a1a10;border:1px solid #40361a;border-radius:4px;padding:3px 10px;font-size:11px;color:#d4af37;display:inline-block;font-family:'DM Mono',monospace;">
      Ensemble · {sb_mode}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  IDLE PANEL — DATA SOURCE + PIPELINE CONTROLS
# ─────────────────────────────────────────────────────────────────────────────
main_run = False
if "pipeline_result" not in st.session_state:
    st.markdown('<div class="pg-idle-panel">'
                '<div style="color:var(--gold);font-size:1.05rem;font-weight:600;margin-bottom:0.4rem;">🛡️ &nbsp; PayGuard Intelligence Engine Ready</div>'
                '<div style="color:var(--gold-dark);font-size:0.72rem;line-height:1.8;margin-bottom:1.2rem;">'
                'Choose a data source below. Stable Demo generates a reproducible 60-day ATM dataset.<br>'
                'First run trains the model (~2 min). Subsequent runs load from cache.'
                '</div>', unsafe_allow_html=True)

    input_mode = st.radio(
        "Data Source",
        ["🔬 Generate Demo Data", "📂 Upload CSV", "🧪 Manual Entry + Analysis"],
        horizontal=True,
        key="input_mode_select",
        label_visibility="collapsed",
    )

    # ── Mode A: Generate Demo Data ──────────────────────────────────────
    if input_mode == "🔬 Generate Demo Data":
        st.markdown('<div class="pg-launch-section">', unsafe_allow_html=True)
        mc1, mc2, mc3, mc4 = st.columns([1.6, 1, 1, 1])
        with mc1: main_mode    = st.radio("Mode", [STABLE_DEMO, LIVE_SIM], index=0, key="main_mode", horizontal=True)
        with mc2: main_days    = st.slider("History (days)", 7, 90, 60, key="main_days")
        with mc3: main_n_per_atm = st.slider("N per ATM", 5, 50, 20, step=5, key="main_n_per_atm")
        with mc4: main_retrain = st.checkbox("Force Retrain", value=False, key="main_retrain")
        main_run = st.button("▶  Run Pipeline", type="primary", use_container_width=True, key="main_run_btn")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Mode B: Upload CSV ──────────────────────────────────────────────
    elif input_mode == "📂 Upload CSV":
        st.markdown('<div class="pg-launch-section">', unsafe_allow_html=True)
        st.markdown(f'<div style="font-family:var(--font-mono);font-size:0.67rem;color:var(--gold-dark);margin-bottom:0.6rem;">'
                    f'Required columns: {", ".join(REQUIRED_CSV_COLUMNS)}</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload CSV", type=["csv"], key="csv_upload")
        if uploaded is not None:
            try:
                _df_up = pd.read_csv(uploaded)
                if all(col in _df_up.columns for col in REQUIRED_CSV_COLUMNS):
                    st.session_state["raw_df"] = _df_up
                    st.success(f"✓ CSV loaded — {len(_df_up):,} rows, {_df_up['atm_id'].nunique()} ATMs")
                    st.dataframe(_df_up.head(5), use_container_width=True, hide_index=True)
                else:
                    missing = [c for c in REQUIRED_CSV_COLUMNS if c not in _df_up.columns]
                    st.error(f"Invalid CSV — missing columns: {', '.join(missing)}")
            except Exception as _e:
                st.error(f"Failed to read CSV: {_e}")
        if "raw_df" in st.session_state:
            st.info("CSV loaded. Use the sidebar ▶ Run Pipeline button to analyse, or switch to Demo mode to run the full pipeline.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Mode C: Manual Entry + ML Analysis ────────────────────────────────
    elif input_mode == "🧪 Manual Entry + Analysis":
        st.markdown("""
        <div style="background:rgba(212,175,55,0.05);border:1px solid rgba(212,175,55,0.25);
             border-left:3px solid #d4af37;border-radius:10px;padding:0.75rem 1rem;
             font-family:var(--font-mono);font-size:0.72rem;color:var(--gold-dark);margin-bottom:1rem;">
          🧪 <strong style="color:#d4af37;">MANUAL ENTRY + ANALYSIS</strong>
          &nbsp;·&nbsp; Simulate ATM conditions and analyze risk instantly
        </div>""", unsafe_allow_html=True)

        # ── Init session state ──────────────────────────────────────────
        if "manual_entries" not in st.session_state:
            st.session_state["manual_entries"] = pd.DataFrame()
        if "manual_results" not in st.session_state:
            st.session_state["manual_results"] = None

        _ISSUE_TYPES = ["cash_out", "network_failure", "auth_timeout",
                        "card_declined", "hardware_fault", "software_crash"]
        _LOCATIONS = ["Mumbai_Central", "Delhi_North", "Bangalore_Koramangala",
                      "Chennai_T_Nagar", "Pune_Hinjewadi", "Hyderabad_Gachibowli"]

        # ── Input form ──────────────────────────────────────────────────
        st.markdown('<div class="pg-section-label">📝&nbsp; Add ATM Incident</div>', unsafe_allow_html=True)
        with st.form("manual_entry_form", clear_on_submit=True):
            me_c1, me_c2, me_c3 = st.columns(3)
            with me_c1:
                me_atm = st.text_input("ATM ID", value="ATM_CUSTOM_01", key="me_atm")
                me_location = st.selectbox("Location", _LOCATIONS, key="me_loc")
                me_issue = st.selectbox("Issue Type", _ISSUE_TYPES, key="me_issue")
            with me_c2:
                me_txn = st.number_input("Transaction Volume", 0, 5000, 250, step=50, key="me_txn")
                me_amount = st.number_input("Avg Amount (₹)", 100, 50000, 3500, step=100, key="me_amount")
                me_downtime = st.number_input("Downtime (min)", 0, 480, 30, step=5, key="me_dt")
            with me_c3:
                me_complaints = st.number_input("Complaints", 0, 100, 5, step=1, key="me_cc")
                me_drift = st.slider("Drift Signal", 0.0, 100.0, 20.0, step=1.0, key="me_drift")
                me_age = st.number_input("ATM Age (years)", 1, 20, 5, step=1, key="me_age")
            me_c4, me_c5 = st.columns(2)
            with me_c4:
                me_hour = st.slider("Hour of Day", 0, 23, 14, key="me_hour")
            with me_c5:
                me_cascade = st.checkbox("Is Cascade?", value=False, key="me_cascade")

            me_submitted = st.form_submit_button("➕  Add Entry", use_container_width=True)

        if me_submitted:
            import datetime as _dt
            _new_row = pd.DataFrame([{
                "timestamp":          _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "date":               _dt.datetime.now().strftime("%Y-%m-%d"),
                "hour":               int(me_hour),
                "day_of_week":        _dt.datetime.now().weekday(),
                "atm_id":             me_atm,
                "location":           me_location,
                "region":             me_location.split("_")[0],
                "atm_age_years":      int(me_age),
                "atm_type":           "Lobby",
                "operational_status": "active",
                "transaction_volume": int(me_txn),
                "avg_amount":         float(me_amount),
                "drift_signal":       float(me_drift),
                "issue_type":         me_issue,
                "error_code":         f"E{np.random.randint(100,999)}",
                "downtime_minutes":   int(me_downtime),
                "complaint_count":    int(me_complaints),
                "escalated":          0,
                "resolution_mode":    "",
                "resolution_minutes": 0,
                "is_cascade":         int(me_cascade),
                "cascade_parent":     "",
                "in_cluster":         0,
            }])
            st.session_state["manual_entries"] = pd.concat(
                [st.session_state["manual_entries"], _new_row], ignore_index=True
            )
            st.session_state["manual_results"] = None  # clear stale results
            st.success(f"✓ Added entry for {me_atm} — {me_issue.replace('_',' ').title()}")

        # ── Show collected entries ───────────────────────────────────────
        _me_df = st.session_state.get("manual_entries", pd.DataFrame())

        st.markdown('<div class="pg-section-label" style="margin-top:1rem;">📋&nbsp; Collected Entries</div>', unsafe_allow_html=True)
        if _me_df.empty:
            st.markdown(
                '<div class="pg-empty-state" style="padding:1.5rem">'
                '<span class="pg-empty-icon" style="font-size:1.2rem">📋</span>'
                'No entries yet. Fill the form above and click <strong>➕ Add Entry</strong>.</div>',
                unsafe_allow_html=True
            )
        else:
            _show_cols = [c for c in ["atm_id","location","issue_type","downtime_minutes",
                                      "complaint_count","drift_signal","transaction_volume"] if c in _me_df.columns]
            st.dataframe(_me_df[_show_cols], use_container_width=True, hide_index=True, height=200)
            st.caption(f"{len(_me_df)} entry(ies) collected")

        # ── Analysis controls ───────────────────────────────────────────
        me_btn_c1, me_btn_c2 = st.columns(2)
        with me_btn_c1:
            _run_analysis = st.button(
                "🚀  Run Analysis on Manual Data", type="primary",
                use_container_width=True, key="me_run_analysis",
                disabled=_me_df.empty,
            )
        with me_btn_c2:
            if st.button("🗑  Clear All Entries", use_container_width=True, key="me_clear"):
                st.session_state["manual_entries"] = pd.DataFrame()
                st.session_state["manual_results"] = None
                st.rerun()

        # ── Run ML pipeline ─────────────────────────────────────────────
        if _run_analysis and not _me_df.empty:
            with st.spinner("Running ML pipeline on manual data…"):
                try:
                    _model = get_model()
                    if _model is None:
                        st.error("⚠ Model not loaded. Run the full pipeline first (Demo Data mode) to train the model.")
                    else:
                        df = _me_df.copy()

                        # 🧠 STEP 1 — ensure timestamp is datetime
                        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

                        # 🧠 STEP 2 — simulate short history if too small
                        if len(df) < 5:
                            base = df.iloc[0].to_dict()
                            rows = []

                            for i in range(5):
                                r = base.copy()
                                r["timestamp"] = pd.Timestamp.now() - pd.Timedelta(hours=5 - i)

                                # realistic variation
                                r["transaction_volume"] = float(r["transaction_volume"]) * (0.9 + 0.05*i)
                                r["downtime_minutes"] = float(r["downtime_minutes"]) * (1 + 0.1*i)
                                r["complaint_count"] = int(r["complaint_count"]) + i

                                rows.append(r)

                            df = pd.DataFrame(rows)

                        # 🧠 STEP 3 — sort for time-series (CRITICAL)
                        df = df.sort_values(["atm_id", "timestamp"])

                        # 🧠 STEP 4 — run feature engineering
                        _feat = engineer_features(df, add_target=False)
                        _feat = _feat.fillna(0)
                        _scored = score_batch(_feat, artifact=_model)
                        # Sanitize numpy types
                        for _col in _scored.columns:
                            _scored[_col] = _scored[_col].apply(
                                lambda x: float(x) if isinstance(x, (np.float32, np.float64)) else
                                          int(x)   if isinstance(x, (np.int32,  np.int64))   else x
                            )
                        st.session_state["manual_results"] = _scored
                except Exception as _me_err:
                    st.error(f"Analysis failed: {_me_err}")

        # ── Display results ─────────────────────────────────────────────
        _me_results = st.session_state.get("manual_results")
        if _me_results is not None and not _me_results.empty:
            st.markdown('<div class="pg-section-label" style="margin-top:1.2rem;">🧠&nbsp; Analysis Results</div>', unsafe_allow_html=True)

            # Summary metrics
            _n_high   = int((_me_results["risk_label"] == "HIGH").sum())   if "risk_label" in _me_results.columns else 0
            _n_medium = int((_me_results["risk_label"] == "MEDIUM").sum()) if "risk_label" in _me_results.columns else 0
            _n_low    = int((_me_results["risk_label"] == "LOW").sum())    if "risk_label" in _me_results.columns else 0
            _avg_risk = float(_me_results["pre_failure_risk_score"].mean()) if "pre_failure_risk_score" in _me_results.columns else 0

            rs1, rs2, rs3, rs4 = st.columns(4)
            rs1.metric("🔴 HIGH Risk", _n_high)
            rs2.metric("🟡 MEDIUM Risk", _n_medium)
            rs3.metric("🟢 LOW Risk", _n_low)
            rs4.metric("📊 Avg Risk Score", f"{_avg_risk:.1f}")

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            # Results table
            _res_cols = [c for c in ["atm_id","location","issue_type","pre_failure_risk_score",
                                     "risk_label","escalation_probability","downtime_minutes",
                                     "resolution_mode"] if c in _me_results.columns]
            _res_disp = _me_results[_res_cols].copy()
            if "pre_failure_risk_score" in _res_disp.columns:
                _res_disp["pre_failure_risk_score"] = _res_disp["pre_failure_risk_score"].apply(lambda x: f"{x:.1f}")
            if "escalation_probability" in _res_disp.columns:
                _res_disp["escalation_probability"] = _res_disp["escalation_probability"].apply(lambda x: f"{x:.1%}")
            def _hl_manual(row):
                if row.get("risk_label") == "HIGH":
                    return ["background-color:rgba(255,77,77,0.12);color:#ff4d4d;font-weight:600"] * len(row)
                if row.get("risk_label") == "MEDIUM":
                    return ["background-color:rgba(245,158,11,0.08)"] * len(row)
                return [""] * len(row)
            st.dataframe(_res_disp.style.apply(_hl_manual, axis=1), use_container_width=True, hide_index=True, height=300)

            # Per-ATM decision cards for HIGH risk entries
            if "risk_label" in _me_results.columns:
                _high_entries = _me_results[_me_results["risk_label"] == "HIGH"]
            else:
                _high_entries = pd.DataFrame()
            if not _high_entries.empty:
                st.markdown('<div class="pg-section-label" style="margin-top:1rem;">🚨&nbsp; High Risk — Immediate Action Required</div>', unsafe_allow_html=True)
                for _, _hr in _high_entries.iterrows():
                    _hrs = float(_hr.get("pre_failure_risk_score", 0))
                    st.markdown(f"""
                    <div class="pg-pred-card" style="padding:0.8rem 1.2rem;margin-bottom:0.5rem;">
                      <div style="font-family:var(--font-mono);font-size:0.62rem;text-transform:uppercase;letter-spacing:0.12em;color:var(--gold-dark);margin-bottom:0.2rem;">
                        ATM: {_hr.get('atm_id','—')} &nbsp;·&nbsp; {str(_hr.get('issue_type','—')).replace('_',' ').title()} &nbsp;·&nbsp; {_hr.get('location','—')}
                      </div>
                      <div style="display:flex;align-items:baseline;gap:0.8rem;">
                        <div class="pg-pred-score" style="color:#ff4d4d;font-size:2rem;">{_hrs:.1f}</div>
                        <span class="risk-pill risk-high" style="font-size:0.75rem;padding:2px 8px;">HIGH RISK</span>
                        <span style="font-family:var(--font-mono);font-size:0.68rem;color:var(--gold-dark);">Esc: {float(_hr.get('escalation_probability',0)):.1%} · Downtime: {float(_hr.get('downtime_minutes',0)):.0f}m</span>
                      </div>
                    </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)



# Resolve trigger and config
_triggered = sb_run or main_run
_mode    = st.session_state.get("main_mode",    sb_mode)  if main_run else sb_mode
_days    = st.session_state.get("main_days",    sb_days)  if main_run else sb_days
_n_per_atm = st.session_state.get("main_n_per_atm", sb_n_per_atm) if main_run else sb_n_per_atm
_retrain = st.session_state.get("main_retrain", sb_retrain) if main_run else sb_retrain

# Invalidate scored cache when N slider changes
if st.session_state.get("_n_per_atm_used") != _n_per_atm:
    st.session_state.pop("df_scored_cache", None)
    st.session_state.pop("df_scored_key", None)

if _triggered:
    for k in ["pipeline_result","pipeline_error","pipeline_traceback","df_scored_cache","df_scored_key"]:
        st.session_state.pop(k, None)

    # ── PROBLEM 1+3 FIX: Bust CSV cache when Stable Demo params change ────
    # reload_history=False in Stable Demo means the pipeline reuses the cached
    # CSV — so a fresh seed only takes effect after we delete the old file.
    _cur_params = (_mode, _days, _n_per_atm)
    if _mode == STABLE_DEMO and st.session_state.get("_last_pipeline_params") != _cur_params:
        _hist_cache = os.path.join("data", "historical_logs.csv")
        if os.path.exists(_hist_cache):
            try:
                os.remove(_hist_cache)
                print(f"[PayGuard] Busted CSV cache — params changed to {_cur_params}")
            except OSError:
                pass
    st.session_state["_last_pipeline_params"] = _cur_params

    try:
        with st.spinner("Running PayGuard Intelligence Pipeline…"):
            _res = execute_pipeline(_mode, _days, 5000, _retrain, _n_per_atm)
        st.session_state["pipeline_result"] = _res
    except Exception as _exc:
        import traceback as _tb
        st.session_state["pipeline_error"]     = str(_exc)
        st.session_state["pipeline_traceback"] = _tb.format_exc()
    st.rerun()

if "pipeline_error" in st.session_state:
    st.error(f"⚠ Pipeline failed: {st.session_state['pipeline_error']}")
    with st.expander("Show traceback"):
        st.code(st.session_state.get("pipeline_traceback",""))

if "pipeline_result" not in st.session_state:
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
#  LOAD + DERIVE DATA
# ─────────────────────────────────────────────────────────────────────────────
result: PipelineResult = st.session_state["pipeline_result"]

if result is None or result.scored_batch is None or len(result.scored_batch) == 0:
    st.error("Pipeline result is empty. Please re-run.")
    st.stop()

for err in (result.errors or []):
    st.warning(f"⚠ Pipeline layer warning: {err}")

history_df    = result.historical_logs
scored_full   = result.scored_batch
rc            = result.root_cause_summary
avail         = result.availability_summary
model_metrics = result.model_metrics

# ── PROBLEM 3 FIX: Apply history_days slider to historical data ───────────
# The pipeline generates up to 90 days; filter to the user-selected window
# so different slider values produce visibly different chart and KPI outputs.
if "timestamp" in history_df.columns and len(history_df) > 0:
    _ts = pd.to_datetime(history_df["timestamp"])
    _cutoff = _ts.max() - pd.Timedelta(days=_days)
    _hist_filtered = history_df[_ts >= _cutoff].copy()
    # Only use the filtered view if it's non-empty (safety fallback)
    if len(_hist_filtered) > 0:
        history_df = _hist_filtered

# ── FIX 1+2+3: Use scored_batch (already engineered+scored by pipeline) ──
N = _n_per_atm
_cache_key = f"{id(result)}_{N}"

if st.session_state.get("df_scored_key") != _cache_key or st.session_state.get("df_scored_cache") is None:
    # scored_full already has 65+ engineered features + risk scores from the pipeline
    _scored = _clean_numeric(scored_full.copy())
    _scored = _scored[_scored["issue_type"] != ""]
    _scored = _scored.sort_values("timestamp").groupby("atm_id", group_keys=False).tail(N)
    st.session_state["df_scored_cache"] = _scored
    st.session_state["df_scored_key"] = _cache_key
    st.session_state["_n_per_atm_used"] = N

rt_sample   = st.session_state["df_scored_cache"]
atm_risk_df = aggregate_atm_risk(rt_sample)


hist_incidents   = rc.get("total_incidents", int((history_df["issue_type"] != "").sum()))
hist_escalations = rc.get("total_escalations", int(history_df["escalated"].sum()))
hist_esc_rate    = rc.get("overall_escalation_rate", 0.0)
n_clusters       = len([c for c in rc.get("issue_clusters",[]) if c.get("is_systemic")])

rt_risk_counts = atm_risk_df["risk_label"].value_counts().to_dict() if "risk_label" in atm_risk_df.columns else {}
rt_high        = rt_risk_counts.get("HIGH",   0)
rt_medium      = rt_risk_counts.get("MEDIUM", 0)
rt_low         = rt_risk_counts.get("LOW",    0)

alert_atms   = atm_risk_df[atm_risk_df["risk_label"] == "HIGH"].copy()

fleet_avail_r = avail.get("fleet_availability_reactive",  0)
fleet_avail_p = avail.get("fleet_availability_proactive", 0)
fleet_improve = avail.get("fleet_improvement_proactive_pct", 0)
esc_avoided   = avail.get("escalations_avoided_proactive", 0)
dt_prevented  = avail.get("total_downtime_prevented_proactive_min", 0)

repeat_atms_df = get_root_cause_repeat_atms(result)
avail_table    = get_availability_comparison_table(result)

# ── FIX 5: Filter out empty issue_type for charts ────────────────────────
_inc_df = history_df[(history_df["issue_type"] != "") & (history_df["issue_type"].notna())]
chart_df = (
    _inc_df.sample(n=min(_MAX_CHART_ROWS, len(_inc_df)), random_state=42)
    if len(_inc_df) > _MAX_CHART_ROWS else _inc_df.copy()
)

# ── FIX 4: Automation metrics using automation_engine.py ─────────────────
_auto_df = rt_sample.copy()
_auto_df = _auto_df[(_auto_df["issue_type"] != "") & (_auto_df["issue_type"].notna())]
if "resolution_mode" in _auto_df.columns:
    _auto_df = _auto_df[(_auto_df["resolution_mode"] != "NONE") & (_auto_df["resolution_mode"].notna())]
if "auto_resolution_time_sec" not in _auto_df.columns:
    _auto_df["auto_resolution_time_sec"] = 0

# ── PROBLEM 2 FIX: Synthesize impact_score when missing or all-zero ───────
# compute_automation_metrics() needs impact_score to calculate revenue_auto_contained.
# The pipeline's scored_batch may not carry this column — derive it from
# downtime × avg_amount proxy (₹/min × minutes × complaint multiplier).
if "impact_score" not in _auto_df.columns or _auto_df["impact_score"].fillna(0).sum() == 0:
    _dt_col  = pd.to_numeric(_auto_df.get("downtime_minutes",  pd.Series(0, index=_auto_df.index)), errors="coerce").fillna(0)
    _amt_col = pd.to_numeric(_auto_df.get("avg_amount",        pd.Series(3500, index=_auto_df.index)), errors="coerce").fillna(3500)
    _cc_col  = pd.to_numeric(_auto_df.get("complaint_count",   pd.Series(0, index=_auto_df.index)), errors="coerce").fillna(0)
    # ₹ exposure = downtime(min) × txn rate(₹/min) × complaint severity multiplier
    _txn_rate = _amt_col / 10.0   # rough: avg_amount ÷ 10 ≈ ₹/min revenue at that ATM
    _auto_df = _auto_df.copy()
    _auto_df["impact_score"] = (_dt_col * _txn_rate * (1.0 + _cc_col * 0.15)).round(0)

_auto_metrics    = compute_automation_metrics(_auto_df) if len(_auto_df) > 0 else {}
n_auto_resolved  = _auto_metrics.get("auto_resolved_count", 0)
n_auto_attempt   = _auto_metrics.get("auto_attempted_count", 0)
n_manual         = _auto_metrics.get("manual_required_count", 0)
n_total_inc      = _auto_metrics.get("total_incidents", len(_auto_df))
pct_manual_saved = _auto_metrics.get("manual_reduction_pct", 0)
avg_auto_time    = _auto_metrics.get("avg_auto_time_sec", 0) / 60
avg_manual_time  = float(_auto_df[_auto_df["resolution_mode"]=="MANUAL_REQUIRED"]["resolution_minutes"].mean()) if "resolution_minutes" in _auto_df.columns and n_manual else 0
downtime_saved   = float(_auto_df[_auto_df["resolution_mode"]=="AUTO_RESOLVED"]["downtime_minutes"].sum()) if "downtime_minutes" in _auto_df.columns else 0


# ─────────────────────────────────────────────────────────────────────────────
#  ALERT BANNER
# ─────────────────────────────────────────────────────────────────────────────
if not alert_atms.empty:
    # ── TASK 1: Detailed alert using highest-impact HIGH/ESCALATED ATM ──
    _top_alert = alert_atms.sort_values("pre_failure_risk_score", ascending=False).iloc[0]
    _alert_atm_id    = str(_top_alert.get("atm_id", "—"))
    _alert_location  = str(_top_alert.get("location", "—"))
    _alert_issue     = str(_top_alert.get("issue_type", "—")).replace("_", " ").title()
    _alert_impact    = float(_top_alert.get("pre_failure_risk_score", 0)) * 1000   # proxy ₹ exposure
    _alert_cc        = int(float(_top_alert.get("complaint_count", 0)))
    _alert_dt        = int(float(_top_alert.get("downtime_minutes", 0)))
    _alert_esc_prob  = float(_top_alert.get("escalation_probability", 0))
    _alert_esc_label = "→ ESCALATED" if _alert_esc_prob >= 0.5 else "→ Normal"
    st.error(
        f"🚨 **{_alert_atm_id} · {_alert_location}**\n\n"
        f"**{_alert_issue}** — ₹{_alert_impact:,.0f} exposure\n\n"
        f"{_alert_cc} complaints · {_alert_dt} min downtime · "
        f"{_alert_esc_label}  ({len(alert_atms)} HIGH-risk ATM(s) total)"
    )


# ─────────────────────────────────────────────────────────────────────────────
#  TABS
# ─────────────────────────────────────────────────────────────────────────────
TAB_OV, TAB_HR, TAB_MR, TAB_LR, TAB_AUTO, TAB_RC, TAB_AV, TAB_FB = st.tabs([
    "📊  Overview",
    "🔴  High Risk",
    "🟡  Medium Risk",
    "🟢  Low Risk",
    "🤖  Automation",
    "🔍  Root Cause",
    "📈  Availability",
    "🔁  Feedback",
])


# ═══════════════════════════════════════════════════════════════════════════
#  TAB 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════
with TAB_OV:
    st.markdown(f'<div class="pg-ctx-hist">📊 <strong>Historical Performance</strong> — Full {_days}-day dataset · {hist_incidents:,} incidents · Source: historical_logs.csv</div>', unsafe_allow_html=True)
    st.markdown("### FLEET PERFORMANCE (HISTORICAL)")
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.markdown(metric_card("Total Incidents",   f"{hist_incidents:,}",   "#f0e6d2","warning"), unsafe_allow_html=True)
    with c2: st.markdown(metric_card("Total Escalations", f"{hist_escalations:,}", _R,       "shield"),  unsafe_allow_html=True)
    with c3: st.markdown(metric_card("Escalation Rate",   f"{hist_esc_rate:.1%}",  _GD,      "flag"),    unsafe_allow_html=True)
    with c4: st.markdown(metric_card("Systemic Clusters", str(n_clusters),          _GL,      "chain"),   unsafe_allow_html=True)
    with c5:
        roc = model_metrics.get("roc_auc",0)
        st.markdown(metric_card("Model ROC-AUC", f"{roc:.4f}", _GL, "star"), unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    n_atms_scored = atm_risk_df["atm_id"].nunique() if not atm_risk_df.empty else 0
    st.markdown(f'<div class="pg-ctx-rt">⚡ <strong>Current System State</strong> (Last {N} incidents per ATM — balanced sample) · {n_atms_scored} ATMs · Aggregated per-ATM view</div>', unsafe_allow_html=True)
    st.markdown("### CURRENT RISK DISTRIBUTION (PER ATM)")
    a1,a2,a3,a4,a5 = st.columns(5)
    with a1: st.markdown(metric_card("HIGH Risk ATMs",   str(rt_high),   _R,       "warning"), unsafe_allow_html=True)
    with a2: st.markdown(metric_card("MEDIUM Risk ATMs", str(rt_medium), "#f59e0b","refresh"), unsafe_allow_html=True)
    with a3: st.markdown(metric_card("LOW Risk ATMs",    str(rt_low),    _G,       "check"),   unsafe_allow_html=True)
    with a4:
        avg_pr = model_metrics.get("avg_precision",0)
        st.markdown(metric_card("Avg Precision", f"{avg_pr:.4f}", _GD, "timer"), unsafe_allow_html=True)
    with a5: st.markdown(metric_card("ATMs Need Action", str(len(alert_atms)), _R, "brain"), unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown("### AVAILABILITY & DOWNTIME PREVENTION")
    b1,b2,b3,b4 = st.columns(4)
    with b1: st.markdown(metric_card("Fleet Availability (Proactive)", f"{fleet_avail_p:.4%}", _G,  "check"),    unsafe_allow_html=True)
    with b2: st.markdown(metric_card("Availability Improvement",       f"+{fleet_improve:.3f}pp", _GL,"trend_up"), unsafe_allow_html=True)
    with b3: st.markdown(metric_card("Escalations Avoided",            f"{esc_avoided:,}",     _G,  "shield"),   unsafe_allow_html=True)
    with b4:
        dt_hrs = dt_prevented/60
        st.markdown(metric_card("Downtime Prevented", f"{dt_prevented:,.0f} min ({dt_hrs:.1f} hrs)", _GL, "timer"), unsafe_allow_html=True)

    if not alert_atms.empty:
        section_label("⚡","ATMs Requiring Proactive Intervention Now")
        show_c = [c for c in ["atm_id","location","issue_type","pre_failure_risk_score",
                               "risk_label","drift_signal","escalation_probability","downtime_minutes","incident_count"]
                  if c in alert_atms.columns]
        disp = alert_atms[show_c].head(_MAX_DF_ROWS).copy()
        if "escalation_probability" in disp.columns:
            disp["escalation_probability"] = disp["escalation_probability"].apply(lambda x: f"{x:.1%}")
        def _hl(row):
            if row.get("risk_label")=="HIGH": return ["background-color:rgba(255,77,77,0.10);color:#ff4d4d;font-weight:600"]*len(row)
            return [""]*len(row)
        st.dataframe(disp.style.apply(_hl,axis=1), use_container_width=True, hide_index=True, height=260)

    # ── TASK 2: System Intelligence Panel ───────────────────────────────
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    section_label("🧠", "System Intelligence")

    # ── PROBLEM 2 FIX: Compute revenue protected correctly ───────────────────
    # Primary: sum impact_score for AUTO_RESOLVED rows (direct calculation).
    # Fallback 1: use automation_engine's revenue_auto_contained if > 0.
    # Fallback 2: proxy from downtime × txn rate for AUTO_RESOLVED rows.
    _auto_resolved_rows = _auto_df[_auto_df["resolution_mode"] == "AUTO_RESOLVED"]
    _n_auto_resolved_check = len(_auto_resolved_rows)

    # Direct impact_score sum (most accurate if column is present and non-zero)
    _direct_rev = float(_auto_resolved_rows["impact_score"].sum()) if "impact_score" in _auto_resolved_rows.columns else 0.0

    # automation_engine's calculation
    _engine_rev = float(_auto_metrics.get("revenue_auto_contained", 0) or 0)

    # Downtime proxy: ₹850/min × downtime of AUTO_RESOLVED incidents
    _dt_auto = float(_auto_resolved_rows["downtime_minutes"].sum()) if "downtime_minutes" in _auto_resolved_rows.columns else 0.0
    _proxy_rev = _dt_auto * 850.0

    # Choose best non-zero value
    if _direct_rev > 0:
        _si_rev = _direct_rev
        _rev_source = "direct"
    elif _engine_rev > 0:
        _si_rev = _engine_rev
        _rev_source = "engine"
    elif _proxy_rev > 0:
        _si_rev = _proxy_rev
        _rev_source = "proxy"
    else:
        _si_rev = downtime_saved * 850
        _rev_source = "fallback"

    _si_dt    = _auto_metrics.get("downtime_saved_minutes", downtime_saved)
    _si_dt_hr = round(_si_dt / 60, 1)
    _si_ar    = _auto_metrics.get("auto_resolved_pct",
                    round(n_auto_resolved / max(n_total_inc, 1) * 100, 1))
    _si_mr    = _auto_metrics.get("manual_reduction_pct", pct_manual_saved)
    si1, si2, si3, si4 = st.columns(4)
    _rev_note = " *(proxy)*" if _rev_source in ("proxy", "fallback") else ""
    si1.metric("💸 Revenue Protected",  f"₹{_si_rev:,.0f}{_rev_note}")
    si2.metric("⏱ Downtime Saved",     f"{_si_dt:,.0f} min",
               delta=f"{_si_dt_hr} hrs saved")
    si3.metric("🤖 Auto-Resolved %",   f"{_si_ar:.1f}%")
    si4.metric("📉 Manual Reduction %", f"{_si_mr:.1f}%")
    if n_auto_resolved == 0 and _n_auto_resolved_check == 0:
        st.caption("ℹ No incidents auto-resolved in this run — revenue figure uses downtime proxy.")
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    st.markdown("### ANALYTICS")
    ch1,ch2,ch3 = st.columns(3)
    _bg = dict(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
               margin=dict(l=10,r=10,t=10,b=10),font=dict(color="#8c7e5a",family="DM Mono, monospace",size=11),height=220)
    _gg = "rgba(212,175,55,0.08)"

    try:
        import plotly.express as px
        import plotly.graph_objects as go

        with ch1:
            st.markdown('<div class="dash-card"><p style="color:#f0e6d2;font-weight:600;font-size:14px;margin-bottom:0">Issue Distribution</p>', unsafe_allow_html=True)
            _cdf = chart_df[(chart_df["issue_type"] != "") & (chart_df["issue_type"].notna())]
            ic = _cdf["issue_type"].value_counts().reset_index(); ic.columns=["issue_type","count"]
            fig1 = px.pie(ic,names="issue_type",values="count",hole=0.6,
                          color_discrete_sequence=["#d4af37","#f7e092","#8c7e5a","#544726","#2a2414","#60a5fa"])
            fig1.update_traces(textposition="inside",textinfo="percent+label",textfont_color="#080808",textfont_size=11)
            fig1.update_layout(**_bg,showlegend=False)
            st.plotly_chart(fig1,use_container_width=True,config={"displayModeBar":False})
            # ── TASK 4: Percentage captions per issue ──────────────────
            if len(ic) > 0:
                _ic_total = ic["count"].sum()
                _captions = "  ·  ".join(
                    f"{r['issue_type'].replace('_',' ')} {round(r['count']/_ic_total*100):.0f}%"
                    for _, r in ic.head(4).iterrows()
                )
                st.caption(_captions)
            st.markdown('</div>', unsafe_allow_html=True)

        with ch2:
            st.markdown('<div class="dash-card"><p style="color:#f0e6d2;font-weight:600;font-size:14px;margin-bottom:0">Daily Risk Score Trend</p>', unsafe_allow_html=True)
            if "pre_failure_risk_score" in rt_sample.columns and "timestamp" in rt_sample.columns:
                ts_df = rt_sample.copy(); ts_df["date"]=pd.to_datetime(ts_df["timestamp"]).dt.date
                daily = ts_df.groupby("date").agg(mean_risk=("pre_failure_risk_score","mean"),
                    high_count=("risk_label",lambda x:(x=="HIGH").sum())).reset_index()
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=daily["date"].astype(str),y=daily["mean_risk"],mode="lines+markers",
                    name="Avg Risk",line=dict(color="#d4af37",width=2.5,shape="spline"),marker=dict(size=4,color="#d4af37")))
                fig2.add_trace(go.Bar(x=daily["date"].astype(str),y=daily["high_count"],
                    name="HIGH Count",marker_color="rgba(255,77,77,0.30)",yaxis="y2"))
                fig2.update_layout(**_bg,showlegend=True,
                    legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1,
                                font=dict(size=9,color="#8c7e5a"),bgcolor="rgba(0,0,0,0)"),
                    xaxis=dict(showgrid=False,zeroline=False,color="#544726",tickfont=dict(size=8),nticks=8),
                    yaxis=dict(showgrid=True,gridcolor=_gg,zeroline=False,color="#544726"),
                    yaxis2=dict(overlaying="y",side="right",showgrid=False,color="#544726"))
            else:
                fig2=go.Figure(); fig2.update_layout(**_bg)
            st.plotly_chart(fig2,use_container_width=True,config={"displayModeBar":False})
            st.markdown('</div>', unsafe_allow_html=True)

        with ch3:
            st.markdown('<div class="dash-card"><p style="color:#f0e6d2;font-weight:600;font-size:14px;margin-bottom:0">Availability by Strategy</p>', unsafe_allow_html=True)
            avail_r=fleet_avail_r*100; avail_a=avail.get("fleet_availability_automated",fleet_avail_r)*100; avail_p=fleet_avail_p*100
            fig3=go.Figure(go.Bar(x=["Reactive","Automated","Proactive"],y=[avail_r,avail_a,avail_p],
                marker_color=["#544726","#8c7e5a","#d4af37"],marker_line_width=0,
                text=[f"{v:.3f}%" for v in [avail_r,avail_a,avail_p]],textposition="outside",
                textfont=dict(color="#8c7e5a",size=10,family="DM Mono")))
            fig3.update_layout(**_bg,showlegend=False,bargap=0.35,
                xaxis=dict(showgrid=False,zeroline=False,color="#544726"),
                yaxis=dict(showgrid=True,gridcolor=_gg,zeroline=False,color="#544726",
                           range=[max(0,avail_r*0.999),avail_p*1.001]))
            st.plotly_chart(fig3,use_container_width=True,config={"displayModeBar":False})
            st.markdown('</div>', unsafe_allow_html=True)

    except ImportError:
        st.warning("📦 Plotly not installed — `pip install plotly`")

    st.markdown("### INCIDENT MANAGEMENT")
    tbl_col, form_col = st.columns([2.5,1])

    with tbl_col:
        st.markdown('<div class="dash-card"><p style="color:#f0e6d2;font-weight:600;font-size:14px;margin-bottom:8px;">Top Risk ATMs — Current Snapshot</p>', unsafe_allow_html=True)
        show_c = [c for c in ["atm_id","issue_type","pre_failure_risk_score","risk_label",
                               "escalation_probability","downtime_minutes","resolution_mode","incident_count"]
                  if c in atm_risk_df.columns]
        disp_df = atm_risk_df.head(10)[show_c].copy()
        if "escalation_probability" in disp_df.columns:
            disp_df["escalation_probability"]=disp_df["escalation_probability"].apply(lambda x:f"{x:.1%}")
        def _hl_r(row):
            if row.get("risk_label")=="HIGH": return ["background-color:rgba(255,77,77,0.12);color:#ff4d4d;font-weight:600"]*len(row)
            if row.get("risk_label")=="MEDIUM": return ["background-color:rgba(245,158,11,0.08)"]*len(row)
            return [""]*len(row)
        sc_max = float(atm_risk_df["pre_failure_risk_score"].max()) if "pre_failure_risk_score" in atm_risk_df.columns and len(atm_risk_df) else 100.0
        st.dataframe(disp_df.style.apply(_hl_r,axis=1),use_container_width=True,hide_index=True,height=300,
            column_config={"pre_failure_risk_score":st.column_config.ProgressColumn("Risk Score",format="%d",min_value=0,max_value=int(sc_max))})
        st.markdown('</div>', unsafe_allow_html=True)

    with form_col:
        st.markdown('<div class="dash-card"><p style="color:#f0e6d2;font-weight:600;font-size:14px;margin-bottom:8px;">Quick Feedback</p>', unsafe_allow_html=True)
        with st.form("qfb_form"):
            atm_sel = st.selectbox("Select ATM", atm_risk_df["atm_id"].head(15).tolist() if len(atm_risk_df) else ["—"])
            mr = atm_risk_df[atm_risk_df["atm_id"]==atm_sel]
            predicted = mr["issue_type"].values[0] if len(mr) else "network_failure"
            pd_disp = "Unknown" if pd.isna(predicted) else str(predicted).replace("_"," ").title()
            st.markdown(f'<div class="pg-form-card"><div class="pg-form-label">Issue Type</div><div class="pg-form-value">{pd_disp}</div></div>', unsafe_allow_html=True)
            fb_ok    = st.radio("Prediction correct?",("Correct","Incorrect"),horizontal=True)
            fb_notes = st.text_area("Notes",placeholder="…",height=68)
            if st.form_submit_button("Submit",use_container_width=True):
                save_feedback(atm_id=atm_sel,predicted_issue=str(predicted),technician_actual_issue=str(predicted),
                    action_helpful="yes" if fb_ok=="Correct" else "no",technician_notes=fb_notes,resolution_time_minutes=0)
                st.success("Feedback recorded.")
        st.markdown('</div>', unsafe_allow_html=True)

    section_label("⬇","Export")
    exp_c = [c for c in ["atm_id","location","timestamp","issue_type","downtime_minutes","complaint_count",
        "drift_signal","escalated","escalation_probability","pre_failure_risk_score","risk_label",
        "resolution_mode","in_cluster","is_cascade","atm_age_years"] if c in scored_full.columns]
    st.download_button("⬇  Download Scored Incidents (CSV)",scored_full[exp_c].to_csv(index=False),
        file_name="payguard_v2_scored.csv",mime="text/csv")


# ═══════════════════════════════════════════════════════════════════════════
#  TAB 2 — HIGH RISK
# ═══════════════════════════════════════════════════════════════════════════
with TAB_HR:
    st.markdown('<div class="pg-ctx-rt">⚡ Per-ATM aggregated view · Max risk score per ATM across recent incidents</div>', unsafe_allow_html=True)
    st.caption("ATMs with predicted escalation risk score ≥ 65. Proactive intervention recommended.")
    render_risk_panel(atm_risk_df,"HIGH","red","🔴","HIGH RISK — Proactive Intervention Required")


# ═══════════════════════════════════════════════════════════════════════════
#  TAB 3 — MEDIUM RISK
# ═══════════════════════════════════════════════════════════════════════════
with TAB_MR:
    st.markdown('<div class="pg-ctx-rt">⚡ Per-ATM aggregated view · Max risk score per ATM across recent incidents</div>', unsafe_allow_html=True)
    st.caption("ATMs with risk score 35–64. Monitor closely and prepare automated response.")
    render_risk_panel(atm_risk_df,"MEDIUM","amber","🟡","MEDIUM RISK — Monitor and Stage Response")


# ═══════════════════════════════════════════════════════════════════════════
#  TAB 4 — LOW RISK
# ═══════════════════════════════════════════════════════════════════════════
with TAB_LR:
    st.markdown('<div class="pg-ctx-rt">⚡ Per-ATM aggregated view · ATMs within normal operating parameters</div>', unsafe_allow_html=True)
    st.caption("ATMs with risk score < 35. Continue scheduled monitoring.")
    render_risk_panel(atm_risk_df,"LOW","green","🟢","LOW RISK — Normal Operations")


# ═══════════════════════════════════════════════════════════════════════════
#  TAB 5 — AUTOMATION
# ═══════════════════════════════════════════════════════════════════════════
with TAB_AUTO:
    st.markdown('<div class="pg-ctx-hist">📊 Automation analysis from historical resolution data (full dataset)</div>', unsafe_allow_html=True)

    section_label("🤖","Automation Metrics")
    am1,am2,am3,am4,am5 = st.columns(5)
    am1.metric("Auto Resolved",   f"{n_auto_resolved:,}")
    am2.metric("Auto Attempted",  f"{n_auto_attempt:,}")
    am3.metric("Manual Required", f"{n_manual:,}")
    am4.metric("Manual Saved %",  f"{pct_manual_saved:.1f}%")
    am5.metric("Avg Auto Time",   f"{avg_auto_time:.0f} min")

    am6,am7,am8,am9 = st.columns(4)
    am6.metric("Downtime Saved (Auto)", f"{downtime_saved:,.0f} min")
    am7.metric("Total Incidents",       f"{n_total_inc:,}")
    am8.metric("Avg Manual Time",       f"{avg_manual_time:.0f} min")
    am9.metric("Esc. Avoided (Pro)",    f"{esc_avoided:,}")

    try:
        import plotly.express as px
        import plotly.graph_objects as go

        a_ch1, a_ch2 = st.columns(2)
        _bg_a = dict(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                     margin=dict(l=10,r=10,t=10,b=10),font=dict(color="#8c7e5a",family="DM Mono, monospace",size=11),height=240)
        _gg_a = "rgba(212,175,55,0.08)"

        with a_ch1:
            st.markdown('<div class="dash-card"><p style="color:#f0e6d2;font-weight:600;font-size:14px;margin-bottom:0">Resolution Mode Distribution</p>', unsafe_allow_html=True)
            rm_df = _auto_df[(_auto_df["resolution_mode"] != "NONE") & (_auto_df["resolution_mode"].notna())]["resolution_mode"].value_counts().reset_index(); rm_df.columns=["mode","count"]
            fig_rm = px.pie(rm_df,names="mode",values="count",hole=0.55,
                            color_discrete_sequence=["#22c55e","#f59e0b","#ff4d4d","#8c7e5a"])
            fig_rm.update_traces(textposition="inside",textinfo="percent+label",textfont_color="#080808",textfont_size=11)
            fig_rm.update_layout(**_bg_a,showlegend=False)
            st.plotly_chart(fig_rm,use_container_width=True,config={"displayModeBar":False})
            st.markdown('</div>', unsafe_allow_html=True)

        with a_ch2:
            st.markdown('<div class="dash-card"><p style="color:#f0e6d2;font-weight:600;font-size:14px;margin-bottom:0">Avg Downtime by Resolution Mode</p>', unsafe_allow_html=True)
            _rm_filt = _auto_df[(_auto_df["resolution_mode"] != "NONE") & (_auto_df["resolution_mode"].notna())]
            rm_dt = _rm_filt.groupby("resolution_mode")["downtime_minutes"].mean().reset_index()
            rm_dt.columns = ["mode","avg_downtime"]
            mode_clr = {"AUTO_RESOLVED":"#22c55e","AUTO_ATTEMPTED":"#f59e0b","MANUAL_REQUIRED":"#ff4d4d"}
            fig_dt = go.Figure(go.Bar(
                x=rm_dt["mode"], y=rm_dt["avg_downtime"],
                marker_color=[mode_clr.get(m,"#8c7e5a") for m in rm_dt["mode"]],
                marker_line_width=0, text=rm_dt["avg_downtime"].round(1), textposition="outside",
                textfont=dict(color="#8c7e5a",size=10,family="DM Mono")))
            fig_dt.update_layout(**_bg_a,showlegend=False,bargap=0.35,
                xaxis=dict(showgrid=False,zeroline=False,color="#544726",tickfont=dict(size=9)),
                yaxis=dict(showgrid=True,gridcolor=_gg_a,zeroline=False,color="#544726",title="Avg Downtime (min)"))
            st.plotly_chart(fig_dt,use_container_width=True,config={"displayModeBar":False})
            st.markdown('</div>', unsafe_allow_html=True)

    except ImportError:
        pass

    section_label("📋","Recent Automation Log")
    _log_df   = _auto_df.sort_values("timestamp", ascending=False).head(30)
    _log_cols = [c for c in ["timestamp","atm_id","location","issue_type","resolution_mode",
                              "downtime_minutes","escalated","resolution_minutes"] if c in _log_df.columns]
    _log_disp = _log_df[_log_cols].copy()
    if "timestamp" in _log_disp.columns:
        _log_disp["timestamp"] = pd.to_datetime(_log_disp["timestamp"]).dt.strftime("%Y-%m-%d %H:%M")

    def _hl_log(row):
        rm = row.get("resolution_mode","")
        if rm == "AUTO_RESOLVED":   return ["background-color:rgba(34,197,94,0.08);color:#22c55e"]*len(row)
        if rm == "AUTO_ATTEMPTED":  return ["background-color:rgba(245,158,11,0.06)"]*len(row)
        if rm == "MANUAL_REQUIRED": return ["background-color:rgba(255,77,77,0.06)"]*len(row)
        return [""]*len(row)

    st.dataframe(_log_disp.style.apply(_hl_log,axis=1),use_container_width=True,hide_index=True,height=300)

    section_label("◈","Automatable Issue Types")
    AUTOMATABLE = {"network_failure","auth_timeout","card_declined","software_crash"}
    elig_df = _auto_df.copy()
    elig_df["automatable"] = elig_df["issue_type"].isin(AUTOMATABLE)
    elig_agg = elig_df.groupby(["issue_type","automatable"]).agg(
        count=("atm_id","count"),
        auto_resolved=("resolution_mode", lambda x:(x=="AUTO_RESOLVED").sum()),
        escalation_rate=("escalated","mean")
    ).reset_index()
    elig_agg["eligibility"] = elig_agg["automatable"].map({True:"✓ Eligible",False:"✗ Manual-only"})
    elig_agg["escalation_rate"] = elig_agg["escalation_rate"].apply(lambda x:f"{x:.1%}")
    st.dataframe(elig_agg[["issue_type","eligibility","count","auto_resolved","escalation_rate"]],
                 use_container_width=True,hide_index=True,height=240)


# ═══════════════════════════════════════════════════════════════════════════
#  TAB 6 — ROOT CAUSE
# ═══════════════════════════════════════════════════════════════════════════
with TAB_RC:
    st.markdown(f'<div class="pg-ctx-hist">📊 Historical pattern mining · {_days}-day logs · Incident rows only · Max 30,000 rows analysed</div>', unsafe_allow_html=True)
    st.caption("Repeat failures, cascade chains, systemic weak points.")

    if not rc or "error" in rc:
        st.error(f"⚠ Root cause unavailable: {rc.get('error','Unknown') if rc else 'No data'}")
    else:
        section_label("⚠","Repeat Failure ATMs")
        if not repeat_atms_df.empty:
            rc_c = [c for c in ["atm_id","location","total_incidents","escalation_count",
                "escalation_rate","dominant_issue","avg_downtime_min","recurrence_score","recommendation"]
                if c in repeat_atms_df.columns]
            disp_rc = repeat_atms_df[rc_c].head(_MAX_DF_ROWS).copy()
            if "escalation_rate" in disp_rc.columns:
                disp_rc["escalation_rate"]=disp_rc["escalation_rate"].apply(lambda x:f"{x:.1%}")
            st.dataframe(disp_rc,use_container_width=True,hide_index=True,height=280,
                column_config={"recurrence_score":st.column_config.ProgressColumn("Recurrence Score",format="%d",min_value=0,max_value=100)}
                if "recurrence_score" in disp_rc.columns else {})

            section_label("◈","Recommended Actions per Repeat ATM")
            for _,p in repeat_atms_df.head(5).iterrows():
                with st.expander(f"{p['atm_id']}  ·  {p.get('location','—')}  ·  Score {p.get('recurrence_score',0):.0f}"):
                    st.markdown(f'<div class="pg-action-box">⚡&nbsp; {p.get("recommendation","—")}</div>',unsafe_allow_html=True)
                    cd=st.columns(4)
                    cd[0].metric("Incidents",       int(p.get("total_incidents",0)))
                    cd[1].metric("Escalation Rate", f"{float(p.get('escalation_rate',0)):.1%}" if isinstance(p.get("escalation_rate"),float) else str(p.get("escalation_rate","—")))
                    cd[2].metric("Avg Downtime",    f"{float(p.get('avg_downtime_min',0)):.0f} min")
                    cd[3].metric("Dominant Issue",  str(p.get("dominant_issue","—")).replace("_"," ").title())
        else:
            st.markdown('<div class="pg-empty-state"><span class="pg-empty-icon">✓</span>No repeat ATM patterns detected.</div>',unsafe_allow_html=True)

        section_label("🔗","Cascade Failure Chains")
        chains=rc.get("failure_chains",[])
        if chains:
            cr=[{"Chain ID":c.get("chain_id",""),"ATM":c.get("atm_id",""),
                 "Root Issue":c.get("root_issue","").replace("_"," ").title(),
                 "Cascades To":", ".join(c.get("cascade_issues",[])),
                 "Chain Length":c.get("chain_length",1),
                 "Total Downtime":f"{c.get('total_downtime_min',0):.0f} min",
                 "Escalated":"🚨 Yes" if c.get("escalated") else "✓ No"}
                for c in chains[:_MAX_DF_ROWS]]
            st.dataframe(pd.DataFrame(cr),use_container_width=True,hide_index=True,height=280)
        else:
            st.caption("No cascade chains detected.")

        section_label("📌","Systemic Weak Points")
        wps=rc.get("systemic_weak_points",[])
        if wps:
            wr=[{"Dimension":w.get("dimension","").title(),"Value":w.get("value",""),
                 "Incidents":w.get("incident_count",0),"Esc. Rate":f"{float(w.get('escalation_rate',0)):.1%}",
                 "Avg Downtime":f"{float(w.get('avg_downtime_min',0)):.0f} min","Risk Level":w.get("risk_level","LOW"),
                 "Detail":w.get("detail","")} for w in wps[:_MAX_DF_ROWS]]
            wd=pd.DataFrame(wr)
            def _hl_wp(row):
                if row.get("Risk Level")=="HIGH": return ["background-color:rgba(255,77,77,0.10);color:#ff4d4d;font-weight:600"]*len(row)
                if row.get("Risk Level")=="MEDIUM": return ["background-color:rgba(245,158,11,0.08)"]*len(row)
                return [""]*len(row)
            st.dataframe(wd.style.apply(_hl_wp,axis=1),use_container_width=True,hide_index=True,height=320)

        section_label("⚡","Systemic Cluster Events (Multi-ATM)")
        sc_list=[c for c in rc.get("issue_clusters",[]) if c.get("is_systemic")]
        if sc_list:
            sr=[{"Cluster ID":cl.get("cluster_id",""),"Issue":cl.get("issue_type","").replace("_"," ").title(),
                 "Start":cl.get("start_time","")[:16],"ATMs Affected":cl.get("atm_count",0),
                 "Incidents":cl.get("incident_count",0),"Total Downtime":f"{cl.get('total_downtime_min',0):.0f} min",
                 "Regions":", ".join(cl.get("affected_regions",[])),"Probable Cause":cl.get("probable_cause","")}
                for cl in sc_list[:_MAX_DF_ROWS]]
            st.dataframe(pd.DataFrame(sr),use_container_width=True,hide_index=True,height=280)
        else:
            st.caption("No systemic multi-ATM clusters detected.")


# ═══════════════════════════════════════════════════════════════════════════
#  TAB 7 — AVAILABILITY
# ═══════════════════════════════════════════════════════════════════════════
with TAB_AV:
    st.markdown('<div class="pg-ctx-hist">📊 Computed from full historical dataset · Three resolution strategy comparison</div>',unsafe_allow_html=True)
    st.caption("Reactive, Automated, and Proactive Prevention strategies.")
    section_label("📈","Fleet Availability by Resolution Strategy")
    av1,av2,av3=st.columns(3)
    av1.metric("Reactive Availability",  f"{avail.get('fleet_availability_reactive',0):.4%}","Baseline")
    av2.metric("Automated Availability", f"{avail.get('fleet_availability_automated',0):.4%}",f"+{avail.get('fleet_improvement_auto_pct',0):.3f}pp")
    av3.metric("Proactive Availability", f"{fleet_avail_p:.4%}",f"+{fleet_improve:.3f}pp")
    st.markdown("<div style='height:6px'></div>",unsafe_allow_html=True)
    ap1,ap2,ap3,ap4=st.columns(4)
    ap1.metric("Esc. Avoided (Auto)",       f"{avail.get('escalations_avoided_automated',0):,}")
    ap2.metric("Esc. Avoided (Proactive)",  f"{esc_avoided:,}")
    ap3.metric("Downtime Prevented (Auto)", f"{avail.get('total_downtime_prevented_auto_min',0):,.0f} min")
    ap4.metric("Downtime Prevented (Pro)",  f"{dt_prevented:,.0f} min")

    section_label("📉","Daily Availability Trend — All Strategies")
    trends=avail.get("daily_trends",{})
    if trends and trends.get("dates"):
        try:
            import plotly.graph_objects as go
            tf=go.Figure()
            for label,col,lw in [("Reactive","#544726",1.5),("Automated","#8c7e5a",2.0),("Proactive","#d4af37",2.5)]:
                tf.add_trace(go.Scatter(x=trends["dates"],y=[v*100 for v in trends.get(label.lower(),[])],
                    mode="lines",name=label,line=dict(color=col,width=lw,shape="spline")))
            tf.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10,r=10,t=10,b=10),font=dict(color="#8c7e5a",family="DM Mono",size=11),height=260,showlegend=True,
                legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1,font=dict(size=10,color="#8c7e5a"),bgcolor="rgba(0,0,0,0)"),
                xaxis=dict(showgrid=False,zeroline=False,color="#544726",nticks=10),
                yaxis=dict(showgrid=True,gridcolor="rgba(212,175,55,0.08)",zeroline=False,color="#544726",title="Availability %"))
            st.plotly_chart(tf,use_container_width=True,config={"displayModeBar":False})
        except ImportError:
            pass

    section_label("◈","Per-ATM Availability Breakdown")
    if not avail_table.empty:
        st.dataframe(avail_table.head(_MAX_DF_ROWS),use_container_width=True,hide_index=True,height=350)
        st.download_button("⬇  Download Availability Report (CSV)",avail_table.to_csv(index=False),
            file_name="payguard_v2_availability.csv",mime="text/csv")
    else:
        st.caption("Availability table unavailable.")


# ═══════════════════════════════════════════════════════════════════════════
#  TAB 8 — FEEDBACK
# ═══════════════════════════════════════════════════════════════════════════
with TAB_FB:
    section_label("🔁","Technician Feedback Loop")
    st.caption("Submit corrections to improve model accuracy. Written to data/feedback.csv.")
    ISSUE_TYPES_ALL=["network_failure","card_declined","hardware_fault","cash_out","auth_timeout","software_crash"]

    if len(atm_risk_df)==0:
        st.markdown('<div class="pg-empty-state"><span class="pg-empty-icon">📋</span>No scored incidents available.</div>',unsafe_allow_html=True)
    else:
        fb_cands = atm_risk_df[atm_risk_df["risk_label"].isin(["HIGH","MEDIUM"])].copy()
        if fb_cands.empty: fb_cands = atm_risk_df.copy()
        fb1,fb2=st.columns(2)
        with fb1:
            section_label("◈","Select Incident")
            fb_atm = st.selectbox("ATM ID",fb_cands["atm_id"].head(30).tolist(),key="fb_atm2")
            fm = fb_cands[fb_cands["atm_id"]==fb_atm]
            if len(fm):
                m=fm.iloc[0]; rs=float(m.get("pre_failure_risk_score",0)); ep=float(m.get("escalation_probability",0)); rl=str(m.get("risk_label","LOW"))
                st.markdown(f"""<div class="pg-form-card">
                  <div class="pg-form-label">Issue Type</div><div class="pg-form-value">{str(m.get('issue_type','—')).replace('_',' ').title()}</div>
                  <div class="pg-form-label">Risk Score</div><div class="pg-form-value">{rs:.1f}/100 &nbsp; {risk_pill_html(rl)}</div>
                  <div class="pg-form-label">Escalation Probability</div><div class="pg-form-value">{ep:.1%}</div>
                  <div class="pg-form-label">Drift Signal</div><div class="pg-form-value">{float(m.get('drift_signal',0)):.1f}</div>
                </div>""",unsafe_allow_html=True)
        with fb2:
            if len(fm):
                m=fm.iloc[0]; ci=str(m.get("issue_type","network_failure"))
                section_label("◈","Technician Assessment")
                fb_act = st.selectbox("Actual Issue Diagnosed",ISSUE_TYPES_ALL,
                    index=ISSUE_TYPES_ALL.index(ci) if ci in ISSUE_TYPES_ALL else 0,key="fb_act2")
                fb_rk  = st.radio("Was risk prediction appropriate?",
                    ["Correct — escalated as predicted","Over-predicted","Under-predicted"],horizontal=False,key="fb_rk2")
                fb_rt  = st.number_input("Actual Resolution Time (min)",0,600,30,key="fb_rt2")
                fb_nt  = st.text_area("Notes (optional)",key="fb_nt2",height=80)
                if st.button("✅  Submit Feedback",type="primary"):
                    save_feedback(atm_id=fb_atm,predicted_issue=ci,technician_actual_issue=fb_act,
                        action_helpful={"Correct — escalated as predicted":"yes","Over-predicted":"partial","Under-predicted":"no"}.get(fb_rk,"partial"),
                        technician_notes=fb_nt,resolution_time_minutes=fb_rt)
                    st.success("Feedback recorded successfully.")
                    st.rerun()

    fb_df=load_feedback()
    if not fb_df.empty:
        section_label("◈","Feedback History (last 20)")
        st.dataframe(fb_df.tail(20),use_container_width=True,hide_index=True,height=280)