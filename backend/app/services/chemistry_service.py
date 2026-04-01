from __future__ import annotations

from app.core.chemistry_rules import (
    ALLOWED_MOLECULES,
    MODE_THRESHOLDS,
    PRIMARY_REGIME_ABUNDANCE_PRIORS,
    QUANTUM_PRIORITY,
)
from app.models.chemistry import (
    CandidateRequest,
    CandidateResponse,
    MoleculeCandidate,
    QuantumCandidateInput,
)
from app.models.planet import PlanetProfile, ValidationIssue, ValidationResult
from app.models.state import PlanetAtmosphereState
from app.services.planet_service import validate_planet_profile


def get_candidate_molecules(request: CandidateRequest) -> CandidateResponse:
    validation = request.validation or validate_planet_profile(request.profile)
    modes = classify_chemistry_modes(request.profile, validation, request.state)
    abundance_proxies = estimate_abundance_proxies(request.profile, validation, modes, request.state)

    scored_candidates = [
        _build_candidate(request.profile, validation, modes, abundance_proxies, formula, request.state)
        for formula in ALLOWED_MOLECULES
    ]
    scored_candidates.sort(key=lambda candidate: candidate.classical_score, reverse=True)
    candidates = scored_candidates[: request.max_candidates]
    selected_for_quantum = select_for_quantum(candidates, modes)

    return CandidateResponse(
        candidates=candidates,
        selected_for_quantum=selected_for_quantum,
        abundance_proxies=abundance_proxies,
        chemistry_mode_summary=", ".join(modes) if modes else "balanced atmosphere",
        chemistry_modes=modes,
    )


def classify_chemistry_modes(
    profile: PlanetProfile,
    validation: ValidationResult,
    state: PlanetAtmosphereState | None = None,
) -> list[str]:
    if state is not None:
        return _modes_from_state(profile, validation, state)

    fractions = profile.atmosphere.gas_fractions
    warnings = {issue.code for issue in validation.issues if issue.severity == "warning"}
    modes: list[str] = []

    oxygen_fraction = fractions.get("O2", 0.0)
    reducing_fraction = fractions.get("H2", 0.0) + fractions.get("CH4", 0.0) + fractions.get("NH3", 0.0)
    carbon_fraction = fractions.get("CO2", 0.0) + fractions.get("CH4", 0.0) + fractions.get("CO", 0.0) + fractions.get("HCN", 0.0)
    nitrogen_fraction = fractions.get("N2", 0.0) + fractions.get("NH3", 0.0) + fractions.get("HCN", 0.0)

    if oxygen_fraction >= MODE_THRESHOLDS["oxidizing_o2_fraction"]:
        modes.append("oxidizing")
    if reducing_fraction >= MODE_THRESHOLDS["reducing_fraction"]:
        modes.append("reducing")
    if carbon_fraction >= MODE_THRESHOLDS["carbon_rich_fraction"]:
        modes.append("carbon-rich")
    if nitrogen_fraction >= MODE_THRESHOLDS["nitrogen_rich_fraction"]:
        modes.append("nitrogen-rich")
    if profile.atmosphere.temperature_k >= MODE_THRESHOLDS["hot_temperature_k"]:
        modes.append("hot atmosphere")
    if profile.atmosphere.temperature_k <= MODE_THRESHOLDS["cold_temperature_k"]:
        modes.append("cold atmosphere")
    if profile.atmosphere.pressure_bar <= MODE_THRESHOLDS["thin_pressure_bar"]:
        modes.append("thin atmosphere")
    if profile.atmosphere.pressure_bar >= MODE_THRESHOLDS["dense_pressure_bar"]:
        modes.append("dense atmosphere")
    if profile.radiation_level >= MODE_THRESHOLDS["high_radiation"] or "radiation_high_warning" in warnings:
        modes.append("high-radiation")

    if not modes:
        modes.append("balanced atmosphere")
    return modes


