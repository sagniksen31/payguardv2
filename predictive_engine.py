"""
predictive_engine.py
====================
Layer 3 - Predictive Engine  (v2.3 - XGBoost + LightGBM + CatBoost ensemble)
PayGuard Predictive Intelligence Backend

Architecture change from v2.2  (single XGBoost + Calibration)
==============================================================

ENSEMBLE
  Three independently trained, isotonic-calibrated base models:
    1. XGBoost   -- GPU via tree_method="hist", device="cuda"; silent CPU fallback
    2. LightGBM  -- GPU via device="gpu"; silent CPU fallback
    3. CatBoost  -- GPU via task_type="GPU"; silent CPU fallback
  Final blended probability:
    p = 0.40 * p_xgb  +  0.35 * p_lgbm  +  0.25 * p_cat
  Weights reflect expected relative Average-Precision contribution on tabular
  imbalanced data (XGBoost strongest, CatBoost most conservative).
  Each base model is wrapped individually in CalibratedClassifierCV
  (method="isotonic", cv=3) so probabilities are well-calibrated before blend.

CLASS IMBALANCE
  XGBoost  : scale_pos_weight = n_neg / n_pos  (explicit ratio)
  LightGBM : class_weight="balanced"           (LGBM computes per fold)
  CatBoost : auto_class_weights="Balanced"     (CatBoost handles internally)
  All computed / applied on the training split only.

GPU HANDLING
  Each model has its own independent probe function (_probe_xgb_gpu,
  _probe_lgbm_gpu, _probe_cat_gpu).  A failed probe for one library does
  not affect the others.  All probes are silent -- no warnings, no raises.
  Results are cached per process in module-level booleans.

TEMPORAL SPLIT
  Training : first 80% of chronologically sorted rows
  Test     : most recent 20%
  No random shuffle -- avoids look-ahead bias on hourly time-series data
  where future rows must never influence evaluation of earlier rows.

FEATURE SELECTION  (two-pass training strategy)
  Pass 1: train all three models on the full feature set.
  Compute ensemble mean importance = weighted average of each model's
  normalised feature_importances_.
  Drop any feature with ensemble mean importance < IMPORTANCE_THRESHOLD (0.002).
  Pass 2: retrain all three models on the reduced feature set only.
  If no features are dropped, pass-1 models are reused directly.

EVALUATION (temporal test set only)
  ROC-AUC, Average Precision, Brier Score
  Per-threshold breakdown at 0.30 and 0.50 (P / R / F1)
  Per-model individual AUC and AP for diagnostics
  Top-15 features by ensemble mean importance

UNCHANGED  (zero breaking changes to intelligence_pipeline.py)
  MODEL_PATH / MODEL_DIR
  RISK_HIGH_THRESHOLD / RISK_MEDIUM_THRESHOLD / ISSUE_SEVERITY
  risk_label logic (LOW / MEDIUM / HIGH thresholds and labels)
  score_batch() -- same signature, same return columns
  load_model()  -- same signature
  ensure_model_trained() -- same signature
  train_model() -- same signature (use_optuna silently ignored in v2.3;
    reserved for future per-model HPO; optuna_n_trials likewise ignored)
"""

from __future__ import annotations

import os
import pickle
import warnings
import numpy as np
import pandas as pd

from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    roc_auc_score,
    classification_report,
    average_precision_score,
    brier_score_loss,
    precision_score,
    recall_score,
    f1_score,
)

from feature_engineering import get_ml_feature_columns


# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------
MODEL_DIR  = "model"
MODEL_PATH = os.path.join(MODEL_DIR, "predictive_model.pkl")

RISK_HIGH_THRESHOLD   = 65
RISK_MEDIUM_THRESHOLD = 35

# Ensemble blending weights: (XGB, LGBM, CatBoost)
ENSEMBLE_WEIGHTS: tuple[float, float, float] = (0.40, 0.35, 0.25)

# Feature selection: drop features with ensemble mean importance below this
IMPORTANCE_THRESHOLD: float = 0.002

# Calibration inner CV folds applied to each base model independently
CALIB_CV_FOLDS: int = 3

ISSUE_SEVERITY: dict[str, float] = {
    "hardware_fault":  1.40,
    "cash_out":        1.30,
    "network_failure": 1.15,
    "software_crash":  1.10,
    "auth_timeout":    1.00,
    "card_declined":   0.90,
}


