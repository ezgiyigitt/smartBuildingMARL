# Occupant-Aware, Uncertainty-Calibrated Safe MARL for Smart Building Energy Management

Simulation-based academic research software. It does **not** control physical HVAC equipment.

**Türkçe:** Kullanıcı odaklı, belirsizlik kalibrasyonuna sahip, güvenlik kısıtlı çoklu ajan pekiştirmeli öğrenme ile akıllı bina enerji yönetimi. Sistem yalnızca simülasyondur; gerçek bir binayı kontrol etmez.

## Current status

Phase 1 (repository architecture) is in progress. No thermal models have been trained, no CityLearn policies have been evaluated, and no experimental results exist yet.

Raw ASHRAE and Zenodo files are **not** in this repository. They must be downloaded by the researcher under the published licenses.

## Research question

Can an uncertainty-aware, occupant-sensitive and safety-constrained multi-agent reinforcement learning framework achieve a better balance between building energy efficiency, occupant thermal sensation risk, and operational reliability than conventional rule-based and reinforcement learning methods under uncertain operating conditions?

Predicted thermal sensation is **not** treated as measured thermal comfort unless a valid Thermal Comfort Vote (TCV) or acceptability label is used.

## Layout

| Path | Role |
| --- | --- |
| `backend/` | FastAPI application, scientific modules, tests |
| `frontend/` | Flutter MVVM research dashboard |
| `configs/` | Dataset registry, feature mapping, CityLearn pin |
| `data/` | Local raw/processed data (git-ignored) |
| `experiments/` | Run directories with configs and metrics |
| `artifacts/` | Models, figures, reports |
| `docs/` | Phase reports |

Key documents:

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [RESEARCH_METHODOLOGY.md](RESEARCH_METHODOLOGY.md)
- [DATASET_DOCUMENTATION.md](DATASET_DOCUMENTATION.md)
- [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md)
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- [LITERATURE_REVIEW.md](LITERATURE_REVIEW.md)
- [LIMITATIONS.md](LIMITATIONS.md)
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
- [CITATION.bib](CITATION.bib)

## Environment

This workstation’s default `python` is **3.14.7**. CityLearn 3.5.0 is not validated on 3.14. Use **Python 3.11**:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .\backend\[dev]
```

Pinned scientific simulator: **CityLearn 3.5.0** (Gymnasium API, `gymnasium>=0.28.1,<2.0.0`).

Do not upgrade CityLearn, NumPy, or Gymnasium casually. Compatibility is recorded after a successful install in `backend/requirements/lock.txt`.

## Flutter dashboard

```powershell
cd frontend
flutter pub get
flutter test
flutter run
```

The UI must not train models. It calls the FastAPI backend.

## Tests

```powershell
.\.venv\Scripts\python -m pytest backend\tests -q
```

## Scientific rules

1. Do not invent metrics, citations, or trained-model performance.
2. Do not row-merge ASHRAE occupant surveys with CityLearn building timesteps.
3. Do not claim formal safety from conformal prediction.
4. Do not use Challenge 2022 battery-only control as HVAC comfort control without schema evidence that indoor temperature is action-dependent.
