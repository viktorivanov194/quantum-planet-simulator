from __future__ import annotations

import math
import random

from app.core.planet_rules import PLANET_PRESETS, PLANET_RULES
from app.core.state_rules import (
    ATMOSPHERE_FAMILY_TEMPLATES,
    ATMOSPHERE_FAMILY_THRESHOLDS,
    CO_RATIO_DEFAULTS,
    METALLICITY_DEFAULTS,
    ORBIT_ZONE_ALBEDO,
    ORBIT_ZONE_INSOLATION,
    STAR_STATE_RULES,
)
from app.models.planet import (
    AtmosphericProfile,
    AtmosphericProfileInput,
    PlanetGenerationRequest,
    PlanetProfile,
    ValidationIssue,
    ValidationResult,
)
from app.models.state import PlanetAtmosphereState


def generate_planet_profile(request: PlanetGenerationRequest) -> PlanetProfile:
    profile, _ = generate_planet_profile_and_state(request)
    return profile


def generate_planet_state(request: PlanetGenerationRequest) -> PlanetAtmosphereState:
    _, state = generate_planet_profile_and_state(request)
    return state


def generate_planet_profile_and_state(request: PlanetGenerationRequest) -> tuple[PlanetProfile, PlanetAtmosphereState]:
    rng = random.Random(request.seed)
    preset = _resolve_preset(request.preset_name)
    star_type = request.star_type if request.star_type in PLANET_RULES["star_types"] else preset.get("star_type", "K-type")
    orbit_zone = request.orbit_zone if request.orbit_zone in PLANET_RULES["orbit_zones"] else preset.get("orbit_zone", "temperate")
    star_rule = STAR_STATE_RULES.get(star_type, STAR_STATE_RULES["K-type"])

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
    bond_albedo_proxy = _resolve_bond_albedo_proxy(
        orbit_zone=orbit_zone,
        preset=preset,
        radius_rearth=radius_rearth,
        rng=rng,
    )
    insolation_proxy = _resolve_insolation_proxy(
        star_type=star_type,
        orbit_zone=orbit_zone,
        request=request,
        preset=preset,
        bond_albedo_proxy=bond_albedo_proxy,
        rng=rng,
    )
    equilibrium_temperature_k = _resolve_numeric(
        request.equilibrium_temperature_k,
        preset.get("equilibrium_temperature_k"),
        lambda: _estimate_equilibrium_temperature(insolation_proxy, bond_albedo_proxy),
    )
    provisional_pressure_bar = _resolve_numeric(
        request.atmosphere.pressure_bar if request.atmosphere else None,
        (preset.get("atmosphere") or {}).get("pressure_bar"),
        lambda: _estimate_pressure(radius_rearth, equilibrium_temperature_k, rng),
    )
    atmosphere_family = _infer_atmosphere_family(
        radius_rearth=radius_rearth,
        mass_mearth=mass_mearth,
        pressure_bar=provisional_pressure_bar,
        temperature_k=equilibrium_temperature_k,
        manual_atmosphere=request.atmosphere,
        preset_atmosphere=preset.get("atmosphere"),
    )
    gas_fractions = _resolve_gas_fractions(
        manual_atmosphere=request.atmosphere,
        preset_atmosphere=preset.get("atmosphere"),
        atmosphere_family=atmosphere_family,
        equilibrium_temperature_k=equilibrium_temperature_k,
        rng=rng,
    )
    hydrogen_inventory_proxy = _estimate_hydrogen_inventory(gas_fractions)
    carbon_to_oxygen_ratio = _estimate_carbon_to_oxygen_ratio(gas_fractions, atmosphere_family)
    oxidation_reduction_proxy = _estimate_oxidation_reduction_proxy(gas_fractions)
    metallicity_proxy = _estimate_metallicity_proxy(atmosphere_family, gas_fractions)
    atmospheric_temperature_k = _resolve_numeric(
        request.atmosphere.temperature_k if request.atmosphere else None,
        (preset.get("atmosphere") or {}).get("temperature_k"),
        lambda: _estimate_atmospheric_temperature(
            equilibrium_temperature_k=equilibrium_temperature_k,
            pressure_bar=provisional_pressure_bar,
            atmosphere_family=atmosphere_family,
            gas_fractions=gas_fractions,
        ),
    )
    mean_molecular_weight = _estimate_mean_molecular_weight(gas_fractions)
    scale_height_km = _estimate_scale_height_km(
        atmospheric_temperature_k=atmospheric_temperature_k,
        gravity_ms2=gravity_ms2,
        mean_molecular_weight=mean_molecular_weight,
    )
    tau_cloud = _estimate_tau_cloud(
        atmospheric_temperature_k=atmospheric_temperature_k,
        pressure_bar=provisional_pressure_bar,
        gas_fractions=gas_fractions,
        metallicity_proxy=metallicity_proxy,
        hydrogen_inventory_proxy=hydrogen_inventory_proxy,
        uv_activity=star_rule["uv_activity"],
    )
    cloud_haze_opacity_proxy = tau_cloud
    escape_susceptibility_proxy = _estimate_escape_susceptibility_proxy(
        atmospheric_temperature_k=atmospheric_temperature_k,
        gravity_ms2=gravity_ms2,
        mean_molecular_weight=mean_molecular_weight,
        uv_activity=star_rule["uv_activity"],
    )
    vertical_mixing_class = _estimate_vertical_mixing_class(
        hydrogen_inventory_proxy=hydrogen_inventory_proxy,
        gravity_ms2=gravity_ms2,
        pressure_bar=provisional_pressure_bar,
    )
    quench_strength_proxy = _estimate_quench_strength_proxy(
        atmospheric_temperature_k=atmospheric_temperature_k,
        pressure_bar=provisional_pressure_bar,
        vertical_mixing_class=vertical_mixing_class,
    )
    radiation_level = _resolve_numeric(
        request.radiation_level,
        preset.get("radiation_level"),
        lambda: _estimate_radiation_level(star_type, insolation_proxy, star_rule["uv_activity"], rng),
    )
    atmosphere = _build_atmospheric_profile(
        gas_fractions=gas_fractions,
        pressure_bar=provisional_pressure_bar,
        temperature_k=atmospheric_temperature_k,
    )

    mode = _resolved_mode(request)
    notes = [
        f"Generation mode: {mode}.",
        f"Seed: {request.seed}" if request.seed is not None else "Seed not provided.",
        f"Context: {star_type} star with insolation proxy {insolation_proxy:.2f}.",
        f"Atmosphere family: {atmosphere_family}.",
    ]
    if request.preset_name and preset:
        notes.append(f"Preset applied: {request.preset_name}.")

    planet_name = request.planet_name or preset.get("planet_name", _generate_planet_name(star_type, orbit_zone, rng))
    primary_atmospheric_regime = _classify_primary_regime(
        atmosphere_family=atmosphere_family,
        atmospheric_temperature_k=atmospheric_temperature_k,
        carbon_to_oxygen_ratio=carbon_to_oxygen_ratio,
        hydrogen_inventory_proxy=hydrogen_inventory_proxy,
        oxidation_reduction_proxy=oxidation_reduction_proxy,
        pressure_class=_classify_pressure(provisional_pressure_bar),
    )
    secondary_regime_modifiers = _classify_secondary_modifiers(
        atmospheric_temperature_k=atmospheric_temperature_k,
        pressure_bar=provisional_pressure_bar,
        uv_activity=star_rule["uv_activity"],
        escape_susceptibility_proxy=escape_susceptibility_proxy,
        cloud_haze_opacity_proxy=cloud_haze_opacity_proxy,
        gas_fractions=gas_fractions,
    )
    notes.append(f"Primary regime: {primary_atmospheric_regime}.")
    if secondary_regime_modifiers:
        notes.append(f"Secondary modifiers: {', '.join(secondary_regime_modifiers)}.")

    state = PlanetAtmosphereState(
        planet_name=planet_name,
        star_type=star_type,
        stellar_radius_rsun=round(star_rule["stellar_radius_rsun"], 3),
        insolation_proxy=round(insolation_proxy, 3),
        uv_activity=star_rule["uv_activity"],
        radius_rearth=round(radius_rearth, 3),
        mass_mearth=round(mass_mearth, 3),
        gravity_ms2=round(gravity_ms2, 3),
        bond_albedo_proxy=round(bond_albedo_proxy, 3),
        equilibrium_temperature_k=round(equilibrium_temperature_k, 2),
        atmospheric_temperature_k=round(atmospheric_temperature_k, 2),
        reference_pressure_bar=round(provisional_pressure_bar, 3),
        pressure_class=_classify_pressure(provisional_pressure_bar),
        atmosphere_family=atmosphere_family,
        primary_atmospheric_regime=primary_atmospheric_regime,
        secondary_regime_modifiers=secondary_regime_modifiers,
        metallicity_proxy=round(metallicity_proxy, 3),
        carbon_to_oxygen_ratio=round(carbon_to_oxygen_ratio, 3),
        hydrogen_inventory_proxy=round(hydrogen_inventory_proxy, 3),
        oxidation_reduction_proxy=round(oxidation_reduction_proxy, 3),
        mean_molecular_weight=round(mean_molecular_weight, 2),
        scale_height_km=round(scale_height_km, 3),
        tau_cloud=round(tau_cloud, 3),
        cloud_haze_opacity_proxy=round(cloud_haze_opacity_proxy, 3),
        escape_susceptibility_proxy=round(escape_susceptibility_proxy, 3),
        vertical_mixing_class=vertical_mixing_class,
        quench_strength_proxy=round(quench_strength_proxy, 3),
        notes=notes,
    )
    profile = PlanetProfile(
        planet_name=planet_name,
        star_type=state.star_type,
        orbit_zone=orbit_zone,
        generation_mode=mode,
        radius_rearth=state.radius_rearth,
        mass_mearth=state.mass_mearth,
        gravity_ms2=state.gravity_ms2,
        equilibrium_temperature_k=state.equilibrium_temperature_k,
        radiation_level=round(radiation_level, 3),
        atmosphere=atmosphere,
        notes=notes,
    )
    return profile, state


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


