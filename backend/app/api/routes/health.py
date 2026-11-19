import sys

from fastapi import APIRouter

from app.api.schemas.health import HealthResponse
from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    version = sys.version_info
    python_ok = version[:2] == (3, 11)
    return HealthResponse(
        status="ok" if python_ok else "python_version_unsupported",
        service=settings.app_name,
        citylearn_pin=settings.citylearn_pin,
        python_ok=python_ok,
        simulation_only=True,
        message=(
            "Research API skeleton. No trained models or experimental results are served."
        ),
    )
