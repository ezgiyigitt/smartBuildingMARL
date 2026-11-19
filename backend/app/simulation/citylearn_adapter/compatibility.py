"""CityLearn schema gates. No environment is created until Phase 5 unless explicitly requested."""

from __future__ import annotations

from dataclasses import dataclass

HVAC_ACTIONS = {
    "cooling_device",
    "heating_device",
    "cooling_or_heating_device",
}

STORAGE_ONLY_HINTS = {
    "electrical_storage",
    "cooling_storage",
    "heating_storage",
    "dhw_storage",
}


@dataclass(frozen=True)
class ScenarioCompatibility:
    dataset_name: str
    action_names: tuple[str, ...]
    observation_names: tuple[str, ...]
    indoor_temperature_actionable: bool
    has_occupancy: bool
    reasons: tuple[str, ...]

    @property
    def occupant_aware_hvac_supported(self) -> bool:
        return self.indoor_temperature_actionable


def assess_scenario(
    dataset_name: str,
    action_names: list[str] | list[list[str]],
    observation_names: list[str] | list[list[str]],
) -> ScenarioCompatibility:
    flat_actions = _flatten_names(action_names)
    flat_obs = _flatten_names(observation_names)
    hvac = HVAC_ACTIONS.intersection(flat_actions)
    reasons: list[str] = []
    indoor_actionable = bool(hvac)
    if not indoor_actionable:
        reasons.append(
            "No cooling/heating device actions. Indoor temperature is likely exogenous; "
            "do not attach occupant-aware HVAC control."
        )
    if "indoor_dry_bulb_temperature" not in flat_obs:
        reasons.append("Observation indoor_dry_bulb_temperature is absent.")
        indoor_actionable = False
    has_occupancy = "occupant_count" in flat_obs
    if not has_occupancy:
        reasons.append("occupant_count is absent; occupancy forecasting cannot use this schema as-is.")
    if not reasons:
        reasons.append("Schema exposes HVAC-related actions and indoor temperature observations.")
    return ScenarioCompatibility(
        dataset_name=dataset_name,
        action_names=tuple(sorted(flat_actions)),
        observation_names=tuple(sorted(flat_obs)),
        indoor_temperature_actionable=indoor_actionable,
        has_occupancy=has_occupancy,
        reasons=tuple(reasons),
    )


def _flatten_names(names: list[str] | list[list[str]]) -> set[str]:
    flat: set[str] = set()
    for item in names:
        if isinstance(item, str):
            flat.add(item)
        else:
            flat.update(item)
    return flat
