from __future__ import annotations

from app.models.molecular_probe import MolecularProbeRequest
from app.models.quantum import QuantumEvaluationRequest, QuantumEvaluationResponse, QuantumEvaluationResult
from app.services.molecular_probe_service import build_molecular_probe_request, run_molecular_probe


def evaluate_candidates(request: QuantumEvaluationRequest) -> QuantumEvaluationResponse:
    translated_mode = {"demo_balanced": "auto", "cached_only": "cached_only", "fallback_only": "disabled"}.get(
        request.runtime_mode,
        "auto",
    )
    probe_request = MolecularProbeRequest(
        candidates=request.candidates,
        runtime_mode=translated_mode,
        selected_formula=request.selected_formula,
        cache_path=request.cache_path,
        allow_live_probe=True,
        allow_cached_reference=True,
        selected_by_pipeline=True,
        selection_reason="legacy_quantum_wrapper",
    )
    probe_response = run_molecular_probe(probe_request)
    results = [_translate_probe_result(result) for result in probe_response.results]
    selected_result = _pick_selected_result(results, request.selected_formula)
    return QuantumEvaluationResponse(
        results=results,
        selected_result=selected_result,
        runtime_mode=request.runtime_mode,
        live_evaluation_used=probe_response.live_probe_used,
    )


def build_quantum_request(
    candidates,
    runtime_mode: str = "demo_balanced",
    selected_formula: str | None = None,
) -> QuantumEvaluationRequest:
    translated_mode = {"auto": "demo_balanced", "cached_only": "cached_only", "disabled": "fallback_only"}.get(runtime_mode, runtime_mode)
    return QuantumEvaluationRequest(
        candidates=candidates,
        runtime_mode=translated_mode,
        selected_formula=selected_formula,
    )


def _translate_probe_result(result) -> QuantumEvaluationResult:
    source_map = {
        "live": "live",
        "cached_reference": "cached",
        "unsupported": "fallback",
        "failed": "fallback",
    }
    notes = list(result.provenance_details)
    if result.failure_message:
        notes.append(result.failure_message)
    if not notes:
        notes = list(result.scientific_caveats)
    return QuantumEvaluationResult(
        name=result.molecule_name,
        formula=result.formula,
        ground_state_energy_proxy=float(result.electronic_energy_proxy or result.reference_energy_proxy or -1.0),
        stability_score=float(result.probe_agreement or 0.0),
        source=source_map[result.probe_status],
        notes=notes,
        confidence_score=float(result.probe_agreement or 0.0),
        classical_reference_energy_proxy=result.reference_energy_proxy,
        baseline_agreement_score=result.probe_agreement,
        verification_mode=result.probe_model,
    )


def _pick_selected_result(results: list[QuantumEvaluationResult], selected_formula: str | None) -> QuantumEvaluationResult | None:
    if not results:
        return None
    if selected_formula is None:
        return results[0]
    selected_lower = selected_formula.lower()
    for result in results:
        if result.formula.lower() == selected_lower or result.name.lower() == selected_lower:
            return result
    return results[0]
