ALLOWED_MOLECULES = {
    "H2": {"name": "Hydrogen", "base_score": 0.32},
    "O2": {"name": "Oxygen", "base_score": 0.34},
    "N2": {"name": "Nitrogen", "base_score": 0.36},
    "CO2": {"name": "Carbon Dioxide", "base_score": 0.38},
    "CH4": {"name": "Methane", "base_score": 0.3},
    "NH3": {"name": "Ammonia", "base_score": 0.24},
    "H2O": {"name": "Water Vapor", "base_score": 0.37},
    "HCN": {"name": "Hydrogen Cyanide", "base_score": 0.14},
    "CO": {"name": "Carbon Monoxide", "base_score": 0.22},
    "SO2": {"name": "Sulfur Dioxide", "base_score": 0.2},
}

MODE_THRESHOLDS = {
    "oxidizing_o2_fraction": 0.12,
    "reducing_fraction": 0.08,
    "carbon_rich_fraction": 0.35,
    "nitrogen_rich_fraction": 0.45,
    "hot_temperature_k": 380.0,
    "cold_temperature_k": 220.0,
    "thin_pressure_bar": 0.2,
    "dense_pressure_bar": 5.0,
    "high_radiation": 3.0,
}

QUANTUM_PRIORITY = ["H2O", "CH4", "CO2", "NH3", "HCN", "CO", "SO2", "O2", "N2", "H2"]
