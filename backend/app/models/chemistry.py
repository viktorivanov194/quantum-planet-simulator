from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.planet import PlanetProfile, ValidationResult


class CandidateRequest(BaseModel):
    profile: PlanetProfile
    validation: ValidationResult | None = None
    max_candidates: int = Field(default=5, ge=1, le=20)


class MoleculeCandidate(BaseModel):
    name: str
    formula: str
    classical_score: float
    rationale: str
    tag: str


class QuantumCandidateInput(BaseModel):
    name: str
    formula: str
    classical_score: float
    tag: str
    rationale: str
    chemistry_modes: list[str] = Field(default_factory=list)


class CandidateResponse(BaseModel):
    candidates: list[MoleculeCandidate] = Field(default_factory=list)
    selected_for_quantum: list[QuantumCandidateInput] = Field(default_factory=list)
    chemistry_mode_summary: str = Field(default="")
    chemistry_modes: list[str] = Field(default_factory=list)
