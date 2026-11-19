"""Phase 5: Run CityLearn 2023 Phase 1 baselines and log reproducible experiments."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.simulation.citylearn_adapter.compatibility import assess_scenario
from app.simulation.citylearn_adapter.controllers import (
    BusinessAsUsualController,
    CityLearnBasicRBCController,
    ComfortPriceRuleBasedController,
    RandomActionController,
)
from app.simulation.citylearn_adapter.env_factory import create_citylearn_env
from app.simulation.citylearn_adapter.runner import run_simulation

SCHEMA_PATH = ROOT / "data/raw/citylearn/citylearn_challenge_2023_phase_1/schema.json"
TSV_MODEL = ROOT / "artifacts/models/tsv_transfer_random_forest.joblib"
EXPERIMENTS_DIR = ROOT / "experiments/runs"
REPORTS_DIR = ROOT / "artifacts/reports"


def main() -> int:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=== Phase 5: CityLearn Baseline Simulations ===")
    print(f"Loading schema from: {SCHEMA_PATH}")

    # 1. Inspect live env and enforce compatibility
    test_env, metadata_info, compat = create_citylearn_env(schema_path=SCHEMA_PATH, central_agent=False)
    print("\n--- Live Environment Schema Inspection ---")
    print(f"Dataset name:      {metadata_info.dataset_name}")
    print(f"Buildings count:   {metadata_info.n_buildings} ({metadata_info.building_names})")
    print(f"Building class:    {metadata_info.building_class}")
    print(f"Central agent:     {metadata_info.central_agent}")
    print(f"Simulation steps:  {metadata_info.time_steps} ({metadata_info.seconds_per_time_step} s/step)")
    print(f"Active actions:    {metadata_info.action_names[0]}")
    print(f"Observation count: {len(metadata_info.observation_names[0])} per building")
    print(f"Compatibility:     occupant_aware_hvac_supported={compat.occupant_aware_hvac_supported}")

    # 2. Instantiate baselines
    seed = 0
    controllers = [
        ("business_as_usual", BusinessAsUsualController()),
        ("basic_rbc", CityLearnBasicRBCController(env=test_env)),
        ("comfort_price_rbc", ComfortPriceRuleBasedController()),
        ("random", RandomActionController(seed=seed)),
    ]

    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    results: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "phase": 5,
        "dataset_name": metadata_info.dataset_name,
        "schema_path": str(SCHEMA_PATH),
        "n_buildings": metadata_info.n_buildings,
        "building_names": metadata_info.building_names,
        "building_class": metadata_info.building_class,
        "action_names": metadata_info.action_names[0],
        "observation_count_per_building": len(metadata_info.observation_names[0]),
        "central_agent": metadata_info.central_agent,
        "timesteps": metadata_info.time_steps,
        "seed": seed,
        "runs": {},
    }

    print("\n--- Stepping Baselines (720 timesteps / 30 days) ---")
    for name, ctrl in controllers:
        run_name = f"{timestamp_str}_{name}_seed{seed}"
        run_dir = EXPERIMENTS_DIR / run_name
        print(f"\nRunning baseline: {name} -> {run_dir.relative_to(ROOT)}...")

        metrics = run_simulation(
            schema_path=SCHEMA_PATH,
            controller=ctrl,
            seed=seed,
            output_dir=run_dir,
            tsv_model_path=TSV_MODEL if TSV_MODEL.exists() else None,
        )

        results["runs"][name] = {
            "controller_name": ctrl.name,
            "run_dir": str(run_dir.relative_to(ROOT)),
            "district_energy_kwh": metrics["district"]["total_electricity_consumption_kwh"],
            "citylearn_district_kpis": metrics["district"]["citylearn_kpis"],
            "buildings": metrics["buildings"],
            "diagnostic_comfort_tsv": metrics["diagnostic_comfort_tsv"],
        }

        dist_kpis = metrics["district"]["citylearn_kpis"]
        cost = dist_kpis.get("cost_total", "N/A")
        carbon = dist_kpis.get("carbon_emissions_total", "N/A")
        print(f"  Total Electricity: {metrics['district']['total_electricity_consumption_kwh']:.2f} kWh")
        print(f"  CityLearn Cost KPI: {cost}")
        print(f"  CityLearn Carbon KPI: {carbon}")

    report_path = REPORTS_DIR / "phase5_baselines.json"
    report_path.write_text(
        json.dumps(results, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o)),
        encoding="utf-8",
    )
    print(f"\nSaved consolidated Phase 5 report to {report_path}")

    # Summary table
    print("\n" + "=" * 90)
    print(f"{'Baseline':22s} | {'Energy (kWh)':12s} | {'Cost KPI':10s} | {'Carbon KPI':10s} | {'Violation Rate':14s} | {'Occupant-Viol-DegH':18s}")
    print("-" * 90)
    for name in results["runs"]:
        r = results["runs"][name]
        e = r["district_energy_kwh"]
        kpis = r["citylearn_district_kpis"]
        c_cost = f"{kpis.get('cost_total', 0.0):.3f}" if kpis.get('cost_total') is not None else "N/A"
        c_carb = f"{kpis.get('carbon_emissions_total', 0.0):.3f}" if kpis.get('carbon_emissions_total') is not None else "N/A"

        # Mean violation rate across buildings
        v_rates = [b_data["setpoint_violation_rate"] for b_data in r["buildings"].values()]
        mean_v = f"{sum(v_rates)/len(v_rates)*100:.1f}%"

        # Sum of occupant weighted violation degree hours
        occ_v = sum(b_data["occupant_weighted_violation_degree_hours"] for b_data in r["buildings"].values())
        print(f"{name:22s} | {e:12.1f} | {c_cost:10s} | {c_carb:10s} | {mean_v:14s} | {occ_v:18.1f}")
    print("=" * 90)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
