from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.planet import PlanetProfile, ValidationResult
from app.models.state import PlanetAtmosphereState


class CandidateRequest(BaseModel):
    profile: PlanetProfile
    state: PlanetAtmosphereState | None = None
    validation: ValidationResult | None = None
    max_candidates: int = Field(default=5, ge=1, le=20)


class MoleculeCandidate(BaseModel):
    name: str
    formula: str
    classical_score: float
    mixing_ratio_proxy: float = Field(default=0.0, ge=0.0, le=1.0)
    rationale: str
    tag: str


class QuantumCandidateInput(BaseModel):
    name: str
    formula: str
    classical_score: float
    mixing_ratio_proxy: float = Field(default=0.0, ge=0.0, le=1.0)
    tag: str
    rationale: str
    chemistry_modes: list[str] = Field(default_factory=list)


class CandidateResponse(BaseModel):
    candidates: list[MoleculeCandidate] = Field(default_factory=list)
    selected_for_quantum: list[QuantumCandidateInput] = Field(default_factory=list)
    abundance_proxies: dict[str, float] = Field(default_factory=dict)
    chemistry_mode_summary: str = Field(default="")
    chemistry_modes: list[str] = Field(default_factory=list)
