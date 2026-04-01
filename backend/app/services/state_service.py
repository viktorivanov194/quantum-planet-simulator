from __future__ import annotations

import math

from app.core.state_rules import (
    ATMOSPHERE_FAMILY_THRESHOLDS,
    CO_RATIO_DEFAULTS,
    METALLICITY_DEFAULTS,
    MIXING_CLASS_THRESHOLDS,
    ORBIT_ZONE_ALBEDO,
    ORBIT_ZONE_INSOLATION,
    PRESSURE_CLASS_THRESHOLDS,
    STAR_STATE_RULES,
)
from app.models.planet import PlanetProfile
from app.models.state import PlanetAtmosphereState

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

EARTH_MEAN_MOLECULAR_WEIGHT = 28.97
EARTH_SCALE_HEIGHT_KM = 8.5


def build_planet_atmosphere_state(profile: PlanetProfile) -> PlanetAtmosphereState:
    star_rule = STAR_STATE_RULES.get(profile.star_type, STAR_STATE_RULES["K-type"])
    insolation_proxy = _estimate_insolation_proxy(profile)
    bond_albedo_proxy = _estimate_bond_albedo_proxy(profile)
    atmosphere_family = _infer_atmosphere_family(profile)
    metallicity_proxy = METALLICITY_DEFAULTS[atmosphere_family]
    carbon_to_oxygen_ratio = _estimate_carbon_to_oxygen_ratio(profile, atmosphere_family)
    hydrogen_inventory_proxy = _estimate_hydrogen_inventory(profile)
    oxidation_reduction_proxy = _estimate_oxidation_reduction_proxy(profile)
    mean_molecular_weight = _estimate_mean_molecular_weight(profile)
    scale_height_km = _estimate_scale_height_km(profile, mean_molecular_weight)
    pressure_class = _classify_pressure(profile.atmosphere.pressure_bar)
    escape_susceptibility_proxy = _estimate_escape_susceptibility(profile, mean_molecular_weight, star_rule["uv_activity"])
    vertical_mixing_class = _estimate_vertical_mixing_class(profile, hydrogen_inventory_proxy)
    quench_strength_proxy = _estimate_quench_strength(profile, vertical_mixing_class)
    cloud_haze_opacity_proxy = _estimate_cloud_haze_opacity(profile, metallicity_proxy, hydrogen_inventory_proxy)

    notes = [
        "Shared scientific backbone derived from lightweight physical proxies.",
        f"Atmosphere family inferred as {atmosphere_family}.",
        f"Pressure class resolved as {pressure_class}.",
    ]

    return PlanetAtmosphereState(
        planet_name=profile.planet_name,
        star_type=profile.star_type,
        stellar_radius_rsun=star_rule["stellar_radius_rsun"],
        insolation_proxy=round(insolation_proxy, 3),
        uv_activity=star_rule["uv_activity"],
        radius_rearth=profile.radius_rearth,
        mass_mearth=profile.mass_mearth,
        gravity_ms2=profile.gravity_ms2,
        bond_albedo_proxy=round(bond_albedo_proxy, 3),
        equilibrium_temperature_k=profile.equilibrium_temperature_k,
        atmospheric_temperature_k=profile.atmosphere.temperature_k,
        reference_pressure_bar=profile.atmosphere.pressure_bar,
        pressure_class=pressure_class,
        atmosphere_family=atmosphere_family,
        metallicity_proxy=round(metallicity_proxy, 3),
        carbon_to_oxygen_ratio=round(carbon_to_oxygen_ratio, 3),
        hydrogen_inventory_proxy=round(hydrogen_inventory_proxy, 3),
        oxidation_reduction_proxy=round(oxidation_reduction_proxy, 3),
        mean_molecular_weight=round(mean_molecular_weight, 2),
        scale_height_km=round(scale_height_km, 3),
        cloud_haze_opacity_proxy=round(cloud_haze_opacity_proxy, 3),
        escape_susceptibility_proxy=round(escape_susceptibility_proxy, 3),
        vertical_mixing_class=vertical_mixing_class,
        quench_strength_proxy=round(quench_strength_proxy, 3),
        notes=notes,
    )


def _estimate_insolation_proxy(profile: PlanetProfile) -> float:
    zone_base = ORBIT_ZONE_INSOLATION.get(profile.orbit_zone, 1.0)
    return zone_base * (278.0 / max(profile.equilibrium_temperature_k, 120.0)) ** -0.2


def _estimate_bond_albedo_proxy(profile: PlanetProfile) -> float:
    base = ORBIT_ZONE_ALBEDO.get(profile.orbit_zone, 0.3)
    if profile.atmosphere.pressure_bar > 3.0:
        base += 0.04
    if profile.atmosphere.gas_fractions.get("H2", 0.0) > 0.2:
        base += 0.03
    if profile.atmosphere.temperature_k > 450:
        base -= 0.05
    return max(0.05, min(base, 0.8))


def _infer_atmosphere_family(profile: PlanetProfile) -> str:
    hydrogen_inventory = _estimate_hydrogen_inventory(profile)
    thresholds = ATMOSPHERE_FAMILY_THRESHOLDS
    if hydrogen_inventory >= thresholds["h2_rich_inventory"]:
        return "h2_rich"
    if (
        hydrogen_inventory >= thresholds["volatile_rich_inventory"]
        or profile.radius_rearth >= thresholds["volatile_rich_radius_rearth"]
        or profile.atmosphere.pressure_bar >= 3.0
    ):
        return "volatile_rich"
    return "secondary_terrestrial"


