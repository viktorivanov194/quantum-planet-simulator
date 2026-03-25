from fastapi import APIRouter

from app.models.quantum import QuantumEvaluationRequest, QuantumEvaluationResponse
from app.services.quantum_service import evaluate_candidates

router = APIRouter()


@router.post("/quantum/evaluate", response_model=QuantumEvaluationResponse)
def quantum_evaluate(request: QuantumEvaluationRequest) -> QuantumEvaluationResponse:
    return evaluate_candidates(request)
