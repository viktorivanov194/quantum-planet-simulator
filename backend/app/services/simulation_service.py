from __future__ import annotations

from app.core.planet_rules import PLANET_PRESETS
from app.models.chemistry import CandidateRequest, MoleculeCandidate, QuantumCandidateInput
from app.models.planet import PlanetGenerationRequest
from app.models.quantum import QuantumEvaluationResult
from app.models.simulation import SimulationRunRequest, SimulationRunResponse
from app.models.spectrum import SpectrumRequest
from app.services.chemistry_service import get_candidate_molecules
from app.services.planet_service import generate_planet_profile, validate_planet_profile
from app.services.quantum_service import build_quantum_request, evaluate_candidates
from app.services.report_service import build_final_report
from app.services.scientific_proxy_service import (
    build_scientific_proxy_profile,
    build_visual_physics_profile,
)
from app.services.spectrum_service import generate_synthetic_spectrum


def run_simulation_pipeline(request: SimulationRunRequest) -> SimulationRunResponse:
    preset = PLANET_PRESETS.get(request.preset_name or "", {})
    star_type = request.star_type
    orbit_zone = request.orbit_zone
    if request.preset_name:
        if star_type == SimulationRunRequest.model_fields["star_type"].default:
            star_type = preset.get("star_type", star_type)
        if orbit_zone == SimulationRunRequest.model_fields["orbit_zone"].default:
            orbit_zone = preset.get("orbit_zone", orbit_zone)

    profile = generate_planet_profile(
        PlanetGenerationRequest(
            generation_mode=request.generation_mode,
            star_type=star_type,
            orbit_zone=orbit_zone,
            seed=request.seed,
            preset_name=request.preset_name,
            planet_name=request.planet_name,
            radius_rearth=request.radius_rearth,
            mass_mearth=request.mass_mearth,
            gravity_ms2=request.gravity_ms2,
            equilibrium_temperature_k=request.equilibrium_temperature_k,
            radiation_level=request.radiation_level,
            atmosphere=request.atmosphere,
        )
    )
    validation = validate_planet_profile(profile)
    chemistry = get_candidate_molecules(
        CandidateRequest(profile=profile, validation=validation, max_candidates=request.max_candidates)
    )

    quantum_candidates = chemistry.selected_for_quantum or _fallback_quantum_candidates(chemistry.candidates)
    selected_candidate = _pick_quantum_candidate(quantum_candidates, request.selected_candidate)
    quantum = None
    spectrum = None
    final_report = None
    scientific_proxy_profile = None

    if selected_candidate is not None:
        quantum_response = evaluate_candidates(
            build_quantum_request(
                candidates=quantum_candidates,
                runtime_mode=request.quantum_runtime_mode,
                selected_formula=selected_candidate.formula,
            )
        )
        quantum = quantum_response.selected_result
        scientific_proxy_profile = build_scientific_proxy_profile(
            profile=profile,
            validation=validation,
            chemistry=chemistry,
            quantum=quantum,
        )
        spectrum = generate_synthetic_spectrum(
            SpectrumRequest(
                profile=profile,
                chemistry_modes=chemistry.chemistry_modes,
                quantum_result=quantum,
                chemistry_candidates=quantum_candidates,
                scientific_profile=scientific_proxy_profile,
            )
        )
        final_report = build_final_report(
            profile=profile,
            validation=validation,
            chemistry=chemistry,
            selected_candidate=selected_candidate,
            quantum=quantum,
            spectrum=spectrum,
            scientific=scientific_proxy_profile,
        )

    scientific_proxy_profile = scientific_proxy_profile or build_scientific_proxy_profile(
        profile=profile,
        validation=validation,
        chemistry=chemistry,
        quantum=quantum,
    )
    visual_physics_profile = build_visual_physics_profile(
        profile=profile,
        validation=validation,
        chemistry=chemistry,
        scientific=scientific_proxy_profile,
        quantum=quantum,
        spectrum=spectrum,
    )

    return SimulationRunResponse(
        profile=profile,
        validation=validation,
        chemistry=chemistry,
        selected_candidate=selected_candidate,
        quantum=quantum,
        spectrum=spectrum,
        scientific_proxy_profile=scientific_proxy_profile,
        visual_physics_profile=visual_physics_profile,
        report_summary=final_report.discovery_headline if final_report else "Simulation run completed without a final report.",
        final_report=final_report,
    )

def _pick_quantum_candidate(
    candidates: list[QuantumCandidateInput],
    selected_name: str | None,
) -> QuantumCandidateInput | None:
    if not candidates:
        return None
    if selected_name is None:
        return candidates[0]

    selected_lower = selected_name.lower()
    for candidate in candidates:
        if candidate.name.lower() == selected_lower or candidate.formula.lower() == selected_lower:
            return candidate
    return candidates[0]


def _fallback_quantum_candidates(candidates: list[MoleculeCandidate]) -> list[QuantumCandidateInput]:
    return [
        QuantumCandidateInput(
            name=candidate.name,
            formula=candidate.formula,
            classical_score=candidate.classical_score,
            tag=candidate.tag,
            rationale=candidate.rationale,
            chemistry_modes=[],
        )
        for candidate in candidates[:3]
    ]
