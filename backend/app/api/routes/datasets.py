from fastapi import APIRouter

from app.data.repositories.dataset_registry import load_dataset_registry
from app.domain.entities.dataset import DatasetRecord

router = APIRouter(tags=["datasets"])


@router.get("/api/datasets", response_model=list[DatasetRecord])
def list_datasets() -> list[DatasetRecord]:
    return load_dataset_registry()
