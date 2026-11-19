from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    citylearn_pin: str
    python_ok: bool
    simulation_only: bool = True
    message: str
