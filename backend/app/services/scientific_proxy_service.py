from __future__ import annotations

from app.models.chemistry import CandidateResponse
from app.models.planet import PlanetProfile, ValidationResult
from app.models.qfg import QFGSimulationResult
from app.models.quantum import QuantumEvaluationResult
from app.models.scientific import ScientificProxyProfile, VisualPhysicsProfile
from app.models.state import PlanetAtmosphereState
from app.models.spectrum import SpectrumResponse

EARTH_MEAN_MOLECULAR_WEIGHT = 28.97

MOLECULAR_WEIGHTS = {
    "H2": 2.02,
    "He": 4.0,
    "NH3": 17.03,
    "H2O": 18.02,
    "CH4": 16.04,
    "HCN": 27.03,
    "N2": 28.01,
    "CO": 28.01,
    "O2": 32.0,
    "Ar": 39.95,
    "CO2": 44.01,
    "SO2": 64.07,
}

STAR_COLORS = {
    "M-type": "#ffb38d",
    "K-type": "#ffd6a3",
    "G-type": "#fff0bf",
    "F-type": "#f7f7ff",
}

SPECTRUM_PALETTES = {
    "H2O": ["#7dd3fc", "#67e8f9", "#dbeafe"],
    "CO2": ["#fde68a", "#fca5a5", "#fb7185"],
    "CH4": ["#93c5fd", "#a78bfa", "#e9d5ff"],
    "NH3": ["#86efac", "#7dd3fc", "#d9f99d"],
    "SO2": ["#fca5a5", "#fdba74", "#fef08a"],
    "CO": ["#f5d0fe", "#c4b5fd", "#fef3c7"],
}


def build_scientific_proxy_profile(
    profile: PlanetProfile,
    validation: ValidationResult,
    chemistry: CandidateResponse,
    quantum: QuantumEvaluationResult | None,
    state: PlanetAtmosphereState | None = None,
) -> ScientificProxyProfile:
    fractions = profile.atmosphere.gas_fractions
    if state is not None:
        mean_weight = state.mean_molecular_weight
        scale_height_proxy = _clamp(state.scale_height_km / 8.5, 0.2, 3.0)
    else:
        mean_weight = sum(
            max(0.0, fraction) * MOLECULAR_WEIGHTS.get(gas, EARTH_MEAN_MOLECULAR_WEIGHT)
            for gas, fraction in fractions.items()
        )
        mean_weight = max(2.0, mean_weight or EARTH_MEAN_MOLECULAR_WEIGHT)

        scale_ratio = (
            (profile.atmosphere.temperature_k / 288.0)
            * (EARTH_MEAN_MOLECULAR_WEIGHT / mean_weight)
            * (9.81 / max(profile.gravity_ms2, 1.0))
        )
        scale_height_proxy = _clamp(scale_ratio, 0.2, 3.0)

    carbon_richness_proxy = _clamp(
        fractions.get("CO2", 0.0)
        + fractions.get("CH4", 0.0)
        + fractions.get("CO", 0.0)
        + fractions.get("HCN", 0.0),
        0.0,
        1.0,
    )
    nitrogen_richness_proxy = _clamp(
        fractions.get("N2", 0.0) + fractions.get("NH3", 0.0) + 0.5 * fractions.get("HCN", 0.0),
        0.0,
        1.0,
    )
    oxidation_index_proxy = (
        _clamp(state.oxidation_reduction_proxy, -1.0, 1.0)
        if state is not None
        else _clamp(
            fractions.get("O2", 0.0)
            + 0.45 * fractions.get("CO2", 0.0)
            + 0.25 * fractions.get("SO2", 0.0)
            - fractions.get("H2", 0.0)
            - 0.8 * fractions.get("CH4", 0.0)
            - 0.6 * fractions.get("NH3", 0.0),
            -1.0,
            1.0,
        )
    )

    if state is not None:
        cloud_haze_factor = _clamp(state.tau_cloud / 1.25, 0.05, 1.0)
    else:
        haze_seed = 0.12
        haze_seed += 0.15 if profile.atmosphere.pressure_bar > 2.5 else 0.0
        haze_seed += 0.12 if profile.atmosphere.pressure_bar < 0.25 else 0.0
        haze_seed += 0.12 if profile.atmosphere.temperature_k > 380 else 0.0
        haze_seed += 0.10 * fractions.get("CH4", 0.0)
        haze_seed += 0.08 * fractions.get("H2O", 0.0)
        haze_seed += 0.08 if "dense atmosphere" in chemistry.chemistry_modes else 0.0
        haze_seed += 0.10 if "high-radiation" in chemistry.chemistry_modes else 0.0
        haze_seed += 0.06 if any(issue.severity == "warning" for issue in validation.issues) else 0.0
        cloud_haze_factor = _clamp(haze_seed, 0.05, 1.0)

    visibility = 0.48
    visibility += 0.22 * _normalize(scale_height_proxy, 0.2, 3.0)
    visibility += 0.10 * fractions.get("H2O", 0.0)
    visibility += 0.08 * carbon_richness_proxy
    visibility -= 0.26 * cloud_haze_factor
    visibility -= 0.08 if profile.radiation_level > 2.5 else 0.0
    visibility += 0.04 * (quantum.confidence_score or 0.0) if quantum else 0.0
    spectral_visibility_score = _clamp(visibility, 0.0, 1.0)

    atmospheric_clarity_mode = _classify_atmospheric_clarity(cloud_haze_factor, spectral_visibility_score, profile)
    observation_confidence_mode = _classify_observation_confidence(
        validation=validation,
        spectral_visibility_score=spectral_visibility_score,
        atmospheric_clarity_mode=atmospheric_clarity_mode,
        quantum=quantum,
    )
    observation_risk_notes = _build_observation_risk_notes(
        validation=validation,
        cloud_haze_factor=cloud_haze_factor,
        atmospheric_clarity_mode=atmospheric_clarity_mode,
        observation_confidence_mode=observation_confidence_mode,
        profile=profile,
    )

    disclaimers = [
        "This simulation uses lightweight atmospheric proxy logic rather than full radiative-transfer physics.",
        "Chemistry scoring is rule-based and explainable, not a retrieval or equilibrium solver.",
        "Quantum output is a focused molecular proxy signal for tiny systems only.",
        "Transmission spectra are synthetic signatures informed by known molecular absorption behavior.",
    ]
    if observation_confidence_mode in {"ambiguous", "null-signal"}:
        disclaimers.append("Observed-like ambiguity is represented with synthetic proxy logic and should not be treated as a detection claim.")

    return ScientificProxyProfile(
        mean_molecular_weight_proxy=round(mean_weight, 2),
        scale_height_proxy=round(scale_height_proxy, 3),
        cloud_haze_factor=round(cloud_haze_factor, 3),
        oxidation_index_proxy=round(oxidation_index_proxy, 3),
        carbon_richness_proxy=round(carbon_richness_proxy, 3),
        nitrogen_richness_proxy=round(nitrogen_richness_proxy, 3),
        spectral_visibility_score=round(spectral_visibility_score, 3),
        atmospheric_clarity_mode=atmospheric_clarity_mode,
        observation_confidence_mode=observation_confidence_mode,
        observation_risk_notes=observation_risk_notes,
        scientific_disclaimers=disclaimers,
    )