def _modes_from_state(
    profile: PlanetProfile,
    validation: ValidationResult,
    state: PlanetAtmosphereState,
) -> list[str]:
    warnings = {issue.code for issue in validation.issues if issue.severity == "warning"}
    modes: list[str] = []

    regime_mode_map = {
        "oxidized_terrestrial": ["oxidizing"],
        "volatile_rich_temperate": ["dense atmosphere"],
        "h2_rich_mini_neptune": ["reducing", "dense atmosphere"],
        "hot_co2_co_atmosphere": ["hot atmosphere", "carbon-rich"],
        "cold_methane_atmosphere": ["cold atmosphere", "reducing", "carbon-rich"],
    }
    for mode in regime_mode_map.get(state.primary_atmospheric_regime, []):
        if mode not in modes:
            modes.append(mode)

    if state.oxidation_reduction_proxy >= 0.12 and "oxidizing" not in modes:
        modes.append("oxidizing")
    if state.oxidation_reduction_proxy <= -0.12 and "reducing" not in modes:
        modes.append("reducing")
    if state.carbon_to_oxygen_ratio >= 0.8 and "carbon-rich" not in modes:
        modes.append("carbon-rich")
    if profile.atmosphere.gas_fractions.get("N2", 0.0) + profile.atmosphere.gas_fractions.get("NH3", 0.0) >= MODE_THRESHOLDS["nitrogen_rich_fraction"]:
        modes.append("nitrogen-rich")
    if state.atmospheric_temperature_k >= MODE_THRESHOLDS["hot_temperature_k"] and "hot atmosphere" not in modes:
        modes.append("hot atmosphere")
    if state.atmospheric_temperature_k <= MODE_THRESHOLDS["cold_temperature_k"] and "cold atmosphere" not in modes:
        modes.append("cold atmosphere")
    if state.pressure_class == "thin" and "thin atmosphere" not in modes:
        modes.append("thin atmosphere")
    if state.pressure_class == "dense" and "dense atmosphere" not in modes:
        modes.append("dense atmosphere")
    if state.uv_activity == "high" or "radiation_high_warning" in warnings:
        modes.append("high-radiation")

    modifier_mode_map = {
        "photochemical_haze": "hazy",
        "cloud_muted": "dense atmosphere",
        "escape_stressed": "thin atmosphere",
        "high_uv_processed": "high-radiation",
    }
    for modifier in state.secondary_regime_modifiers:
        mapped = modifier_mode_map.get(modifier)
        if mapped and mapped not in modes:
            modes.append(mapped)

    if not modes:
        modes.append("balanced atmosphere")
    return modes


def select_for_quantum(
    candidates: list[MoleculeCandidate],
    chemistry_modes: list[str],
) -> list[QuantumCandidateInput]:
    supported = [candidate for candidate in candidates if candidate.formula in QUANTUM_PRIORITY]
    if not supported:
        return []

    priority_map = {formula: index for index, formula in enumerate(QUANTUM_PRIORITY)}
    ordered = sorted(
        supported,
        key=lambda candidate: (
            priority_map.get(candidate.formula, len(priority_map)),
            -candidate.classical_score,
        ),
    )
    shortlist_size = 3 if len(ordered) >= 3 else len(ordered)
    return [
        QuantumCandidateInput(
            name=candidate.name,
            formula=candidate.formula,
            classical_score=candidate.classical_score,
            mixing_ratio_proxy=candidate.mixing_ratio_proxy,
            tag=candidate.tag,
            rationale=candidate.rationale,
            chemistry_modes=chemistry_modes,
        )
        for candidate in ordered[:shortlist_size]
    ]


