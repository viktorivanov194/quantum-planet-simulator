from __future__ import annotations

import random

from app.core.planet_rules import PLANET_PRESETS, PLANET_RULES
from app.models.planet import (
    AtmosphericProfile,
    AtmosphericProfileInput,
    PlanetGenerationRequest,
    PlanetProfile,
    ValidationIssue,
    ValidationResult,
)


def generate_planet_profile(request: PlanetGenerationRequest) -> PlanetProfile:
    rng = random.Random(request.seed)
    preset = _resolve_preset(request.preset_name)
    star_type = request.star_type if request.star_type in PLANET_RULES["star_types"] else preset.get("star_type", "K-type")
    orbit_zone = request.orbit_zone if request.orbit_zone in PLANET_RULES["orbit_zones"] else preset.get("orbit_zone", "temperate")

    radius_rearth = _resolve_numeric(
        request.radius_rearth,
        preset.get("radius_rearth"),
        lambda: rng.uniform(*PLANET_RULES["ranges"]["radius_rearth"]),
    )
    mass_mearth = _resolve_numeric(
        request.mass_mearth,
        preset.get("mass_mearth"),
        lambda: _estimate_mass_from_radius(radius_rearth, rng),
    )
    gravity_ms2 = _resolve_numeric(
        request.gravity_ms2,
        preset.get("gravity_ms2"),
        lambda: _estimate_gravity(radius_rearth, mass_mearth),
    )
    equilibrium_temperature_k = _resolve_numeric(
        request.equilibrium_temperature_k,
        preset.get("equilibrium_temperature_k"),
        lambda: _estimate_equilibrium_temperature(star_type, orbit_zone, rng),
    )
    radiation_level = _resolve_numeric(
        request.radiation_level,
        preset.get("radiation_level"),
        lambda: _estimate_radiation_level(star_type, orbit_zone, rng),
    )
    atmosphere = _resolve_atmosphere(
        request.atmosphere,
        preset.get("atmosphere"),
        orbit_zone,
        equilibrium_temperature_k,
        rng,
    )

    mode = _resolved_mode(request)
    notes = [
        f"Generation mode: {mode}.",
        f"Seed: {request.seed}" if request.seed is not None else "Seed not provided.",
        f"Context: {star_type} star in {orbit_zone} orbit zone.",
    ]
    if request.preset_name and preset:
        notes.append(f"Preset applied: {request.preset_name}.")

    return PlanetProfile(
        planet_name=request.planet_name or preset.get("planet_name", _generate_planet_name(star_type, orbit_zone, rng)),
        star_type=star_type,
        orbit_zone=orbit_zone,
        generation_mode=mode,
        radius_rearth=round(radius_rearth, 3),
        mass_mearth=round(mass_mearth, 3),
        gravity_ms2=round(gravity_ms2, 3),
        equilibrium_temperature_k=round(equilibrium_temperature_k, 2),
        radiation_level=round(radiation_level, 3),
        atmosphere=atmosphere,
        notes=notes,
    )


def validate_planet_profile(profile: PlanetProfile) -> ValidationResult:
    issues: list[ValidationIssue] = []
    gas_sum = sum(profile.atmosphere.gas_fractions.values())
    warning_delta = PLANET_RULES["warning_thresholds"]["gas_fraction_sum_warning_delta"]
    error_delta = PLANET_RULES["warning_thresholds"]["gas_fraction_sum_error_delta"]

    if abs(gas_sum - 1.0) > error_delta:
        issues.append(
            ValidationIssue(
                code="atmosphere_fraction_sum_error",
                message=f"Atmosphere fractions sum to {gas_sum:.3f}; expected approximately 1.0.",
                severity="error",
            )
        )
    elif abs(gas_sum - 1.0) > warning_delta:
        issues.append(
            ValidationIssue(
                code="atmosphere_fraction_sum_warning",
                message=f"Atmosphere fractions sum to {gas_sum:.3f}; slight normalization may be needed.",
                severity="warning",
            )
        )

    _validate_range(
        issues,
        "equilibrium_temperature_k",
        profile.equilibrium_temperature_k,
        PLANET_RULES["ranges"]["equilibrium_temperature_k"],
        "Planet equilibrium temperature is outside the configured demo range.",
    )
    _validate_range(
        issues,
        "atmospheric_temperature_k",
        profile.atmosphere.temperature_k,
        PLANET_RULES["ranges"]["atmospheric_temperature_k"],
        "Atmospheric temperature is outside the configured demo range.",
    )
    _validate_range(
        issues,
        "pressure_bar",
        profile.atmosphere.pressure_bar,
        PLANET_RULES["ranges"]["pressure_bar"],
        "Atmospheric pressure is outside the configured demo range.",
    )
    _validate_range(
        issues,
        "gravity_ms2",
        profile.gravity_ms2,
        PLANET_RULES["ranges"]["gravity_ms2"],
        "Surface gravity is outside the configured demo range.",
    )
    _validate_range(
        issues,
        "radiation_level",
        profile.radiation_level,
        PLANET_RULES["ranges"]["radiation_level"],
        "Radiation level is outside the configured demo range.",
    )

    _append_plausibility_warnings(profile, issues)

    error_count = sum(1 for issue in issues if issue.severity == "error")
    warning_count = sum(1 for issue in issues if issue.severity == "warning")
    score = max(0.0, min(1.0, 1.0 - (error_count * 0.35) - (warning_count * 0.08)))
    return ValidationResult(
        is_valid=error_count == 0,
        score=round(score, 2),
        issues=issues,
    )


