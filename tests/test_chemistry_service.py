from app.models.chemistry import CandidateRequest
from app.models.planet import AtmosphericProfile, PlanetProfile, ValidationIssue, ValidationResult
from app.models.state import PlanetAtmosphereState
from app.services.chemistry_service import get_candidate_molecules


def test_oxidizing_atmosphere_case() -> None:
    profile = PlanetProfile(
        planet_name="Ox-1",
        star_type="G-type",
        orbit_zone="temperate",
        generation_mode="manual",
        radius_rearth=1.0,
        mass_mearth=1.0,
        gravity_ms2=9.8,
        equilibrium_temperature_k=290.0,
        radiation_level=0.9,
        atmosphere=AtmosphericProfile(
            gas_fractions={"N2": 0.68, "O2": 0.24, "CO2": 0.05, "Ar": 0.03},
            dominant_gases=["N2", "O2", "CO2", "Ar"],
            pressure_bar=1.0,
            temperature_k=292.0,
        ),
    )

    result = get_candidate_molecules(
        CandidateRequest(profile=profile, validation=ValidationResult(is_valid=True, score=1.0, issues=[]))
    )

    formulas = [candidate.formula for candidate in result.candidates]
    assert "oxidizing" in result.chemistry_modes
    assert formulas[0] in {"O2", "CO2", "H2O", "N2"}
    assert any(candidate.formula == "O2" and candidate.tag == "allowed" for candidate in result.candidates)
    assert result.abundance_proxies["O2"] > result.abundance_proxies["CH4"]


def test_reducing_methane_friendly_case() -> None:
    profile = PlanetProfile(
        planet_name="Red-1",
        star_type="M-type",
        orbit_zone="cold",
        generation_mode="manual",
        radius_rearth=1.2,
        mass_mearth=1.6,
        gravity_ms2=10.9,
        equilibrium_temperature_k=210.0,
        radiation_level=1.1,
        atmosphere=AtmosphericProfile(
            gas_fractions={"N2": 0.55, "CH4": 0.2, "H2": 0.15, "NH3": 0.1},
            dominant_gases=["N2", "CH4", "H2", "NH3"],
            pressure_bar=1.4,
            temperature_k=205.0,
        ),
    )

    result = get_candidate_molecules(
        CandidateRequest(profile=profile, validation=ValidationResult(is_valid=True, score=0.9, issues=[]))
    )

    assert "reducing" in result.chemistry_modes
    assert result.candidates[0].formula in {"CH4", "N2", "H2", "NH3"}
    assert any(candidate.formula == "CH4" and candidate.tag == "allowed" for candidate in result.candidates)
    assert result.abundance_proxies["CH4"] > 0.0


def test_hot_thin_atmosphere_case() -> None:
    profile = PlanetProfile(
        planet_name="HotThin-1",
        star_type="M-type",
        orbit_zone="hot",
        generation_mode="manual",
        radius_rearth=0.9,
        mass_mearth=0.8,
        gravity_ms2=7.2,
        equilibrium_temperature_k=470.0,
        radiation_level=3.2,
        atmosphere=AtmosphericProfile(
            gas_fractions={"CO2": 0.62, "CO": 0.18, "N2": 0.12, "SO2": 0.08},
            dominant_gases=["CO2", "CO", "N2", "SO2"],
            pressure_bar=0.09,
            temperature_k=490.0,
        ),
    )
    validation = ValidationResult(
        is_valid=True,
        score=0.72,
        issues=[
            ValidationIssue(code="pressure_low_warning", message="thin", severity="warning"),
            ValidationIssue(code="radiation_high_warning", message="rad", severity="warning"),
            ValidationIssue(code="hot_thin_atmosphere_warning", message="combo", severity="warning"),
        ],
    )

    result = get_candidate_molecules(CandidateRequest(profile=profile, validation=validation))

    assert "hot atmosphere" in result.chemistry_modes
    assert "thin atmosphere" in result.chemistry_modes
    assert result.candidates[0].formula in {"CO2", "CO", "SO2"}


def test_high_radiation_warning_influence() -> None:
    profile = PlanetProfile(
        planet_name="Rad-1",
        star_type="M-type",
        orbit_zone="temperate",
        generation_mode="manual",
        radius_rearth=1.0,
        mass_mearth=1.0,
        gravity_ms2=9.8,
        equilibrium_temperature_k=300.0,
        radiation_level=3.8,
        atmosphere=AtmosphericProfile(
            gas_fractions={"N2": 0.6, "CH4": 0.18, "CO2": 0.12, "H2": 0.1},
            dominant_gases=["N2", "CH4", "CO2", "H2"],
            pressure_bar=0.25,
            temperature_k=310.0,
        ),
    )
    validation = ValidationResult(
        is_valid=True,
        score=0.8,
        issues=[ValidationIssue(code="radiation_high_warning", message="rad", severity="warning")],
    )

    result = get_candidate_molecules(CandidateRequest(profile=profile, validation=validation))
    methane = next(candidate for candidate in result.candidates if candidate.formula == "CH4")
    carbon_dioxide = next(candidate for candidate in result.candidates if candidate.formula == "CO2")

    assert "high-radiation" in result.chemistry_modes
    assert methane.classical_score < carbon_dioxide.classical_score