def _build_candidate(
    profile: PlanetProfile,
    validation: ValidationResult,
    modes: list[str],
    abundance_proxies: dict[str, float],
    formula: str,
    state: PlanetAtmosphereState | None,
) -> MoleculeCandidate:
    metadata = ALLOWED_MOLECULES[formula]
    score = metadata["base_score"]
    abundance_proxy = abundance_proxies.get(formula, 0.0)
    reasons: list[str] = []

    if abundance_proxy >= 0.2:
        score += 0.34
        reasons.append("mixing-ratio proxy is high in the current atmospheric regime")
    elif abundance_proxy >= 0.08:
        score += 0.2
        reasons.append("mixing-ratio proxy is moderately supported by the current atmospheric regime")
    elif abundance_proxy > 0.0:
        score += min(0.16, abundance_proxy * 1.5)
        reasons.append("mixing-ratio proxy remains non-zero in the current atmospheric regime")

    mode_adjustments = _score_mode_effects(formula, modes)
    score += mode_adjustments["score_delta"]
    reasons.extend(mode_adjustments["reasons"])

    env_adjustments = _score_environment_effects(profile, validation.issues, formula, state)
    score += env_adjustments["score_delta"]
    reasons.extend(env_adjustments["reasons"])

    score += min(abundance_proxy * 0.35, 0.24)
    if abundance_proxy >= 0.12:
        reasons.append("abundance proxy elevates this molecule above trace-only status")

    tag = _tag_candidate(score, formula, modes)
    rationale = _compress_rationale(reasons, profile, formula)

    return MoleculeCandidate(
        name=metadata["name"],
        formula=formula,
        classical_score=round(max(0.0, min(score, 1.0)), 3),
        mixing_ratio_proxy=round(max(0.0, min(abundance_proxy, 1.0)), 4),
        rationale=rationale,
        tag=tag,
    )


def _score_mode_effects(formula: str, modes: list[str]) -> dict[str, float | list[str]]:
    score_delta = 0.0
    reasons: list[str] = []
    mode_set = set(modes)

    if "oxidizing" in mode_set:
        if formula in {"O2", "H2O", "CO2", "SO2"}:
            score_delta += 0.18
            reasons.append("favored by oxidizing conditions")
        if formula in {"CH4", "NH3", "H2", "HCN"}:
            score_delta -= 0.16
            reasons.append("less favored in oxidizing conditions")

    if "reducing" in mode_set:
        if formula in {"CH4", "NH3", "H2", "HCN"}:
            score_delta += 0.22
            reasons.append("favored by reducing conditions")
        if formula == "O2":
            score_delta -= 0.2
            reasons.append("less favored in reducing conditions")

    if "carbon-rich" in mode_set:
        if formula in {"CO2", "CH4", "CO", "HCN"}:
            score_delta += 0.18
            reasons.append("supported by carbon-rich chemistry")

    if "nitrogen-rich" in mode_set:
        if formula in {"N2", "NH3", "HCN"}:
            score_delta += 0.16
            reasons.append("supported by nitrogen-rich chemistry")

    if "hot atmosphere" in mode_set:
        if formula in {"CO2", "CO", "SO2"}:
            score_delta += 0.16
            reasons.append("stable enough for hotter atmosphere scenarios")
        if formula in {"NH3", "H2O"}:
            score_delta -= 0.08
            reasons.append("less stable at the hot edge of the demo range")

    if "cold atmosphere" in mode_set:
        if formula in {"NH3", "CH4", "N2"}:
            score_delta += 0.12
            reasons.append("cold conditions make it more plausible in the demo model")

    if "thin atmosphere" in mode_set:
        if formula in {"CO", "H2", "N2"}:
            score_delta += 0.1
            reasons.append("thin atmosphere favors simpler retained species")
        if formula in {"H2O", "NH3"}:
            score_delta -= 0.1
            reasons.append("thin atmosphere makes this candidate less persistent")

    if "dense atmosphere" in mode_set:
        if formula in {"CO2", "SO2", "H2O"}:
            score_delta += 0.12
            reasons.append("dense atmosphere can support stronger absorption candidates")

    if "high-radiation" in mode_set:
        if formula in {"CH4", "NH3", "HCN"}:
            score_delta -= 0.14
            reasons.append("high radiation can reduce persistence of fragile molecules")
        if formula in {"CO", "CO2", "SO2"}:
            score_delta += 0.08
            reasons.append("high radiation leaves more conservative candidates attractive")

    return {"score_delta": score_delta, "reasons": reasons}


