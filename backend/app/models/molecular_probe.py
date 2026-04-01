from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.models.chemistry import QuantumCandidateInput

ProbeRuntimeMode = Literal["auto", "live_if_supported", "cached_only", "disabled"]
ProbeStatus = Literal["live", "cached_reference", "unsupported", "failed"]
ProbeModel = Literal["toy_hamiltonian", "reduced_basis_reference", "offline_reference", "none"]
ProbeFailureReason = Literal[
    "solver_unavailable",
    "solver_error",
    "cache_missing",
    "molecule_unsupported",
    "live_not_permitted",
    "invalid_request",
]


class MolecularProbeRequest(BaseModel):
    candidates: list[QuantumCandidateInput] = Field(default_factory=list)
    runtime_mode: ProbeRuntimeMode = Field(default="auto")
    selected_formula: str | None = Field(default=None)
    cache_path: str | None = Field(default=None)
    allow_live_probe: bool = Field(default=True)
    allow_cached_reference: bool = Field(default=True)
    selected_by_pipeline: bool = Field(default=True)
    selection_reason: str = Field(default="chemistry_shortlist")
    report_context_label: str | None = Field(default=None)


class MolecularProbeResult(BaseModel):
    molecule_name: str
    formula: str

    probe_status: ProbeStatus
    probe_model: ProbeModel

    live_calculation_attempted: bool = False
    live_calculation_allowed: bool = False
    cached_reference_allowed: bool = False

    geometry_reference: str | None = None
    method_label: str | None = None
    basis_label: str | None = None

    electronic_energy_proxy: float | None = None
    reference_energy_proxy: float | None = None
    probe_agreement: float | None = Field(default=None, ge=0.0, le=1.0)

    provenance_label: str = Field(default="")
    provenance_details: list[str] = Field(default_factory=list)

    educational_note: str = Field(default="")
    scientific_caveats: list[str] = Field(default_factory=list)

    failure_reason: ProbeFailureReason | None = None
    failure_message: str | None = None

    cross_species_comparable: bool = Field(default=False)
    atmospheric_inference_allowed: bool = Field(default=False)
    spectrum_influence_allowed: bool = Field(default=False)


class MolecularProbeResponse(BaseModel):
    results: list[MolecularProbeResult] = Field(default_factory=list)
    selected_result: MolecularProbeResult | None = None
    runtime_mode: str
    live_probe_used: bool = False
