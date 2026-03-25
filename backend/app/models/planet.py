from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PlanetGenerationRequest(BaseModel):
    generation_mode: Literal["auto", "manual", "random"] = Field(default="auto")
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


class AtmosphericProfileInput(BaseModel):
    pressure_bar: float | None = Field(default=None, ge=0.0)
    temperature_k: float | None = Field(default=None, ge=0.0)
    gas_fractions: dict[str, float] | None = Field(default=None)


class AtmosphericProfile(BaseModel):
    gas_fractions: dict[str, float] = Field(default_factory=lambda: {"N2": 0.78, "O2": 0.21, "Ar": 0.01})
    dominant_gases: list[str] = Field(default_factory=lambda: ["N2", "O2", "Ar"])
    pressure_bar: float = Field(default=1.0, ge=0.0)
    temperature_k: float = Field(default=288.0, ge=0.0)


class PlanetProfile(BaseModel):
    planet_name: str = Field(default="QPS-001")
    star_type: str = Field(default="K-type")
    orbit_zone: str = Field(default="temperate")
    generation_mode: str = Field(default="auto")
    radius_rearth: float = Field(default=1.3, ge=0.0)
    mass_mearth: float = Field(default=1.8, ge=0.0)
    gravity_ms2: float = Field(default=10.4, ge=0.0)
    equilibrium_temperature_k: float = Field(default=285.0, ge=0.0)
    radiation_level: float = Field(default=1.0, ge=0.0)
    atmosphere: AtmosphericProfile = Field(default_factory=AtmosphericProfile)
    notes: list[str] = Field(default_factory=list)


class PlanetValidationRequest(BaseModel):
    profile: PlanetProfile


class ValidationIssue(BaseModel):
    code: str
    message: str
    severity: str = Field(default="info")


class ValidationResult(BaseModel):
    is_valid: bool = True
    score: float = Field(default=0.8, ge=0.0, le=1.0)
    issues: list[ValidationIssue] = Field(default_factory=list)
