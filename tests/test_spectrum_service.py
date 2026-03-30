from app.models.chemistry import QuantumCandidateInput
from app.models.planet import AtmosphericProfile, PlanetProfile
from app.models.quantum import QuantumEvaluationResult
from app.models.scientific import ScientificProxyProfile
from app.models.spectrum import SpectrumRequest
from app.services.spectrum_service import generate_synthetic_spectrum


def test_spectrum_generation_shape() -> None:
    response = generate_synthetic_spectrum(_request())

    assert len(response.wavelengths) == len(response.absorption_values)
    assert len(response.points) == len(response.wavelengths)
    assert response.summary_text


def test_molecule_signature_inclusion() -> None:
    response = generate_synthetic_spectrum(_request())

    assert any(feature.molecule == "H2O" for feature in response.highlighted_features)
    assert "H2O" in response.dominant_molecules


def test_selected_quantum_result_influence() -> None:
    water_response = generate_synthetic_spectrum(_request(selected_formula="H2O"))
    methane_response = generate_synthetic_spectrum(_request(selected_formula="CH4"))

    water_peak = max(
        point.absorption for point in water_response.points if 1.35 <= point.wavelength_um <= 1.45
    )
    methane_peak = max(
        point.absorption for point in methane_response.points if 1.35 <= point.wavelength_um <= 1.45
    )

    assert water_peak > methane_peak


def test_unsupported_molecule_graceful_handling() -> None:
    response = generate_synthetic_spectrum(_request(selected_formula="Ar"))

    assert response.wavelengths
    assert response.metadata.selected_formula == "Ar"


def test_stable_response_structure() -> None:
    response = generate_synthetic_spectrum(_request())

    assert hasattr(response, "highlighted_features")
    assert hasattr(response, "dominant_molecules")
    assert hasattr(response, "metadata")
    assert response.metadata.generator == "synthetic_signature_blend"
    assert response.metadata.atmospheric_clarity_mode == "clear"


def test_feature_flat_mode_reduces_peak_contrast() -> None:
    clear_response = generate_synthetic_spectrum(_request())
    flat_response = generate_synthetic_spectrum(_request(clarity_mode="feature-flat", observation_mode="null-signal"))

    clear_span = max(clear_response.absorption_values) - min(clear_response.absorption_values)
    flat_span = max(flat_response.absorption_values) - min(flat_response.absorption_values)

    assert flat_span < clear_span


def _request(
    selected_formula: str = "H2O",
    clarity_mode: str = "clear",
    observation_mode: str = "strong-feature",
) -> SpectrumRequest:
    return SpectrumRequest(
        profile=PlanetProfile(
            planet_name="Spec-1",
            star_type="K-type",
            orbit_zone="temperate",
            generation_mode="manual",
            radius_rearth=1.1,
            mass_mearth=1.3,
            gravity_ms2=10.1,
            equilibrium_temperature_k=292.0,
            radiation_level=1.0,
            atmosphere=AtmosphericProfile(
                gas_fractions={"N2": 0.68, "H2O": 0.12, "CO2": 0.1, "CH4": 0.1},
                dominant_gases=["N2", "H2O", "CO2", "CH4"],
                pressure_bar=1.1,
                temperature_k=295.0,
            ),
        ),
        chemistry_modes=["oxidizing", "temperate"],
        quantum_result=QuantumEvaluationResult(
            name="Selected Candidate",
            formula=selected_formula,
            ground_state_energy_proxy=-1.58,
            stability_score=0.84,
            source="cached",
            notes=["test"],
            confidence_score=0.85,
        ),
        chemistry_candidates=[
            QuantumCandidateInput(
                name="Water Vapor",
                formula="H2O",
                classical_score=0.84,
                tag="allowed",
                rationale="Strong water feature",
                chemistry_modes=["oxidizing"],
            ),
            QuantumCandidateInput(
                name="Carbon Dioxide",
                formula="CO2",
                classical_score=0.8,
                tag="allowed",
                rationale="Strong carbon feature",
                chemistry_modes=["oxidizing"],
            ),
        ],
        scientific_profile=ScientificProxyProfile(
            mean_molecular_weight_proxy=24.5,
            scale_height_proxy=1.05,
            cloud_haze_factor=0.18 if clarity_mode == "clear" else 0.78,
            oxidation_index_proxy=0.42,
            carbon_richness_proxy=0.22,
            nitrogen_richness_proxy=0.68,
            spectral_visibility_score=0.82 if observation_mode == "strong-feature" else 0.2,
            atmospheric_clarity_mode=clarity_mode,
            observation_confidence_mode=observation_mode,
            observation_risk_notes=[],
            scientific_disclaimers=[],
        ),
    )