# ---------------------------------------------------------------------------
# GPU probes  --  one per library, independent, cached per process
# ---------------------------------------------------------------------------
_XGB_GPU:  bool | None = None
_LGBM_GPU: bool | None = None
_CAT_GPU:  bool | None = None


def _probe_xgb_gpu() -> bool:
    """Probe CUDA availability for XGBoost.  Silent on failure."""
    try:
        import xgboost as xgb
        m = xgb.XGBClassifier(
            n_estimators=1, max_depth=1,
            tree_method="hist", device="cuda",
            verbosity=0,
        )
        m.fit(np.zeros((4, 2)), np.array([0, 0, 1, 1]))
        return True
    except Exception:
        return False


def _probe_lgbm_gpu() -> bool:
    """Probe GPU availability for LightGBM.  Silent on failure."""
    try:
        import lightgbm as lgb
        m = lgb.LGBMClassifier(n_estimators=1, device="gpu", verbose=-1)
        m.fit(np.zeros((4, 2)), np.array([0, 0, 1, 1]))
        return True
    except Exception:
        return False


def _probe_cat_gpu() -> bool:
    """Probe GPU availability for CatBoost.  Silent on failure."""
    try:
        from catboost import CatBoostClassifier
        m = CatBoostClassifier(iterations=1, task_type="GPU", verbose=False)
        m.fit(np.zeros((4, 2)), np.array([0, 0, 1, 1]))
        return True
    except Exception:
        return False


def _xgb_device_kwargs() -> dict:
    global _XGB_GPU
    if _XGB_GPU is None:
        _XGB_GPU = _probe_xgb_gpu()
        print(f"[PredictiveEngine] XGBoost  : {'GPU (cuda)' if _XGB_GPU else 'CPU'}")
    return {"tree_method": "hist", "device": "cuda" if _XGB_GPU else "cpu"}


def _lgbm_device_kwargs() -> dict:
    global _LGBM_GPU
    if _LGBM_GPU is None:
        _LGBM_GPU = _probe_lgbm_gpu()
        print(f"[PredictiveEngine] LightGBM : {'GPU' if _LGBM_GPU else 'CPU'}")
    return {"device": "gpu"} if _LGBM_GPU else {}


def _cat_device_kwargs() -> dict:
    global _CAT_GPU
    if _CAT_GPU is None:
        _CAT_GPU = _probe_cat_gpu()
        print(f"[PredictiveEngine] CatBoost : {'GPU' if _CAT_GPU else 'CPU'}")
    return {"task_type": "GPU"} if _CAT_GPU else {"task_type": "CPU"}


# ---------------------------------------------------------------------------
# Class-imbalance helpers
# ---------------------------------------------------------------------------
def _neg_pos_ratio(y: np.ndarray) -> float:
    """
    n_neg / n_pos, guarded against divide-by-zero.
    Used as scale_pos_weight for XGBoost.
    Always computed on the training split only.
    """
    n_pos = max(int(y.sum()), 1)
    n_neg = int(len(y) - n_pos)
    return round(n_neg / n_pos, 4)


# ---------------------------------------------------------------------------
# Base model constructors
# ---------------------------------------------------------------------------
def _build_xgb(spw: float, seed: int | None):
    """
    XGBClassifier with production hyperparams, GPU device, and imbalance weight.
    eval_metric="aucpr" directs boosting round selection towards PR-AUC.
    """
    import xgboost as xgb
    return xgb.XGBClassifier(
        n_estimators=800,
        max_depth=6,
        learning_rate=0.03,
        subsample=0.85,
        colsample_bytree=0.80,
        reg_lambda=1.5,
        reg_alpha=0.5,
        min_child_weight=3,
        gamma=0.1,
        eval_metric="aucpr",
        verbosity=0,
        n_jobs=-1,
        scale_pos_weight=spw,
        random_state=seed if seed is not None else 0,
        use_label_encoder=False,
        **_xgb_device_kwargs(),
    )


def _build_lgbm(seed: int | None):
    """
    LGBMClassifier with production hyperparams, GPU device, and balanced weights.
    num_leaves=63 approximates max_depth=6 (2^6 - 1) for the leaf-wise grower.
    subsample_freq=1 activates row subsampling every boosting round.
    """
    import lightgbm as lgb
    return lgb.LGBMClassifier(
        n_estimators=800,
        max_depth=-1,
        num_leaves=63,
        learning_rate=0.03,
        subsample=0.85,
        subsample_freq=1,
        colsample_bytree=0.80,
        reg_lambda=1.5,
        reg_alpha=0.5,
        min_child_samples=20,
        class_weight="balanced",
        metric="average_precision",
        verbose=-1,
        n_jobs=-1,
        random_state=seed if seed is not None else 0,
        **_lgbm_device_kwargs(),
    )


