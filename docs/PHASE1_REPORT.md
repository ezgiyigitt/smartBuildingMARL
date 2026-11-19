# Phase 1 report

Date: 2026-11-19

## 1. What was implemented

- Repository architecture and scientific documentation (no fabricated results).
- Dataset registry and ASHRAE↔CityLearn feature contract (TSV ≠ TCV; no row merge).
- FastAPI health and registry endpoints.
- Flutter MVVM skeleton (Riverpod ViewModels, repositories, Dio).
- Python 3.11 virtual environment.
- CityLearn **3.5.0** installed and dataset names listed from the live API.

## 2. Files created

See repository root documentation, `backend/`, `frontend/lib/`, `configs/`, and tests. Raw ASHRAE/Zenodo files were **not** created.

## 3. Tests executed

Backend: `pytest backend/tests -q`  
Frontend: `flutter test` (in `frontend/`)

## 4. Test results

- Backend: **10 passed**, 0 failed (after CityLearn install).
- Frontend: **2 passed**, 0 failed (widget test uses a fake health repository so it does not depend on a live server).

## 5. Known limitations

- ASHRAE Dryad and Zenodo files are not downloaded (Phase 2).
- No CityLearn episode has been stepped; only package import and `DataSet().get_dataset_names()`.
- Scenario HVAC-causality is gated in code but not yet applied to a live schema.
- Reward weights are unset.
- Dashboard pages other than datasets/health are honest placeholders.

## 6. Next steps (Phase 2)

1. Download Dryad ASHRAE GCDB II with checksums and license notes.
2. Download Zenodo complete-case xlsx.
3. Copy `citylearn_challenge_2023_phase_1` (candidate) locally and inspect `schema.json` / `action_names`.
4. Produce EDA quality reports on **real** files only.
