from app.models.planet import AtmosphericProfile, PlanetProfile
from app.services.state_service import build_planet_atmosphere_state


def test_state_backbone_builds_for_temperate_world() -> None:
    state = build_planet_atmosphere_state(_temperate_profile())

    assert state.star_type == "K-type"
    assert state.stellar_radius_rsun > 0.0
    assert state.insolation_proxy > 0.0
    assert state.atmosphere_family == "secondary_terrestrial"
    assert state.pressure_class == "moderate"
    assert state.primary_atmospheric_regime == "oxidized_terrestrial"
    assert 2.0 <= state.mean_molecular_weight <= 100.0
    assert state.scale_height_km > 0.0
    assert state.tau_cloud >= 0.0


def test_hydrogen_rich_world_maps_to_h2_rich_family() -> None:
    profile = PlanetProfile(
        planet_name="State-H2",
        star_type="K-type",
        orbit_zone="temperate",
        generation_mode="manual",
        radius_rearth=2.0,
        mass_mearth=6.0,
        gravity_ms2=14.7,
        equilibrium_temperature_k=330.0,
        radiation_level=1.2,
        atmosphere=AtmosphericProfile(
            gas_fractions={"H2": 0.5, "He": 0.2, "H2O": 0.1, "CH4": 0.1, "N2": 0.1},
            dominant_gases=["H2", "He", "H2O", "CH4", "N2"],
            pressure_bar=4.0,
            temperature_k=345.0,
        ),
    )

    state = build_planet_atmosphere_state(profile)

    assert state.atmosphere_family == "h2_rich"
    assert state.vertical_mixing_class in {"moderate", "high"}
    assert state.hydrogen_inventory_proxy > 0.45


def test_scale_height_reacts_to_temperature_and_gravity() -> None:
    cool_dense = build_planet_atmosphere_state(_temperate_profile())
    hot_low_gravity = build_planet_atmosphere_state(
        PlanetProfile(
            planet_name="State-Hot",
            star_type="G-type",
            orbit_zone="hot",
            generation_mode="manual",
            radius_rearth=1.6,
            mass_mearth=1.9,
            gravity_ms2=7.3,
            equilibrium_temperature_k=470.0,
            radiation_level=2.4,
            atmosphere=AtmosphericProfile(
                gas_fractions={"CO2": 0.45, "N2": 0.25, "H2O": 0.15, "H2": 0.1, "CO": 0.05},
                dominant_gases=["CO2", "N2", "H2O", "H2", "CO"],
                pressure_bar=1.3,
                temperature_k=490.0,
            ),
        )
    )

    assert hot_low_gravity.scale_height_km > cool_dense.scale_height_km


def _temperate_profile() -> PlanetProfile:
    return PlanetProfile(
        planet_name="State-1",
        star_type="K-type",
        orbit_zone="temperate",
        generation_mode="manual",
        radius_rearth=1.1,
        mass_mearth=1.3,
        gravity_ms2=10.2,
        equilibrium_temperature_k=290.0,
        radiation_level=0.9,
        atmosphere=AtmosphericProfile(
            gas_fractions={"N2": 0.71, "O2": 0.19, "H2O": 0.06, "CO2": 0.03, "Ar": 0.01},
            dominant_gases=["N2", "O2", "H2O", "CO2", "Ar"],
            pressure_bar=1.05,
            temperature_k=293.0,
        ),
    )