def _build_catboost(seed: int | None):
    """
    CatBoostClassifier with production hyperparams, GPU device, and balanced weights.
    colsample_bylevel is CatBoost's equivalent of colsample_bytree.
    l2_leaf_reg is CatBoost's L2 regularisation (analogous to reg_lambda).
    """
    from catboost import CatBoostClassifier
    return CatBoostClassifier(
        iterations=800,
        depth=6,
        learning_rate=0.03,
        subsample=0.85,
        colsample_bylevel=0.80,
        l2_leaf_reg=3.0,
        min_data_in_leaf=20,
        auto_class_weights="Balanced",
        eval_metric="PRAUC",
        random_seed=seed if seed is not None else 0,
        verbose=False,
        **_cat_device_kwargs(),
    )


# ---------------------------------------------------------------------------
# Calibration wrapper
# ---------------------------------------------------------------------------
def _calibrated(base_model) -> CalibratedClassifierCV:
    """Wrap any sklearn-compatible estimator in isotonic calibration (cv=3)."""
    return CalibratedClassifierCV(base_model, method="isotonic", cv=CALIB_CV_FOLDS)


# ---------------------------------------------------------------------------
# Feature importance extraction  (normalised, unified interface)
# ---------------------------------------------------------------------------
def _extract_importances(
    cal_model: CalibratedClassifierCV,
    feature_names: list[str],
    model_label: str,
) -> dict[str, float]:
    """
    Extract normalised feature importances from a CalibratedClassifierCV.

    Averages feature_importances_ across all CALIB_CV_FOLDS internal
    estimators, then normalises so values sum to 1.0.

    Returns {feature_name: mean_normalised_importance}.
    Returns {} if extraction fails for any reason.
    """
    rows: list[np.ndarray] = []
    try:
        for cc in cal_model.calibrated_classifiers_:
            est = cc.estimator
            if hasattr(est, "feature_importances_"):
                rows.append(np.asarray(est.feature_importances_, dtype=float))
    except Exception as exc:
        print(f"[PredictiveEngine] {model_label}: importance extraction failed: {exc}")
        return {}

    if not rows:
        return {}

    mean_imp = np.mean(np.vstack(rows), axis=0)
    total = float(mean_imp.sum())
    if total > 0:
        mean_imp = mean_imp / total

    return dict(zip(feature_names, mean_imp.tolist()))


# ---------------------------------------------------------------------------
# Feature selection
# ---------------------------------------------------------------------------
def _select_features(
    ensemble_fi: dict[str, float],
    all_features: list[str],
    threshold: float = IMPORTANCE_THRESHOLD,
) -> list[str]:
    """
    Return features whose ensemble mean importance >= threshold.

    Safety floor: always retains at least 10 features even if all fall below
    threshold, selecting the top-10 by importance to prevent degenerate models.

    Preserves the original order of all_features in the returned list.
    """
    above = [f for f in all_features if ensemble_fi.get(f, 0.0) >= threshold]

    if len(above) < 10:
        ranked  = sorted(all_features, key=lambda f: ensemble_fi.get(f, 0.0), reverse=True)
        above   = ranked[:max(10, len(above))]

    dropped = len(all_features) - len(above)
    if dropped > 0:
        print(
            f"[PredictiveEngine] Feature selection: dropped {dropped} features "
            f"(importance < {threshold}) | {len(above)} retained"
        )
    else:
        print(
            f"[PredictiveEngine] Feature selection: "
            f"all {len(all_features)} features retained (none below threshold)"
        )

    # Preserve original column order
    above_set = set(above)
    return [f for f in all_features if f in above_set]


