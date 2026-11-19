"""Unit tests for Phase 4: uncertainty calibration, split conformal prediction, gating, and explainability."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier

from app.ml.explainability.importance import (
    ImportanceResult,
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

ROOT = Path(__file__).resolve().parents[3]
REPORT_PATH = ROOT / "artifacts/reports/phase4_uncertainty.json"


def test_expected_calibration_error_bounds() -> None:
    # 3 classes, 10 samples
    y_true = np.array([0, 1, 2, 0, 1, 2, 0, 1, 2, 0])
    # Perfect probabilities
    eye = np.eye(3)
    perfect_probs = eye[y_true]
    ece_perf = expected_calibration_error(y_true, perfect_probs, n_bins=5)
    assert 0.0 <= ece_perf <= 1.0
    assert ece_perf == pytest.approx(0.0, abs=1e-5)

    # Uniform inaccurate probabilities
    uniform_probs = np.full((10, 3), 1.0 / 3.0)
    ece_unif = expected_calibration_error(y_true, uniform_probs, n_bins=5)
    assert 0.0 <= ece_unif <= 1.0


def test_brier_score_properties() -> None:
    y_true = np.array([0, 1, 2])
    classes = [0, 1, 2]
    # Perfect prediction: Brier score is 0
    perf = np.eye(3)
    assert brier_score(y_true, perf, classes=classes) == pytest.approx(0.0, abs=1e-6)

    # Worst prediction: predict wrong class with 100% prob
    worst = np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]], dtype=float)
    score_worst = brier_score(y_true, worst, classes=classes)
    assert score_worst > 0.0
    assert score_worst <= 2.0


def test_temperature_scaler_optimization() -> None:
    np.random.seed(42)
    # 100 samples, 3 classes
    y_val = np.random.choice([0, 1, 2], size=100)
    # Overconfident noisy probabilities
    logits = np.random.randn(100, 3) * 5.0
    from scipy.special import softmax

    probs_val = softmax(logits, axis=1)

    scaler = TemperatureScaler()
    scaler.fit(probs_val, y_val, classes=[0, 1, 2])
    assert scaler.temperature > 0.0

    cal_eval = scaler.evaluate(probs_val, y_val, classes=[0, 1, 2])
    assert 0.0 <= cal_eval.uncalibrated_ece <= 1.0
    assert 0.0 <= cal_eval.calibrated_ece <= 1.0
    assert cal_eval.calibrated_brier >= 0.0


def test_split_conformal_classifier_coverage_and_size() -> None:
    np.random.seed(42)
    classes = [-3, -2, -1, 0, 1, 2, 3]
    n_cal = 200
    n_test = 100
    n_classes = len(classes)

    y_cal = np.random.choice(classes, size=n_cal)
    y_test = np.random.choice(classes, size=n_test)

    # Simulated probabilities with signal towards true class
    eye = np.eye(n_classes)
    class_to_idx = {c: i for i, c in enumerate(classes)}

    def make_noisy_probs(y_arr):
        idx = np.array([class_to_idx[y] for y in y_arr])
        probs = eye[idx] * 0.6 + 0.4 / n_classes
        # Normalize
        return probs / np.sum(probs, axis=1, keepdims=True)

    probs_cal = make_noisy_probs(y_cal)
    probs_test = make_noisy_probs(y_test)

    conformal = SplitConformalClassifier(classes=classes)
    conformal.fit(probs_cal, y_cal, calibration_split_name="validation")

    pred_sets = conformal.predict_sets(probs_test, alpha=0.10, guarantee_non_empty=True)
    assert len(pred_sets) == n_test

    for s in pred_sets:
        assert len(s) >= 1  # non-empty guarantee
        assert all(c in classes for c in s)

    eval_result = conformal.evaluate(probs_test, y_test, alpha=0.10)
    assert 0.0 <= eval_result.empirical_coverage <= 1.0
    assert eval_result.mean_set_size >= 1.0
    assert eval_result.median_set_size >= 1.0
    assert eval_result.target_coverage == pytest.approx(0.90)


def test_comfort_gating_filter_logic() -> None:
    gating = ComfortGatingFilter(max_confident_size=2, severe_discomfort_threshold=2)

    # 1. Confident neutral sensation {0} -> no conservative override
    d1 = gating.evaluate_set([0])
    assert not d1.is_uncertain
    assert not d1.has_severe_discomfort_risk
    assert not d1.conservative_action_recommended
    assert d1.discomfort_direction == "neutral"

    # 2. Severe cold discomfort {-2} -> flags discomfort and conservative
    d2 = gating.evaluate_set([-2, -1])
    assert not d2.is_uncertain
    assert d2.has_severe_discomfort_risk
    assert d2.conservative_action_recommended
    assert d2.discomfort_direction == "cold_risk"

    # 3. Severe hot discomfort {2, 3} -> flags hot risk
    d3 = gating.evaluate_set([2, 3])
    assert d3.has_severe_discomfort_risk
    assert d3.conservative_action_recommended
    assert d3.discomfort_direction == "hot_risk"

    # 4. Large uncertain set {-1, 0, 1} (size 3 > 2) -> flags uncertainty
    d4 = gating.evaluate_set([-1, 0, 1])
    assert d4.is_uncertain
    assert not d4.has_severe_discomfort_risk
    assert d4.conservative_action_recommended

    # Batch evaluation
    batch = gating.evaluate_batch([[0], [-2], [-1, 0, 1]])
    assert batch["n_samples"] == 3
    assert 0.0 <= batch["conservative_rate"] <= 1.0
    assert batch["conservative_rate"] == pytest.approx(2 / 3)


def test_explainability_helpers() -> None:
    X = np.random.randn(50, 4)
    y = np.random.choice([0, 1], size=50)
    features = ["f1", "f2", "f3", "f4"]

    rf = RandomForestClassifier(n_estimators=10, random_state=0)
    rf.fit(X, y)

    tree_imp = compute_tree_importance(rf, features)
    assert tree_imp is not None
    assert len(tree_imp.ranking) == 4
    assert set(tree_imp.ranking) == set(features)
    assert sum(tree_imp.mean_importance.values()) == pytest.approx(1.0, abs=1e-5)

    svg = render_importance_svg(tree_imp, title="Test Importance")
    assert "<svg" in svg
    assert "</svg>" in svg
    for f in features:
        assert f in svg


def test_phase4_report_file_structure_if_present() -> None:
    if not REPORT_PATH.exists():
        pytest.skip("phase4_uncertainty.json not yet generated on disk.")

    data = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    assert data["phase"] == 4
    assert "protocol" in data
    assert "comfort_full_features" in data
    assert "comfort_transfer_features" in data

    for tag in ("comfort_full_features", "comfort_transfer_features"):
        sub = data[tag]
        assert "models" in sub
        assert "random_forest" in sub["models"]
        rf = sub["models"]["random_forest"]

        # Check calibration
        cal = rf["calibration"]
        assert 0.0 <= cal["uncalibrated_ece"] <= 1.0
        assert 0.0 <= cal["calibrated_ece"] <= 1.0
        assert cal["uncalibrated_brier"] >= 0.0
        assert cal["calibrated_brier"] >= 0.0

        # Check conformal
        conf = rf["conformal_calibrated"]
        assert 0.0 <= conf["empirical_coverage"] <= 1.0
        assert conf["mean_set_size"] >= 1.0
        assert conf["target_coverage"] == 0.90

        # Check gating
        gating = rf["gating_diagnostics"]
        assert 0.0 <= gating["conservative_rate"] <= 1.0
        assert 0.0 <= gating["severe_discomfort_risk_rate"] <= 1.0
