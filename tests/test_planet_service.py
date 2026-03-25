from app.models.planet import AtmosphericProfile, AtmosphericProfileInput, PlanetGenerationRequest, PlanetProfile
from app.services.planet_service import generate_planet_profile, validate_planet_profile


def test_random_plausible_generation_is_deterministic() -> None:
    request = PlanetGenerationRequest(generation_mode="random", star_type="K-type", orbit_zone="temperate", seed=42)

    first = generate_planet_profile(request)
    second = generate_planet_profile(request)

    assert first == second
    assert first.generation_mode == "random"
    assert 0.5 <= first.radius_rearth <= 2.5
    assert 1.0 <= first.gravity_ms2 <= 35.0
    assert abs(sum(first.atmosphere.gas_fractions.values()) - 1.0) < 0.01


def test_manual_generation_prefers_user_values() -> None:
    request = PlanetGenerationRequest(
        generation_mode="manual",
        star_type="G-type",
        orbit_zone="temperate",
        planet_name="Manual-1",
        radius_rearth=1.25,
        mass_mearth=1.9,
        gravity_ms2=11.9,
        equilibrium_temperature_k=301.0,
        radiation_level=1.2,
        atmosphere=AtmosphericProfileInput(
            pressure_bar=1.3,
            temperature_k=304.0,
            gas_fractions={"N2": 0.7, "O2": 0.2, "CO2": 0.1},
        ),
    )

    profile = generate_planet_profile(request)

    assert profile.planet_name == "Manual-1"
    assert profile.radius_rearth == 1.25
    assert profile.mass_mearth == 1.9
    assert profile.gravity_ms2 == 11.9
    assert profile.equilibrium_temperature_k == 301.0
    assert profile.radiation_level == 1.2
    assert profile.atmosphere.pressure_bar == 1.3
    assert profile.atmosphere.temperature_k == 304.0
    assert profile.atmosphere.gas_fractions == {"N2": 0.7, "O2": 0.2, "CO2": 0.1}


def test_validation_success_case() -> None:
    profile = PlanetProfile(
        planet_name="Stable-1",
        star_type="K-type",
        orbit_zone="temperate",
        generation_mode="manual",
        radius_rearth=1.1,
        mass_mearth=1.3,
        gravity_ms2=10.5,
        equilibrium_temperature_k=288.0,
        radiation_level=0.9,
        atmosphere=AtmosphericProfile(
            pressure_bar=1.0,
            temperature_k=290.0,
            gas_fractions={"N2": 0.75, "O2": 0.2, "CO2": 0.03, "Ar": 0.02},
            dominant_gases=["N2", "O2", "CO2", "Ar"],
        ),
    )

    result = validate_planet_profile(profile)

    assert result.is_valid is True
    assert result.issues == []
    assert result.score == 1.0


def test_validation_warning_case() -> None:
    profile = PlanetProfile(
        planet_name="Warn-1",
        star_type="M-type",
        orbit_zone="hot",
        generation_mode="manual",
        radius_rearth=1.0,
        mass_mearth=1.0,
        gravity_ms2=9.81,
        equilibrium_temperature_k=430.0,
        radiation_level=3.4,
        atmosphere=AtmosphericProfile(
            pressure_bar=0.06,
            temperature_k=390.0,
            gas_fractions={"CO2": 0.71, "N2": 0.2, "Ar": 0.07},
            dominant_gases=["CO2", "N2", "Ar"],
        ),
    )

    result = validate_planet_profile(profile)

    assert result.is_valid is True
    assert any(issue.severity == "warning" for issue in result.issues)
    assert any(issue.code == "pressure_low_warning" for issue in result.issues)
    assert any(issue.code == "radiation_high_warning" for issue in result.issues)


def test_validation_failure_case() -> None:
    profile = PlanetProfile(
        planet_name="Fail-1",
        star_type="G-type",
        orbit_zone="temperate",
        generation_mode="manual",
        radius_rearth=1.2,
        mass_mearth=1.4,
        gravity_ms2=40.0,
        equilibrium_temperature_k=295.0,
        radiation_level=1.0,
        atmosphere=AtmosphericProfile(
            pressure_bar=1.0,
            temperature_k=300.0,
            gas_fractions={"N2": 0.6, "O2": 0.2, "CO2": 0.1},
            dominant_gases=["N2", "O2", "CO2"],
        ),
    )

    result = validate_planet_profile(profile)

    assert result.is_valid is False
    assert any(issue.severity == "error" for issue in result.issues)
    assert any(issue.code == "atmosphere_fraction_sum_error" for issue in result.issues)
    assert any(issue.code == "gravity_ms2" for issue in result.issues)
