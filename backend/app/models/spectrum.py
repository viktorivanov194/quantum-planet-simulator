from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.chemistry import QuantumCandidateInput
from app.models.planet import PlanetProfile
from app.models.quantum import QuantumEvaluationResult


class SpectrumRequest(BaseModel):
    profile: PlanetProfile
    chemistry_modes: list[str] = Field(default_factory=list)
    quantum_result: QuantumEvaluationResult | None = None
    chemistry_candidates: list[QuantumCandidateInput] = Field(default_factory=list)


class SpectrumPoint(BaseModel):
    wavelength_um: float
    absorption: float


class SpectrumFeature(BaseModel):
    wavelength_um: float
    label: str
    molecule: str
    strength: float


class SpectrumMetadata(BaseModel):
    dominant_molecules: list[str] = Field(default_factory=list)
    summary_text: str = Field(default="")
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    generator: str = Field(default="synthetic_signature_blend")
    selected_formula: str | None = None


class SpectrumResponse(BaseModel):
    wavelengths: list[float] = Field(default_factory=list)
    absorption_values: list[float] = Field(default_factory=list)
    points: list[SpectrumPoint] = Field(default_factory=list)
    highlighted_features: list[SpectrumFeature] = Field(default_factory=list)
    dominant_molecules: list[str] = Field(default_factory=list)
    summary_text: str = Field(default="")
    metadata: SpectrumMetadata = Field(default_factory=SpectrumMetadata)