def _resolve_bond_albedo_proxy(
    orbit_zone: str,
    preset: dict,
    radius_rearth: float,
    rng: random.Random,
) -> float:
    if "bond_albedo_proxy" in preset:
        return float(preset["bond_albedo_proxy"])
    base = ORBIT_ZONE_ALBEDO.get(orbit_zone, 0.3)
    base += 0.03 if radius_rearth > 1.8 else 0.0
    return max(0.05, min(base + rng.uniform(-0.04, 0.04), 0.85))


def _resolve_insolation_proxy(
    star_type: str,
    orbit_zone: str,
    request: PlanetGenerationRequest,
    preset: dict,
    bond_albedo_proxy: float,
    rng: random.Random,
) -> float:
    if "insolation_proxy" in preset:
        return float(preset["insolation_proxy"])
    if request.equilibrium_temperature_k is not None:
        return _estimate_insolation_from_temperature(request.equilibrium_temperature_k, bond_albedo_proxy)
    if preset.get("equilibrium_temperature_k") is not None:
        return _estimate_insolation_from_temperature(float(preset["equilibrium_temperature_k"]), bond_albedo_proxy)
    star_rule = STAR_STATE_RULES.get(star_type, STAR_STATE_RULES["K-type"])
    zone_base = ORBIT_ZONE_INSOLATION.get(orbit_zone, 1.0)
    jitter = rng.uniform(0.82, 1.18)
    return max(0.05, zone_base * star_rule["insolation_factor"] * jitter)