def test_shortlist_selection_case() -> None:
    profile = PlanetProfile(
        planet_name="Short-1",
        star_type="K-type",
        orbit_zone="temperate",
        generation_mode="manual",
        radius_rearth=1.1,
        mass_mearth=1.3,
        gravity_ms2=10.2,
        equilibrium_temperature_k=289.0,
        radiation_level=1.0,
        atmosphere=AtmosphericProfile(
            gas_fractions={"N2": 0.7, "O2": 0.15, "H2O": 0.1, "CO2": 0.05},
            dominant_gases=["N2", "O2", "H2O", "CO2"],
            pressure_bar=1.1,
            temperature_k=291.0,
        ),
    )

    result = get_candidate_molecules(
        CandidateRequest(profile=profile, validation=ValidationResult(is_valid=True, score=0.95, issues=[]))
    )

    assert 2 <= len(result.selected_for_quantum) <= 3
    assert all(candidate.formula in {"H2O", "CH4", "CO2", "NH3", "HCN", "CO", "SO2", "O2", "N2", "H2"} for candidate in result.selected_for_quantum)
    assert all(hasattr(candidate, "chemistry_modes") for candidate in result.selected_for_quantum)
    assert all(not hasattr(candidate, "cached") for candidate in result.selected_for_quantum)
    assert result.abundance_proxies


def test_state_regime_drives_chemistry_modes() -> None:
    profile = PlanetProfile(
        planet_name="Reg-1",
        star_type="K-type",
        orbit_zone="temperate",
        generation_mode="manual",
        radius_rearth=2.0,
        mass_mearth=6.0,
        gravity_ms2=14.5,
        equilibrium_temperature_k=330.0,
        radiation_level=1.3,
        atmosphere=AtmosphericProfile(
            gas_fractions={"H2": 0.48, "He": 0.22, "H2O": 0.1, "CH4": 0.08, "CO2": 0.06, "N2": 0.06},
            dominant_gases=["H2", "He", "H2O", "CH4", "CO2", "N2"],
            pressure_bar=4.4,
            temperature_k=346.0,
        ),
    )
    state = PlanetAtmosphereState(
        planet_name="Reg-1",
        star_type="K-type",
        stellar_radius_rsun=0.78,
        insolation_proxy=1.45,
        uv_activity="moderate",
        radius_rearth=2.0,
        mass_mearth=6.0,
        gravity_ms2=14.5,
        bond_albedo_proxy=0.28,
        equilibrium_temperature_k=330.0,
        atmospheric_temperature_k=346.0,
        reference_pressure_bar=4.4,
        pressure_class="dense",
        atmosphere_family="h2_rich",
        primary_atmospheric_regime="h2_rich_mini_neptune",
        secondary_regime_modifiers=["cloud_muted"],
        metallicity_proxy=0.12,
        carbon_to_oxygen_ratio=0.92,
        hydrogen_inventory_proxy=0.6,
        oxidation_reduction_proxy=-0.35,
        mean_molecular_weight=8.6,
        scale_height_km=28.0,
        cloud_haze_opacity_proxy=0.52,
        escape_susceptibility_proxy=0.34,
        vertical_mixing_class="high",
        quench_strength_proxy=0.78,
        notes=[],
    )

    result = get_candidate_molecules(
        CandidateRequest(profile=profile, state=state, validation=ValidationResult(is_valid=True, score=0.92, issues=[]))
    )

    assert "reducing" in result.chemistry_modes
    assert "dense atmosphere" in result.chemistry_modes
    assert result.abundance_proxies["H2"] > result.abundance_proxies["O2"]
    assert any(candidate.mixing_ratio_proxy >= 0.05 for candidate in result.candidates)


def test_hot_regime_boosts_co_and_co2_over_methane() -> None:
    profile = PlanetProfile(
        planet_name="HotReg-1",
        star_type="G-type",
        orbit_zone="hot",
        generation_mode="manual",
        radius_rearth=1.3,
        mass_mearth=2.1,
        gravity_ms2=12.2,
        equilibrium_temperature_k=470.0,
        radiation_level=2.8,
        atmosphere=AtmosphericProfile(
            gas_fractions={"CO2": 0.58, "CO": 0.16, "N2": 0.14, "SO2": 0.08, "H2O": 0.04},
            dominant_gases=["CO2", "CO", "N2", "SO2", "H2O"],
            pressure_bar=2.2,
            temperature_k=492.0,
        ),
    )
    state = PlanetAtmosphereState(
        planet_name="HotReg-1",
        star_type="G-type",
        stellar_radius_rsun=1.0,
        insolation_proxy=2.6,
        uv_activity="moderate",
        radius_rearth=1.3,
        mass_mearth=2.1,
        gravity_ms2=12.2,
        bond_albedo_proxy=0.18,
        equilibrium_temperature_k=470.0,
        atmospheric_temperature_k=492.0,
        reference_pressure_bar=2.2,
        pressure_class="moderate",
        atmosphere_family="volatile_rich",
        primary_atmospheric_regime="hot_co2_co_atmosphere",
        secondary_regime_modifiers=[],
        metallicity_proxy=0.42,
        carbon_to_oxygen_ratio=0.95,
        hydrogen_inventory_proxy=0.06,
        oxidation_reduction_proxy=0.18,
        mean_molecular_weight=35.0,
        scale_height_km=11.0,
        cloud_haze_opacity_proxy=0.18,
        escape_susceptibility_proxy=0.22,
        vertical_mixing_class="moderate",
        quench_strength_proxy=0.48,
        notes=[],
    )

    result = get_candidate_molecules(
        CandidateRequest(profile=profile, state=state, validation=ValidationResult(is_valid=True, score=0.9, issues=[]))
    )

    assert result.abundance_proxies["CO2"] > result.abundance_proxies["CH4"]
    assert result.abundance_proxies["CO"] > result.abundance_proxies["CH4"]
    assert result.candidates[0].formula in {"CO2", "CO", "SO2"}
