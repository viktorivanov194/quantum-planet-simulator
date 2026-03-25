from __future__ import annotations

from app.models.chemistry import CandidateResponse, QuantumCandidateInput
from app.models.planet import PlanetProfile, ValidationResult
from app.models.quantum import QuantumEvaluationResult
from app.models.report import FinalDiscoveryReport
from app.models.spectrum import SpectrumResponse


def build_final_report(
    profile: PlanetProfile,
    validation: ValidationResult,
    chemistry: CandidateResponse,
    selected_candidate: QuantumCandidateInput | None,
    quantum: QuantumEvaluationResult | None,
    spectrum: SpectrumResponse | None,
) -> FinalDiscoveryReport:
    chemistry_modes = ", ".join(chemistry.chemistry_modes[:3]) if chemistry.chemistry_modes else "balanced atmospheric"
    candidate_formula = selected_candidate.formula if selected_candidate else "the leading candidate"
    candidate_name = selected_candidate.name if selected_candidate else "the leading candidate"
    dominant_spectrum = ", ".join((spectrum.dominant_molecules if spectrum else chemistry.chemistry_modes)[:3]) if (spectrum or chemistry.chemistry_modes) else "baseline gases"
    confidence_score = _compute_report_confidence(validation, quantum, spectrum)

    discovery_headline = (
        f"Synthetic analysis points to {candidate_formula} as a high-visibility signature under {profile.orbit_zone} {chemistry_modes} conditions."
    )
    discovery_summary = (
        f"This synthetic planetary analysis suggests that {candidate_formula} and nearby atmospheric contributors would dominate "
        f"the observable transmission signature for {profile.planet_name}. The result is a demo-grade inference built from "
        f"rule-based chemistry, cache-first quantum scoring, and lightweight spectral signatures."
    )

    key_highlights = [
        f"{profile.planet_name} was generated as a {profile.orbit_zone} world around a {profile.star_type} star.",
        f"Validation score reached {validation.score:.2f} with {len(validation.issues)} flagged issue(s).",
        f"{candidate_name} ({candidate_formula}) was selected for quantum follow-up with chemistry tag '{selected_candidate.tag if selected_candidate else 'n/a'}'.",
        f"Spectrum synthesis highlights: {dominant_spectrum}.",
    ]
    caution_notes = _build_caution_notes(validation, quantum, spectrum)

    return FinalDiscoveryReport(
        title="Quantum Planet Simulator",
        subtitle="Synthetic exoplanet discovery report for hackathon demonstration",
        discovery_headline=discovery_headline,
        discovery_summary=discovery_summary,
        planet_overview=(
            f"{profile.planet_name} is modeled with radius {profile.radius_rearth:.2f} R⊕, mass {profile.mass_mearth:.2f} M⊕, "
            f"equilibrium temperature {profile.equilibrium_temperature_k:.1f} K, and pressure {profile.atmosphere.pressure_bar:.2f} bar."
        ),
        chemistry_overview=(
            f"The atmosphere is interpreted as {chemistry_modes}, with top candidates led by "
            f"{', '.join(candidate.formula for candidate in chemistry.candidates[:3])}."
        ),
        quantum_overview=(
            f"Quantum evaluation selected {candidate_formula} with energy proxy "
            f"{quantum.ground_state_energy_proxy:.3f} and stability score {quantum.stability_score:.2f} "
            f"from source '{quantum.source}'." if quantum else "Quantum evaluation did not return a selected result."
        ),
        spectrum_overview=(
            spectrum.summary_text if spectrum else "Synthetic spectrum was not generated for this run."
        ),
        key_highlights=key_highlights,
        caution_notes=caution_notes,
        confidence_score=confidence_score,
        novelty_tagline=(
            "A CPU-first discovery stack that turns plausible worlds into presentable spectral stories."
        ),
    )


def _compute_report_confidence(
    validation: ValidationResult,
    quantum: QuantumEvaluationResult | None,
    spectrum: SpectrumResponse | None,
) -> float:
    confidence = 0.45 + validation.score * 0.25
    if quantum is not None:
        confidence += quantum.stability_score * 0.15
        confidence += (quantum.confidence_score or 0.5) * 0.1
    if spectrum is not None:
        confidence += (spectrum.metadata.confidence_score or 0.5) * 0.05
    return round(max(0.0, min(confidence, 0.96)), 3)


def _build_caution_notes(
    validation: ValidationResult,
    quantum: QuantumEvaluationResult | None,
    spectrum: SpectrumResponse | None,
) -> list[str]:
    cautions = [
        "This report is synthetic and intended for MVP demonstration, not observational validation.",
        "The spectrum is signature-based and does not perform full radiative transfer.",
    ]
    cautions.extend(issue.message for issue in validation.issues[:3])
    if quantum and quantum.source == "fallback":
        cautions.append("Quantum result used fallback mode, so interpret comparative stability conservatively.")
    if quantum and quantum.source == "cached":
        cautions.append("Quantum result came from local cache rather than a fresh live evaluation.")
    if spectrum and spectrum.metadata.confidence_score and spectrum.metadata.confidence_score < 0.75:
        cautions.append("Spectrum confidence is moderate; highlighted bands should be treated as illustrative.")
    return cautions[:5]
