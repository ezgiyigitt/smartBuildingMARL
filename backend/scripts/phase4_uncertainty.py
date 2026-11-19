"""Phase 4: Uncertainty calibration, split conformal prediction, and explainability for TSV classifiers."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.ml.comfort_prediction.prepare import FEATURES_FULL, FEATURES_TRANSFER, load_measurements, make_tsv_frame
from app.ml.explainability.importance import (
    compute_permutation_importance,
    compute_tree_importance,
    render_importance_svg,
)
from app.ml.uncertainty.calibration import (
    TemperatureScaler,
    brier_score,
    expected_calibration_error,
)
from app.ml.uncertainty.conformal import SplitConformalClassifier
from app.ml.uncertainty.gating import ComfortGatingFilter

MEAS = ROOT / "data/raw/ashrae_gcdb2/extracted/v2.1.0/db_measurements_v2.1.0.csv.gz"
ART_MODELS = ROOT / "artifacts/models"
ART_REPORTS = ROOT / "artifacts/reports"
ART_FIGURES = ROOT / "artifacts/figures"


def get_or_fit_models(
    frame: pd.DataFrame,
    features: list[str],
    tag: str,
) -> tuple[dict[str, Any], dict[str, pd.DataFrame]]:
    """Load existing trained models or retrain if checkpoint missing."""
    splits = {name: frame[frame["split"] == name].copy() for name in ("train", "validation", "test")}
    classes = sorted(frame["tsv_class"].unique())
    y_map = {c: i for i, c in enumerate(classes)}
    inv_map = {i: c for c, i in y_map.items()}

    models: dict[str, Any] = {}

    # 1. Random Forest
    rf_path = ART_MODELS / f"tsv_{tag}_random_forest.joblib"
    if rf_path.exists():
        rf = joblib.load(rf_path)
    else:
        rf = RandomForestClassifier(
            n_estimators=80, max_depth=12, min_samples_leaf=5, n_jobs=-1, random_state=0, class_weight="balanced"
        )
        rf.fit(splits["train"][features], splits["train"]["tsv_class"])
        joblib.dump(rf, rf_path)
    models["random_forest"] = rf

    # 2. XGBoost
    xgb_path = ART_MODELS / f"tsv_{tag}_xgboost.joblib"
    try:
        from xgboost import XGBClassifier

        if xgb_path.exists():
            xgb = joblib.load(xgb_path)
        else:
            xgb = XGBClassifier(
                n_estimators=80,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                n_jobs=-1,
                random_state=0,
                eval_metric="mlogloss",
            )
            y_train_mapped = splits["train"]["tsv_class"].map(y_map)
            xgb.fit(splits["train"][features], y_train_mapped)
            joblib.dump(xgb, xgb_path)
        models["xgboost"] = xgb
    except Exception as exc:
        print(f"XGBoost loading/training skipped: {exc}")

    # 3. Logistic Regression
    lr_path = ART_MODELS / f"tsv_{tag}_logreg.joblib"
    if lr_path.exists():
        lr = joblib.load(lr_path)
    else:
        lr = Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(max_iter=400, class_weight="balanced")),
            ]
        )
        lr.fit(splits["train"][features], splits["train"]["tsv_class"])
        joblib.dump(lr, lr_path)
    models["logreg"] = lr

    return models, splits


def get_probabilities(model: Any, X: pd.DataFrame, is_xgb: bool = False, classes: list[int] | None = None) -> np.ndarray:
    """Extract class probability distribution aligned with target classes [-3..3]."""
    raw_probs = model.predict_proba(X)
    model_classes = list(model.classes_)

    if is_xgb and classes is not None:
        # XGBoost outputs classes [0..K-1] corresponding to sorted classes
        return raw_probs

    if classes is not None and model_classes != classes:
        # Re-align probability columns to full target classes
        aligned = np.zeros((len(X), len(classes)), dtype=float)
        class_to_aligned_idx = {c: i for i, c in enumerate(classes)}
        for m_idx, c in enumerate(model_classes):
            if c in class_to_aligned_idx:
                aligned[:, class_to_aligned_idx[c]] = raw_probs[:, m_idx]
        return aligned

    return raw_probs


def evaluate_uncertainty_for_feature_set(
    features: list[str],
    tag: str,
    alpha: float = 0.10,
) -> dict[str, Any]:
    print(f"\n--- Running Phase 4 Uncertainty & Calibration for {tag} ({features}) ---")
    frame = make_tsv_frame(load_measurements(MEAS), features)
    models, splits = get_or_fit_models(frame, features, tag)

    classes = sorted(frame["tsv_class"].unique())
    y_val = splits["validation"]["tsv_class"].to_numpy()
    y_test = splits["test"]["tsv_class"].to_numpy()

    result: dict[str, Any] = {
        "tag": tag,
        "features": features,
        "classes": classes,
        "split_counts": {k: len(v) for k, v in splits.items()},
        "calibration_split": "validation_buildings",
        "test_split": "test_buildings",
        "alpha": alpha,
        "target_coverage": float(1.0 - alpha),
        "models": {},
    }

    gating_filter = ComfortGatingFilter(max_confident_size=2, severe_discomfort_threshold=2)

    for model_name, model in models.items():
        is_xgb = (model_name == "xgboost")

        val_probs = get_probabilities(model, splits["validation"][features], is_xgb=is_xgb, classes=classes)
        test_probs = get_probabilities(model, splits["test"][features], is_xgb=is_xgb, classes=classes)

        # 1. Calibration via Temperature Scaling on validation
        scaler = TemperatureScaler()
        scaler.fit(val_probs, y_val, classes=classes)
        cal_eval = scaler.evaluate(test_probs, y_test, classes=classes)

        # 2. Conformal Prediction on uncalibrated and calibrated probabilities
        conformal_uncal = SplitConformalClassifier(classes=classes)
        conformal_uncal.fit(val_probs, y_val, calibration_split_name="validation_buildings")
        conf_eval_uncal = conformal_uncal.evaluate(test_probs, y_test, alpha=alpha)

        calibrated_test_probs = scaler.calibrate_proba(test_probs)
        calibrated_val_probs = scaler.calibrate_proba(val_probs)
        conformal_cal = SplitConformalClassifier(classes=classes)
        conformal_cal.fit(calibrated_val_probs, y_val, calibration_split_name="validation_buildings")
        conf_eval_cal = conformal_cal.evaluate(calibrated_test_probs, y_test, alpha=alpha)

        # 3. Action Gating Evaluation on test prediction sets
        test_pred_sets = conformal_cal.predict_sets(calibrated_test_probs, alpha=alpha)
        gating_stats = gating_filter.evaluate_batch(test_pred_sets)

        result["models"][model_name] = {
            "calibration": {
                "optimal_temperature": float(cal_eval.optimal_temperature),
                "uncalibrated_ece": float(cal_eval.uncalibrated_ece),
                "calibrated_ece": float(cal_eval.calibrated_ece),
                "ece_improvement": float(cal_eval.uncalibrated_ece - cal_eval.calibrated_ece),
                "uncalibrated_brier": float(cal_eval.uncalibrated_brier),
                "calibrated_brier": float(cal_eval.calibrated_brier),
            },
            "conformal_uncalibrated": conf_eval_uncal.to_dict(),
            "conformal_calibrated": conf_eval_cal.to_dict(),
            "gating_diagnostics": gating_stats,
        }

    # 4. Explainability on selected Random Forest (and XGBoost if present)
    explainability: dict[str, Any] = {}
    rf = models["random_forest"]

    # Tree impurity importance
    rf_tree_imp = compute_tree_importance(rf, features)
    if rf_tree_imp:
        explainability["random_forest_tree_gini"] = rf_tree_imp.to_dict()

    # Permutation importance on test set (or validation set)
    print("Computing permutation importance for Random Forest on test set...")
    rf_perm_imp = compute_permutation_importance(
        rf, splits["test"][features], y_test, features, n_repeats=5, random_state=0, scoring="f1_macro"
    )
    explainability["random_forest_permutation_macro_f1"] = rf_perm_imp.to_dict()

    # Render SVG chart
    svg_path = ART_FIGURES / f"feature_importance_{tag}_rf.svg"
    render_importance_svg(rf_perm_imp, title=f"TSV RF Feature Importance ({tag})", out_path=svg_path)
    print(f"Saved feature importance figure to {svg_path}")

    if "xgboost" in models:
        xgb = models["xgboost"]
        xgb_tree_imp = compute_tree_importance(xgb, features)
        if xgb_tree_imp:
            explainability["xgboost_tree_gain"] = xgb_tree_imp.to_dict()

    result["explainability"] = explainability
    return result


def main() -> int:
    ART_MODELS.mkdir(parents=True, exist_ok=True)
    ART_REPORTS.mkdir(parents=True, exist_ok=True)
    ART_FIGURES.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "phase": 4,
        "protocol": {
            "split_type": "grouped_by_building_id (seed 0)",
            "calibration_split": "validation buildings (n=6153)",
            "evaluation_split": "test buildings (n=5721)",
            "nominal_target_coverage": 0.90,
            "significance_alpha": 0.10,
            "disclaimer": (
                "Split conformal prediction requires exchangeability. Cross-building validation and test sets "
                "experience distribution shift across climates, building typologies, and occupant demographics. "
                "Empirical coverage may deviate from nominal coverage (1 - alpha); this layer is a heuristic diagnostic."
            ),
        },
        "comfort_full_features": evaluate_uncertainty_for_feature_set(FEATURES_FULL, "full", alpha=0.10),
        "comfort_transfer_features": evaluate_uncertainty_for_feature_set(FEATURES_TRANSFER, "transfer", alpha=0.10),
    }

    report_path = ART_REPORTS / "phase4_uncertainty.json"
    report_path.write_text(
        json.dumps(report, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o)),
        encoding="utf-8",
    )
    print(f"\nWritten Phase 4 report to {report_path}")

    # Also save a dedicated small JSON of feature importances
    shap_summary = {
        "generated_at_utc": report["generated_at_utc"],
        "full_features_rf_permutation": report["comfort_full_features"]["explainability"]["random_forest_permutation_macro_f1"],
        "transfer_features_rf_permutation": report["comfort_transfer_features"]["explainability"]["random_forest_permutation_macro_f1"],
    }
    (ART_REPORTS / "phase4_feature_importance.json").write_text(
        json.dumps(shap_summary, indent=2), encoding="utf-8"
    )

    # Print summary table for key metrics
    rf_full = report["comfort_full_features"]["models"]["random_forest"]
    print("\n=== PHASE 4 UNCERTAINTY & CALIBRATION SUMMARY (Selected RF - Full Features) ===")
    print(f"Optimal Temperature T: {rf_full['calibration']['optimal_temperature']:.4f}")
    print(f"Uncalibrated ECE:      {rf_full['calibration']['uncalibrated_ece']:.4f}")
    print(f"Calibrated ECE:        {rf_full['calibration']['calibrated_ece']:.4f}")
    print(f"Uncalibrated Brier:    {rf_full['calibration']['uncalibrated_brier']:.4f}")
    print(f"Calibrated Brier:      {rf_full['calibration']['calibrated_brier']:.4f}")
    print(f"Conformal Coverage:    {rf_full['conformal_calibrated']['empirical_coverage']:.4f} (target: 0.90)")
    print(f"Mean Set Size:         {rf_full['conformal_calibrated']['mean_set_size']:.2f} / 7 classes")
    print(f"Gating Conservative %: {rf_full['gating_diagnostics']['conservative_rate']*100:.1f}%")
    print(f"Discomfort Risk %:     {rf_full['gating_diagnostics']['severe_discomfort_risk_rate']*100:.1f}%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
