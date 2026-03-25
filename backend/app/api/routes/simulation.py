from fastapi import APIRouter

from app.models.simulation import SimulationRunRequest, SimulationRunResponse
from app.services.simulation_service import run_simulation_pipeline

router = APIRouter()


@router.post("/simulation/run", response_model=SimulationRunResponse)
def simulation_run(request: SimulationRunRequest) -> SimulationRunResponse:
    return run_simulation_pipeline(request)

