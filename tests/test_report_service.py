from app.models.chemistry import CandidateResponse, MoleculeCandidate, QuantumCandidateInput
from app.models.planet import AtmosphericProfile, PlanetProfile, ValidationResult
from app.models.quantum import QuantumEvaluationResult
from app.models.spectrum import SpectrumMetadata, SpectrumResponse
from app.services.report_service import build_final_report


def test_build_final_report_shape() -> None:
    report = build_final_report(
        profile=_profile(),
        validation=ValidationResult(is_valid=True, score=0.88, issues=[]),
        chemistry=_chemistry(),
        selected_candidate=_selected_candidate(),
        quantum=_quantum(),
        spectrum=_spectrum(),
    )

    assert report.title
    assert report.discovery_headline
    assert report.key_highlights
    assert 0.0 <= report.confidence_score <= 1.0


def _profile() -> PlanetProfile:
    return PlanetProfile(
        planet_name="Report-1",
        star_type="K-type",
        orbit_zone="temperate",
        generation_mode="manual",
        radius_rearth=1.1,
        mass_mearth=1.3,
        gravity_ms2=10.2,
        equilibrium_temperature_k=290.0,
        radiation_level=0.9,
        atmosphere=AtmosphericProfile(
            gas_fractions={"N2": 0.7, "H2O": 0.12, "CO2": 0.1, "O2": 0.08},
            dominant_gases=["N2", "H2O", "CO2", "O2"],
            pressure_bar=1.05,
            temperature_k=293.0,
        ),
    )


def _chemistry() -> CandidateResponse:
    return CandidateResponse(
        candidates=[
            MoleculeCandidate(
                name="Water Vapor",
                formula="H2O",
                classical_score=0.84,
                rationale="Strong oxidizing signature.",
                tag="allowed",
            ),
            MoleculeCandidate(
                name="Carbon Dioxide",
                formula="CO2",
                classical_score=0.8,
                rationale="Carbon baseline candidate.",
                tag="allowed",
            ),
        ],
        selected_for_quantum=[_selected_candidate()],
        chemistry_mode_summary="oxidizing, temperate",
        chemistry_modes=["oxidizing", "temperate"],
    )


def _selected_candidate() -> QuantumCandidateInput:
    return QuantumCandidateInput(
        name="Water Vapor",
        formula="H2O",
        classical_score=0.84,
        tag="allowed",
        rationale="Strong oxidizing signature.",
        chemistry_modes=["oxidizing", "temperate"],
    )


def _quantum() -> QuantumEvaluationResult:
    return QuantumEvaluationResult(
        name="Water Vapor",
        formula="H2O",
        ground_state_energy_proxy=-1.58,
        stability_score=0.83,
        source="cached",
        notes=["cached demo result"],
        confidence_score=0.85,
    )


def _spectrum() -> SpectrumResponse:
    return SpectrumResponse(
        wavelengths=[0.6, 0.65],
        absorption_values=[0.03, 0.04],
        dominant_molecules=["H2O", "CO2"],
        summary_text="Synthetic transmission spectrum emphasizes H2O.",
        metadata=SpectrumMetadata(
            dominant_molecules=["H2O", "CO2"],
            summary_text="Synthetic transmission spectrum emphasizes H2O.",
            confidence_score=0.9,
            selected_formula="H2O",
        ),
    )
