"""Interface stub for uncertainty-aware comfort gating of HVAC control actions.

RESEARCH CONTEXT:
In Phase 6, MARL agents optimize multi-objective rewards (energy, comfort, emissions).
This module defines a heuristic diagnostic/gating layer based on conformal prediction sets.
When the prediction set is large (high epistemic/aleatoric uncertainty) or contains severe
discomfort votes (|TSV| >= 2: cold/hot extremes), the gating layer signals a conservative override flag.

DISCLAIMER:
This is a heuristic safety filter and diagnostic interface, NOT a formal safety certificate.
Exchangeability is violated under non-stationary weather, occupancy dynamics, and RL closed-loop feedback.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence


@dataclass
class GatingDecision:
    prediction_set: list[int]
    set_size: int
    is_uncertain: bool
    has_severe_discomfort_risk: bool
    discomfort_direction: str  # "neutral", "cold_risk", "hot_risk", "dual_risk"
    conservative_action_recommended: bool
    diagnostic_reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ComfortGatingFilter:
    """Evaluates prediction sets to produce control flags for downstream RL/RBC."""

    def __init__(
        self,
        max_confident_size: int = 2,
        severe_discomfort_threshold: int = 2,
    ) -> None:
        self.max_confident_size = max_confident_size
        self.severe_discomfort_threshold = severe_discomfort_threshold

    def evaluate_set(self, prediction_set: Sequence[int]) -> GatingDecision:
        p_set = sorted(int(x) for x in prediction_set)
        size = len(p_set)

        is_uncertain = size > self.max_confident_size

        has_cold_risk = any(c <= -self.severe_discomfort_threshold for c in p_set)
        has_hot_risk = any(c >= self.severe_discomfort_threshold for c in p_set)
        has_severe_discomfort = has_cold_risk or has_hot_risk

        if has_cold_risk and has_hot_risk:
            direction = "dual_risk"
        elif has_cold_risk:
            direction = "cold_risk"
        elif has_hot_risk:
            direction = "hot_risk"
        else:
            direction = "neutral"

        conservative = is_uncertain or has_severe_discomfort

        reasons = []
        if is_uncertain:
            reasons.append(f"large prediction set (|C|={size} > {self.max_confident_size})")
        if has_severe_discomfort:
            reasons.append(f"severe discomfort class in set ({direction})")
        if not reasons:
            reasons.append("confident acceptable sensation; nominal control allowed")

        return GatingDecision(
            prediction_set=p_set,
            set_size=size,
            is_uncertain=is_uncertain,
            has_severe_discomfort_risk=has_severe_discomfort,
            discomfort_direction=direction,
            conservative_action_recommended=conservative,
            diagnostic_reason="; ".join(reasons),
        )

    def evaluate_batch(self, prediction_sets: Sequence[Sequence[int]]) -> dict[str, Any]:
        decisions = [self.evaluate_set(s) for s in prediction_sets]
        n = len(decisions)
        if n == 0:
            return {"n_samples": 0}

        n_conservative = sum(1 for d in decisions if d.conservative_action_recommended)
        n_uncertain = sum(1 for d in decisions if d.is_uncertain)
        n_discomfort = sum(1 for d in decisions if d.has_severe_discomfort_risk)

        return {
            "n_samples": n,
            "conservative_rate": float(n_conservative / n),
            "uncertainty_rate": float(n_uncertain / n),
            "severe_discomfort_risk_rate": float(n_discomfort / n),
            "max_confident_size_threshold": self.max_confident_size,
            "severe_discomfort_threshold": self.severe_discomfort_threshold,
        }
