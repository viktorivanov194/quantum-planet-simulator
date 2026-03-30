from __future__ import annotations

from pydantic import BaseModel, Field


class ScientificProxyProfile(BaseModel):
    mean_molecular_weight_proxy: float = Field(default=28.0, ge=0.0)
    scale_height_proxy: float = Field(default=1.0, ge=0.0)
    cloud_haze_factor: float = Field(default=0.25, ge=0.0, le=1.0)
    oxidation_index_proxy: float = Field(default=0.0, ge=-1.0, le=1.0)
    carbon_richness_proxy: float = Field(default=0.0, ge=0.0, le=1.0)
    nitrogen_richness_proxy: float = Field(default=0.0, ge=0.0, le=1.0)
    spectral_visibility_score: float = Field(default=0.5, ge=0.0, le=1.0)
    atmospheric_clarity_mode: str = Field(default="clear")
    observation_confidence_mode: str = Field(default="strong-feature")
    observation_risk_notes: list[str] = Field(default_factory=list)
    scientific_disclaimers: list[str] = Field(default_factory=list)


class VisualPhysicsProfile(BaseModel):
    surface_palette: list[str] = Field(default_factory=lambda: ["#d8f1ff", "#7fc9ff", "#204d7d"])
    surface_variation_intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    terminator_contrast: float = Field(default=0.55, ge=0.0, le=1.0)
    host_star_light_color: str = Field(default="#fff0bf")
    fill_light_color: str = Field(default="#6ca4ff")
    atmosphere_glow_color: str = Field(default="#80d9ff")
    atmosphere_glow_intensity: float = Field(default=0.55, ge=0.0, le=1.0)
    atmosphere_rim_width: float = Field(default=0.5, ge=0.0, le=1.0)
    atmosphere_thickness_visual: float = Field(default=0.5, ge=0.0, le=1.0)
    cloud_tint: str = Field(default="#eefbff")
    cloud_opacity: float = Field(default=0.12, ge=0.0, le=1.0)
    cloud_motion_speed: float = Field(default=0.3, ge=0.0, le=1.0)
    haze_intensity: float = Field(default=0.2, ge=0.0, le=1.0)
    camera_distance: float = Field(default=4.8, ge=0.0)
    camera_fov: float = Field(default=34.0, ge=10.0, le=120.0)
    auto_rotate_speed: float = Field(default=0.25, ge=0.0, le=2.0)
    starfield_density: float = Field(default=1.0, ge=0.1, le=3.0)
    particle_density: float = Field(default=1.0, ge=0.1, le=3.0)
    spectrum_accent_palette: list[str] = Field(default_factory=lambda: ["#7dd3fc", "#fde68a", "#c4b5fd"])
    quantum_chamber_intensity: float = Field(default=0.55, ge=0.0, le=1.0)
    quantum_ring_speed: float = Field(default=0.5, ge=0.0, le=2.0)
    qfg_resonance_intensity: float = Field(default=0.45, ge=0.0, le=1.0)
    qfg_density_band: list[float] = Field(default_factory=lambda: [0.0, 0.0])
    validation_overlay_tone: str = Field(default="stable")
