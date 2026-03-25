from __future__ import annotations

import json
from pathlib import Path

from app.core.quantum_rules import (
    DEFAULT_CACHE_PATH,
    DEFAULT_RUNTIME_MODE,
    FALLBACK_RESULTS,
    LIVE_SUPPORTED_FORMULAS,
    PROXY_HAMILTONIANS,
    SUPPORTED_FORMULAS,
)
from app.models.chemistry import QuantumCandidateInput
from app.models.quantum import QuantumEvaluationRequest, QuantumEvaluationResponse, QuantumEvaluationResult


def evaluate_candidates(request: QuantumEvaluationRequest) -> QuantumEvaluationResponse:
    cache_path = Path(request.cache_path) if request.cache_path else DEFAULT_CACHE_PATH
    cache = _load_quantum_cache(cache_path)
    runtime_mode = request.runtime_mode or DEFAULT_RUNTIME_MODE
    results: list[QuantumEvaluationResult] = []
    live_evaluation_used = False

    for candidate in request.candidates:
        result: QuantumEvaluationResult

        if candidate.formula not in SUPPORTED_FORMULAS:
            result = _build_fallback_result(candidate, "Formula is outside the supported MVP quantum set.")
        elif runtime_mode == "fallback_only":
            result = _build_fallback_result(candidate, "Fallback-only mode requested.")
        elif runtime_mode == "demo_balanced" and not live_evaluation_used and candidate.formula in LIVE_SUPPORTED_FORMULAS:
            result = _evaluate_live_or_fallback(candidate, cache, cache_path)
            live_evaluation_used = result.source == "live"
        elif runtime_mode in {"cached_only", "demo_balanced"}:
            result = _lookup_cache_or_fallback(candidate, cache)
        else:
            result = _build_fallback_result(candidate, "Unknown runtime mode. Safe fallback applied.")

        results.append(result)

    selected_result = _pick_selected_result(results, request.selected_formula)
    return QuantumEvaluationResponse(
        results=results,
        selected_result=selected_result,
        runtime_mode=runtime_mode,
        live_evaluation_used=live_evaluation_used,
    )


def _lookup_cache_or_fallback(
    candidate: QuantumCandidateInput,
    cache: dict,
) -> QuantumEvaluationResult:
    cached_entry = cache.get(candidate.formula)
    if cached_entry:
        return _build_cached_result(candidate, cached_entry)
    return _build_fallback_result(candidate, "No cache entry found for candidate.")


def _evaluate_live_or_fallback(
    candidate: QuantumCandidateInput,
    cache: dict,
    cache_path: Path,
) -> QuantumEvaluationResult:
    try:
        live_result = _run_live_proxy_evaluation(candidate)
        _persist_live_result(candidate, live_result, cache, cache_path)
        return live_result
    except Exception as exc:
        cached_entry = cache.get(candidate.formula)
        if cached_entry:
            cached_result = _build_cached_result(candidate, cached_entry)
            cached_result.notes.append(f"Live evaluation skipped after error: {exc.__class__.__name__}.")
            return cached_result
        return _build_fallback_result(candidate, f"Live evaluation failed: {exc.__class__.__name__}.")


def _build_cached_result(candidate: QuantumCandidateInput, cached_entry: dict) -> QuantumEvaluationResult:
    metadata = cached_entry.get("metadata", {})
    notes = [cached_entry.get("notes", "Loaded from local quantum cache.")]
    if metadata.get("method"):
        notes.append(f"Method: {metadata['method']}.")

    return QuantumEvaluationResult(
        name=candidate.name,
        formula=candidate.formula,
        ground_state_energy_proxy=float(cached_entry["ground_state_energy_proxy"]),
        stability_score=float(cached_entry["stability_score"]),
        source="cached",
        notes=notes,
        confidence_score=float(cached_entry.get("confidence_score", 0.82)),
    )


def _build_fallback_result(candidate: QuantumCandidateInput, reason: str) -> QuantumEvaluationResult:
    baseline = FALLBACK_RESULTS.get(candidate.formula, {"energy": -1.0, "stability": 0.55})
    adjusted_stability = max(0.0, min(1.0, baseline["stability"] * (0.85 + candidate.classical_score * 0.15)))
    return QuantumEvaluationResult(
        name=candidate.name,
        formula=candidate.formula,
        ground_state_energy_proxy=float(baseline["energy"]),
        stability_score=round(adjusted_stability, 3),
        source="fallback",
        notes=[reason, "Returned a safe proxy result to keep the demo pipeline stable."],
        confidence_score=0.45,
    )