def _resolved_mode(request: PlanetGenerationRequest) -> str:
    if request.generation_mode == "auto":
        return "manual" if _has_manual_overrides(request) else "random"
    return request.generation_mode


def _has_manual_overrides(request: PlanetGenerationRequest) -> bool:
    return any(
        value is not None
        for value in [
            request.planet_name,
            request.radius_rearth,
            request.mass_mearth,
            request.gravity_ms2,
            request.equilibrium_temperature_k,
            request.radiation_level,
            request.atmosphere,
        ]
    )


def _resolve_preset(preset_name: str | None) -> dict:
    if preset_name and preset_name in PLANET_PRESETS:
        return PLANET_PRESETS[preset_name]
    return {}


def _resolve_numeric(manual_value: float | None, preset_value: float | None, generator: callable) -> float:
    if manual_value is not None:
        return manual_value
    if preset_value is not None:
        return preset_value
    return generator()


def _estimate_mass_from_radius(radius_rearth: float, rng: random.Random) -> float:
    density_factor = rng.uniform(0.75, 1.35)
    return max(PLANET_RULES["ranges"]["mass_mearth"][0], radius_rearth**3 * density_factor)


def _estimate_gravity(radius_rearth: float, mass_mearth: float) -> float:
    return 9.81 * mass_mearth / max(radius_rearth**2, 0.1)


def _estimate_equilibrium_temperature(star_type: str, orbit_zone: str, rng: random.Random) -> float:
    zone = PLANET_RULES["orbit_zones"][orbit_zone]
    star = PLANET_RULES["star_types"][star_type]
    jitter = rng.uniform(-18.0, 18.0)
    return zone["temperature_base_k"] + star["temperature_offset_k"] + jitter


def _estimate_radiation_level(star_type: str, orbit_zone: str, rng: random.Random) -> float:
    zone = PLANET_RULES["orbit_zones"][orbit_zone]
    star = PLANET_RULES["star_types"][star_type]
    jitter = rng.uniform(-0.2, 0.35)
    return max(0.0, star["radiation_base"] * zone["radiation_multiplier"] + jitter)


def _resolve_atmosphere(
    manual_atmosphere: AtmosphericProfileInput | None,
    preset_atmosphere: dict | None,
    orbit_zone: str,
    equilibrium_temperature_k: float,
    rng: random.Random,
) -> AtmosphericProfile:
    preset_atmosphere = preset_atmosphere or {}
    pressure_bar = _resolve_numeric(
        manual_atmosphere.pressure_bar if manual_atmosphere else None,
        preset_atmosphere.get("pressure_bar"),
        lambda: _estimate_pressure(orbit_zone, rng),
    )
    temperature_k = _resolve_numeric(
        manual_atmosphere.temperature_k if manual_atmosphere else None,
        preset_atmosphere.get("temperature_k"),
        lambda: equilibrium_temperature_k + rng.uniform(-12.0, 20.0),
    )
    gas_fractions = (
        (manual_atmosphere.gas_fractions if manual_atmosphere else None)
        or preset_atmosphere.get("gas_fractions")
        or _sample_atmosphere_template(orbit_zone, rng)
    )
    normalized_fractions = _normalize_gas_fractions(gas_fractions)
    dominant_gases = sorted(normalized_fractions, key=normalized_fractions.get, reverse=True)

    return AtmosphericProfile(
        gas_fractions=normalized_fractions,
        dominant_gases=dominant_gases,
        pressure_bar=round(pressure_bar, 3),
        temperature_k=round(temperature_k, 2),
    )