# ---------------------------------------------------------------------------
# Single-pass ensemble training helper
# ---------------------------------------------------------------------------
def _train_one_pass(
    X_train: np.ndarray,
    y_train: np.ndarray,
    feature_names: list[str],
    seed: int | None,
    pass_label: str,
) -> tuple[
    CalibratedClassifierCV,
    CalibratedClassifierCV,
    CalibratedClassifierCV,
    dict[str, float],
]:
    """
    Train XGBoost, LightGBM, CatBoost; calibrate each; extract ensemble FI.

    Returns (cal_xgb, cal_lgbm, cal_cat, ensemble_feature_importances).
    ensemble_feature_importances is the ENSEMBLE_WEIGHTS-weighted mean of
    the three models' normalised importances.
    """
    spw = _neg_pos_ratio(y_train)

    # XGBoost
    print(f"[PredictiveEngine] [{pass_label}] Training XGBoost ...")
    cal_xgb = _calibrated(_build_xgb(spw, seed))
    cal_xgb.fit(X_train, y_train)

    # LightGBM  (suppress internal convergence warnings from LGBM)
    print(f"[PredictiveEngine] [{pass_label}] Training LightGBM ...")
    cal_lgbm = _calibrated(_build_lgbm(seed))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cal_lgbm.fit(X_train, y_train)

    # CatBoost
    print(f"[PredictiveEngine] [{pass_label}] Training CatBoost ...")
    cal_cat = _calibrated(_build_catboost(seed))
    cal_cat.fit(X_train, y_train)

    # Feature importances per model
    fi_xgb  = _extract_importances(cal_xgb,  feature_names, "XGBoost")
    fi_lgbm = _extract_importances(cal_lgbm, feature_names, "LightGBM")
    fi_cat  = _extract_importances(cal_cat,  feature_names, "CatBoost")

    w_xgb, w_lgbm, w_cat = ENSEMBLE_WEIGHTS
    ensemble_fi: dict[str, float] = {
        f: (
            w_xgb  * fi_xgb.get(f,  0.0)
            + w_lgbm * fi_lgbm.get(f, 0.0)
            + w_cat  * fi_cat.get(f,  0.0)
        )
        for f in feature_names
    }

    return cal_xgb, cal_lgbm, cal_cat, ensemble_fi


