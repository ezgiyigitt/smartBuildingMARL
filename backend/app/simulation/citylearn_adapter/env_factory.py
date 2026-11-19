"""CityLearn environment factory and runtime compatibility verification."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from citylearn.citylearn import CityLearnEnv

from app.simulation.citylearn_adapter.compatibility import ScenarioCompatibility, assess_scenario


@dataclass(frozen=True)
class EnvMetadata:
    dataset_name: str
    schema_path: str
    n_buildings: int
    building_names: list[str]
    building_class: str
    action_names: list[list[str]]
    observation_names: list[list[str]]
    central_agent: bool
    time_steps: int
    seconds_per_time_step: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def create_citylearn_env(
    schema_path: str | Path,
    central_agent: bool = False,
    simulation_start_time_step: int | None = None,
    simulation_end_time_step: int | None = None,
) -> tuple[CityLearnEnv, EnvMetadata, ScenarioCompatibility]:
    """Construct CityLearnEnv from schema and enforce live compatibility gates.

    Hard rule: If cooling_device is absent at runtime, STOP and raise RuntimeError;
    never attach comfort logic to non-HVAC scenarios.
    """
    path_obj = Path(schema_path).resolve()
    if not path_obj.exists():
        raise FileNotFoundError(f"CityLearn schema not found at {path_obj}")

    env = CityLearnEnv(
        schema=str(path_obj),
        central_agent=central_agent,
        simulation_start_time_step=simulation_start_time_step,
        simulation_end_time_step=simulation_end_time_step,
    )

    # Re-run compatibility check on LIVE environment names
    compat = assess_scenario(
        dataset_name=path_obj.parent.name,
        action_names=env.action_names,
        observation_names=env.observation_names,
    )

    if not compat.indoor_temperature_actionable:
        raise RuntimeError(
            f"Compatibility check failed for scenario {compat.dataset_name}: "
            f"indoor_temperature_actionable=False. Reasons: {compat.reasons}"
        )

    # Explicit check for cooling_device in active actions
    active_flat_actions = set(compat.action_names)
    if "cooling_device" not in active_flat_actions:
        raise RuntimeError(
            f"cooling_device missing at runtime from active actions: {active_flat_actions}. "
            "Do not attach comfort logic."
        )

    metadata = EnvMetadata(
        dataset_name=path_obj.parent.name,
        schema_path=str(path_obj),
        n_buildings=len(env.buildings),
        building_names=[b.name for b in env.buildings],
        building_class=type(env.buildings[0]).__name__ if env.buildings else "Unknown",
        action_names=env.action_names,
        observation_names=env.observation_names,
        central_agent=env.central_agent,
        time_steps=int(env.time_steps),
        seconds_per_time_step=float(env.seconds_per_time_step),
    )

    return env, metadata, compat