def _estimate_pressure(orbit_zone: str, rng: random.Random) -> float:
    if orbit_zone == "cold":
        return rng.uniform(0.08, 3.5)
    if orbit_zone == "hot":
        return rng.uniform(0.4, 18.0)
    return rng.uniform(0.4, 4.0)


def _sample_atmosphere_template(orbit_zone: str, rng: random.Random) -> dict[str, float]:
    base = PLANET_RULES["atmosphere_templates"][orbit_zone]
    perturbed = {gas: max(0.0, value + rng.uniform(-0.03, 0.03)) for gas, value in base.items()}
    return _normalize_gas_fractions(perturbed)


def _normalize_gas_fractions(gas_fractions: dict[str, float]) -> dict[str, float]:
    positive = {gas: max(0.0, fraction) for gas, fraction in gas_fractions.items()}
    total = sum(positive.values())
    if total <= 0:
        fallback = PLANET_RULES["atmosphere_templates"]["temperate"]
        total = sum(fallback.values())
        positive = fallback
    return {gas: round(value / total, 4) for gas, value in positive.items()}


def _generate_planet_name(star_type: str, orbit_zone: str, rng: random.Random) -> str:
    prefix = star_type[0]
    zone = orbit_zone[0].upper()
    return f"QPS-{prefix}{zone}-{rng.randint(100, 999)}"


def _validate_range(
    issues: list[ValidationIssue],
    code: str,
    value: float,
    valid_range: tuple[float, float],
    message: str,
) -> None:
    lower, upper = valid_range
    if value < lower or value > upper:
        issues.append(ValidationIssue(code=code, message=message, severity="error"))


def _append_plausibility_warnings(profile: PlanetProfile, issues: list[ValidationIssue]) -> None:
    thresholds = PLANET_RULES["warning_thresholds"]

    if profile.atmosphere.temperature_k < thresholds["temperature_low_k"]:
        issues.append(
            ValidationIssue(
                code="temperature_low_warning",
                message="Atmospheric temperature is at the cold edge of the demo plausibility window.",
                severity="warning",
            )
        )
    if profile.atmosphere.temperature_k > thresholds["temperature_high_k"]:
        issues.append(
            ValidationIssue(
                code="temperature_high_warning",
                message="Atmospheric temperature is at the hot edge of the demo plausibility window.",
                severity="warning",
            )
        )
    if profile.atmosphere.pressure_bar < thresholds["pressure_low_bar"]:
        issues.append(
            ValidationIssue(
                code="pressure_low_warning",
                message="Very thin atmosphere may reduce long-term atmospheric stability.",
                severity="warning",
            )
        )
    if profile.atmosphere.pressure_bar > thresholds["pressure_high_bar"]:
        issues.append(
            ValidationIssue(
                code="pressure_high_warning",
                message="Very dense atmosphere may produce difficult-to-interpret chemistry and spectra.",
                severity="warning",
            )
        )
    if profile.gravity_ms2 < thresholds["gravity_low_ms2"]:
        issues.append(
            ValidationIssue(
                code="gravity_low_warning",
                message="Low gravity may make atmospheric retention less stable in this demo model.",
                severity="warning",
            )
        )
    if profile.gravity_ms2 > thresholds["gravity_high_ms2"]:
        issues.append(
            ValidationIssue(
                code="gravity_high_warning",
                message="High gravity may imply a dense world outside the most comfortable MVP assumptions.",
                severity="warning",
            )
        )
    if profile.radiation_level > thresholds["radiation_high"]:
        issues.append(
            ValidationIssue(
                code="radiation_high_warning",
                message="Elevated radiation may challenge atmospheric persistence and surface habitability assumptions.",
                severity="warning",
            )
        )

    if profile.radiation_level > 2.5 and profile.atmosphere.pressure_bar < 0.2:
        issues.append(
            ValidationIssue(
                code="thin_atmosphere_high_radiation",
                message="Thin atmosphere combined with elevated radiation looks potentially unstable.",
                severity="warning",
            )
        )
    if profile.atmosphere.temperature_k > 450 and profile.atmosphere.gas_fractions.get("CH4", 0.0) > 0.1:
        issues.append(
            ValidationIssue(
                code="hot_methane_warning",
                message="Methane-rich atmosphere at high temperature may be short-lived in this simplified model.",
                severity="warning",
            )
        )
    if profile.atmosphere.pressure_bar < 0.1 and profile.atmosphere.temperature_k > 380:
        issues.append(
            ValidationIssue(
                code="hot_thin_atmosphere_warning",
                message="Hot, very thin atmosphere is flagged as a potentially unstable combination.",
                severity="warning",
            )
        )