def _score_environment_effects(
    profile: PlanetProfile,
    issues: list[ValidationIssue],
    formula: str,
    state: PlanetAtmosphereState | None,
) -> dict[str, float | list[str]]:
    score_delta = 0.0
    reasons: list[str] = []
    warning_codes = {issue.code for issue in issues if issue.severity == "warning"}

    if profile.orbit_zone == "cold" and formula in {"CH4", "NH3", "N2"}:
        score_delta += 0.08
        reasons.append("cold orbit zone supports this candidate")
    if profile.orbit_zone == "hot" and formula in {"CO2", "CO", "SO2"}:
        score_delta += 0.1
        reasons.append("hot orbit zone supports thermally robust species")

    if profile.star_type == "M-type" and formula in {"CH4", "HCN", "CO"}:
        score_delta += 0.05
        reasons.append("M-type stellar context keeps reduced carbon species interesting")
    if profile.star_type == "G-type" and formula in {"O2", "H2O", "CO2"}:
        score_delta += 0.05
        reasons.append("G-type stellar context fits conservative oxidized candidates")

    if state is not None:
        if state.escape_susceptibility_proxy >= 0.9 and formula in {"H2", "CH4", "NH3"}:
            score_delta -= 0.12
            reasons.append("escape susceptibility suppresses fragile reduced species")
        if state.quench_strength_proxy >= 0.65 and formula in {"CH4", "NH3", "CO"}:
            score_delta += 0.08
            reasons.append("quench proxy keeps this species competitive above equilibrium expectations")
        if state.metallicity_proxy >= 0.4 and formula in {"H2O", "CO2", "CO", "SO2"}:
            score_delta += 0.05
            reasons.append("higher metallicity proxy favors heavy volatile species")

    if "thin_atmosphere_high_radiation" in warning_codes and formula in {"CH4", "NH3", "HCN"}:
        score_delta -= 0.12
        reasons.append("validation flagged the atmosphere as harsh for fragile candidates")
    if "hot_thin_atmosphere_warning" in warning_codes and formula in {"CO", "SO2"}:
        score_delta += 0.08
        reasons.append("warning pattern shifts attention to hot thin-atmosphere survivors")
    if "pressure_high_warning" in warning_codes and formula in {"CO2", "SO2", "H2O"}:
        score_delta += 0.06
        reasons.append("dense-atmosphere warning boosts strong absorber candidates")

    return {"score_delta": score_delta, "reasons": reasons}


def _tag_candidate(score: float, formula: str, modes: list[str]) -> str:
    if score >= 0.68:
        return "allowed"
    if score >= 0.42:
        return "speculative"
    if formula in {"HCN", "NH3"} and "oxidizing" in modes:
        return "discouraged"
    return "discouraged"


def _compress_rationale(reasons: list[str], profile: PlanetProfile, formula: str) -> str:
    unique_reasons: list[str] = []
    for reason in reasons:
        if reason not in unique_reasons:
            unique_reasons.append(reason)
    if not unique_reasons:
        unique_reasons.append("included as a controlled baseline candidate for the MVP shortlist")
    prefix = f"{formula} scored against {profile.star_type} / {profile.orbit_zone} conditions"
    return f"{prefix}: " + "; ".join(unique_reasons[:3]) + "."


def estimate_abundance_proxies(
    profile: PlanetProfile,
    validation: ValidationResult,
    modes: list[str],
    state: PlanetAtmosphereState | None,
) -> dict[str, float]:
    if state is None:
        return _legacy_abundance_proxies(profile)
    return _state_abundance_proxies(profile, validation, modes, state)


def _legacy_abundance_proxies(profile: PlanetProfile) -> dict[str, float]:
    abundance = {formula: 0.0 for formula in ALLOWED_MOLECULES}
    for formula, fraction in profile.atmosphere.gas_fractions.items():
        if formula in abundance:
            abundance[formula] = round(max(fraction, 0.0), 4)
    return abundance


