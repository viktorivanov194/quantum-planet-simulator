from pathlib import Path


SUPPORTED_FORMULAS = {"H2", "O2", "N2", "CO2", "CH4", "NH3", "H2O", "CO", "HCN", "SO2"}
LIVE_SUPPORTED_FORMULAS = {"H2", "H2O"}
DEFAULT_RUNTIME_MODE = "demo_balanced"
DEFAULT_CACHE_PATH = Path("data/cache/quantum_results.json")

PROXY_HAMILTONIANS = {
    "H2": {
        "offset": -1.05,
        "theta": 0.62,
        "symbols": ["H", "H"],
        "paulis": [("ZI", -0.82), ("IZ", -0.82), ("ZZ", 0.18), ("XX", 0.12)],
    },
    "H2O": {
        "offset": -1.78,
        "theta": 0.91,
        "symbols": ["O", "H", "H"],
        "paulis": [("ZI", -0.94), ("IZ", -0.68), ("ZZ", 0.22), ("XX", 0.08)],
    },
}

FALLBACK_RESULTS = {
    "H2": {"energy": -1.05, "stability": 0.81},
    "O2": {"energy": -1.32, "stability": 0.76},
    "N2": {"energy": -1.48, "stability": 0.84},
    "CO2": {"energy": -1.66, "stability": 0.87},
    "CH4": {"energy": -1.21, "stability": 0.7},
    "NH3": {"energy": -1.09, "stability": 0.66},
    "H2O": {"energy": -1.58, "stability": 0.83},
    "CO": {"energy": -1.29, "stability": 0.79},
    "HCN": {"energy": -1.18, "stability": 0.61},
    "SO2": {"energy": -1.42, "stability": 0.73},
}
