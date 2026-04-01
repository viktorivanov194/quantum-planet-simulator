from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.chemistry import QuantumCandidateInput
from app.models.planet import PlanetProfile
from app.models.quantum import QuantumEvaluationResult
from app.models.scientific import ScientificProxyProfile
from app.models.state import PlanetAtmosphereState


class SpectrumRequest(BaseModel):
    profile: PlanetProfile
    state: PlanetAtmosphereState | None = None
    chemistry_modes: list[str] = Field(default_factory=list)
    abundance_proxies: dict[str, float] = Field(default_factory=dict)
    quantum_result: QuantumEvaluationResult | None = None
    chemistry_candidates: list[QuantumCandidateInput] = Field(default_factory=list)
    scientific_profile: ScientificProxyProfile | None = None


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
    generator: str = Field(default="geometry_aware_transmission_proxy")
    selected_formula: str | None = None
    atmospheric_clarity_mode: str = Field(default="clear")
    observation_confidence_mode: str = Field(default="strong-feature")
    spectral_resolution_proxy: float = Field(default=80.0, ge=1.0)
    signal_to_noise_proxy: float = Field(default=10.0, ge=0.0)
    noise_floor_proxy: float = Field(default=0.003, ge=0.0)
    stellar_variability_proxy: float = Field(default=0.05, ge=0.0)


class SpectrumResponse(BaseModel):
    wavelengths: list[float] = Field(default_factory=list)
    absorption_values: list[float] = Field(default_factory=list)
    points: list[SpectrumPoint] = Field(default_factory=list)
    highlighted_features: list[SpectrumFeature] = Field(default_factory=list)
    dominant_molecules: list[str] = Field(default_factory=list)
    summary_text: str = Field(default="")
    metadata: SpectrumMetadata = Field(default_factory=SpectrumMetadata)