def build_visual_physics_profile(
    profile: PlanetProfile,
    validation: ValidationResult,
    chemistry: CandidateResponse,
    scientific: ScientificProxyProfile,
    quantum: QuantumEvaluationResult | None,
    spectrum: SpectrumResponse | None,
    qfg: QFGSimulationResult | None,
) -> VisualPhysicsProfile:
    temperature = profile.atmosphere.temperature_k
    pressure = profile.atmosphere.pressure_bar
    gravity = profile.gravity_ms2
    radiation = profile.radiation_level
    fractions = profile.atmosphere.gas_fractions
    selected_formula = quantum.formula if quantum else (spectrum.metadata.selected_formula if spectrum else None)

    warmth = _clamp((temperature - 180.0) / 340.0, 0.0, 1.0)
    pressure_factor = _clamp(pressure / 4.0, 0.0, 1.0)
    gravity_inverse = _clamp(1.0 - (gravity / 28.0), 0.0, 1.0)
    radiation_factor = _clamp(radiation / 4.0, 0.0, 1.0)
    scale_factor = _normalize(scientific.scale_height_proxy, 0.2, 3.0)

    surface_palette = _surface_palette(warmth, chemistry.chemistry_modes, fractions)
    atmosphere_glow_color = _atmosphere_color(chemistry.chemistry_modes, fractions)
    cloud_tint = _cloud_tint(fractions, chemistry.chemistry_modes)
    host_star_light_color = STAR_COLORS.get(profile.star_type, "#fff0bf")
    fill_light_color = _fill_light_color(warmth, radiation_factor)

    atmosphere_glow_intensity = _clamp(0.35 + 0.35 * scale_factor + 0.12 * radiation_factor, 0.15, 1.0)
    atmosphere_rim_width = _clamp(0.25 + 0.45 * scale_factor + 0.12 * gravity_inverse, 0.1, 1.0)
    atmosphere_thickness_visual = _clamp(0.25 + 0.45 * scale_factor + 0.20 * pressure_factor, 0.1, 1.0)
    cloud_opacity = _clamp(0.06 + 0.42 * scientific.cloud_haze_factor, 0.04, 0.75)
    cloud_motion_speed = _clamp(0.18 + 0.38 * warmth - 0.10 * pressure_factor, 0.08, 0.75)
    haze_intensity = _clamp(0.12 + 0.65 * scientific.cloud_haze_factor, 0.05, 1.0)
    camera_distance = round(_clamp(4.2 + profile.radius_rearth * 0.45, 4.2, 5.9), 2)
    camera_fov = round(_clamp(33.0 + 2.8 * profile.radius_rearth, 30.0, 42.0), 1)
    auto_rotate_speed = round(_clamp(0.16 + 0.25 * scientific.spectral_visibility_score, 0.1, 0.5), 3)
    starfield_density = round(_clamp(0.75 + 0.35 * radiation_factor + (0.12 if profile.star_type == "M-type" else 0.0), 0.6, 1.8), 3)
    particle_density = round(_clamp(0.65 + 0.45 * radiation_factor + 0.25 * scientific.cloud_haze_factor, 0.5, 2.0), 3)
    spectrum_accent_palette = SPECTRUM_PALETTES.get(selected_formula or "", ["#7dd3fc", "#fde68a", "#c4b5fd"])
    quantum_chamber_intensity = round(
        _clamp(
            0.35
            + 0.30 * (quantum.stability_score if quantum else 0.45)
            + 0.15 * radiation_factor
            + 0.10 * _qfg_resonance_intensity(qfg)
            - (0.08 if scientific.observation_confidence_mode == "ambiguous" else 0.0)
            - (0.16 if scientific.observation_confidence_mode == "null-signal" else 0.0),
            0.25,
            1.0,
        ),
        3,
    )
    quantum_ring_speed = round(
        _clamp(
            (0.35 + 0.35 * (quantum.confidence_score or 0.55) + 0.15 * radiation_factor if quantum else 0.45)
            + (0.15 * qfg.coherence_score if qfg else 0.0),
            0.2,
            1.2,
        ),
        3,
    )
    validation_overlay_tone = _validation_tone(validation)
    if validation_overlay_tone == "stable" and scientific.observation_confidence_mode == "ambiguous":
        validation_overlay_tone = "watch"
    elif scientific.observation_confidence_mode == "null-signal":
        validation_overlay_tone = "caution"

    qfg_resonance_intensity = _qfg_resonance_intensity(qfg)
    qfg_density_band = _qfg_density_band(qfg)

    return VisualPhysicsProfile(
        surface_palette=surface_palette,
        surface_variation_intensity=round(_clamp(0.35 + 0.25 * scientific.carbon_richness_proxy + 0.18 * warmth, 0.2, 0.95), 3),
        terminator_contrast=round(_clamp(0.35 + 0.38 * warmth + 0.16 * radiation_factor, 0.25, 1.0), 3),
        host_star_light_color=host_star_light_color,
        fill_light_color=fill_light_color,
        atmosphere_glow_color=atmosphere_glow_color,
        atmosphere_glow_intensity=atmosphere_glow_intensity,
        atmosphere_rim_width=atmosphere_rim_width,
        atmosphere_thickness_visual=atmosphere_thickness_visual,
        cloud_tint=cloud_tint,
        cloud_opacity=round(cloud_opacity, 3),
        cloud_motion_speed=round(cloud_motion_speed, 3),
        haze_intensity=round(haze_intensity, 3),
        camera_distance=camera_distance,
        camera_fov=camera_fov,
        auto_rotate_speed=auto_rotate_speed,
        starfield_density=starfield_density,
        particle_density=particle_density,
        spectrum_accent_palette=spectrum_accent_palette,
        quantum_chamber_intensity=quantum_chamber_intensity,
        quantum_ring_speed=quantum_ring_speed,
        qfg_resonance_intensity=round(qfg_resonance_intensity, 3),
        qfg_density_band=[round(value, 3) for value in qfg_density_band],
        validation_overlay_tone=validation_overlay_tone,
    )


