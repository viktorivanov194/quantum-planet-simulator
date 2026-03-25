from fastapi import APIRouter

from app.models.spectrum import SpectrumRequest, SpectrumResponse
from app.services.spectrum_service import generate_synthetic_spectrum

router = APIRouter()


@router.post("/spectrum/generate", response_model=SpectrumResponse)
def spectrum_generate(request: SpectrumRequest) -> SpectrumResponse:
    return generate_synthetic_spectrum(request)

