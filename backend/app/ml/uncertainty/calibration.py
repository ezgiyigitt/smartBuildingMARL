"""Probability calibration metrics and temperature scaling for multi-class TSV models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import softmax


def expected_calibration_error(
    y_true: Sequence[int] | np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10,
    classes: Sequence[int] | None = None,
) -> float:
    """Compute multi-class top-label Expected Calibration Error (ECE).

    Bins predictions by top-class confidence into n_bins equal-width intervals in (0, 1].
    ECE = sum_{m=1}^M (|B_m| / N) * |acc(B_m) - conf(B_m)|.
    """
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)

    if classes is not None:
        class_to_idx = {c: i for i, c in enumerate(classes)}
        y_true_idx = np.array([class_to_idx[y] for y in y_true])
    else:
        y_true_idx = y_true

    confidences = np.max(y_prob, axis=1)
    predictions = np.argmax(y_prob, axis=1)
    accuracies = (predictions == y_true_idx).astype(float)

    n_samples = len(y_true)
    if n_samples == 0:
        return 0.0

    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        if i == 0:
            in_bin = (confidences >= bin_lower) & (confidences <= bin_upper)
        else:
            in_bin = (confidences > bin_lower) & (confidences <= bin_upper)

        bin_size = np.sum(in_bin)
        if bin_size > 0:
            bin_acc = np.mean(accuracies[in_bin])
            bin_conf = np.mean(confidences[in_bin])
            ece += (bin_size / n_samples) * np.abs(bin_acc - bin_conf)

    return float(ece)


def brier_score(
    y_true: Sequence[int] | np.ndarray,
    y_prob: np.ndarray,
    classes: Sequence[int] | None = None,
) -> float:
    """Compute multi-class Brier score: (1/N) * sum_{i=1}^N sum_{k=1}^K (p_{ik} - y_{ik})^2.

    Lower is better; bounded in [0, 2].
    """
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    n_samples, n_classes = y_prob.shape

    if classes is not None:
        class_to_idx = {c: i for i, c in enumerate(classes)}
        y_indices = np.array([class_to_idx[y] for y in y_true])
    else:
        y_indices = y_true.astype(int)

    one_hot = np.zeros((n_samples, n_classes), dtype=float)
    for i, idx in enumerate(y_indices):
        if 0 <= idx < n_classes:
            one_hot[i, idx] = 1.0

    squared_errors = np.sum((y_prob - one_hot) ** 2, axis=1)
    return float(np.mean(squared_errors))


@dataclass
class CalibrationEvaluation:
    uncalibrated_ece: float
    calibrated_ece: float
    uncalibrated_brier: float
    calibrated_brier: float
    optimal_temperature: float


class TemperatureScaler:
    """Post-hoc probability calibration via temperature scaling on logits.

    T > 1 softens overconfident probabilities; T < 1 sharpens underconfident probabilities.
    Fitted on validation set to minimize negative log-likelihood (cross-entropy).
    """

    def __init__(self, eps: float = 1e-7) -> None:
        self.eps = eps
        self.temperature: float = 1.0
        self.classes_: np.ndarray | None = None

    def _probs_to_logits(self, probs: np.ndarray) -> np.ndarray:
        clipped = np.clip(probs, self.eps, 1.0 - self.eps)
        return np.log(clipped)

    def fit(
        self,
        y_prob_val: np.ndarray,
        y_val: Sequence[int] | np.ndarray,
        classes: Sequence[int] | None = None,
    ) -> TemperatureScaler:
        """Fit temperature parameter T on validation probabilities and labels."""
        probs = np.asarray(y_prob_val)
        y_val = np.asarray(y_val)

        if classes is not None:
            self.classes_ = np.asarray(classes)
            class_to_idx = {c: i for i, c in enumerate(self.classes_)}
            y_indices = np.array([class_to_idx[y] for y in y_val])
        else:
            self.classes_ = np.unique(y_val)
            class_to_idx = {c: i for i, c in enumerate(self.classes_)}
            y_indices = np.array([class_to_idx.get(y, 0) for y in y_val])

        logits = self._probs_to_logits(probs)
        n_samples = len(y_indices)

        def nll_loss(t: float) -> float:
            scaled = logits / max(t, 1e-4)
            scaled_probs = softmax(scaled, axis=1)
            # Gather probability of true class
            true_probs = scaled_probs[np.arange(n_samples), y_indices]
            clipped_true = np.clip(true_probs, self.eps, 1.0)
            return float(-np.mean(np.log(clipped_true)))

        res = minimize_scalar(nll_loss, bounds=(0.05, 10.0), method="bounded")
        self.temperature = float(res.x)
        return self

    def calibrate_proba(self, probs: np.ndarray) -> np.ndarray:
        """Calibrate probability distribution using learned temperature."""
        probs = np.asarray(probs)
        logits = self._probs_to_logits(probs)
        scaled = logits / max(self.temperature, 1e-4)
        return softmax(scaled, axis=1)

    def evaluate(
        self,
        y_prob_test: np.ndarray,
        y_test: Sequence[int] | np.ndarray,
        classes: Sequence[int] | None = None,
        n_bins: int = 10,
    ) -> CalibrationEvaluation:
        """Evaluate calibration improvement on test set."""
        classes_seq = classes if classes is not None else self.classes_
        calibrated_probs = self.calibrate_proba(y_prob_test)

        uncal_ece = expected_calibration_error(y_test, y_prob_test, n_bins=n_bins, classes=classes_seq)
        cal_ece = expected_calibration_error(y_test, calibrated_probs, n_bins=n_bins, classes=classes_seq)
        uncal_brier = brier_score(y_test, y_prob_test, classes=classes_seq)
        cal_brier = brier_score(y_test, calibrated_probs, classes=classes_seq)

        return CalibrationEvaluation(
            uncalibrated_ece=uncal_ece,
            calibrated_ece=cal_ece,
            uncalibrated_brier=uncal_brier,
            calibrated_brier=cal_brier,
            optimal_temperature=self.temperature,
        )