def _estimate_hydrogen_inventory(profile: PlanetProfile) -> float:
    fractions = profile.atmosphere.gas_fractions
    inventory = fractions.get("H2", 0.0) + 0.5 * fractions.get("CH4", 0.0) + 0.35 * fractions.get("NH3", 0.0)
    inventory += 0.15 * fractions.get("H2O", 0.0)
    return max(0.0, min(inventory, 1.0))


def _estimate_carbon_to_oxygen_ratio(profile: PlanetProfile, atmosphere_family: str) -> float:
    fractions = profile.atmosphere.gas_fractions
    carbon = fractions.get("CO2", 0.0) + fractions.get("CO", 0.0) + fractions.get("CH4", 0.0) + fractions.get("HCN", 0.0)
    oxygen = (
        2.0 * fractions.get("CO2", 0.0)
        + fractions.get("CO", 0.0)
        + fractions.get("H2O", 0.0)
        + 2.0 * fractions.get("O2", 0.0)
        + 2.0 * fractions.get("SO2", 0.0)
    )
    if oxygen <= 0.02:
        return min(2.0, CO_RATIO_DEFAULTS[atmosphere_family] + carbon)
    return max(0.1, min(carbon / oxygen, 2.0))


def _estimate_oxidation_reduction_proxy(profile: PlanetProfile) -> float:
    fractions = profile.atmosphere.gas_fractions
    return max(
        -1.0,
        min(
            fractions.get("O2", 0.0)
            + 0.45 * fractions.get("CO2", 0.0)
            + 0.2 * fractions.get("SO2", 0.0)
            - fractions.get("H2", 0.0)
            - 0.8 * fractions.get("CH4", 0.0)
            - 0.6 * fractions.get("NH3", 0.0),
            1.0,
        ),
    )


def _estimate_mean_molecular_weight(profile: PlanetProfile) -> float:
    total = 0.0
    fractions = profile.atmosphere.gas_fractions
    for gas, fraction in fractions.items():
        total += max(0.0, fraction) * MOLECULAR_WEIGHTS.get(gas, EARTH_MEAN_MOLECULAR_WEIGHT)
    return max(2.0, total or EARTH_MEAN_MOLECULAR_WEIGHT)


def _estimate_scale_height_km(profile: PlanetProfile, mean_molecular_weight: float) -> float:
    scale_ratio = (
        (profile.atmosphere.temperature_k / 288.0)
        * (EARTH_MEAN_MOLECULAR_WEIGHT / mean_molecular_weight)
        * (9.81 / max(profile.gravity_ms2, 1.0))
    )
    return max(1.2, min(EARTH_SCALE_HEIGHT_KM * scale_ratio, 120.0))


def _classify_pressure(pressure_bar: float) -> str:
    if pressure_bar <= PRESSURE_CLASS_THRESHOLDS["thin_max_bar"]:
        return "thin"
    if pressure_bar >= PRESSURE_CLASS_THRESHOLDS["dense_min_bar"]:
        return "dense"
    return "moderate"


def _estimate_escape_susceptibility(profile: PlanetProfile, mean_molecular_weight: float, uv_activity: str) -> float:
    uv_factor = {"low": 0.8, "moderate": 1.0, "high": 1.35}[uv_activity]
    susceptibility = (
        (profile.atmosphere.temperature_k / 1000.0)
        * uv_factor
        * (28.0 / max(mean_molecular_weight, 2.0))
        * (9.8 / max(profile.gravity_ms2, 1.5)) ** 0.8
    )
    return max(0.0, min(susceptibility, 3.0))


def _estimate_vertical_mixing_class(profile: PlanetProfile, hydrogen_inventory_proxy: float) -> str:
    thresholds = MIXING_CLASS_THRESHOLDS
    if (
        hydrogen_inventory_proxy >= thresholds["high_hydrogen_inventory"]
        or profile.gravity_ms2 <= thresholds["low_gravity_ms2"]
    ):
        return "high"
    if profile.atmosphere.pressure_bar >= thresholds["high_pressure_bar"]:
        return "moderate"
    return "low"


def _estimate_quench_strength(profile: PlanetProfile, vertical_mixing_class: str) -> float:
    mix_factor = {"low": 0.3, "moderate": 0.6, "high": 1.0}[vertical_mixing_class]
    return max(
        0.0,
        min(
            mix_factor
            * math.pow(max(profile.atmosphere.temperature_k, 120.0) / 800.0, 0.6)
            * math.pow(max(profile.atmosphere.pressure_bar, 0.05), 0.2),
            2.0,
        ),
    )


def _estimate_cloud_haze_opacity(profile: PlanetProfile, metallicity_proxy: float, hydrogen_inventory_proxy: float) -> float:
    fractions = profile.atmosphere.gas_fractions
    opacity = 0.12
    opacity += 0.22 if 220.0 <= profile.atmosphere.temperature_k <= 350.0 and fractions.get("H2O", 0.0) > 0.05 else 0.0
    opacity += 0.28 * fractions.get("CH4", 0.0)
    opacity += 0.12 * max(metallicity_proxy, 0.0)
    opacity += 0.08 if profile.atmosphere.pressure_bar >= 3.0 else 0.0
    opacity += 0.08 if hydrogen_inventory_proxy >= 0.3 and profile.atmosphere.temperature_k < 260.0 else 0.0
    return max(0.05, min(opacity, 5.0))
