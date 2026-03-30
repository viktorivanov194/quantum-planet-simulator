from __future__ import annotations

from app.models.chemistry import CandidateResponse, QuantumCandidateInput
from app.models.planet import PlanetProfile, ValidationResult
from app.models.quantum import QuantumEvaluationResult
from app.models.report import FinalDiscoveryReport
from app.models.scientific import ScientificProxyProfile
from app.models.spectrum import SpectrumResponse


def build_final_report(
    profile: PlanetProfile,
    validation: ValidationResult,
    chemistry: CandidateResponse,
    selected_candidate: QuantumCandidateInput | None,
    quantum: QuantumEvaluationResult | None,
    spectrum: SpectrumResponse | None,
    scientific: ScientificProxyProfile | None = None,
) -> FinalDiscoveryReport:
    chemistry_modes = ", ".join(chemistry.chemistry_modes[:3]) if chemistry.chemistry_modes else "balanced atmospheric"
    candidate_formula = selected_candidate.formula if selected_candidate else "the leading candidate"
    candidate_name = selected_candidate.name if selected_candidate else "the leading candidate"
    dominant_spectrum = ", ".join((spectrum.dominant_molecules if spectrum else chemistry.chemistry_modes)[:3]) if (spectrum or chemistry.chemistry_modes) else "baseline gases"
    confidence_score = _compute_report_confidence(validation, quantum, spectrum, scientific)
    clarity_mode = scientific.atmospheric_clarity_mode if scientific else "clear"
    observation_mode = scientific.observation_confidence_mode if scientific else "strong-feature"

    if observation_mode == "null-signal":
        discovery_headline = (
            f"Synthetic analysis suggests a low-contrast or null-signal observational outcome for {profile.planet_name}."
        )
        discovery_summary = (
            f"This proxy run indicates that atmospheric suppression, ambiguity, or weak spectral visibility may prevent a clean "
            f"{candidate_formula} signature from dominating the observable transmission spectrum for {profile.planet_name}. "
            f"The result stays scientifically conservative by treating the outcome as illustrative rather than as a detection."
        )
    elif observation_mode == "ambiguous":
        discovery_headline = (
            f"Synthetic analysis keeps {candidate_formula} in play, but under an observationally ambiguous {clarity_mode} atmosphere."
        )
        discovery_summary = (
            f"This synthetic planetary analysis keeps {candidate_formula} and adjacent contributors in the discovery narrative, "
            f"while acknowledging that the current {clarity_mode} atmosphere may blur a clean interpretation. The result is a "
            f"demo-grade inference built from rule-based chemistry, cache-first quantum scoring, and lightweight spectral signatures."
        )
    else:
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
    if scientific:
        key_highlights.append(
            f"Observation mode resolved to {scientific.observation_confidence_mode} with {scientific.atmospheric_clarity_mode} atmospheric clarity."
        )
    caution_notes = _build_caution_notes(validation, quantum, spectrum)
    if scientific:
        caution_notes.extend(note for note in scientific.observation_risk_notes if note not in caution_notes)
    caution_notes = caution_notes[:5]

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
            f"{', '.join(candidate.formula for candidate in chemistry.candidates[:3])}. "
            f"Clarity mode: {clarity_mode}; observation mode: {observation_mode}."
        ),
        quantum_overview=(
            f"Quantum evaluation selected {candidate_formula} with energy proxy "
            f"{quantum.ground_state_energy_proxy:.3f} and stability score {quantum.stability_score:.2f} "
            f"from source '{quantum.source}'. "
            f"Baseline agreement {(quantum.baseline_agreement_score or 0.0):.2f} via {quantum.verification_mode or 'proxy verification'}."
            if quantum
            else "Quantum evaluation did not return a selected result."
        ),
        spectrum_overview=(
            spectrum.summary_text if spectrum else "Synthetic spectrum was not generated for this run."
        ),
        key_highlights=key_highlights,
        caution_notes=caution_notes,
        confidence_score=confidence_score,
        novelty_tagline=(
            "A CPU-first discovery stack that turns plausible worlds into observational narratives with an honest quantum probe."
        ),
    )


def _compute_report_confidence(
    validation: ValidationResult,
    quantum: QuantumEvaluationResult | None,
    spectrum: SpectrumResponse | None,
    scientific: ScientificProxyProfile | None,
) -> float:
    confidence = 0.45 + validation.score * 0.25
    if quantum is not None:
        confidence += quantum.stability_score * 0.15
        confidence += (quantum.confidence_score or 0.5) * 0.1
        confidence += (quantum.baseline_agreement_score or 0.5) * 0.04
    if spectrum is not None:
        confidence += (spectrum.metadata.confidence_score or 0.5) * 0.05
    if scientific is not None:
        confidence += scientific.spectral_visibility_score * 0.04
        if scientific.observation_confidence_mode == "ambiguous":
            confidence -= 0.08
        if scientific.observation_confidence_mode == "null-signal":
            confidence -= 0.16
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
