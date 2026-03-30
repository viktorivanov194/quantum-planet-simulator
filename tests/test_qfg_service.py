from app.models.planet import AtmosphericProfile, PlanetProfile
from app.models.qfg import QFGSimulationConfig
from app.services.qfg_service import run_qfg_field_simulation


def _sample_profile() -> PlanetProfile:
    return PlanetProfile(
        planet_name="Test World",
        star_type="K-type",
        orbit_zone="temperate",
        generation_mode="preset",
        radius_rearth=1.2,
        mass_mearth=1.4,
        gravity_ms2=10.4,
        equilibrium_temperature_k=305.0,
        radiation_level=1.3,
        atmosphere=AtmosphericProfile(
            gas_fractions={"N2": 0.72, "O2": 0.18, "H2O": 0.08, "CO2": 0.02},
            dominant_gases=["N2", "O2", "H2O"],
            pressure_bar=1.4,
            temperature_k=308.0,
        ),
        notes=[],
    )


def test_qfg_simulation_returns_observables_and_scores() -> None:
    result = run_qfg_field_simulation(QFGSimulationConfig(enabled=True), profile=_sample_profile())

    assert result is not None
    assert len(result.observables) > 3
    assert 0.0 <= result.stability_score <= 1.0
    assert 0.0 <= result.coherence_score <= 1.0
    assert result.density_peak >= result.density_mean >= 0.0
    assert isinstance(result.resonance_detected, bool)


def test_qfg_simulation_can_be_disabled() -> None:
    result = run_qfg_field_simulation(QFGSimulationConfig(enabled=False), profile=_sample_profile())
    assert result is None
