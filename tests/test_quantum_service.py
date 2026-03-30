import json
from pathlib import Path

from app.models.chemistry import QuantumCandidateInput
from app.models.quantum import QuantumEvaluationRequest
from app.services import quantum_service


def test_cached_lookup_success(tmp_path: Path) -> None:
    cache_path = tmp_path / "quantum_cache.json"
    cache_path.write_text(
        json.dumps(
            {
                "CO2": {
                    "ground_state_energy_proxy": -1.66,
                    "stability_score": 0.87,
                    "confidence_score": 0.86,
                    "notes": "cached result",
                    "metadata": {"method": "test_cache"},
                }
            }
        )
    )
    request = QuantumEvaluationRequest(
        candidates=[_candidate("Carbon Dioxide", "CO2")],
        runtime_mode="cached_only",
        cache_path=str(cache_path),
    )

    response = quantum_service.evaluate_candidates(request)

    assert response.results[0].source == "cached"
    assert response.results[0].formula == "CO2"
    assert response.results[0].verification_mode == "cached_reference_proxy"
    assert response.results[0].baseline_agreement_score is not None
    assert response.selected_result is not None


def test_missing_cache_returns_fallback(tmp_path: Path) -> None:
    request = QuantumEvaluationRequest(
        candidates=[_candidate("Ammonia", "NH3")],
        runtime_mode="cached_only",
        cache_path=str(tmp_path / "missing.json"),
    )

    response = quantum_service.evaluate_candidates(request)

    assert response.results[0].source == "fallback"
    assert "No cache entry found" in response.results[0].notes[0]
    assert response.results[0].verification_mode == "fallback_proxy_only"


def test_demo_balanced_mode_uses_live_path(monkeypatch, tmp_path: Path) -> None:
    candidate = _candidate("Hydrogen", "H2")

    def fake_live_eval(input_candidate: QuantumCandidateInput):
        return quantum_service.QuantumEvaluationResult(
            name=input_candidate.name,
            formula=input_candidate.formula,
            ground_state_energy_proxy=-1.111,
            stability_score=0.91,
            source="live",
            notes=["mock live"],
            confidence_score=0.9,
        )

    monkeypatch.setattr(quantum_service, "_run_live_proxy_evaluation", fake_live_eval)
    request = QuantumEvaluationRequest(
        candidates=[candidate],
        runtime_mode="demo_balanced",
        cache_path=str(tmp_path / "demo.json"),
    )

    response = quantum_service.evaluate_candidates(request)

    assert response.results[0].source == "live"
    assert response.live_evaluation_used is True
    assert response.results[0].verification_mode == "live_quantum_proxy_vs_classical_exact"


def test_unsupported_molecule_handling() -> None:
    request = QuantumEvaluationRequest(
        candidates=[_candidate("Argon", "Ar")],
        runtime_mode="cached_only",
    )

    response = quantum_service.evaluate_candidates(request)

    assert response.results[0].source == "fallback"
    assert response.results[0].formula == "Ar"
    assert "supported MVP quantum set" in response.results[0].notes[0]


def test_stable_response_shape(tmp_path: Path) -> None:
    cache_path = tmp_path / "quantum_cache.json"
    cache_path.write_text(
        json.dumps(
            {
                "H2O": {
                    "ground_state_energy_proxy": -1.58,
                    "stability_score": 0.83,
                    "confidence_score": 0.85,
                    "notes": "cached result",
                    "metadata": {"method": "test_cache"},
                }
            }
        )
    )
    request = QuantumEvaluationRequest(
        candidates=[_candidate("Water Vapor", "H2O")],
        runtime_mode="cached_only",
        cache_path=str(cache_path),
    )

    response = quantum_service.evaluate_candidates(request)
    result = response.results[0]

    assert hasattr(result, "name")
    assert hasattr(result, "formula")
    assert hasattr(result, "ground_state_energy_proxy")
    assert hasattr(result, "stability_score")
    assert hasattr(result, "source")
    assert hasattr(result, "notes")
    assert hasattr(result, "confidence_score")
    assert hasattr(result, "classical_reference_energy_proxy")
    assert hasattr(result, "baseline_agreement_score")
    assert hasattr(result, "verification_mode")


def _candidate(name: str, formula: str) -> QuantumCandidateInput:
    return QuantumCandidateInput(
        name=name,
        formula=formula,
        classical_score=0.75,
        tag="allowed",
        rationale="test candidate",
        chemistry_modes=["temperate"],
    )