def _surface_palette(warmth: float, chemistry_modes: list[str], fractions: dict[str, float]) -> list[str]:
    if "hot atmosphere" in chemistry_modes:
        return ["#ffe2b2", "#f38a4f", "#582011"]
    if "cold atmosphere" in chemistry_modes:
        return ["#edf7ff", "#7ccfff", "#1a3e6e"]
    if fractions.get("H2O", 0.0) > 0.08:
        return ["#e1f7ff", "#84d7ff", "#245f96"]
    if fractions.get("CH4", 0.0) > 0.08:
        return ["#eff6ff", "#9fc5ff", "#3d4279"]
    if warmth > 0.55:
        return ["#ffe9bf", "#f3a267", "#6b321a"]
    return ["#eef7ee", "#87cda1", "#2d5f57"]


def _atmosphere_color(chemistry_modes: list[str], fractions: dict[str, float]) -> str:
    if fractions.get("CH4", 0.0) > 0.08:
        return "#9ab8ff"
    if fractions.get("CO2", 0.0) > 0.25:
        return "#ffb07d"
    if "oxidizing" in chemistry_modes:
        return "#7fdcff"
    if "reducing" in chemistry_modes:
        return "#a89dff"
    return "#86e0d0"


def _cloud_tint(fractions: dict[str, float], chemistry_modes: list[str]) -> str:
    if fractions.get("CO2", 0.0) > 0.25:
        return "#fff2e1"
    if fractions.get("CH4", 0.0) > 0.08:
        return "#eef0ff"
    if "oxidizing" in chemistry_modes:
        return "#effcff"
    return "#f4f8ff"


