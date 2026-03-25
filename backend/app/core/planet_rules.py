PLANET_RULES = {
    "star_types": {
        "M-type": {"temperature_offset_k": -35.0, "radiation_base": 1.4},
        "K-type": {"temperature_offset_k": -10.0, "radiation_base": 0.9},
        "G-type": {"temperature_offset_k": 10.0, "radiation_base": 1.0},
    },
    "orbit_zones": {
        "cold": {"temperature_base_k": 210.0, "radiation_multiplier": 0.6},
        "temperate": {"temperature_base_k": 285.0, "radiation_multiplier": 1.0},
        "hot": {"temperature_base_k": 420.0, "radiation_multiplier": 1.8},
    },
    "ranges": {
        "radius_rearth": (0.5, 2.5),
        "mass_mearth": (0.1, 12.0),
        "gravity_ms2": (1.0, 35.0),
        "equilibrium_temperature_k": (80.0, 900.0),
        "atmospheric_temperature_k": (80.0, 900.0),
        "pressure_bar": (0.01, 100.0),
        "radiation_level": (0.0, 10.0),
    },
    "warning_thresholds": {
        "temperature_low_k": 140.0,
        "temperature_high_k": 700.0,
        "pressure_low_bar": 0.08,
        "pressure_high_bar": 20.0,
        "gravity_low_ms2": 3.0,
        "gravity_high_ms2": 25.0,
        "radiation_high": 3.0,
        "gas_fraction_sum_warning_delta": 0.02,
        "gas_fraction_sum_error_delta": 0.05,
    },
    "atmosphere_templates": {
        "cold": {"N2": 0.80, "CO2": 0.15, "Ar": 0.05},
        "temperate": {"N2": 0.74, "O2": 0.20, "CO2": 0.04, "Ar": 0.02},
        "hot": {"CO2": 0.72, "N2": 0.20, "SO2": 0.08},
    },
}

PLANET_PRESETS = {
    "temperate_rocky": {
        "star_type": "K-type",
        "orbit_zone": "temperate",
        "radius_rearth": 1.1,
        "mass_mearth": 1.4,
        "equilibrium_temperature_k": 292.0,
        "radiation_level": 0.9,
        "atmosphere": {
            "pressure_bar": 1.1,
            "temperature_k": 295.0,
            "gas_fractions": {"N2": 0.73, "O2": 0.21, "CO2": 0.04, "Ar": 0.02},
        },
    },
    "hot_dense": {
        "star_type": "G-type",
        "orbit_zone": "hot",
        "radius_rearth": 1.6,
        "mass_mearth": 3.2,
        "equilibrium_temperature_k": 465.0,
        "radiation_level": 2.7,
        "atmosphere": {
            "pressure_bar": 12.0,
            "temperature_k": 510.0,
            "gas_fractions": {"CO2": 0.75, "N2": 0.17, "SO2": 0.08},
        },
    },
}
