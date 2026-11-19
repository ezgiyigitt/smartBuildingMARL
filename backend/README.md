# Research backend

FastAPI service for the simulation-only MARL project. Scientific modules live under `app/` and must remain usable without the HTTP layer.

```powershell
# from repository root, Python 3.11 venv
python -m pip install -e ".\backend[dev]"
python -m pytest backend\tests -q
python -m uvicorn app.main:app --app-dir backend --reload
```

CityLearn is optional in Phase 1:

```powershell
python -m pip install -e ".\backend[sim]"
python backend\scripts\verify_environment.py
```