def _fill_light_color(warmth: float, radiation_factor: float) -> str:
    if radiation_factor > 0.6:
        return "#7e8fff"
    if warmth > 0.6:
        return "#6b84d8"
    return "#73b0ff"


def _validation_tone(validation: ValidationResult) -> str:
    if not validation.is_valid:
        return "critical"
    if any(issue.severity == "warning" for issue in validation.issues):
        return "watch"
    if validation.score > 0.88:
        return "stable"
    return "caution"


def _qfg_resonance_intensity(qfg: QFGSimulationResult | None) -> float:
    if qfg is None:
        return 0.45
    observable_peak = max((point.resonance_signal for point in qfg.observables), default=0.0)
    resonance_seed = 0.45 * observable_peak + 0.35 * qfg.coherence_score + 0.20 * qfg.stability_score
    if qfg.resonance_detected:
        resonance_seed += 0.1
    return _clamp(resonance_seed, 0.0, 1.0)


def _qfg_density_band(qfg: QFGSimulationResult | None) -> list[float]:
    if qfg is None:
        return [0.0, 0.0]
    lower = _clamp(qfg.density_mean, 0.0, 1.0)
    upper = _clamp(qfg.density_peak, lower, max(lower, 1.0))
    return [lower, upper]


def _classify_atmospheric_clarity(
    cloud_haze_factor: float,
    spectral_visibility_score: float,
    profile: PlanetProfile,
) -> str:
    if spectral_visibility_score < 0.22 or cloud_haze_factor > 0.72:
        return "feature-flat"
    if cloud_haze_factor > 0.56 or profile.atmosphere.pressure_bar > 6.0:
        return "cloud-muted"
    if cloud_haze_factor > 0.34:
        return "hazy"
    return "clear"


def _classify_observation_confidence(
    validation: ValidationResult,
    spectral_visibility_score: float,
    atmospheric_clarity_mode: str,
    quantum: QuantumEvaluationResult | None,
) -> str:
    warning_count = sum(1 for issue in validation.issues if issue.severity == "warning")
    quantum_confidence = quantum.confidence_score if quantum and quantum.confidence_score is not None else 0.5

    if not validation.is_valid or spectral_visibility_score < 0.18:
        return "null-signal"
    if atmospheric_clarity_mode == "feature-flat":
        return "null-signal" if spectral_visibility_score < 0.28 else "ambiguous"
    if atmospheric_clarity_mode == "cloud-muted" and (spectral_visibility_score < 0.46 or warning_count >= 2):
        return "ambiguous"
    if warning_count >= 2 or spectral_visibility_score < 0.5 or quantum_confidence < 0.58:
        return "weak-feature"
    return "strong-feature"


def _build_observation_risk_notes(
    validation: ValidationResult,
    cloud_haze_factor: float,
    atmospheric_clarity_mode: str,
    observation_confidence_mode: str,
    profile: PlanetProfile,
) -> list[str]:
    notes: list[str] = []
    if atmospheric_clarity_mode in {"hazy", "cloud-muted", "feature-flat"}:
        notes.append(f"Atmospheric clarity is classified as {atmospheric_clarity_mode}, so features may be suppressed.")
    if observation_confidence_mode in {"ambiguous", "null-signal"}:
        notes.append("Observational interpretation remains ambiguous in this proxy run.")
    if profile.radiation_level > 2.5:
        notes.append("Elevated radiation may reduce clean feature interpretation.")
    if cloud_haze_factor > 0.55:
        notes.append("Cloud and haze proxies are high enough to flatten the synthetic transmission signature.")
    notes.extend(issue.message for issue in validation.issues[:2])
    return notes[:4]


def _normalize(value: float, minimum: float, maximum: float) -> float:
    return _clamp((value - minimum) / max(maximum - minimum, 1e-6), 0.0, 1.0)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
