from app.data.repositories.dataset_registry import load_dataset_registry


def test_registry_contains_required_datasets() -> None:
    records = {item.id: item for item in load_dataset_registry()}
    assert "ashrae_gcdb2" in records
    assert "zenodo_tsv_complete_case" in records
    assert "citylearn_public" in records
    assert records["ashrae_gcdb2"].merge_with_citylearn is False
    assert records["zenodo_tsv_complete_case"].merge_with_citylearn is False
    assert records["ashrae_gcdb2"].status.value == "downloaded"
    caveat = records["zenodo_tsv_complete_case"].scientific_caveat or ""
    assert "NOT a field study of occupants in Turkey" in caveat


def test_registry_does_not_claim_local_ashrae_files() -> None:
    ashrae = next(item for item in load_dataset_registry() if item.id == "ashrae_gcdb2")
    assert ashrae.status.value == "downloaded"
