from __future__ import annotations

import json
from pathlib import Path

from app.core.quantum_rules import DEFAULT_CACHE_PATH, PROXY_HAMILTONIANS
from app.models.chemistry import QuantumCandidateInput
from app.models.molecular_probe import MolecularProbeRequest, MolecularProbeResponse, MolecularProbeResult

LIVE_ALLOWED_FORMULAS = {"H2", "H2O", "CO", "NH3"}
CACHED_ALLOWED_FORMULAS = {"H2", "H2O", "CO", "NH3", "CO2", "CH4", "N2", "O2"}
SUPPORTED_FORMULAS = LIVE_ALLOWED_FORMULAS | CACHED_ALLOWED_FORMULAS


def run_molecular_probe(request: MolecularProbeRequest) -> MolecularProbeResponse:
    if request.runtime_mode == "disabled":
        return MolecularProbeResponse(results=[], selected_result=None, runtime_mode=request.runtime_mode, live_probe_used=False)

    cache_path = Path(request.cache_path) if request.cache_path else DEFAULT_CACHE_PATH
    cache = _load_probe_cache(cache_path)
    results: list[MolecularProbeResult] = []
    live_probe_used = False

    for candidate in request.candidates:
        result = _probe_candidate(candidate, request, cache, cache_path, live_probe_used)
        if result.probe_status == "live":
            live_probe_used = True
        results.append(result)

    selected_result = _pick_selected_result(results, request.selected_formula)
    return MolecularProbeResponse(
        results=results,
        selected_result=selected_result,
        runtime_mode=request.runtime_mode,
        live_probe_used=live_probe_used,
    )


def _probe_candidate(
    candidate: QuantumCandidateInput,
    request: MolecularProbeRequest,
    cache: dict,
    cache_path: Path,
    live_probe_used: bool,
) -> MolecularProbeResult:
    live_allowed = candidate.formula in LIVE_ALLOWED_FORMULAS
    cached_allowed = candidate.formula in CACHED_ALLOWED_FORMULAS

    if candidate.formula not in SUPPORTED_FORMULAS:
        return _unsupported_result(candidate, live_allowed, cached_allowed, "molecule_unsupported", "No lightweight molecular probe is available.")

    if request.runtime_mode == "cached_only":
        return _cached_or_failed(candidate, cache, live_allowed, cached_allowed)

    if request.runtime_mode in {"auto", "live_if_supported"} and request.allow_live_probe and live_allowed and not live_probe_used:
        try:
            result = _run_live_probe(candidate)
            _persist_live_probe(candidate, result, cache, cache_path)
            return result
        except Exception as exc:
            cached_entry = cache.get(candidate.formula)
            if cached_allowed and request.allow_cached_reference and cached_entry:
                result = _build_cached_result(candidate, cached_entry)
                result.provenance_details.append(f"Live probe failed with {exc.__class__.__name__}; cached reference shown instead.")
                result.scientific_caveats.append("Live probe failed; cached molecule-specific reference shown instead.")
                return result
            return _failed_result(
                candidate,
                live_allowed=live_allowed,
                cached_allowed=cached_allowed,
                reason="solver_error",
                message=f"Live molecular probe failed: {exc.__class__.__name__}.",
                attempted=True,
            )

    if cached_allowed and request.allow_cached_reference:
        return _cached_or_failed(candidate, cache, live_allowed, cached_allowed)

    return _unsupported_result(candidate, live_allowed, cached_allowed, "live_not_permitted", "Probe policy does not allow a result for this molecule.")


def _cached_or_failed(
    candidate: QuantumCandidateInput,
    cache: dict,
    live_allowed: bool,
    cached_allowed: bool,
) -> MolecularProbeResult:
    cached_entry = cache.get(candidate.formula)
    if cached_entry and cached_allowed:
        return _build_cached_result(candidate, cached_entry)
    return _failed_result(
        candidate,
        live_allowed=live_allowed,
        cached_allowed=cached_allowed,
        reason="cache_missing",
        message="No cached molecular probe reference is available for this molecule.",
        attempted=False,
    )


