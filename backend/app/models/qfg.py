from __future__ import annotations

from pydantic import BaseModel, Field


class QFGDriveConfig(BaseModel):
    enabled: bool = Field(default=True)
    amplitude_1: float = Field(default=0.012, ge=0.0, le=1.0)
    amplitude_2: float = Field(default=0.009, ge=0.0, le=1.0)
    frequency_1: float = Field(default=0.11, ge=0.0, le=10.0)
    frequency_2: float = Field(default=0.16, ge=0.0, le=10.0)
    phase_offset: float = Field(default=0.0, ge=-6.2832, le=6.2832)


class QFGSimulationConfig(BaseModel):
    enabled: bool = Field(default=True)
    grid_size: int = Field(default=24, ge=12, le=64)
    steps: int = Field(default=40, ge=4, le=200)
    dt: float = Field(default=0.035, gt=0.0, le=1.0)
    alpha: float = Field(default=0.34, ge=0.0, le=2.0)
    lambda_vacuum: float = Field(default=0.28, ge=0.0, le=2.0)
    rho0: float = Field(default=0.72, ge=0.0, le=3.0)
    damping: float = Field(default=0.022, ge=0.0, le=1.0)
    coupling_beta: float = Field(default=0.18, ge=0.0, le=2.0)
    drive: QFGDriveConfig = Field(default_factory=QFGDriveConfig)


class QFGObservablePoint(BaseModel):
    step: int
    total_energy: float
    coherence: float = Field(ge=0.0, le=1.0)
    mode_variance: float = Field(ge=0.0)
    resonance_signal: float = Field(ge=0.0)


class QFGSimulationResult(BaseModel):
    enabled: bool = True
    model_version: str = Field(default="qfg-mvp-0.1")
    grid_size: int
    steps: int
    dt: float
    coupling_beta: float
    resonance_detected: bool = False
    resonance_frequency_delta: float = Field(default=0.0, ge=0.0)
    stability_score: float = Field(default=0.0, ge=0.0, le=1.0)
    coherence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    density_peak: float = Field(default=0.0, ge=0.0)
    density_mean: float = Field(default=0.0, ge=0.0)
    phi_alignment_score: float = Field(default=0.0, ge=0.0, le=1.0)
    dominant_mode_hint: str = Field(default="broadband")
    notes: list[str] = Field(default_factory=list)
    observables: list[QFGObservablePoint] = Field(default_factory=list)
