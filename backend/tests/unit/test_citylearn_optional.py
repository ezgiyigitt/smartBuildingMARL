import pytest


pytest.importorskip("citylearn")


def test_citylearn_version_pin() -> None:
    from importlib import metadata

    version = metadata.version("CityLearn")
    assert version == "3.5.0"


def test_dataset_listing_is_non_empty() -> None:
    from citylearn.data import DataSet

    dataset = DataSet()
    if hasattr(dataset, "get_dataset_names"):
        names = dataset.get_dataset_names()
    else:
        names = DataSet.get_names()  # type: ignore[attr-defined]
    assert isinstance(names, (list, tuple))
    assert len(names) > 0
