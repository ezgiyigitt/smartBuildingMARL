from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["simulation_only"] is True
    assert body["citylearn_pin"] == "3.5.0"
    assert "No trained models" in body["message"]


def test_datasets_registry_endpoint() -> None:
    response = client.get("/api/datasets")
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert ids == {"ashrae_gcdb2", "zenodo_tsv_complete_case", "citylearn_public"}
