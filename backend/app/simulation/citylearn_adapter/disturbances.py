"""Stub observation wrappers and disturbance injection for future Phase 7 robustness testing."""

from __future__ import annotations

from typing import Sequence

import numpy as np


class ObservationDisturbanceWrapper:
    """Wrapper stub for injecting synthetic sensor noise or observation dropouts.

    Full robustness and domain randomization suites are reserved for Phase 7.
    """

    def __init__(
        self,
        noise_std: float = 0.0,
        dropout_prob: float = 0.0,
        seed: int = 0,
    ) -> None:
        self.noise_std = noise_std
        self.dropout_prob = dropout_prob
        self.rng = np.random.default_rng(seed)

    def apply(self, observations: Sequence[Sequence[float]]) -> list[list[float]]:
        disturbed: list[list[float]] = []
        for b_obs in observations:
            obs_arr = np.asarray(b_obs, dtype=float).copy()

            # Additive Gaussian noise
            if self.noise_std > 0.0:
                noise = self.rng.normal(0.0, self.noise_std, size=obs_arr.shape)
                obs_arr += noise

            # Missing observation / sensor dropout (represented by NaN)
            if self.dropout_prob > 0.0:
                mask = self.rng.random(size=obs_arr.shape) < self.dropout_prob
                obs_arr[mask] = np.nan

            disturbed.append([float(x) for x in obs_arr])
        return disturbed


class ObservationSanitizer:
    """Smoke-test utility to sanitize observations with missing values (NaNs)."""

    def __init__(self, fallback_value: float = 0.0) -> None:
        self.fallback_value = fallback_value

    def sanitize(self, observations: Sequence[Sequence[float]]) -> list[list[float]]:
        sanitized: list[list[float]] = []
        for b_obs in observations:
            clean = [self.fallback_value if (x is None or np.isnan(x)) else float(x) for x in b_obs]
            sanitized.append(clean)
        return sanitized
