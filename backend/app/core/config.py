from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SBMARL_", extra="ignore")

    app_name: str = "smartbuilding-marl"
    environment: str = "development"
    project_root: Path = Path(__file__).resolve().parents[3]
    citylearn_pin: str = "3.5.0"

    @property
    def configs_dir(self) -> Path:
        return self.project_root / "configs"

    @property
    def dataset_registry_path(self) -> Path:
        return self.configs_dir / "dataset_registry.yaml"


settings = Settings()
