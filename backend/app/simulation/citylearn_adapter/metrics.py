"""Simulation metrics extraction, CityLearn KPI logging, and diagnostic comfort scoring."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from citylearn.citylearn import CityLearnEnv


def compute_episode_metrics(
    env: CityLearnEnv,
    tsv_model_path: Path | None = None,
    rh_series_per_building: dict[str, Sequence[float]] | None = None,
) -> dict[str, Any]:
    """Extract physics metrics, official CityLearn KPIs, and diagnostic comfort estimates."""
    n_timesteps = env.time_step
    building_names = [b.name for b in env.buildings]

    # 1. Official CityLearn KPIs via env.evaluate()
    kpi_df = env.evaluate()
    kpi_dict: dict[str, Any] = {"district": {}, "buildings": {}}
    if isinstance(kpi_df, pd.DataFrame) and not kpi_df.empty:
        for _, row in kpi_df.iterrows():
            func_name = str(row.get("cost_function", ""))
            val = row.get("value")
            name = str(row.get("name", ""))
            level = str(row.get("level", ""))

            val_float = float(val) if pd.notnull(val) else None

            if level == "district":
                kpi_dict["district"][func_name] = val_float
            else:
                if name not in kpi_dict["buildings"]:
                    kpi_dict["buildings"][name] = {}
                kpi_dict["buildings"][name][func_name] = val_float

    # 2. Building Physics & Operational Metrics
    per_building_metrics: dict[str, Any] = {}
    total_district_energy_kwh = 0.0

    for b in env.buildings:
        net_elec = np.asarray(b.net_electricity_consumption[:n_timesteps], dtype=float)
        indoor_temp = np.asarray(b.indoor_dry_bulb_temperature[:n_timesteps], dtype=float)
        cooling_setpoint = np.asarray(b.indoor_dry_bulb_temperature_cooling_set_point[:n_timesteps], dtype=float)
        occupants = np.asarray(b.occupant_count[:n_timesteps], dtype=float)

        # Non-negative electricity consumption (kWh)
        energy_kwh = float(np.sum(np.clip(net_elec, 0.0, None)))
        total_district_energy_kwh += energy_kwh

        # Setpoint violations (overheating in cooling mode: T_in > T_set + 0.5 C)
        temp_delta = indoor_temp - cooling_setpoint
        overheat_delta = np.maximum(0.0, temp_delta)
        violation_hours = int(np.sum(temp_delta > 0.5))
        violation_rate = float(violation_hours / max(1, len(temp_delta)))

        occupant_weighted_violation = float(np.sum(occupants * overheat_delta))

        per_building_metrics[b.name] = {
            "electricity_consumption_kwh": energy_kwh,
            "mean_indoor_temperature_c": float(np.mean(indoor_temp)),
            "mean_cooling_setpoint_c": float(np.mean(cooling_setpoint)),
            "max_overheat_delta_c": float(np.max(overheat_delta)),
            "mean_overheat_delta_c": float(np.mean(overheat_delta)),
            "setpoint_violation_hours": violation_hours,
            "setpoint_violation_rate": violation_rate,
            "occupant_weighted_violation_degree_hours": occupant_weighted_violation,
        }

    # 3. Diagnostic TSV Predictions (Phase 3/4 Transfer Model)
    diagnostic_comfort: dict[str, Any] = {
        "status": "not_run",
        "domain_shift_warning": (
            "Diagnostic indicator only. ASHRAE field survey models transferred to "
            "CityLearn simulation lack dynamic clo/met/vel states. Do not claim measured comfort."
        ),
    }

    if tsv_model_path is not None and tsv_model_path.exists():
        try:
            model = joblib.load(tsv_model_path)
            weather_out_temp = np.asarray(env.buildings[0].weather.outdoor_dry_bulb_temperature[:n_timesteps], dtype=float)

            tsv_per_building: dict[str, Any] = {}
            for b in env.buildings:
                indoor_temp = np.asarray(b.indoor_dry_bulb_temperature[:n_timesteps], dtype=float)

                # Relative humidity: read from provided series or fallback to default 50%
                if rh_series_per_building and b.name in rh_series_per_building:
                    rh = np.asarray(rh_series_per_building[b.name][:n_timesteps], dtype=float)
                else:
                    rh = np.full(len(indoor_temp), 50.0)

                # Transfer features: ta, rh, t_out
                df_transfer = pd.DataFrame({
                    "ta": indoor_temp,
                    "rh": rh,
                    "t_out": weather_out_temp,
                })

                preds = model.predict(df_transfer)
                preds_arr = np.asarray(preds, dtype=float)

                tsv_per_building[b.name] = {
                    "mean_predicted_tsv": float(np.mean(preds_arr)),
                    "std_predicted_tsv": float(np.std(preds_arr)),
                    "fraction_acceptable_comfort_band": float(np.mean(np.abs(preds_arr) <= 1.0)),
                    "fraction_severe_discomfort": float(np.mean(np.abs(preds_arr) >= 2.0)),
                }

            diagnostic_comfort["status"] = "computed"
            diagnostic_comfort["buildings"] = tsv_per_building
        except Exception as exc:
            diagnostic_comfort["status"] = f"error: {exc}"

    return {
        "timesteps": n_timesteps,
        "district": {
            "total_electricity_consumption_kwh": total_district_energy_kwh,
            "citylearn_kpis": kpi_dict["district"],
        },
        "buildings": per_building_metrics,
        "building_citylearn_kpis": kpi_dict["buildings"],
        "diagnostic_comfort_tsv": diagnostic_comfort,
    }