def _estimate_insolation_from_temperature(equilibrium_temperature_k: float, bond_albedo_proxy: float) -> float:
    retained_flux = max(1.0 - bond_albedo_proxy, 0.05)
    return max(0.05, (equilibrium_temperature_k / 278.0) ** 4 / retained_flux)


def _estimate_equilibrium_temperature(insolation_proxy: float, bond_albedo_proxy: float) -> float:
    retained_flux = max(1.0 - bond_albedo_proxy, 0.05)
    return 278.0 * (max(insolation_proxy, 0.05) * retained_flux) ** 0.25


def _estimate_radiation_level(star_type: str, insolation_proxy: float, uv_activity: str, rng: random.Random) -> float:
    star = PLANET_RULES["star_types"][star_type]
    uv_factor = {"low": 0.85, "moderate": 1.0, "high": 1.28}[uv_activity]
    jitter = rng.uniform(-0.2, 0.35)
    return max(0.0, star["radiation_base"] * uv_factor * (0.75 + 0.35 * math.sqrt(max(insolation_proxy, 0.05))) + jitter)


def _resolve_gas_fractions(
    manual_atmosphere: AtmosphericProfileInput | None,
    preset_atmosphere: dict | None,
    atmosphere_family: str,
    equilibrium_temperature_k: float,
    rng: random.Random,
) -> dict[str, float]:
    preset_atmosphere = preset_atmosphere or {}
    gas_fractions = (
        (manual_atmosphere.gas_fractions if manual_atmosphere else None)
        or preset_atmosphere.get("gas_fractions")
        or _sample_atmosphere_template(atmosphere_family, equilibrium_temperature_k, rng)
    )
    return _normalize_gas_fractions(gas_fractions)