def _state_abundance_proxies(
    profile: PlanetProfile,
    validation: ValidationResult,
    modes: list[str],
    state: PlanetAtmosphereState,
) -> dict[str, float]:
    priors = PRIMARY_REGIME_ABUNDANCE_PRIORS[state.primary_atmospheric_regime].copy()
    fractions = profile.atmosphere.gas_fractions
    abundance = {formula: 0.0 for formula in ALLOWED_MOLECULES}

    for formula in abundance:
        prior = priors.get(formula, 0.0)
        observed_hint = fractions.get(formula, 0.0)
        abundance[formula] = 0.7 * prior + 0.3 * observed_hint

    # Composition controls
    co_ratio = state.carbon_to_oxygen_ratio
    metallicity = max(state.metallicity_proxy, 0.0)
    uv_factor = {"low": 0.85, "moderate": 1.0, "high": 1.25}[state.uv_activity]
    escape = state.escape_susceptibility_proxy
    quench = state.quench_strength_proxy

    if co_ratio < 0.8:
        abundance["H2O"] += 0.08 * (0.8 - co_ratio) / 0.8
        abundance["CO2"] += 0.06 * (0.8 - co_ratio) / 0.8
    else:
        abundance["CH4"] += 0.08 * min(co_ratio - 0.8, 0.7)
        abundance["CO"] += 0.06 * min(co_ratio - 0.8, 0.7)
        abundance["HCN"] += 0.03 * max(co_ratio - 1.0, 0.0)
        abundance["H2O"] *= 0.82

    heavy_factor = 1.0 + 0.18 * metallicity
    for formula in {"H2O", "CO2", "CO", "SO2"}:
        abundance[formula] *= heavy_factor

    abundance["H2"] *= max(0.35, 1.0 - 0.28 * metallicity)
    abundance["He"] *= max(0.45, 1.0 - 0.1 * metallicity)

    if state.primary_atmospheric_regime == "hot_co2_co_atmosphere":
        abundance["CO2"] *= 1.2
        abundance["CO"] *= 1.25
        abundance["CH4"] *= 0.3
        abundance["NH3"] *= 0.2
        abundance["H2O"] *= 0.6
    if state.primary_atmospheric_regime == "cold_methane_atmosphere":
        abundance["CH4"] *= 1.25
        abundance["NH3"] *= 1.18
        abundance["CO"] *= 0.82
    if state.primary_atmospheric_regime == "h2_rich_mini_neptune":
        abundance["H2"] *= 1.1
        abundance["He"] *= 1.08

    # Escape and UV processing
    abundance["H2"] *= max(0.12, 1.0 - 0.55 * escape)
    abundance["CH4"] *= max(0.18, 1.0 - 0.38 * escape) * max(0.3, 1.15 - 0.28 * uv_factor)
    abundance["NH3"] *= max(0.12, 1.0 - 0.44 * escape) * max(0.22, 1.1 - 0.36 * uv_factor)
    abundance["HCN"] *= max(0.2, 1.0 - 0.2 * escape) * (0.92 + 0.08 * uv_factor)

    # Quenching supports reduced carbon / nitrogen persistence.
    abundance["CH4"] += 0.05 * quench * max(state.hydrogen_inventory_proxy, 0.1)
    abundance["NH3"] += 0.04 * quench * max(state.hydrogen_inventory_proxy, 0.1)
    abundance["CO"] += 0.03 * quench * (1.0 if state.atmospheric_temperature_k >= 350 else 0.6)

    # Clouds/haze and modifier effects.
    if "photochemical_haze" in state.secondary_regime_modifiers:
        abundance["CH4"] *= 0.92
        abundance["HCN"] *= 1.12
    if "escape_stressed" in state.secondary_regime_modifiers:
        abundance["H2"] *= 0.82
        abundance["CH4"] *= 0.88
        abundance["NH3"] *= 0.82
    if "high_uv_processed" in state.secondary_regime_modifiers:
        abundance["CO"] *= 1.08
        abundance["CO2"] *= 1.05

    # Preserve explicit user-specified major components as hard hints.
    for formula, fraction in fractions.items():
        if formula in abundance and fraction >= 0.08:
            abundance[formula] = max(abundance[formula], fraction * 0.9)

    total = sum(max(value, 0.0) for value in abundance.values())
    if total <= 0:
        return {formula: 0.0 for formula in ALLOWED_MOLECULES}
    return {formula: round(max(value, 0.0) / total, 4) for formula, value in abundance.items()}
