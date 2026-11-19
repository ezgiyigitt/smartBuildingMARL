"""Unit tests for Phase 5: CityLearn environment adapter, baselines, and compatibility gates."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from app.simulation.citylearn_adapter.compatibility import assess_scenario
from app.simulation.citylearn_adapter.controllers import (
    BusinessAsUsualController,
    CityLearnBasicRBCController,
    ComfortPriceRuleBasedController,
    RandomActionController,
)
from app.simulation.citylearn_adapter.disturbances import (
    ObservationDisturbanceWrapper,
    ObservationSanitizer,
)
from app.simulation.citylearn_adapter.env_factory import create_citylearn_env
from app.simulation.citylearn_adapter.runner import run_simulation

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "data/raw/citylearn/citylearn_challenge_2023_phase_1/schema.json"
REPORT_PATH = ROOT / "artifacts/reports/phase5_baselines.json"


def test_env_constructs_and_metadata_is_valid() -> None:
    if not SCHEMA_PATH.exists():
        pytest.skip(f"CityLearn schema file not found at {SCHEMA_PATH}")

    env, metadata, compat = create_citylearn_env(
        schema_path=SCHEMA_PATH,
        central_agent=False,
    )

    assert metadata.n_buildings == 3
    assert metadata.building_class == "LSTMDynamicsBuilding"
    assert metadata.central_agent is False
    assert metadata.time_steps == 720
    assert metadata.dataset_name == "citylearn_challenge_2023_phase_1"
    assert compat.occupant_aware_hvac_supported is True
    assert compat.indoor_temperature_actionable is True
    assert compat.has_occupancy is True

    # Active actions must contain cooling_device
    flat_actions = set(compat.action_names)
    assert "cooling_device" in flat_actions
    assert "dhw_storage" in flat_actions
    assert "electrical_storage" in flat_actions


def test_invalid_battery_only_fixture_still_rejected() -> None:
    # 1. Toy battery-only scenario without cooling/heating
    toy_report = assess_scenario(
        "toy_battery_only",
        [["electrical_storage"]],
        [["indoor_dry_bulb_temperature", "occupant_count"]],
    )
    assert toy_report.occupant_aware_hvac_supported is False
    assert toy_report.indoor_temperature_actionable is False
    assert any("No cooling/heating" in r for r in toy_report.reasons)

    # 2. Scenario without indoor temperature observation
    no_temp_report = assess_scenario(
        "toy_no_temp",
        [["cooling_device"]],
        [["occupant_count", "net_electricity_consumption"]],
    )
    assert no_temp_report.occupant_aware_hvac_supported is False


def test_controllers_step_short_episode(tmp_path: Path) -> None:
    if not SCHEMA_PATH.exists():
        pytest.skip(f"CityLearn schema file not found at {SCHEMA_PATH}")

    # Run short 3-step test episodes to verify controller prediction and environment stepping
    controllers = [
        BusinessAsUsualController(),
        ComfortPriceRuleBasedController(),
        RandomActionController(seed=42),
    ]

    for ctrl in controllers:
        out_dir = tmp_path / f"test_run_{ctrl.name}"
        metrics = run_simulation(
            schema_path=SCHEMA_PATH,
            controller=ctrl,
            seed=0,
            simulation_start_time_step=0,
            simulation_end_time_step=3,
            output_dir=out_dir,
        )

        assert metrics["timesteps"] >= 3
        assert "district" in metrics
        assert "total_electricity_consumption_kwh" in metrics["district"]
        assert metrics["district"]["total_electricity_consumption_kwh"] >= 0.0
        assert "buildings" in metrics
        assert len(metrics["buildings"]) == 3

        # Verify artifacts written to disk
        assert (out_dir / "config.yaml").exists()
        assert (out_dir / "versions.json").exists()
        assert (out_dir / "metrics.json").exists()

        saved_metrics = json.loads((out_dir / "metrics.json").read_text(encoding="utf-8"))
        assert "total_electricity_consumption_kwh" in saved_metrics["district"]
        for b_name in ("Building_1", "Building_2", "Building_3"):
            assert b_name in saved_metrics["buildings"]
            b_info = saved_metrics["buildings"][b_name]
            assert "electricity_consumption_kwh" in b_info
            assert "mean_indoor_temperature_c" in b_info
            assert "setpoint_violation_rate" in b_info
            assert 0.0 <= b_info["setpoint_violation_rate"] <= 1.0


def test_observation_sanitizer_smoke_test() -> None:
    # Inject NaN observations and verify sanitizer replaces with fallback
    disturber = ObservationDisturbanceWrapper(noise_std=0.0, dropout_prob=1.0, seed=0)
    raw_obs = [[23.0, 0.5, 1.0], [21.5, 0.0, 2.0]]
    dropped_obs = disturber.apply(raw_obs)

    # All should be NaN due to dropout_prob = 1.0
    assert all(np.isnan(x) for b in dropped_obs for x in b)

    sanitizer = ObservationSanitizer(fallback_value=22.0)
    clean_obs = sanitizer.sanitize(dropped_obs)

    assert not any(np.isnan(x) for b in clean_obs for x in b)
    assert clean_obs[0][0] == 22.0


def test_phase5_report_metrics_file_has_required_keys() -> None:
    if not REPORT_PATH.exists():
        pytest.skip("phase5_baselines.json not yet written on disk.")

    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    assert report["phase"] == 5
    assert report["n_buildings"] == 3
    assert "runs" in report

    for baseline_name in ("business_as_usual", "basic_rbc", "comfort_price_rbc", "random"):
        assert baseline_name in report["runs"]
        run_data = report["runs"][baseline_name]
        assert "district_energy_kwh" in run_data
        assert run_data["district_energy_kwh"] > 0.0
        assert "citylearn_district_kpis" in run_data
        assert "buildings" in run_data
        assert "diagnostic_comfort_tsv" in run_data
