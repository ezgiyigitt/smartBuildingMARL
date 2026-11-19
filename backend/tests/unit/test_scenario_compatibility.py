from app.simulation.citylearn_adapter.compatibility import assess_scenario


def test_battery_only_schema_is_rejected_for_hvac_comfort() -> None:
    report = assess_scenario(
        "toy_battery",
        [["electrical_storage"]],
        [["indoor_dry_bulb_temperature", "occupant_count", "non_shiftable_load"]],
    )
    assert report.occupant_aware_hvac_supported is False
    assert report.has_occupancy is True


def test_dynamics_hvac_schema_is_accepted() -> None:
    report = assess_scenario(
        "toy_dynamics",
        [["cooling_device", "heating_device", "electrical_storage"]],
        [["indoor_dry_bulb_temperature", "occupant_count", "outdoor_dry_bulb_temperature"]],
    )
    assert report.occupant_aware_hvac_supported is True
    assert report.indoor_temperature_actionable is True
