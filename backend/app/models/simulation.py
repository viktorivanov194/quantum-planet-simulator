from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.chemistry import CandidateResponse, QuantumCandidateInput
from app.models.planet import AtmosphericProfileInput, PlanetProfile, ValidationResult
from app.models.molecular_probe import MolecularProbeResult
from app.models.qfg import QFGSimulationConfig, QFGSimulationResult
from app.models.report import FinalDiscoveryReport
from app.models.scientific import ScientificProxyProfile, VisualPhysicsProfile
from app.models.state import PlanetAtmosphereState
from app.models.spectrum import SpectrumResponse


class SimulationRunRequest(BaseModel):
    generation_mode: str = Field(default="auto")
    star_type: str = Field(default="K-type")
    orbit_zone: str = Field(default="temperate")
    seed: int | None = Field(default=None)
    preset_name: str | None = Field(default=None)
    planet_name: str | None = Field(default=None)
    radius_rearth: float | None = Field(default=None, ge=0.0)
    mass_mearth: float | None = Field(default=None, ge=0.0)
    gravity_ms2: float | None = Field(default=None, ge=0.0)
    equilibrium_temperature_k: float | None = Field(default=None, ge=0.0)
    radiation_level: float | None = Field(default=None, ge=0.0)
    atmosphere: AtmosphericProfileInput | None = Field(default=None)
    max_candidates: int = Field(default=3, ge=1, le=10)
    selected_candidate: str | None = Field(default=None)
    quantum_runtime_mode: str = Field(default="demo_balanced")
    qfg: QFGSimulationConfig = Field(default_factory=QFGSimulationConfig)


class SimulationRunResponse(BaseModel):
    profile: PlanetProfile
    state: PlanetAtmosphereState
    validation: ValidationResult
    chemistry: CandidateResponse
    selected_candidate: QuantumCandidateInput | None = None
    molecular_probe: MolecularProbeResult | None = None
    spectrum: SpectrumResponse | None = None
    qfg: QFGSimulationResult | None = None
    scientific_proxy_profile: ScientificProxyProfile
    visual_physics_profile: VisualPhysicsProfile
    report_summary: str = Field(default="")
    final_report: FinalDiscoveryReport | None = None
