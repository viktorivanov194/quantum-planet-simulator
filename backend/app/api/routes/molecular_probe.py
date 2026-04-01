from fastapi import APIRouter

from app.models.molecular_probe import MolecularProbeRequest, MolecularProbeResponse
from app.services.molecular_probe_service import run_molecular_probe

router = APIRouter()


@router.post("/molecular-probe/run", response_model=MolecularProbeResponse)
def molecular_probe_run(request: MolecularProbeRequest) -> MolecularProbeResponse:
    return run_molecular_probe(request)
