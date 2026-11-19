"""Baseline controllers for CityLearn 2023 Phase 1.

Includes:
1. Business-as-usual (BAU): Zero storage actions (no battery/DHW shifting) and zero active cooling offset.
2. BasicRBC: Built-in CityLearn Rule-Based Controller.
3. ComfortPriceRuleBasedController: Documented if-then rules on SOC, price, indoor temperature vs setpoint, and occupancy.
4. RandomActionController: Seeded uniform random action baseline within action spaces.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
from citylearn.agents.rbc import BasicRBC
from citylearn.citylearn import CityLearnEnv


class BaseController(ABC):
    """Abstract base class for simulation controllers."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def predict(self, observations: list[list[float]], env: CityLearnEnv) -> list[list[float]]:
        """Given current observations per building, return action list per building."""
        raise NotImplementedError

    def reset(self) -> None:
        """Reset internal state between episodes if needed."""
        pass


class BusinessAsUsualController(BaseController):
    """Business-As-Usual (BAU) / passive environment baseline.

    Storage actions: 0.0 (no battery charging or discharging, no DHW charging/discharging).
    Cooling action: 0.0 (baseline heat pump behavior without agent-commanded cooling override).
    """

    def __init__(self) -> None:
        super().__init__(name="business_as_usual")

    def predict(self, observations: list[list[float]], env: CityLearnEnv) -> list[list[float]]:
        actions: list[list[float]] = []
        for b in env.buildings:
            n_actions = len(b.action_space.low)
            # All zeros: [0.0, 0.0, 0.0] for [dhw_storage, electrical_storage, cooling_device]
            actions.append([0.0] * n_actions)
        return actions


class CityLearnBasicRBCController(BaseController):
    """Wrapper around official CityLearn BasicRBC agent."""

    def __init__(self, env: CityLearnEnv) -> None:
        super().__init__(name="citylearn_basic_rbc")
        self._rbc = BasicRBC(env=env)

    def predict(self, observations: list[list[float]], env: CityLearnEnv) -> list[list[float]]:
        # BasicRBC expects observations list
        raw_actions = self._rbc.predict(observations)
        # Ensure standard python floats
        return [[float(a) for a in b_actions] for b_actions in raw_actions]


class ComfortPriceRuleBasedController(BaseController):
    """Documented rule-based controller balancing energy price, battery/DHW storage, and occupant comfort.

    IF-THEN RULES:
    1. Battery Storage (electrical_storage in [-1.0, 1.0]):
       - Low Price (<= 0.035 $/kWh or off-peak hours <= 6) AND SOC < 0.85:
           Charge battery: +0.5
       - High Price (>= 0.048 $/kWh or peak hours 17..21) AND SOC > 0.20:
           Discharge battery to offset load: -0.5
       - Otherwise: Hold (0.0)

    2. Domestic Hot Water Storage (dhw_storage in [-1.0, 1.0]):
       - Low Price AND dhw_demand > 0 AND SOC < 0.85:
           Charge DHW: +0.4
       - High Price AND dhw_demand > 0 AND SOC > 0.20:
           Discharge DHW: -0.4
       - Otherwise: Hold (0.0)

    3. Cooling Device (cooling_device in [0.0, 1.0]):
       - If indoor_temp > cooling_setpoint + 0.5 °C (overheating risk):
           Boost cooling: 0.80
       - If indoor_temp < cooling_setpoint - 0.5 °C (overcooled):
           Throttle cooling: 0.10
       - If High Price AND indoor_temp <= cooling_setpoint:
           Economize: 0.20
       - If occupant_count > 0 AND indoor_temp > cooling_setpoint:
           Comfort priority cooling: 0.60
       - Otherwise (normal operating regime):
           Nominal cooling: 0.40
    """

    def __init__(
        self,
        price_low_threshold: float = 0.035,
        price_high_threshold: float = 0.048,
    ) -> None:
        super().__init__(name="comfort_price_rbc")
        self.price_low_threshold = price_low_threshold
        self.price_high_threshold = price_high_threshold

    def predict(self, observations: list[list[float]], env: CityLearnEnv) -> list[list[float]]:
        actions: list[list[float]] = []

        for b_idx, b in enumerate(env.buildings):
            obs_dict = {name: val for name, val in zip(env.observation_names[b_idx], observations[b_idx])}

            hour = float(obs_dict.get("hour", 12.0))
            price = float(obs_dict.get("electricity_pricing", 0.04))
            elec_soc = float(obs_dict.get("electrical_storage_soc", 0.0))
            dhw_soc = float(obs_dict.get("dhw_storage_soc", 0.0))
            dhw_demand = float(obs_dict.get("dhw_demand", 0.0))
            indoor_temp = float(obs_dict.get("indoor_dry_bulb_temperature", 23.0))
            setpoint = float(obs_dict.get("indoor_dry_bulb_temperature_cooling_set_point", 23.0))
            occupants = float(obs_dict.get("occupant_count", 0.0))

            is_cheap = (price <= self.price_low_threshold) or (hour <= 6.0)
            is_expensive = (price >= self.price_high_threshold) or (17.0 <= hour <= 21.0)

            # 1. Electrical storage
            if is_cheap and elec_soc < 0.85:
                act_elec = 0.5
            elif is_expensive and elec_soc > 0.20:
                act_elec = -0.5
            else:
                act_elec = 0.0

            # 2. DHW storage
            if is_cheap and dhw_demand > 0.0 and dhw_soc < 0.85:
                act_dhw = 0.4
            elif is_expensive and dhw_demand > 0.0 and dhw_soc > 0.20:
                act_dhw = -0.4
            else:
                act_dhw = 0.0

            # 3. Cooling device
            temp_error = indoor_temp - setpoint
            if temp_error > 0.5:
                act_cool = 0.80
            elif temp_error < -0.5:
                act_cool = 0.10
            elif is_expensive and temp_error <= 0.0:
                act_cool = 0.20
            elif occupants > 0.0 and temp_error > 0.0:
                act_cool = 0.60
            else:
                act_cool = 0.40

            # Active actions order for this schema: ['dhw_storage', 'electrical_storage', 'cooling_device']
            # Align with env.action_names[b_idx]
            b_actions: list[float] = []
            for act_name in env.action_names[b_idx]:
                if act_name == "dhw_storage":
                    b_actions.append(float(np.clip(act_dhw, -1.0, 1.0)))
                elif act_name == "electrical_storage":
                    b_actions.append(float(np.clip(act_elec, -1.0, 1.0)))
                elif act_name == "cooling_device":
                    b_actions.append(float(np.clip(act_cool, 0.0, 1.0)))
                else:
                    b_actions.append(0.0)

            actions.append(b_actions)

        return actions


class RandomActionController(BaseController):
    """Uniform random action controller for exploration and lower-bound baseline."""

    def __init__(self, seed: int = 0) -> None:
        super().__init__(name=f"random_seed{seed}")
        self.rng = np.random.default_rng(seed)

    def predict(self, observations: list[list[float]], env: CityLearnEnv) -> list[list[float]]:
        actions: list[list[float]] = []
        for b in env.buildings:
            low = b.action_space.low
            high = b.action_space.high
            sampled = self.rng.uniform(low=low, high=high)
            actions.append([float(x) for x in sampled])
        return actions
