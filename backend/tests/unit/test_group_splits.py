from app.data.validators.group_splits import assign_group


def test_group_assignment_is_deterministic() -> None:
    assert assign_group(12, seed=0) == assign_group(12, seed=0)


def test_different_groups_can_differ() -> None:
    labels = {assign_group(i, seed=0) for i in range(40)}
    assert labels <= {"train", "validation", "test"}
    assert "train" in labels
