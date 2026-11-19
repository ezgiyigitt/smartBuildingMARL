from pathlib import Path

from app.core.config import settings
from app.data.loaders.yaml_loader import load_yaml
from app.domain.entities.comfort_mapping import ComfortMapping, FeatureSpec, TargetSpec

REQUIRED_ASHRAE_COLUMNS = {
    "ta",
    "rh",
    "vel",
    "clo",
    "met",
    "t_out",
    "thermal_sensation",
    "thermal_comfort",
    "thermal_acceptability",
    "building_id",
}


def load_comfort_mapping(path: Path | None = None) -> ComfortMapping:
    mapping_path = path or settings.configs_dir / "comfort_feature_mapping.yaml"
    raw = load_yaml(mapping_path)
    targets = {key: TargetSpec(**value) for key, value in raw["targets"].items()}
    features = {key: FeatureSpec(**value) for key, value in raw["features"].items()}
    return ComfortMapping(
        targets=targets,
        features=features,
        grouping_keys_for_validation=list(raw["grouping_keys_for_validation"]),
        forbidden_merge=raw["citylearn_bridge_policy"]["forbidden"],
    )


def validate_comfort_mapping(mapping: ComfortMapping) -> list[str]:
    """Return human-readable contract violations. Empty list means the YAML contract holds."""
    issues: list[str] = []
    tsv = mapping.targets.get("thermal_sensation")
    tcv = mapping.targets.get("thermal_comfort")
    if tsv is None or tsv.raw_column != "thermal_sensation":
        issues.append("TSV target must map to thermal_sensation")
    if tcv is None or tcv.raw_column != "thermal_comfort":
        issues.append("TCV target must map to thermal_comfort")
    if tsv and tsv.not_equivalent_to != "thermal_comfort":
        issues.append("TSV must be marked not equivalent to thermal_comfort")
    if tcv and tcv.not_equivalent_to != "thermal_sensation":
        issues.append("TCV must be marked not equivalent to thermal_sensation")
    if mapping.forbidden_merge != "row_wise_dataset_merge":
        issues.append("Bridge policy must forbid row-wise merges")
    mapped_columns = {spec.raw_column for spec in mapping.features.values()}
    mapped_columns.update(spec.raw_column for spec in mapping.targets.values())
    mapped_columns.update(mapping.grouping_keys_for_validation)
    missing = REQUIRED_ASHRAE_COLUMNS - mapped_columns
    if missing:
        issues.append(f"Missing required codebook columns in mapping: {sorted(missing)}")
    return issues
