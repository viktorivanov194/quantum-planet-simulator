from __future__ import annotations

from app.models.chemistry import CandidateResponse, QuantumCandidateInput
from app.models.molecular_probe import MolecularProbeResult
from app.models.planet import PlanetProfile, ValidationResult
from app.models.report import FinalDiscoveryReport
from app.models.scientific import ScientificProxyProfile
from app.models.spectrum import SpectrumResponse


def build_final_report(
    profile: PlanetProfile,
    validation: ValidationResult,
    chemistry: CandidateResponse,
    selected_candidate: QuantumCandidateInput | None,
    molecular_probe: MolecularProbeResult | None,
    spectrum: SpectrumResponse | None,
    scientific: ScientificProxyProfile | None = None,
) -> FinalDiscoveryReport:
    chemistry_modes = ", ".join(chemistry.chemistry_modes[:3]) if chemistry.chemistry_modes else "balanced atmospheric"
    top_formulas = [candidate.formula for candidate in chemistry.candidates[:3]]
    candidate_formula = selected_candidate.formula if selected_candidate else (top_formulas[0] if top_formulas else "the leading candidate")
    candidate_name = selected_candidate.name if selected_candidate else "the leading candidate"
    dominant_spectrum = ", ".join((spectrum.dominant_molecules if spectrum else chemistry.chemistry_modes)[:3]) if (spectrum or chemistry.chemistry_modes) else "baseline gases"
    confidence_score = _compute_report_confidence(validation, spectrum, scientific)
    clarity_mode = scientific.atmospheric_clarity_mode if scientific else "clear"
    observation_mode = scientific.observation_confidence_mode if scientific else "strong-feature"

    if observation_mode == "null-signal":
        discovery_headline = (
            f"Synthetic analysis is consistent with a low-contrast or null-signal observational outcome for {profile.planet_name}."
        )
        discovery_summary = (
            f"This proxy run suggests that atmospheric suppression, ambiguity, or weak spectral visibility may limit a clean "
            f"transmission-spectrum interpretation for {profile.planet_name}. Candidate absorbers such as {candidate_formula} remain "
            f"illustrative contributors rather than detected species."
        )
    elif observation_mode == "ambiguous":
        discovery_headline = (
            f"Synthetic analysis keeps {candidate_formula} among the plausible contributors under an observationally ambiguous {clarity_mode} atmosphere."
        )
        discovery_summary = (
            f"This synthetic planetary analysis keeps {candidate_formula} and adjacent contributors in the interpretive set, "
            f"while acknowledging that the current {clarity_mode} atmosphere may blur clean attribution. The result is a "
            f"regime-based proxy inference rather than a retrieval or detection claim."
        )
    else:
        discovery_headline = (
            f"Synthetic analysis suggests that {candidate_formula} could be a prominent candidate contributor under {profile.orbit_zone} {chemistry_modes} conditions."
        )
        discovery_summary = (
            f"This synthetic planetary analysis suggests that {candidate_formula} and nearby atmospheric contributors could produce "
            f"the clearest proxy features for {profile.planet_name}. The result remains a lightweight, regime-based interpretation "
            f"built from chemistry proxies and synthetic transmission-spectrum logic."
        )

    key_highlights = [
        f"{profile.planet_name} was generated as a {profile.orbit_zone} world around a {profile.star_type} star.",
        f"Validation score reached {validation.score:.2f} with {len(validation.issues)} flagged issue(s).",
        f"Atmospheric interpretation remains consistent with the chemistry regime '{chemistry_modes}'.",
        f"Spectrum synthesis highlights candidate contributors: {dominant_spectrum}.",
    ]
    if selected_candidate:
        key_highlights.append(
            f"{candidate_name} ({candidate_formula}) was selected for optional molecular probe follow-up with chemistry tag '{selected_candidate.tag}'."
        )
    if scientific:
        key_highlights.append(
            f"Observation mode resolved to {scientific.observation_confidence_mode} with {scientific.atmospheric_clarity_mode} atmospheric clarity."
        )
    caution_notes = _build_caution_notes(validation, molecular_probe, spectrum)
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
            f"The atmosphere is interpreted through a regime-based proxy model that is consistent with {chemistry_modes} conditions. "
            f"Leading candidate absorbers are {', '.join(top_formulas) if top_formulas else 'not resolved in this run'}. "
            f"These are plausible contributors, not retrieved abundances or detections."
        ),
        molecular_probe_overview=(
            f"Molecular probe on {candidate_formula}: status '{molecular_probe.probe_status}', "
            f"model '{molecular_probe.probe_model}', "
            f"probe agreement {(molecular_probe.probe_agreement or 0.0):.2f}. "
            f"This result is molecule-specific and is not used for atmospheric inference or spectral weighting."
            if molecular_probe
            else "No molecular probe annotation was produced for this run."
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
    spectrum: SpectrumResponse | None,
    scientific: ScientificProxyProfile | None,
) -> float:
    confidence = 0.45 + validation.score * 0.25
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
    molecular_probe: MolecularProbeResult | None,
    spectrum: SpectrumResponse | None,
) -> list[str]:
    cautions = [
        "This report is synthetic and intended for lightweight scientific interpretation, not observational validation.",
        "The spectrum is a transmission-style proxy and does not perform full radiative transfer or retrieval.",
    ]
    cautions.extend(issue.message for issue in validation.issues[:3])
    if molecular_probe:
        cautions.append("The molecular probe is an educational molecule-specific annotation and does not affect atmospheric or spectral inference.")
        if molecular_probe.probe_status == "cached_reference":
            cautions.append("The molecular probe used a cached reference rather than a fresh live calculation.")
        if molecular_probe.probe_status in {"unsupported", "failed"}:
            cautions.append("No live molecular probe annotation was available for the selected molecule.")
    if spectrum and spectrum.metadata.confidence_score and spectrum.metadata.confidence_score < 0.75:
        cautions.append("Spectrum confidence is moderate; highlighted bands should be treated as illustrative.")
    return cautions[:5]