# ---------------------------------------------------------------------------
# Main training entry-point
# ---------------------------------------------------------------------------
def train_model(
    df_features: pd.DataFrame,
    target_col: str = "will_escalate_next_3h",
    random_state: int | None = 42,
    test_size: float = 0.20,
    save: bool = True,
    use_optuna: bool = False,      # reserved for future HPO; silently ignored
    optuna_n_trials: int = 35,     # reserved; silently ignored
) -> dict:
    """
    Train the three-model ensemble with two-pass feature selection.

    Pass 1: train XGB + LGBM + CatBoost on all available features.
    Select: drop features with ensemble mean importance < IMPORTANCE_THRESHOLD.
    Pass 2: retrain all three models on the reduced feature set.
            (Skipped entirely if no features are dropped.)

    Args:
        df_features    : Feature-engineered DataFrame from feature_engineering.py.
        target_col     : Binary label column name.
        random_state   : RNG seed (42 = deterministic, None = live).
        test_size      : Fraction held out as chronologically latest rows.
        save           : Persist artifact to MODEL_PATH.
        use_optuna     : Reserved for future HPO; ignored in v2.3.
        optuna_n_trials: Reserved; ignored in v2.3.

    Returns dict with keys:
        "model"            -> {"xgb": cal_xgb, "lgbm": cal_lgbm, "cat": cal_cat}
        "feature_cols"     -> list[str]  (final post-selection feature names)
        "metrics"          -> dict  (roc_auc, avg_precision, brier_score, ...)
        "ensemble_weights" -> tuple (0.40, 0.35, 0.25)
    """
    # ------------------------------------------------------------------
    # 1. Prepare features and labels
    # ------------------------------------------------------------------
    all_feat_cols = get_ml_feature_columns()
    available     = [c for c in all_feat_cols if c in df_features.columns]
    missing       = set(all_feat_cols) - set(available)
    if missing:
        n, shown = len(missing), sorted(missing)[:8]
        print(
            f"[PredictiveEngine] WARNING: {n} missing feature(s): "
            f"{shown}{'...' if n > 8 else ''}"
        )

    X_all = df_features[available].fillna(0).values.astype(np.float32)
    y_all = df_features[target_col].astype(int).values

    # ------------------------------------------------------------------
    # 2. Temporal split -- no random shuffle
    # ------------------------------------------------------------------
    split_idx        = int(len(X_all) * (1.0 - test_size))
    X_train, X_test  = X_all[:split_idx], X_all[split_idx:]
    y_train, y_test  = y_all[:split_idx], y_all[split_idx:]

    print(
        f"[PredictiveEngine] Dataset   : {len(X_all):,} rows | "
        f"positive rate = {y_all.mean():.2%}\n"
        f"[PredictiveEngine] Split     : {len(X_train):,} train / "
        f"{len(X_test):,} test  (temporal, no shuffle)\n"
        f"[PredictiveEngine] Features  : {len(available)} available"
    )

    # ------------------------------------------------------------------
    # 3. Pass 1: train on full feature set
    # ------------------------------------------------------------------
    print("[PredictiveEngine] === Pass 1: full feature set ===")
    cal_xgb1, cal_lgbm1, cal_cat1, fi_pass1 = _train_one_pass(
        X_train, y_train, available, random_state, "pass-1"
    )

    # ------------------------------------------------------------------
    # 4. Feature selection
    # ------------------------------------------------------------------
    final_feats   = _select_features(fi_pass1, available, IMPORTANCE_THRESHOLD)
    feats_reduced = len(final_feats) < len(available)

    # ------------------------------------------------------------------
    # 5. Pass 2: retrain on reduced set (or reuse pass-1 if no reduction)
    # ------------------------------------------------------------------
    if feats_reduced:
        feat_idx     = [available.index(f) for f in final_feats]
        X_train_sel  = X_train[:, feat_idx]
        X_test_sel   = X_test[:,  feat_idx]

        print(f"[PredictiveEngine] === Pass 2: {len(final_feats)} features ===")
        cal_xgb, cal_lgbm, cal_cat, fi_final = _train_one_pass(
            X_train_sel, y_train, final_feats, random_state, "pass-2"
        )
    else:
        print("[PredictiveEngine] No features dropped -- reusing pass-1 models.")
        X_test_sel = X_test
        cal_xgb, cal_lgbm, cal_cat = cal_xgb1, cal_lgbm1, cal_cat1
        fi_final = fi_pass1

    # ------------------------------------------------------------------
    # 6. Evaluation on temporal test set
    # ------------------------------------------------------------------
    w_xgb, w_lgbm, w_cat = ENSEMBLE_WEIGHTS
    p_xgb  = cal_xgb.predict_proba(X_test_sel)[:, 1]
    p_lgbm = cal_lgbm.predict_proba(X_test_sel)[:, 1]
    p_cat  = cal_cat.predict_proba(X_test_sel)[:, 1]

    y_prob  = w_xgb * p_xgb + w_lgbm * p_lgbm + w_cat * p_cat
    roc_auc = roc_auc_score(y_test, y_prob)
    avg_pr  = average_precision_score(y_test, y_prob)
    brier   = brier_score_loss(y_test, y_prob)

    print(
        f"[PredictiveEngine] Ensemble ROC-AUC       : {roc_auc:.5f}\n"
        f"[PredictiveEngine] Ensemble Avg Precision : {avg_pr:.5f}\n"
        f"[PredictiveEngine] Ensemble Brier Score   : {brier:.5f}"
    )

    for thresh, tlabel in [(0.30, "@0.30"), (0.50, "@0.50")]:
        yp_t = (y_prob >= thresh).astype(int)
        p_ = precision_score(y_test, yp_t, zero_division=0)
        r_ = recall_score(y_test,    yp_t, zero_division=0)
        f_ = f1_score(y_test,        yp_t, zero_division=0)
        print(f"[PredictiveEngine]   thresh{tlabel}  P={p_:.4f}  R={r_:.4f}  F1={f_:.4f}")

    for mname, probs_i in [("XGBoost", p_xgb), ("LightGBM", p_lgbm), ("CatBoost", p_cat)]:
        auc_i = roc_auc_score(y_test, probs_i)
        ap_i  = average_precision_score(y_test, probs_i)
        print(f"[PredictiveEngine]   {mname:10s}  AUC={auc_i:.5f}  AP={ap_i:.5f}")

    top15 = sorted(fi_final.items(), key=lambda kv: kv[1], reverse=True)[:15]
    print("[PredictiveEngine] Top-15 features (ensemble mean importance):")
    for fname, fval in top15:
        print(f"    {fname:<44s}  {fval:.5f}")

    # ------------------------------------------------------------------
    # 7. Build artifact and persist
    # ------------------------------------------------------------------
    y_pred  = (y_prob >= 0.50).astype(int)
    metrics = {
        "roc_auc":               round(roc_auc, 5),
        "avg_precision":         round(avg_pr, 5),
        "brier_score":           round(brier, 5),
        "test_samples":          int(len(y_test)),
        "positive_rate":         round(float(y_test.mean()), 5),
        "feature_importance":    dict(
            sorted(fi_final.items(), key=lambda kv: kv[1], reverse=True)
        ),
        "ensemble_weights":      ENSEMBLE_WEIGHTS,
        "n_features_pass1":      len(available),
        "n_features_final":      len(final_feats),
        "classification_report": classification_report(y_test, y_pred, output_dict=True),
    }

    artifact = {
        "model": {
            "xgb":  cal_xgb,
            "lgbm": cal_lgbm,
            "cat":  cal_cat,
        },
        "feature_cols":     final_feats,
        "metrics":          metrics,
        "ensemble_weights": ENSEMBLE_WEIGHTS,
    }

    if save:
        os.makedirs(MODEL_DIR, exist_ok=True)
        with open(MODEL_PATH, "wb") as fh:
            pickle.dump(artifact, fh)
        print(f"[PredictiveEngine] Ensemble artifact saved -> {MODEL_PATH}")

    return artifact


