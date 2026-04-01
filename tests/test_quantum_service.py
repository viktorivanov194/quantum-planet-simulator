import json
from pathlib import Path

from app.models.chemistry import QuantumCandidateInput
from app.models.molecular_probe import MolecularProbeRequest
from app.services import molecular_probe_service


def test_cached_lookup_success(tmp_path: Path) -> None:
    cache_path = tmp_path / "probe_cache.json"
    cache_path.write_text(
        json.dumps(
            {
                "CO2": {
                    "electronic_energy_proxy": -1.66,
                    "reference_energy_proxy": -1.66,
                    "probe_agreement": 0.86,
                    "notes": "cached result",
                    "metadata": {"method": "test_cache"},
                }
            }
        )
    )
    request = MolecularProbeRequest(
        candidates=[_candidate("Carbon Dioxide", "CO2")],
        runtime_mode="cached_only",
        cache_path=str(cache_path),
        selection_reason="test",
    )

    response = molecular_probe_service.run_molecular_probe(request)

    assert response.results[0].probe_status == "cached_reference"
    assert response.results[0].formula == "CO2"
    assert response.results[0].probe_agreement is not None
    assert response.selected_result is not None


def test_missing_cache_returns_fallback(tmp_path: Path) -> None:
    request = MolecularProbeRequest(
        candidates=[_candidate("Ammonia", "NH3")],
        runtime_mode="cached_only",
        cache_path=str(tmp_path / "missing.json"),
        selection_reason="test",
    )

    response = molecular_probe_service.run_molecular_probe(request)

    assert response.results[0].probe_status == "failed"
    assert response.results[0].failure_reason == "cache_missing"


def test_live_probe_uses_live_path(monkeypatch, tmp_path: Path) -> None:
    candidate = _candidate("Hydrogen", "H2")

    def fake_live_eval(input_candidate: QuantumCandidateInput):
        from app.models.molecular_probe import MolecularProbeResult

        return MolecularProbeResult(
            molecule_name=input_candidate.name,
            formula=input_candidate.formula,
            probe_status="live",
            probe_model="toy_hamiltonian",
            live_calculation_attempted=True,
            live_calculation_allowed=True,
            cached_reference_allowed=True,
            electronic_energy_proxy=-1.111,
            reference_energy_proxy=-1.111,
            probe_agreement=0.9,
            provenance_label="live_probe",
            provenance_details=["mock live"],
            educational_note="test",
            scientific_caveats=["test"],
        )

    monkeypatch.setattr(molecular_probe_service, "_run_live_probe", fake_live_eval)
    request = MolecularProbeRequest(
        candidates=[candidate],
        runtime_mode="auto",
        cache_path=str(tmp_path / "demo.json"),
        selection_reason="test",
    )

    response = molecular_probe_service.run_molecular_probe(request)

    assert response.results[0].probe_status == "live"
    assert response.live_probe_used is True


def test_unsupported_molecule_handling() -> None:
    request = MolecularProbeRequest(
        candidates=[_candidate("Argon", "Ar")],
        runtime_mode="cached_only",
        selection_reason="test",
    )

    response = molecular_probe_service.run_molecular_probe(request)

    assert response.results[0].probe_status == "unsupported"
    assert response.results[0].formula == "Ar"
    assert response.results[0].failure_reason == "molecule_unsupported"


def test_stable_response_shape(tmp_path: Path) -> None:
    cache_path = tmp_path / "probe_cache.json"
    cache_path.write_text(
        json.dumps(
            {
                "H2O": {
                    "electronic_energy_proxy": -1.58,
                    "reference_energy_proxy": -1.58,
                    "probe_agreement": 0.85,
                    "notes": "cached result",
                    "metadata": {"method": "test_cache"},
                }
            }
        )
    )
    request = MolecularProbeRequest(
        candidates=[_candidate("Water Vapor", "H2O")],
        runtime_mode="cached_only",
        cache_path=str(cache_path),
        selection_reason="test",
    )

    response = molecular_probe_service.run_molecular_probe(request)
    result = response.results[0]

    assert hasattr(result, "molecule_name")
    assert hasattr(result, "formula")
    assert hasattr(result, "electronic_energy_proxy")
    assert hasattr(result, "probe_agreement")
    assert hasattr(result, "probe_status")
    assert result.cross_species_comparable is False
    assert result.atmospheric_inference_allowed is False
    assert result.spectrum_influence_allowed is False


def test_solver_failure_falls_back_to_cached(monkeypatch, tmp_path: Path) -> None:
    cache_path = tmp_path / "probe_cache.json"
    cache_path.write_text(
        json.dumps(
            {
                "H2O": {
                    "electronic_energy_proxy": -1.58,
                    "reference_energy_proxy": -1.58,
                    "probe_agreement": 0.84,
                    "notes": "cached result",
                    "metadata": {"method": "test_cache"},
                }
            }
        )
    )

    def fail_live(_: QuantumCandidateInput):
        raise RuntimeError("boom")

    monkeypatch.setattr(molecular_probe_service, "_run_live_probe", fail_live)
    response = molecular_probe_service.run_molecular_probe(
        MolecularProbeRequest(
            candidates=[_candidate("Water Vapor", "H2O")],
            runtime_mode="auto",
            cache_path=str(cache_path),
            selection_reason="test",
        )
    )

    assert response.results[0].probe_status == "cached_reference"
    assert any("Live probe failed" in note or "cached reference shown instead" in note for note in response.results[0].scientific_caveats + response.results[0].provenance_details)


def _candidate(name: str, formula: str) -> QuantumCandidateInput:
    return QuantumCandidateInput(
        name=name,
        formula=formula,
        classical_score=0.75,
        tag="allowed",
        rationale="test candidate",
        chemistry_modes=["temperate"],
    )
