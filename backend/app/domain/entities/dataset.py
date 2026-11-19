from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class DatasetStatus(str, Enum):
    not_downloaded = "not_downloaded"
    inspect_after_package_install = "inspect_after_package_install"
    downloaded = "downloaded"
    validated = "validated"


class DatasetSource(BaseModel):
    name: str
    url: HttpUrl
    doi: str | None = None


class DatasetRecord(BaseModel):
    id: str
    title: str
    role: str
    official_sources: list[DatasetSource]
    local_path: str
    merge_with_citylearn: bool = False
    status: DatasetStatus
    scientific_caveat: str | None = None
    license_notes: list[str] = Field(default_factory=list)
