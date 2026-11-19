"""Simulation execution runner and experiment logging."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from app.simulation.citylearn_adapter.controllers import BaseController
from app.simulation.citylearn_adapter.env_factory import create_citylearn_env
from app.simulation.citylearn_adapter.metrics import compute_episode_metrics


def get_environment_versions() -> dict[str, str]:
    """Capture pinned library versions for reproducible experiment logs."""
    versions = {}
    for pkg in ("CityLearn", "gymnasium", "torch", "numpy", "pandas", "scikit-learn"):
        try:
            versions[pkg] = metadata.version(pkg)
        except Exception:
            versions[pkg] = "unknown"
    return versions


def run_simulation(
    schema_path: str | Path,
    controller: BaseController,
    seed: int = 0,
    simulation_start_time_step: int | None = None,
    simulation_end_time_step: int | None = None,
    output_dir: Path | None = None,
    tsv_model_path: Path | None = None,
) -> dict[str, Any]:
    """Run an episode with a controller and save standard experiment artifacts."""
    schema_path_obj = Path(schema_path).resolve()

    # Read building CSVs to get indoor_relative_humidity if present
    cl_dir = schema_path_obj.parent
    rh_series_per_building: dict[str, list[float]] = {}
    for csv_file in cl_dir.glob("Building_*.csv"):
        try:
            df = pd.read_csv(csv_file)
            if "indoor_relative_humidity" in df.columns:
                rh_series_per_building[csv_file.stem] = df["indoor_relative_humidity"].tolist()
        except Exception:
            pass

    env, metadata_info, compat = create_citylearn_env(
        schema_path=schema_path_obj,
        central_agent=False,
        simulation_start_time_step=simulation_start_time_step,
        simulation_end_time_step=simulation_end_time_step,
    )

    obs, info = env.reset()
    controller.reset()

    terminated = False
    truncated = False

    while not (terminated or truncated):
        actions = controller.predict(obs, env)
        obs, rewards, terminated, truncated, info = env.step(actions)

    metrics = compute_episode_metrics(
        env=env,
        tsv_model_path=tsv_model_path,
        rh_series_per_building=rh_series_per_building,
    )

    # Logging artifacts
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)

        config_data = {
            "controller": controller.name,
            "seed": seed,
            "dataset_name": metadata_info.dataset_name,
            "schema_path": str(schema_path_obj),
            "n_buildings": metadata_info.n_buildings,
            "building_names": metadata_info.building_names,
            "simulation_start_time_step": simulation_start_time_step,
            "simulation_end_time_step": simulation_end_time_step,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        (output_dir / "config.yaml").write_text(yaml.safe_dump(config_data), encoding="utf-8")

        versions_data = {
            "captured_at_utc": datetime.now(timezone.utc).isoformat(),
            "packages": get_environment_versions(),
        }
        (output_dir / "versions.json").write_text(json.dumps(versions_data, indent=2), encoding="utf-8")

        (output_dir / "metrics.json").write_text(
            json.dumps(metrics, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o)),
            encoding="utf-8",
        )

    return metrics
