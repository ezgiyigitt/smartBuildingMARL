from pydantic import BaseModel


class TargetSpec(BaseModel):
    raw_column: str
    concept: str
    use_as: str
    not_equivalent_to: str | None = None


class FeatureSpec(BaseModel):
    raw_column: str
    citylearn_counterpart: str | None = None
    transfer_status: str


class ComfortMapping(BaseModel):
    targets: dict[str, TargetSpec]
    features: dict[str, FeatureSpec]
    grouping_keys_for_validation: list[str]
    forbidden_merge: str = "row_wise_dataset_merge"