# ---------------------------------------------------------------------------
# Persistence helpers  (interface unchanged from v2.2)
# ---------------------------------------------------------------------------
def load_model() -> dict | None:
    """Load persisted artifact from disk. Returns None if not found."""
    if not os.path.exists(MODEL_PATH):
        return None
    with open(MODEL_PATH, "rb") as fh:
        return pickle.load(fh)


def ensure_model_trained(
    df_features: pd.DataFrame | None = None,
    random_state: int | None = 42,
    force_retrain: bool = False,
    use_optuna: bool = False,
) -> dict:
    """
    Guarantee a trained ensemble artifact is available.
    Loads from disk when present and force_retrain=False; otherwise trains.
    """
    if not force_retrain and os.path.exists(MODEL_PATH):
        art = load_model()
        print("[PredictiveEngine] Loaded existing ensemble artifact from disk.")
        return art
    if df_features is None:
        raise ValueError(
            "[PredictiveEngine] df_features required for training but not provided."
        )
    print("[PredictiveEngine] Training new ensemble model ...")
    return train_model(df_features, random_state=random_state)


# ---------------------------------------------------------------------------
# Vectorised batch scoring  (interface UNCHANGED from v2.2)
# ---------------------------------------------------------------------------
def score_batch(
    df_features: pd.DataFrame,
    artifact: dict | None = None,
) -> pd.DataFrame:
    """
    Score a feature-engineered batch using the three-model ensemble.

    Fully vectorised -- no per-row Python loops.  Scales to 150,000+ rows.
    Interface unchanged from v2.1 / v2.2: same args, same return columns.

    artifact["model"] must be a dict with keys "xgb", "lgbm", "cat".
    Any missing key triggers a warning and that model is excluded from the
    blend (remaining weights are renormalised automatically).

    Returns df_features with three new columns appended:
        escalation_probability  float  0-1   (ensemble blended probability)
        pre_failure_risk_score  float  0-100 (calibrated risk score)
        risk_label              str    LOW / MEDIUM / HIGH
    """
    if artifact is None:
        artifact = load_model()
    if artifact is None:
        raise RuntimeError(
            "[PredictiveEngine] No trained model found. Run train_model() first."
        )

    models_dict  = artifact["model"]
    feature_cols = artifact["feature_cols"]
    weights      = artifact.get("ensemble_weights", ENSEMBLE_WEIGHTS)

    available = [c for c in feature_cols if c in df_features.columns]

    # --- FIXED: keep as named DataFrame so LightGBM doesn't raise UserWarning
    # about missing feature names (it was fitted with a named DataFrame).
    X_df = df_features[available].fillna(0).astype(np.float32)

    # Collect per-model probabilities; skip missing models gracefully
    prob_arrays: list[np.ndarray] = []
    weights_used: list[float]     = []

    for key, w in zip(("xgb", "lgbm", "cat"), weights):
        m = models_dict.get(key)
        if m is None:
            print(f"[PredictiveEngine] WARNING: model '{key}' absent in artifact -- skipped.")
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            prob_arrays.append(m.predict_proba(X_df)[:, 1])
        weights_used.append(w)

    if not prob_arrays:
        raise RuntimeError("[PredictiveEngine] No valid base models found in artifact.")

    total_w = sum(weights_used)
    probs   = sum((w / total_w) * p for w, p in zip(weights_used, prob_arrays))

    # ------------------------------------------------------------------
    # Vectorised risk score formula  (unchanged from v2.2, extended for v2.3)
    # ------------------------------------------------------------------
    def _col(name: str, default: float = 0.0) -> np.ndarray:
        if name in df_features.columns:
            return df_features[name].fillna(default).values.astype(float)
        return np.full(len(df_features), default, dtype=float)

    issue_types  = (
        df_features["issue_type"].values
        if "issue_type" in df_features.columns
        else np.full(len(df_features), "auth_timeout")
    )
    severity_arr = np.array([ISSUE_SEVERITY.get(str(it), 1.0) for it in issue_types])

    drift_signals  = _col("drift_signal")
    downtimes      = _col("downtime_minutes")
    complaints     = _col("complaint_count")

    # Prefer failure_pressure (v2.3); fall back to pressure_index (v2.2 compat)
    failure_press = _col("failure_pressure")
    pressure_idx  = _col("pressure_index")
    composite     = np.where(failure_press > 0, failure_press, pressure_idx)

    base          = probs * 100.0
    drift_boost   = drift_signals * 15.0 / 100.0
    pressure_raw  = np.log1p(downtimes + complaints)
    pressure_norm = np.minimum(pressure_raw / 10.0, 8.0)
    # Composite pressure index: up to +3 bonus points
    cp_boost      = np.minimum(composite / 100.0 * 3.0, 3.0)

    scores = np.clip(
        base * severity_arr + drift_boost + pressure_norm + cp_boost,
        0.0, 100.0,
    )
    scores = np.round(scores, 2)

    labels = np.where(
        scores >= RISK_HIGH_THRESHOLD,   "HIGH",
        np.where(scores >= RISK_MEDIUM_THRESHOLD, "MEDIUM", "LOW")
    )

    out = df_features.copy()
    out["escalation_probability"] = np.round(probs, 5)
    out["pre_failure_risk_score"] = scores
    out["risk_label"]             = labels

    counts = pd.Series(labels).value_counts().to_dict()
    print(f"[PredictiveEngine] Scored {len(out):,} records. Risk distribution: {counts}")
    return out


