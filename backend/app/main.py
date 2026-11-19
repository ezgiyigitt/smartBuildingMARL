from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import datasets, health
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(
    title="Occupant-Aware Safe MARL Research API",
    description=(
        "Simulation-only research backend. Thermal models and CityLearn experiments "
        "are not claimed complete until their phases produce artifacts on disk."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(datasets.router)