def _run_live_proxy_evaluation(candidate: QuantumCandidateInput) -> QuantumEvaluationResult:
    if candidate.formula not in LIVE_SUPPORTED_FORMULAS:
        raise ValueError("Formula is outside the live-evaluation subset.")

    config = PROXY_HAMILTONIANS[candidate.formula]

    try:
        from qiskit import QuantumCircuit, transpile
        from qiskit.quantum_info import SparsePauliOp
        from qiskit_aer import AerSimulator
        from qiskit_algorithms.minimum_eigensolvers import NumPyMinimumEigensolver
        from qiskit_nature.second_q.formats.molecule_info import MoleculeInfo
    except Exception as exc:
        raise RuntimeError("Qiskit stack unavailable in the current environment.") from exc

    operator = SparsePauliOp.from_list(config["paulis"])
    exact_solver = NumPyMinimumEigensolver()
    exact_energy = float(exact_solver.compute_minimum_eigenvalue(operator).eigenvalue.real + config["offset"])

    circuit = QuantumCircuit(2)
    circuit.ry(config["theta"], 0)
    circuit.cx(0, 1)
    circuit.save_statevector()

    simulator = AerSimulator(method="statevector")
    compiled = transpile(circuit, simulator)
    result = simulator.run(compiled, shots=1).result()
    statevector = result.get_statevector(compiled)
    expectation = float(statevector.expectation_value(operator).real + config["offset"])

    molecule_info = MoleculeInfo(
        symbols=config["symbols"],
        coords=[(0.0, 0.0, 0.0)] * len(config["symbols"]),
        multiplicity=1,
        charge=0,
    )
    stability_score = _compute_stability_score(exact_energy, candidate.classical_score)
    confidence_score = 0.88 if candidate.formula == "H2" else 0.81

    return QuantumEvaluationResult(
        name=candidate.name,
        formula=candidate.formula,
        ground_state_energy_proxy=round(min(exact_energy, expectation), 6),
        stability_score=stability_score,
        source="live",
        notes=[
            "Live proxy evaluation completed with a tiny local Qiskit workflow.",
            f"Proxy molecule metadata length: {len(molecule_info.symbols)} symbols.",
            "Used NumPyMinimumEigensolver plus Aer statevector simulation on a 2-qubit proxy Hamiltonian.",
        ],
        confidence_score=confidence_score,
    )


def _compute_stability_score(energy: float, classical_score: float) -> float:
    normalized_energy = min(1.0, max(0.0, abs(energy) / 2.0))
    stability = 0.55 * normalized_energy + 0.45 * classical_score
    return round(max(0.0, min(1.0, stability)), 3)


def _pick_selected_result(
    results: list[QuantumEvaluationResult],
    selected_formula: str | None,
) -> QuantumEvaluationResult | None:
    if not results:
        return None
    if selected_formula is None:
        return results[0]

    selected_lower = selected_formula.lower()
    for result in results:
        if result.formula.lower() == selected_lower or result.name.lower() == selected_lower:
            return result
    return results[0]


def _persist_live_result(
    candidate: QuantumCandidateInput,
    result: QuantumEvaluationResult,
    cache: dict,
    cache_path: Path,
) -> None:
    cache[candidate.formula] = {
        "name": candidate.name,
        "formula": candidate.formula,
        "ground_state_energy_proxy": result.ground_state_energy_proxy,
        "stability_score": result.stability_score,
        "confidence_score": result.confidence_score,
        "notes": "Stored after local live proxy evaluation.",
        "metadata": {
            "method": "qiskit_proxy_solver",
            "mode": "demo_balanced",
        },
    }
    _save_quantum_cache(cache_path, cache)


def _load_quantum_cache(cache_path: Path) -> dict:
    if not cache_path.exists():
        return {}
    try:
        return json.loads(cache_path.read_text())
    except json.JSONDecodeError:
        return {}


def _save_quantum_cache(cache_path: Path, cache: dict) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, indent=2, sort_keys=True))


def build_quantum_request(
    candidates: list[QuantumCandidateInput],
    runtime_mode: str = DEFAULT_RUNTIME_MODE,
    selected_formula: str | None = None,
) -> QuantumEvaluationRequest:
    return QuantumEvaluationRequest(
        candidates=candidates,
        runtime_mode=runtime_mode,
        selected_formula=selected_formula,
    )
