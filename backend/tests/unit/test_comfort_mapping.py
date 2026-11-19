from app.data.validators.comfort_mapping import load_comfort_mapping, validate_comfort_mapping


def test_tsv_is_not_treated_as_tcv() -> None:
    mapping = load_comfort_mapping()
    issues = validate_comfort_mapping(mapping)
    assert issues == []
    assert mapping.targets["thermal_sensation"].not_equivalent_to == "thermal_comfort"
    assert mapping.forbidden_merge == "row_wise_dataset_merge"


def test_citylearn_counterparts_are_explicit() -> None:
    mapping = load_comfort_mapping()
    clo = mapping.features["clothing_insulation_clo"]
    assert clo.citylearn_counterpart is None
    assert "missing_in_citylearn" in clo.transfer_status
    ta = mapping.features["air_temperature_c"]
    assert ta.citylearn_counterpart == "indoor_dry_bulb_temperature"
