from app.models.simulation import SimulationRunRequest
from app.services.simulation_service import run_simulation_pipeline


def test_simulation_pipeline_returns_shared_state() -> None:
    response = run_simulation_pipeline(
        SimulationRunRequest(
            generation_mode="manual",
            quantum_runtime_mode="cached_only",
            planet_name="Pipeline-1",
            star_type="K-type",
            orbit_zone="temperate",
            radius_rearth=1.1,
            mass_mearth=1.4,
            gravity_ms2=10.4,
            equilibrium_temperature_k=292.0,
            radiation_level=0.95,
            atmosphere={
                "pressure_bar": 1.1,
                "temperature_k": 295.0,
                "gas_fractions": {"N2": 0.7, "O2": 0.18, "H2O": 0.08, "CO2": 0.03, "Ar": 0.01},
            },
        )
    )

    assert response.state.planet_name == response.profile.planet_name
    assert response.state.star_type == response.profile.star_type
    assert response.state.reference_pressure_bar == response.profile.atmosphere.pressure_bar
    assert response.state.mean_molecular_weight >= 2.0
    assert response.scientific_proxy_profile.mean_molecular_weight_proxy == response.state.mean_molecular_weight
    assert response.molecular_probe is not None
