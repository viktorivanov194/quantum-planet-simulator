from __future__ import annotations

from app.core.chemistry_rules import ALLOWED_MOLECULES, MODE_THRESHOLDS, QUANTUM_PRIORITY
from app.models.chemistry import (
    CandidateRequest,
    CandidateResponse,
    MoleculeCandidate,
    QuantumCandidateInput,
)
from app.models.planet import PlanetProfile, ValidationIssue, ValidationResult
from app.services.planet_service import validate_planet_profile


def get_candidate_molecules(request: CandidateRequest) -> CandidateResponse:
    validation = request.validation or validate_planet_profile(request.profile)
    modes = classify_chemistry_modes(request.profile, validation)

    scored_candidates = [
        _build_candidate(request.profile, validation, modes, formula)
        for formula in ALLOWED_MOLECULES
    ]
    scored_candidates.sort(key=lambda candidate: candidate.classical_score, reverse=True)
    candidates = scored_candidates[: request.max_candidates]
    selected_for_quantum = select_for_quantum(candidates, modes)

    return CandidateResponse(
        candidates=candidates,
        selected_for_quantum=selected_for_quantum,
        chemistry_mode_summary=", ".join(modes) if modes else "balanced atmosphere",
        chemistry_modes=modes,
    )


def classify_chemistry_modes(profile: PlanetProfile, validation: ValidationResult) -> list[str]:
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


def select_for_quantum(
    candidates: list[MoleculeCandidate],
    chemistry_modes: list[str],
) -> list[QuantumCandidateInput]:
    if not candidates:
        return []

    priority_map = {formula: index for index, formula in enumerate(QUANTUM_PRIORITY)}
    ordered = sorted(
        candidates,
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
    formula: str,
) -> MoleculeCandidate:
    fractions = profile.atmosphere.gas_fractions
    metadata = ALLOWED_MOLECULES[formula]
    score = metadata["base_score"]
    reasons: list[str] = []

    if formula in profile.atmosphere.dominant_gases:
        score += 0.38
        reasons.append("already present among dominant gases")
    elif fractions.get(formula, 0.0) > 0.02:
        score += 0.2
        reasons.append("already present in the atmosphere mix")

    mode_adjustments = _score_mode_effects(formula, modes)
    score += mode_adjustments["score_delta"]
    reasons.extend(mode_adjustments["reasons"])

    env_adjustments = _score_environment_effects(profile, validation.issues, formula)
    score += env_adjustments["score_delta"]
    reasons.extend(env_adjustments["reasons"])

    tag = _tag_candidate(score, formula, modes)
    rationale = _compress_rationale(reasons, profile, formula)

    return MoleculeCandidate(
        name=metadata["name"],
        formula=formula,
        classical_score=round(max(0.0, min(score, 1.0)), 3),
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
