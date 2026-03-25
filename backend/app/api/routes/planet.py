from fastapi import APIRouter

from app.models.planet import (
    PlanetGenerationRequest,
    PlanetProfile,
    PlanetValidationRequest,
    ValidationResult,
)
from app.services.planet_service import generate_planet_profile, validate_planet_profile

router = APIRouter()


@router.post("/planet/generate", response_model=PlanetProfile)
def generate_planet(request: PlanetGenerationRequest) -> PlanetProfile:
    return generate_planet_profile(request)


@router.post("/planet/validate", response_model=ValidationResult)
def validate_planet(request: PlanetValidationRequest) -> ValidationResult:
    return validate_planet_profile(request.profile)

