# Implementation plan

## Phase 1 — Architecture (this phase)

Repository layout, documentation, dataset contracts, FastAPI health/registry, Flutter MVVM skeleton, environment verification, tests of contracts (not of trained models).

## Phase 2 — Datasets

Download Dryad + Zenodo with checksums; CityLearn named-dataset copy; quality reports; grouped-split specification; **no** fabricated tables.

Gate: real files on disk and a validation report. If Dryad is unavailable, stop Dataset A and use only the licensed Zenodo subset while documenting reduced coverage.

## Phase 3 — Prediction models

TSV baselines (ordinal/logistic, RF, XGBoost, LightGBM) and occupancy baselines (persistence, seasonal, tree model). Leakage tests.

Gate: training scripts run on **downloaded** data.

## Phase 4 — Uncertainty and explainability

Calibration, split conformal, ECE/Brier, SHAP on the selected model. Document assumption failures.

## Phase 5 — CityLearn baselines

Import CityLearn 3.5, list datasets, inspect schema, select a Dynamics-capable scenario, run BAU and RBC, log KPIs.

Gate: indoor temperature responds to HVAC-related actions, or the comfort controller is not attached.

## Phase 6 — Proposed MARL + filter

CTDE candidate (MAPPO if compatible), independent RL, safety filter wired to prediction sets.

## Phase 7 — Robustness

Disturbance wrappers, multi-seed evaluation, statistical tests if assumptions hold.

## Phase 8 — Productization

Async jobs, remaining API, dashboard binding to real artifacts, PDF/CSV/JSON export of **existing** files.

## Phase 9 — Tests and paper-facing docs

Expand tests; freeze protocol; no result invention.

## First scientific/technical incompatibilities (design-driving)

| Issue | Decision |
| --- | --- |
| ASHRAE vs CityLearn populations | Interface, not merge |
| Challenge 2022 often battery-only | Prefer 2023/dynamics schemas |
| Python 3.14 | Use 3.11 venv |
| CityLearn 2.5 vs 3.5 on PyPI | Pin **3.5.0** (current docs/API) |
| TSV vs TCV | Separate targets |
| Zenodo “Turkish researchers” dataset | Complete-case global subset |
| Formal safety vs conformal | Heuristic filter + honest language |
