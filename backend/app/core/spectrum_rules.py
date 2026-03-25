WAVELENGTH_GRID = [round(0.6 + 0.05 * index, 2) for index in range(31)]

MOLECULE_SIGNATURES = {
    "H2": {
        "label": "H2 scattering feature",
        "bands": [{"center": 0.8, "width": 0.12, "strength": 0.03}, {"center": 1.6, "width": 0.18, "strength": 0.035}],
    },
    "O2": {
        "label": "O2 absorption band",
        "bands": [{"center": 0.76, "width": 0.05, "strength": 0.08}, {"center": 1.27, "width": 0.07, "strength": 0.06}],
    },
    "N2": {
        "label": "N2 continuum support",
        "bands": [{"center": 1.05, "width": 0.2, "strength": 0.025}],
    },
    "CO2": {
        "label": "CO2 dominant feature",
        "bands": [{"center": 1.4, "width": 0.09, "strength": 0.16}, {"center": 1.6, "width": 0.08, "strength": 0.14}],
    },
    "CH4": {
        "label": "CH4 candidate signature",
        "bands": [{"center": 1.15, "width": 0.08, "strength": 0.11}, {"center": 1.65, "width": 0.07, "strength": 0.13}],
    },
    "NH3": {
        "label": "NH3 candidate signature",
        "bands": [{"center": 1.05, "width": 0.06, "strength": 0.09}, {"center": 1.5, "width": 0.09, "strength": 0.08}],
    },
    "H2O": {
        "label": "H2O absorption band",
        "bands": [{"center": 0.94, "width": 0.06, "strength": 0.1}, {"center": 1.4, "width": 0.08, "strength": 0.18}],
    },
    "CO": {
        "label": "CO candidate signature",
        "bands": [{"center": 1.57, "width": 0.06, "strength": 0.09}],
    },
    "HCN": {
        "label": "HCN candidate signature",
        "bands": [{"center": 1.54, "width": 0.06, "strength": 0.1}],
    },
    "SO2": {
        "label": "SO2 dominant feature",
        "bands": [{"center": 0.72, "width": 0.05, "strength": 0.08}, {"center": 1.33, "width": 0.08, "strength": 0.11}],
    },
}

SPECTRUM_MODE_ADJUSTMENTS = {
    "hot atmosphere": {"amplitude": 1.08, "baseline": -0.006},
    "cold atmosphere": {"amplitude": 0.94, "baseline": 0.004},
    "thin atmosphere": {"amplitude": 0.82, "baseline": 0.008},
    "dense atmosphere": {"amplitude": 1.12, "baseline": -0.01},
    "high-radiation": {"amplitude": 0.9, "baseline": 0.003},
    "oxidizing": {"amplitude": 1.03, "baseline": 0.0},
    "reducing": {"amplitude": 1.04, "baseline": -0.002},
}
