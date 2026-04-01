STAR_STATE_RULES = {
    "M-type": {"stellar_radius_rsun": 0.42, "uv_activity": "high", "insolation_factor": 0.72},
    "K-type": {"stellar_radius_rsun": 0.78, "uv_activity": "moderate", "insolation_factor": 0.94},
    "G-type": {"stellar_radius_rsun": 1.0, "uv_activity": "moderate", "insolation_factor": 1.08},
}

ORBIT_ZONE_INSOLATION = {
    "cold": 0.38,
    "temperate": 1.0,
    "hot": 2.45,
}

ORBIT_ZONE_ALBEDO = {
    "cold": 0.42,
    "temperate": 0.3,
    "hot": 0.18,
}

PRESSURE_CLASS_THRESHOLDS = {
    "thin_max_bar": 0.3,
    "dense_min_bar": 5.0,
}

MIXING_CLASS_THRESHOLDS = {
    "low_gravity_ms2": 8.0,
    "high_hydrogen_inventory": 0.35,
    "high_pressure_bar": 3.5,
}

ATMOSPHERE_FAMILY_THRESHOLDS = {
    "h2_rich_inventory": 0.45,
    "volatile_rich_inventory": 0.18,
    "volatile_rich_radius_rearth": 1.6,
}

METALLICITY_DEFAULTS = {
    "secondary_terrestrial": 0.1,
    "volatile_rich": 0.35,
    "h2_rich": 0.0,
}

CO_RATIO_DEFAULTS = {
    "secondary_terrestrial": 0.55,
    "volatile_rich": 0.75,
    "h2_rich": 0.85,
}

ATMOSPHERE_FAMILY_TEMPLATES = {
    "secondary_terrestrial": {"N2": 0.72, "O2": 0.18, "CO2": 0.06, "H2O": 0.02, "Ar": 0.02},
    "volatile_rich": {"N2": 0.36, "CO2": 0.18, "H2O": 0.16, "CH4": 0.1, "H2": 0.1, "Ar": 0.1},
    "h2_rich": {"H2": 0.54, "He": 0.22, "H2O": 0.08, "CH4": 0.07, "CO2": 0.05, "N2": 0.04},
}
