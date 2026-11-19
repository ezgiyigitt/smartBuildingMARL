from app.core.config import settings
from app.data.loaders.yaml_loader import load_yaml
from app.domain.entities.dataset import DatasetRecord, DatasetSource, DatasetStatus


def load_dataset_registry() -> list[DatasetRecord]:
    raw = load_yaml(settings.dataset_registry_path)
    records: list[DatasetRecord] = []
    for dataset_id, payload in raw["datasets"].items():
        sources = [
            DatasetSource(
                name=item["name"],
                url=item["url"],
                doi=item.get("doi"),
            )
            for item in payload.get("official_sources", [])
        ]
        license_notes = payload.get("license_notes", [])
        if isinstance(license_notes, str):
            license_notes = [license_notes]
        if payload.get("license"):
            license_notes = [*license_notes, str(payload["license"])]
        records.append(
            DatasetRecord(
                id=dataset_id,
                title=payload["title"],
                role=payload["role"],
                official_sources=sources,
                local_path=payload["local_path"],
                merge_with_citylearn=bool(payload.get("merge_with_citylearn", False)),
                status=DatasetStatus(payload["status"]),
                scientific_caveat=payload.get("scientific_caveat"),
                license_notes=license_notes,
            )
        )
    return records
