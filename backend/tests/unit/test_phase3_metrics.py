import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_phase3_metrics_exist() -> None:
    data = json.loads((ROOT / "artifacts/reports/phase3_metrics.json").read_text(encoding="utf-8"))
    assert data["comfort_full_features"]["selected"] in {"logreg", "random_forest", "xgboost", "lightgbm"}
    assert "test" in data["comfort_full_features"]["models"][data["comfort_full_features"]["selected"]]["metrics"]
    assert data["occupancy"]["horizons"]["1"]["selected"] in {"persistence", "ridge", "random_forest", "lightgbm"}
