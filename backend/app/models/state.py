from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


UVActivity = Literal["low", "moderate", "high"]
AtmosphereFamily = Literal["secondary_terrestrial", "volatile_rich", "h2_rich"]
PressureClass = Literal["thin", "moderate", "dense"]
VerticalMixingClass = Literal["low", "moderate", "high"]
PrimaryAtmosphericRegime = Literal[
    "oxidized_terrestrial",
    "volatile_rich_temperate",
    "h2_rich_mini_neptune",
    "hot_co2_co_atmosphere",
    "cold_methane_atmosphere",
]


class PlanetAtmosphereState(BaseModel):
    planet_name: str = Field(default="QPS-001")

    # Shared star / planet backbone used by downstream services.
    star_type: str = Field(default="K-type")
    stellar_radius_rsun: float = Field(default=0.8, gt=0.0)
    insolation_proxy: float = Field(default=1.0, ge=0.0)
    uv_activity: UVActivity = Field(default="moderate")

    radius_rearth: float = Field(default=1.0, gt=0.0)
    mass_mearth: float = Field(default=1.0, gt=0.0)
    gravity_ms2: float = Field(default=9.81, gt=0.0)

    bond_albedo_proxy: float = Field(default=0.3, ge=0.0, le=0.95)
    equilibrium_temperature_k: float = Field(default=288.0, gt=0.0)
    atmospheric_temperature_k: float = Field(default=290.0, gt=0.0)

    reference_pressure_bar: float = Field(default=1.0, gt=0.0)
    pressure_class: PressureClass = Field(default="moderate")
    atmosphere_family: AtmosphereFamily = Field(default="secondary_terrestrial")
    primary_atmospheric_regime: PrimaryAtmosphericRegime = Field(default="oxidized_terrestrial")
    secondary_regime_modifiers: list[str] = Field(default_factory=list)

    metallicity_proxy: float = Field(default=0.0, ge=-1.0, le=2.0)
    carbon_to_oxygen_ratio: float = Field(default=0.55, ge=0.0, le=2.0)
    hydrogen_inventory_proxy: float = Field(default=0.1, ge=0.0, le=1.0)
    oxidation_reduction_proxy: float = Field(default=0.0, ge=-1.0, le=1.0)

    mean_molecular_weight: float = Field(default=28.0, ge=2.0, le=100.0)
    scale_height_km: float = Field(default=8.0, ge=0.0)

    tau_cloud: float = Field(default=0.2, ge=0.0, le=5.0)
    cloud_haze_opacity_proxy: float = Field(default=0.2, ge=0.0, le=5.0)
    escape_susceptibility_proxy: float = Field(default=0.3, ge=0.0, le=3.0)

    vertical_mixing_class: VerticalMixingClass = Field(default="moderate")
    quench_strength_proxy: float = Field(default=0.3, ge=0.0, le=2.0)

    notes: list[str] = Field(default_factory=list)
