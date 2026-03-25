from fastapi import APIRouter

from app.models.chemistry import CandidateRequest, CandidateResponse
from app.services.chemistry_service import get_candidate_molecules

router = APIRouter()


@router.post("/chemistry/candidates", response_model=CandidateResponse)
def chemistry_candidates(request: CandidateRequest) -> CandidateResponse:
    return get_candidate_molecules(request)