# ---------------------------------------------------------------------------
# --- ADDED: score_single — instant single-row live prediction (<100ms)
# ---------------------------------------------------------------------------
def score_single(
    atm_id: str,
    issue_type: str,
    transaction_volume: float,
    downtime_minutes: float,
    complaint_count: float,
    drift_signal: float,
    atm_age_years: float,
    hour: int = 12,
    day_of_week: int = 2,
    in_cluster: int = 0,
    is_cascade: int = 0,
    resolution_mode: str = "MANUAL_REQUIRED",
    artifact: dict | None = None,
) -> dict:
    """
    Instant single-row prediction for the Live Prediction tab.

    Applies minimal feature engineering (static encodings + sensible
    defaults for rolling/lag features, which are unavailable for a single
    isolated row).  Uses the trained ensemble directly.

    Returns dict with keys:
        atm_id, risk_score, risk_label, escalation_probability,
        issue_severity, drift_signal, failure_pressure, feature_snapshot.
    """
    if artifact is None:
        artifact = load_model()
    if artifact is None:
        raise RuntimeError("[PredictiveEngine] No trained model. Run pipeline first.")

    import math
    from feature_engineering import ISSUE_TYPES_ORDERED

    # Encodings
    mode_map = {"AUTO_RESOLVED": 0, "AUTO_ATTEMPTED": 1, "MANUAL_REQUIRED": 2, "NONE": 0}
    res_enc  = mode_map.get(resolution_mode, 1)

    hour_sin = math.sin(2 * math.pi * hour / 24)
    hour_cos = math.cos(2 * math.pi * hour / 24)
    dow_sin  = math.sin(2 * math.pi * day_of_week / 7)
    dow_cos  = math.cos(2 * math.pi * day_of_week / 7)

    issue_flags = {f"issue_{i}": int(issue_type == i) for i in ISSUE_TYPES_ORDERED}

    failure_pressure = 0.4 * downtime_minutes + 0.4 * complaint_count + 0.2 * drift_signal
    drift_x_age      = drift_signal * atm_age_years
    drift_x_downtime = drift_signal * downtime_minutes
    complaint_x_dt   = complaint_count * float(np.log1p(downtime_minutes))

    row: dict = {
        "hour": hour, "day_of_week": day_of_week, "atm_age_years": atm_age_years,
        "transaction_volume": transaction_volume, "avg_amount": 3500.0,
        "downtime_minutes": downtime_minutes, "complaint_count": complaint_count,
        "drift_signal": drift_signal, "is_cascade": is_cascade, "in_cluster": in_cluster,
        "complaint_delta": complaint_count, "downtime_growth_pct": 0.0, "txn_drop_pct": 0.0,
        "hour_sin": hour_sin, "hour_cos": hour_cos, "dow_sin": dow_sin, "dow_cos": dow_cos,
        "resolution_mode_enc": res_enc,
        "drift_x_age": drift_x_age, "drift_x_downtime": drift_x_downtime,
        "complaint_x_downtime": complaint_x_dt, "cluster_pressure": float(in_cluster) * 0.0,
        "drift_velocity": 0.0, "drift_acceleration": 0.0,
        "pressure_index": failure_pressure, "failure_pressure": failure_pressure,
        "escalation_momentum": 0.0,
        **{f"failure_freq_{w}h":           1.0             for w in [3,6,12]},
        **{f"escalation_freq_{w}h":         0.0             for w in [3,6,12]},
        **{f"rolling_complaint_delta_{w}h": complaint_count for w in [3,6,12]},
        **{f"rolling_downtime_growth_{w}h": 0.0             for w in [3,6,12]},
        **{f"rolling_txn_drop_{w}h":        0.0             for w in [3,6,12]},
        **{f"total_downtime_{w}h":          downtime_minutes for w in [3,6,12]},
        **{f"mean_complaints_{w}h":         complaint_count  for w in [3,6,12]},
        **{f"cascade_density_{w}h":         0.0              for w in [3,6,12]},
        **{f"lag_{lag}_{field}": 0.0
           for lag in [1,2] for field in ["downtime","complaints","escalated","txn_volume"]},
        **issue_flags,
    }

    feature_cols = artifact["feature_cols"]
    row_filled   = {f: row.get(f, 0.0) for f in feature_cols}
    X_df = pd.DataFrame([row_filled], columns=feature_cols).astype(np.float32)

    models_dict  = artifact["model"]
    weights      = artifact.get("ensemble_weights", ENSEMBLE_WEIGHTS)
    prob_arrays: list[np.ndarray] = []
    weights_used: list[float] = []

    for key, w in zip(("xgb","lgbm","cat"), weights):
        m = models_dict.get(key)
        if m is None:
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            prob_arrays.append(m.predict_proba(X_df)[:, 1])
        weights_used.append(w)

    if not prob_arrays:
        raise RuntimeError("[PredictiveEngine] No valid base models.")

    total_w = sum(weights_used)
    prob    = float(sum((w / total_w) * p[0] for w, p in zip(weights_used, prob_arrays)))

    severity      = ISSUE_SEVERITY.get(issue_type, 1.0)
    base_score    = prob * 100.0
    drift_boost   = drift_signal * 15.0 / 100.0
    pressure_raw  = float(np.log1p(downtime_minutes + complaint_count))
    pressure_norm = min(pressure_raw / 10.0, 8.0)
    cp_boost      = min(failure_pressure / 100.0 * 3.0, 3.0)
    risk_score    = float(np.clip(base_score * severity + drift_boost + pressure_norm + cp_boost, 0.0, 100.0))
    risk_score    = round(risk_score, 2)

    label = ("HIGH" if risk_score >= RISK_HIGH_THRESHOLD
             else "MEDIUM" if risk_score >= RISK_MEDIUM_THRESHOLD else "LOW")

    return {
        "atm_id":                 atm_id,
        "risk_score":             risk_score,
        "risk_label":             label,
        "escalation_probability": round(prob, 5),
        "issue_severity":         severity,
        "drift_signal":           drift_signal,
        "failure_pressure":       round(failure_pressure, 2),
        "feature_snapshot":       row_filled,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train PayGuard v2.3 ensemble model")
    parser.add_argument("--days",    type=int, default=60, help="History days to generate")
    parser.add_argument("--retrain", action="store_true",  help="Force retrain even if saved model exists")
    args = parser.parse_args()

    from historical_log_generator import generate_historical_logs
    from feature_engineering      import engineer_features

    print(f"Generating {args.days}-day logs for 100 ATMs ...")
    raw  = generate_historical_logs(n_days=args.days, n_atms=100, seed=42)
    print("Engineering features ...")
    feat = engineer_features(raw, add_target=True)

    art = ensure_model_trained(
        feat,
        random_state=42,
        force_retrain=args.retrain,
    )

    print("\nScoring sample (first 500 rows) ...")
    scored = score_batch(feat.head(500), artifact=art)
    print(scored[[
        "atm_id", "timestamp", "issue_type",
        "escalation_probability", "pre_failure_risk_score", "risk_label",
    ]].head(15).to_string(index=False))