def _unsupported_result(
    candidate: QuantumCandidateInput,
    live_allowed: bool,
    cached_allowed: bool,
    reason: str,
    message: str,
) -> MolecularProbeResult:
    return MolecularProbeResult(
        molecule_name=candidate.name,
        formula=candidate.formula,
        probe_status="unsupported",
        probe_model="none",
        live_calculation_attempted=False,
        live_calculation_allowed=live_allowed,
        cached_reference_allowed=cached_allowed,
        provenance_label="unsupported",
        provenance_details=["This molecule is outside the supported lightweight molecular probe set."],
        educational_note="No molecular quantum probe is provided for this molecule in the current simulator.",
        scientific_caveats=[
            "Molecular probe support is intentionally limited to avoid misleading electronic-structure claims.",
            "Unsupported molecules do not receive substitute proxy scores.",
        ],
        failure_reason=reason,
        failure_message=message,
    )


def _failed_result(
    candidate: QuantumCandidateInput,
    live_allowed: bool,
    cached_allowed: bool,
    reason: str,
    message: str,
    attempted: bool,
) -> MolecularProbeResult:
    return MolecularProbeResult(
        molecule_name=candidate.name,
        formula=candidate.formula,
        probe_status="failed",
        probe_model="none",
        live_calculation_attempted=attempted,
        live_calculation_allowed=live_allowed,
        cached_reference_allowed=cached_allowed,
        provenance_label="probe_failed",
        provenance_details=[message],
        educational_note="The molecular probe is optional and does not influence atmospheric interpretation.",
        scientific_caveats=[
            "No fallback electronic score is fabricated when the molecular probe fails.",
            "Atmospheric inference and spectrum synthesis remain independent of the molecular probe.",
        ],
        failure_reason=reason,
        failure_message=message,
    )


def _build_cached_result(candidate: QuantumCandidateInput, cached_entry: dict) -> MolecularProbeResult:
    metadata = cached_entry.get("metadata", {})
    method_label = metadata.get("method", "offline_reference")
    return MolecularProbeResult(
        molecule_name=candidate.name,
        formula=candidate.formula,
        probe_status="cached_reference",
        probe_model="offline_reference",
        live_calculation_attempted=False,
        live_calculation_allowed=candidate.formula in LIVE_ALLOWED_FORMULAS,
        cached_reference_allowed=True,
        geometry_reference=metadata.get("geometry_reference", "internal_fixed_geometry_v1"),
        method_label=method_label,
        basis_label=metadata.get("basis_label", "offline_reference"),
        electronic_energy_proxy=float(cached_entry.get("electronic_energy_proxy", cached_entry.get("ground_state_energy_proxy"))),
        reference_energy_proxy=float(cached_entry.get("reference_energy_proxy", cached_entry.get("classical_reference_energy_proxy", cached_entry.get("ground_state_energy_proxy")))),
        probe_agreement=float(cached_entry.get("probe_agreement", cached_entry.get("baseline_agreement_score", 0.84))),
        provenance_label="cached_reference",
        provenance_details=[
            cached_entry.get("notes", "Loaded from local molecular probe cache."),
            f"Method: {method_label}.",
        ],
        educational_note="This cached molecular probe is a same-molecule electronic-structure reference, not an atmospheric stability metric.",
        scientific_caveats=[
            "Cached molecular probe values are molecule-specific and setup-specific.",
            "Molecular probe results are not used in abundance scoring, regime classification, or spectral amplitude.",
        ],
        failure_reason=None,
        failure_message=None,
    )


