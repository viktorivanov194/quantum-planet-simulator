from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.models.chemistry import QuantumCandidateInput


class QuantumEvaluationRequest(BaseModel):
    candidates: list[QuantumCandidateInput] = Field(default_factory=list)
    runtime_mode: Literal["cached_only", "demo_balanced", "fallback_only"] = Field(default="demo_balanced")
    selected_formula: str | None = Field(default=None)
    cache_path: str | None = Field(default=None)


class QuantumEvaluationResult(BaseModel):
    name: str
    formula: str
    ground_state_energy_proxy: float
    stability_score: float = Field(ge=0.0, le=1.0)
    source: Literal["cached", "live", "fallback"]
    notes: list[str] = Field(default_factory=list)
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    classical_reference_energy_proxy: float | None = Field(default=None)
    baseline_agreement_score: float | None = Field(default=None, ge=0.0, le=1.0)
    verification_mode: str | None = Field(default=None)


class QuantumEvaluationResponse(BaseModel):
    results: list[QuantumEvaluationResult] = Field(default_factory=list)
    selected_result: QuantumEvaluationResult | None = None
    runtime_mode: str
    live_evaluation_used: bool = False
