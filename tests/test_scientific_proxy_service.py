from app.models.chemistry import CandidateResponse, MoleculeCandidate
from app.models.planet import AtmosphericProfile, PlanetProfile, ValidationIssue, ValidationResult
from app.models.quantum import QuantumEvaluationResult
from app.services.scientific_proxy_service import build_scientific_proxy_profile


def test_clear_atmosphere_maps_to_strong_feature_mode() -> None:
    profile = _profile(
        pressure_bar=1.05,
        temperature_k=294.0,
        gas_fractions={"N2": 0.66, "O2": 0.16, "H2O": 0.1, "CO2": 0.06, "Ar": 0.02},
        radiation_level=0.9,
    )
    scientific = build_scientific_proxy_profile(
        profile=profile,
        validation=ValidationResult(is_valid=True, score=0.94, issues=[]),
        chemistry=_chemistry(["oxidizing", "temperate"]),
        quantum=_quantum(confidence_score=0.85),
    )

    assert scientific.atmospheric_clarity_mode == "clear"
    assert scientific.observation_confidence_mode == "strong-feature"


def test_hazy_case_becomes_ambiguous_or_null_signal() -> None:
    profile = _profile(
        pressure_bar=8.2,
        temperature_k=420.0,
        gas_fractions={"CO2": 0.36, "CH4": 0.18, "H2O": 0.16, "N2": 0.2, "Ar": 0.1},
        radiation_level=2.8,
    )
    scientific = build_scientific_proxy_profile(
        profile=profile,
        validation=ValidationResult(
            is_valid=True,
            score=0.74,
            issues=[ValidationIssue(code="pressure_high_warning", message="Dense atmosphere warning.", severity="warning")],
        ),
        chemistry=_chemistry(["dense atmosphere", "high-radiation", "carbon-rich"]),
        quantum=_quantum(confidence_score=0.52),
    )

    assert scientific.atmospheric_clarity_mode in {"cloud-muted", "feature-flat"}
    assert scientific.observation_confidence_mode in {"ambiguous", "null-signal", "weak-feature"}
    assert scientific.observation_risk_notes


def _profile(
    pressure_bar: float,
    temperature_k: float,
    gas_fractions: dict[str, float],
    radiation_level: float,
) -> PlanetProfile:
    return PlanetProfile(
        planet_name="Science-1",
        star_type="K-type",
        orbit_zone="temperate",
        generation_mode="manual",
        radius_rearth=1.2,
        mass_mearth=1.5,
        gravity_ms2=10.3,
        equilibrium_temperature_k=temperature_k - 6.0,
        radiation_level=radiation_level,
        atmosphere=AtmosphericProfile(
            gas_fractions=gas_fractions,
            dominant_gases=sorted(gas_fractions, key=gas_fractions.get, reverse=True),
            pressure_bar=pressure_bar,
            temperature_k=temperature_k,
        ),
    )


def _chemistry(modes: list[str]) -> CandidateResponse:
    return CandidateResponse(
        candidates=[
            MoleculeCandidate(
                name="Water Vapor",
                formula="H2O",
                classical_score=0.83,
                rationale="Test rationale",
                tag="allowed",
            )
        ],
        selected_for_quantum=[],
        chemistry_mode_summary=", ".join(modes),
        chemistry_modes=modes,
    )


def _quantum(confidence_score: float) -> QuantumEvaluationResult:
    return QuantumEvaluationResult(
        name="Water Vapor",
        formula="H2O",
        ground_state_energy_proxy=-1.58,
        stability_score=0.82,
        source="cached",
        notes=["cached"],
        confidence_score=confidence_score,
        classical_reference_energy_proxy=-1.58,
        baseline_agreement_score=0.84,
        verification_mode="cached_reference_proxy",
    )
