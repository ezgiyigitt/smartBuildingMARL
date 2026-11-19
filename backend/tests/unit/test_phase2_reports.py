from pathlib import Path

import json

ROOT = Path(__file__).resolve().parents[3]


def test_phase2_quality_report_exists_and_uses_real_counts() -> None:
    path = ROOT / "artifacts" / "reports" / "phase2_quality.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["ashrae"]["n_measurement_rows"] == 109033
    assert data["ashrae"]["target_non_null"]["thermal_comfort"] < data["ashrae"]["target_non_null"]["thermal_sensation"]
    assert data["zenodo"]["n_rows"] == 10618
    assert data["citylearn"]["compatibility"]["indoor_temperature_actionable"] is True