def _estimate_pressure(radius_rearth: float, equilibrium_temperature_k: float, rng: random.Random) -> float:
    if radius_rearth >= 1.9:
        return rng.uniform(2.5, 14.0)
    if equilibrium_temperature_k > 420:
        return rng.uniform(0.3, 12.0)
    if equilibrium_temperature_k < 220:
        return rng.uniform(0.08, 3.8)
    return rng.uniform(0.4, 4.5)


def _sample_atmosphere_template(atmosphere_family: str, equilibrium_temperature_k: float, rng: random.Random) -> dict[str, float]:
    base = dict(ATMOSPHERE_FAMILY_TEMPLATES[atmosphere_family])
    if equilibrium_temperature_k > 420:
        base["CO2"] = base.get("CO2", 0.0) + 0.08
        base["CO"] = base.get("CO", 0.0) + 0.06
        base["CH4"] = max(0.0, base.get("CH4", 0.0) - 0.04)
        base["NH3"] = max(0.0, base.get("NH3", 0.0) - 0.03)
        base["H2O"] = max(0.0, base.get("H2O", 0.0) - 0.02)
    elif equilibrium_temperature_k < 220:
        base["CH4"] = base.get("CH4", 0.0) + 0.06
        base["NH3"] = base.get("NH3", 0.0) + (0.05 if atmosphere_family == "h2_rich" else 0.02)
        base["CO2"] = max(0.0, base.get("CO2", 0.0) - 0.03)
    else:
        base["H2O"] = base.get("H2O", 0.0) + 0.03
    perturbed = {gas: max(0.0, value + rng.uniform(-0.03, 0.03)) for gas, value in base.items()}
    return _normalize_gas_fractions(perturbed)


def _infer_atmosphere_family(
    radius_rearth: float,
    mass_mearth: float,
    pressure_bar: float,
    temperature_k: float,
    manual_atmosphere: AtmosphericProfileInput | None,
    preset_atmosphere: dict | None,
) -> str:
    preset_atmosphere = preset_atmosphere or {}
    gas_fractions = (manual_atmosphere.gas_fractions if manual_atmosphere else None) or preset_atmosphere.get("gas_fractions")
    if gas_fractions:
        hydrogen_inventory = _estimate_hydrogen_inventory(_normalize_gas_fractions(gas_fractions))
        if hydrogen_inventory >= ATMOSPHERE_FAMILY_THRESHOLDS["h2_rich_inventory"]:
            return "h2_rich"
        if hydrogen_inventory >= ATMOSPHERE_FAMILY_THRESHOLDS["volatile_rich_inventory"]:
            return "volatile_rich"

    density_proxy = mass_mearth / max(radius_rearth**3, 0.2)
    if radius_rearth >= 2.0 or density_proxy < 0.7:
        return "h2_rich"
    if pressure_bar >= 3.0 or radius_rearth >= ATMOSPHERE_FAMILY_THRESHOLDS["volatile_rich_radius_rearth"]:
        return "volatile_rich"
    if temperature_k > 430 and density_proxy < 1.0:
        return "volatile_rich"
    return "secondary_terrestrial"


def _estimate_atmospheric_temperature(
    equilibrium_temperature_k: float,
    pressure_bar: float,
    atmosphere_family: str,
    gas_fractions: dict[str, float],
) -> float:
    greenhouse = 6.0 + 8.0 * math.log10(max(pressure_bar, 0.08) / 0.8 + 1.0)
    greenhouse += 10.0 * gas_fractions.get("CO2", 0.0)
    greenhouse += 7.0 * gas_fractions.get("H2O", 0.0)
    greenhouse += 5.0 * gas_fractions.get("H2", 0.0)
    if atmosphere_family == "h2_rich":
        greenhouse += 10.0
    elif atmosphere_family == "volatile_rich":
        greenhouse += 5.0
    return max(80.0, equilibrium_temperature_k + greenhouse)