def _run_live_probe(candidate: QuantumCandidateInput) -> MolecularProbeResult:
    if candidate.formula not in LIVE_ALLOWED_FORMULAS:
        raise ValueError("Live probe not permitted for this molecule.")

    config = PROXY_HAMILTONIANS[candidate.formula]
    try:
        from qiskit import QuantumCircuit, transpile
        from qiskit.quantum_info import SparsePauliOp
        from qiskit_aer import AerSimulator
        from qiskit_algorithms.minimum_eigensolvers import NumPyMinimumEigensolver
    except Exception as exc:
        raise RuntimeError("Qiskit stack unavailable in the current environment.") from exc

    operator = SparsePauliOp.from_list(config["paulis"])
    exact_solver = NumPyMinimumEigensolver()
    reference_energy = float(exact_solver.compute_minimum_eigenvalue(operator).eigenvalue.real + config["offset"])

    circuit = QuantumCircuit(2)
    circuit.ry(config["theta"], 0)
    circuit.cx(0, 1)
    circuit.save_statevector()

    simulator = AerSimulator(method="statevector")
    compiled = transpile(circuit, simulator)
    result = simulator.run(compiled, shots=1).result()
    statevector = result.get_statevector(compiled)
    electronic_energy = float(statevector.expectation_value(operator).real + config["offset"])

    probe_agreement = _compute_probe_agreement(abs(reference_energy - electronic_energy), reference_energy)
    return MolecularProbeResult(
        molecule_name=candidate.name,
        formula=candidate.formula,
        probe_status="live",
        probe_model="toy_hamiltonian",
        live_calculation_attempted=True,
        live_calculation_allowed=True,
        cached_reference_allowed=True,
        geometry_reference="internal_fixed_geometry_v1",
        method_label="qiskit_toy_hamiltonian_statevector",
        basis_label="reduced_two_qubit_proxy",
        electronic_energy_proxy=round(electronic_energy, 6),
        reference_energy_proxy=round(reference_energy, 6),
        probe_agreement=probe_agreement,
        provenance_label="live_probe",
        provenance_details=[
            "Live molecular probe completed with a reduced 2-qubit educational Hamiltonian.",
            "A same-molecule classical reference was computed with NumPyMinimumEigensolver.",
        ],
        educational_note="This live molecular probe illustrates a molecule-specific reduced electronic-structure calculation.",
        scientific_caveats=[
            "The reported energy proxy applies only to this molecule within this internal probe setup.",
            "The molecular probe is not cross-species comparable and is not used for atmospheric inference or spectral weighting.",
        ],
        failure_reason=None,
        failure_message=None,
    )


def _compute_probe_agreement(delta: float, reference_energy: float) -> float:
    relative_delta = delta / max(abs(reference_energy), 0.75)
    agreement = 1.0 - min(relative_delta, 1.0) * 0.45
    return round(max(0.55, min(1.0, agreement)), 3)


def _pick_selected_result(results: list[MolecularProbeResult], selected_formula: str | None) -> MolecularProbeResult | None:
    if not results:
        return None
    if selected_formula is None:
        return results[0]
    selected_lower = selected_formula.lower()
    for result in results:
        if result.formula.lower() == selected_lower or result.molecule_name.lower() == selected_lower:
            return result
    return results[0]


def _persist_live_probe(candidate: QuantumCandidateInput, result: MolecularProbeResult, cache: dict, cache_path: Path) -> None:
    cache[candidate.formula] = {
        "name": candidate.name,
        "formula": candidate.formula,
        "electronic_energy_proxy": result.electronic_energy_proxy,
        "reference_energy_proxy": result.reference_energy_proxy,
        "probe_agreement": result.probe_agreement,
        "notes": "Stored after local live molecular probe.",
        "metadata": {
            "method": result.method_label,
            "basis_label": result.basis_label,
            "geometry_reference": result.geometry_reference,
        },
    }
    _save_probe_cache(cache_path, cache)


def _load_probe_cache(cache_path: Path) -> dict:
    if not cache_path.exists():
        return {}
    try:
        return json.loads(cache_path.read_text())
    except json.JSONDecodeError:
        return {}


def _save_probe_cache(cache_path: Path, cache: dict) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, indent=2, sort_keys=True))


def build_molecular_probe_request(
    candidates: list[QuantumCandidateInput],
    runtime_mode: str = "auto",
    selected_formula: str | None = None,
) -> MolecularProbeRequest:
    return MolecularProbeRequest(
        candidates=candidates,
        runtime_mode=runtime_mode,
        selected_formula=selected_formula,
        selection_reason="chemistry_shortlist",
    )
