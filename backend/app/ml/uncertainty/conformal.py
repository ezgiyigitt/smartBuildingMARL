"""Split conformal prediction for multi-class thermal sensation classification."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Sequence

import numpy as np


@dataclass
class ConformalEvaluation:
    alpha: float
    target_coverage: float
    empirical_coverage: float
    mean_set_size: float
    median_set_size: float
    quantile: float
    calibration_size: int
    test_size: int
    set_size_distribution: dict[int, float]
    coverage_gap: float  # empirical - target; negative indicates undercoverage

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SplitConformalClassifier:
    """Split Conformal Prediction for multi-class classification.

    Uses Least Ambiguous Set (LAC) non-conformity score: s_i = 1 - P(Y = y_i | X = x_i).
    Fitted on an exchangeable calibration split (e.g. validation buildings).

    CRITICAL SCIENTIFIC NOTE:
    Theoretical coverage guarantees (1 - alpha) strictly require exchangeability between
    calibration and test samples. In grouped cross-building splits (and building HVAC control),
    exchangeability is violated by cross-building domain shift, sensor drift, and temporal autocorrelation.
    Therefore, this layer functions as a heuristic uncertainty diagnostic / safety filter,
    NOT a formal safety proof.
    """

    def __init__(self, classes: Sequence[int]) -> None:
        self.classes = np.asarray(classes)
        self.class_to_idx = {c: i for i, c in enumerate(self.classes)}
        self.calibration_scores: np.ndarray | None = None
        self.calibration_split_name: str = "validation_buildings"

    def fit(
        self,
        y_prob_cal: np.ndarray,
        y_cal: Sequence[int] | np.ndarray,
        calibration_split_name: str = "validation_buildings",
    ) -> SplitConformalClassifier:
        """Compute non-conformity scores on calibration set."""
        self.calibration_split_name = calibration_split_name
        probs = np.asarray(y_prob_cal)
        y_cal = np.asarray(y_cal)

        n_samples = len(y_cal)
        y_indices = np.array([self.class_to_idx[y] for y in y_cal])

        # Non-conformity score: 1 - prob of true class
        true_class_probs = probs[np.arange(n_samples), y_indices]
        self.calibration_scores = 1.0 - true_class_probs
        return self

    def compute_quantile(self, alpha: float) -> float:
        """Compute conformal quantile with finite-sample correction."""
        if self.calibration_scores is None:
            raise ValueError("Conformal predictor must be fit before computing quantiles.")
        n = len(self.calibration_scores)
        q_level = min(1.0, math.ceil((n + 1) * (1.0 - alpha)) / n)
        # Higher/inverted quantile
        return float(np.quantile(self.calibration_scores, q_level, method="higher"))

    def predict_sets(
        self,
        y_prob: np.ndarray,
        alpha: float = 0.10,
        guarantee_non_empty: bool = True,
    ) -> list[list[int]]:
        """Construct prediction sets for each sample at significance level alpha.

        C(x) = { c in Y : 1 - P(c|x) <= q } = { c in Y : P(c|x) >= 1 - q }.
        """
        probs = np.asarray(y_prob)
        q = self.compute_quantile(alpha)
        threshold = 1.0 - q

        prediction_sets: list[list[int]] = []
        for i in range(len(probs)):
            p = probs[i]
            included_indices = np.where(p >= threshold)[0]

            if len(included_indices) == 0 and guarantee_non_empty:
                # Include argmax class to avoid empty sets
                included_indices = np.array([int(np.argmax(p))])

            pred_set = [int(self.classes[idx]) for idx in included_indices]
            prediction_sets.append(sorted(pred_set))

        return prediction_sets

    def evaluate(
        self,
        y_prob_test: np.ndarray,
        y_test: Sequence[int] | np.ndarray,
        alpha: float = 0.10,
    ) -> ConformalEvaluation:
        """Evaluate empirical coverage and set size efficiency on test data."""
        y_test = np.asarray(y_test)
        pred_sets = self.predict_sets(y_prob_test, alpha=alpha, guarantee_non_empty=True)
        q = self.compute_quantile(alpha)

        covered = [y_test[i] in pred_sets[i] for i in range(len(y_test))]
        set_sizes = [len(s) for s in pred_sets]

        emp_cov = float(np.mean(covered))
        mean_size = float(np.mean(set_sizes))
        med_size = float(np.median(set_sizes))

        # Size distribution
        unique_sizes, counts = np.unique(set_sizes, return_counts=True)
        total_test = len(set_sizes)
        size_dist = {int(sz): float(cnt / total_test) for sz, cnt in zip(unique_sizes, counts)}

        return ConformalEvaluation(
            alpha=float(alpha),
            target_coverage=float(1.0 - alpha),
            empirical_coverage=emp_cov,
            mean_set_size=mean_size,
            median_set_size=med_size,
            quantile=q,
            calibration_size=len(self.calibration_scores) if self.calibration_scores is not None else 0,
            test_size=total_test,
            set_size_distribution=size_dist,
            coverage_gap=float(emp_cov - (1.0 - alpha)),
        )