def _build_atmospheric_profile(
    gas_fractions: dict[str, float],
    pressure_bar: float,
    temperature_k: float,
) -> AtmosphericProfile:
    dominant_gases = sorted(gas_fractions, key=gas_fractions.get, reverse=True)
    return AtmosphericProfile(
        gas_fractions=gas_fractions,
        dominant_gases=dominant_gases,
        pressure_bar=round(pressure_bar, 3),
        temperature_k=round(temperature_k, 2),
    )


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


def _estimate_hydrogen_inventory(gas_fractions: dict[str, float]) -> float:
    inventory = gas_fractions.get("H2", 0.0) + 0.5 * gas_fractions.get("CH4", 0.0) + 0.35 * gas_fractions.get("NH3", 0.0)
    inventory += 0.15 * gas_fractions.get("H2O", 0.0)
    return max(0.0, min(inventory, 1.0))


def _estimate_carbon_to_oxygen_ratio(gas_fractions: dict[str, float], atmosphere_family: str) -> float:
    carbon = gas_fractions.get("CO2", 0.0) + gas_fractions.get("CO", 0.0) + gas_fractions.get("CH4", 0.0) + gas_fractions.get("HCN", 0.0)
    oxygen = (
        2.0 * gas_fractions.get("CO2", 0.0)
        + gas_fractions.get("CO", 0.0)
        + gas_fractions.get("H2O", 0.0)
        + 2.0 * gas_fractions.get("O2", 0.0)
        + 2.0 * gas_fractions.get("SO2", 0.0)
    )
    if oxygen <= 0.02:
        return min(2.0, CO_RATIO_DEFAULTS[atmosphere_family] + carbon)
    return max(0.1, min(carbon / oxygen, 2.0))


def _estimate_oxidation_reduction_proxy(gas_fractions: dict[str, float]) -> float:
    return max(
        -1.0,
        min(
            gas_fractions.get("O2", 0.0)
            + 0.45 * gas_fractions.get("CO2", 0.0)
            + 0.2 * gas_fractions.get("SO2", 0.0)
            - gas_fractions.get("H2", 0.0)
            - 0.8 * gas_fractions.get("CH4", 0.0)
            - 0.6 * gas_fractions.get("NH3", 0.0),
            1.0,
        ),
    )


def _estimate_metallicity_proxy(atmosphere_family: str, gas_fractions: dict[str, float]) -> float:
    proxy = METALLICITY_DEFAULTS[atmosphere_family]
    proxy += 0.45 * gas_fractions.get("CO2", 0.0)
    proxy += 0.25 * gas_fractions.get("H2O", 0.0)
    proxy += 0.2 * gas_fractions.get("SO2", 0.0)
    proxy -= 0.15 * gas_fractions.get("H2", 0.0)
    return max(-1.0, min(proxy, 2.0))


def _estimate_mean_molecular_weight(gas_fractions: dict[str, float]) -> float:
    weights = {
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
    total = sum(max(0.0, fraction) * weights.get(gas, 28.97) for gas, fraction in gas_fractions.items())
    return max(2.0, total or 28.97)


def _estimate_scale_height_km(atmospheric_temperature_k: float, gravity_ms2: float, mean_molecular_weight: float) -> float:
    scale_ratio = (
        (atmospheric_temperature_k / 288.0)
        * (28.97 / mean_molecular_weight)
        * (9.81 / max(gravity_ms2, 1.0))
    )
    return max(1.2, min(8.5 * scale_ratio, 120.0))


def _estimate_tau_cloud(
    atmospheric_temperature_k: float,
    pressure_bar: float,
    gas_fractions: dict[str, float],
    metallicity_proxy: float,
    hydrogen_inventory_proxy: float,
    uv_activity: str,
) -> float:
    uv_factor = {"low": 0.85, "moderate": 1.0, "high": 1.25}[uv_activity]
    tau = 0.08
    # Condensation/cloud contribution.
    if 220.0 <= atmospheric_temperature_k <= 350.0:
        tau += 0.35 * gas_fractions.get("H2O", 0.0)
    if pressure_bar >= 2.5:
        tau += min(0.35, 0.06 * pressure_bar)
    # Photochemical haze contribution.
    tau += 0.45 * gas_fractions.get("CH4", 0.0) * uv_factor
    tau += 0.12 * max(metallicity_proxy, 0.0)
    tau += 0.08 if hydrogen_inventory_proxy >= 0.3 and atmospheric_temperature_k < 260.0 else 0.0
    if atmospheric_temperature_k > 500.0 and gas_fractions.get("SO2", 0.0) > 0.03:
        tau += 0.12
    return max(0.03, min(tau, 5.0))


def _estimate_escape_susceptibility_proxy(
    atmospheric_temperature_k: float,
    gravity_ms2: float,
    mean_molecular_weight: float,
    uv_activity: str,
) -> float:
    uv_factor = {"low": 0.8, "moderate": 1.0, "high": 1.35}[uv_activity]
    susceptibility = (
        (atmospheric_temperature_k / 1000.0)
        * uv_factor
        * (28.0 / max(mean_molecular_weight, 2.0))
        * (9.8 / max(gravity_ms2, 1.5)) ** 0.8
    )
    return max(0.0, min(susceptibility, 3.0))


def _classify_pressure(pressure_bar: float) -> str:
    if pressure_bar <= 0.3:
        return "thin"
    if pressure_bar >= 5.0:
        return "dense"
    return "moderate"


def _estimate_vertical_mixing_class(hydrogen_inventory_proxy: float, gravity_ms2: float, pressure_bar: float) -> str:
    if hydrogen_inventory_proxy >= 0.35 or gravity_ms2 <= 8.0:
        return "high"
    if pressure_bar >= 3.5:
        return "moderate"
    return "low"


def _estimate_quench_strength_proxy(atmospheric_temperature_k: float, pressure_bar: float, vertical_mixing_class: str) -> float:
    mix_factor = {"low": 0.3, "moderate": 0.6, "high": 1.0}[vertical_mixing_class]
    return max(
        0.0,
        min(
            mix_factor
            * math.pow(max(atmospheric_temperature_k, 120.0) / 800.0, 0.6)
            * math.pow(max(pressure_bar, 0.05), 0.2),
            2.0,
        ),
    )


def _classify_primary_regime(
    atmosphere_family: str,
    atmospheric_temperature_k: float,
    carbon_to_oxygen_ratio: float,
    hydrogen_inventory_proxy: float,
    oxidation_reduction_proxy: float,
    pressure_class: str,
) -> str:
    if atmospheric_temperature_k <= 220.0 and hydrogen_inventory_proxy >= 0.18:
        return "cold_methane_atmosphere"
    if atmospheric_temperature_k >= 430.0 and carbon_to_oxygen_ratio >= 0.45:
        return "hot_co2_co_atmosphere"
    if atmosphere_family == "h2_rich":
        return "h2_rich_mini_neptune"
    if atmosphere_family == "volatile_rich":
        return "volatile_rich_temperate"
    if oxidation_reduction_proxy >= -0.05 or pressure_class == "thin":
        return "oxidized_terrestrial"
    return "volatile_rich_temperate"


def _classify_secondary_modifiers(
    atmospheric_temperature_k: float,
    pressure_bar: float,
    uv_activity: str,
    escape_susceptibility_proxy: float,
    cloud_haze_opacity_proxy: float,
    gas_fractions: dict[str, float],
) -> list[str]:
    modifiers: list[str] = []
    if uv_activity == "high" and gas_fractions.get("CH4", 0.0) >= 0.05:
        modifiers.append("photochemical_haze")
    if cloud_haze_opacity_proxy >= 0.45 or pressure_bar >= 4.0:
        modifiers.append("cloud_muted")
    if escape_susceptibility_proxy >= 0.9:
        modifiers.append("escape_stressed")
    if uv_activity == "high":
        modifiers.append("high_uv_processed")
    if atmospheric_temperature_k < 180.0:
        modifiers.append("cold_edge")
    elif atmospheric_temperature_k > 520.0:
        modifiers.append("hot_edge")
    return modifiers


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
