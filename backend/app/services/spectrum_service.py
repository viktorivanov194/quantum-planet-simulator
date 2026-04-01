from __future__ import annotations

import math

from app.core.spectrum_rules import MOLECULE_SIGNATURES, SPECTRUM_MODE_ADJUSTMENTS, WAVELENGTH_GRID
from app.models.chemistry import QuantumCandidateInput
from app.models.quantum import QuantumEvaluationResult
from app.models.scientific import ScientificProxyProfile
from app.models.spectrum import SpectrumFeature, SpectrumMetadata, SpectrumPoint, SpectrumRequest, SpectrumResponse


def generate_synthetic_spectrum(request: SpectrumRequest) -> SpectrumResponse:
    chemistry_modes = request.chemistry_modes or _infer_modes_from_candidates(request.chemistry_candidates)
    dominant_molecules = _collect_dominant_molecules(request)
    amplitude_scale, baseline_shift = _mode_scalars(chemistry_modes)
    amplitude_scale, baseline_shift = _apply_clarity_scalars(
        amplitude_scale,
        baseline_shift,
        request.scientific_profile.atmospheric_clarity_mode if request.scientific_profile else "clear",
        request.scientific_profile.spectral_visibility_score if request.scientific_profile else 0.5,
    )
    geometry_factor = _geometry_factor(request)
    cloud_suppression = _cloud_suppression_factor(request)
    observation = _observation_proxies(request, geometry_factor)
    absorption_values = []
    for wavelength in WAVELENGTH_GRID:
        absorption = 0.02 + baseline_shift
        for molecule in dominant_molecules:
            abundance = _molecule_abundance(request, molecule)
            intrinsic = _molecule_absorption(
                molecule=molecule,
                wavelength=wavelength,
                abundance=abundance,
                amplitude_scale=amplitude_scale,
                geometry_factor=geometry_factor,
                cloud_suppression=cloud_suppression,
            )
            absorption += _observed_feature_amplitude(intrinsic, observation, molecule)
        absorption += _instrument_effect(
            wavelength=wavelength,
            radiation_level=request.profile.radiation_level,
            pressure_bar=request.profile.atmosphere.pressure_bar,
            observation=observation,
        )
        absorption_values.append(round(max(0.0, min(absorption, 0.95)), 4))

    absorption_values = _flatten_if_needed(
        absorption_values=absorption_values,
        atmospheric_clarity_mode=request.scientific_profile.atmospheric_clarity_mode if request.scientific_profile else "clear",
        observation_confidence_mode=request.scientific_profile.observation_confidence_mode if request.scientific_profile else "strong-feature",
    )

    points = [
        SpectrumPoint(wavelength_um=wavelength, absorption=absorption)
        for wavelength, absorption in zip(WAVELENGTH_GRID, absorption_values)
    ]
    features = _extract_features(
        dominant_molecules=dominant_molecules,
        quantum_result=request.quantum_result,
        request=request,
        amplitude_scale=amplitude_scale,
        geometry_factor=geometry_factor,
        cloud_suppression=cloud_suppression,
        observation=observation,
    )
    features = _limit_features_for_observation_mode(
        features,
        request.scientific_profile.observation_confidence_mode if request.scientific_profile else "strong-feature",
    )
    confidence_score = _spectrum_confidence(dominant_molecules, request.scientific_profile, observation)
    summary_text = _build_summary(
        dominant_molecules,
        request.quantum_result,
        chemistry_modes,
        confidence_score,
        request.scientific_profile.atmospheric_clarity_mode if request.scientific_profile else "clear",
        request.scientific_profile.observation_confidence_mode if request.scientific_profile else "strong-feature",
        observation,
    )

    metadata = SpectrumMetadata(
        dominant_molecules=dominant_molecules,
        summary_text=summary_text,
        confidence_score=confidence_score,
        generator="geometry_aware_transmission_proxy",
        selected_formula=request.quantum_result.formula if request.quantum_result else None,
        atmospheric_clarity_mode=request.scientific_profile.atmospheric_clarity_mode if request.scientific_profile else "clear",
        observation_confidence_mode=request.scientific_profile.observation_confidence_mode if request.scientific_profile else "strong-feature",
        spectral_resolution_proxy=round(observation["spectral_resolution_proxy"], 1),
        signal_to_noise_proxy=round(observation["signal_to_noise_proxy"], 2),
        noise_floor_proxy=round(observation["noise_floor_proxy"], 5),
        stellar_variability_proxy=round(observation["stellar_variability_proxy"], 4),
    )

    return SpectrumResponse(
        wavelengths=WAVELENGTH_GRID,
        absorption_values=absorption_values,
        points=points,
        highlighted_features=features,
        dominant_molecules=dominant_molecules,
        summary_text=summary_text,
        metadata=metadata,
    )


def _collect_dominant_molecules(request: SpectrumRequest) -> list[str]:
    dominant = [gas for gas in request.profile.atmosphere.dominant_gases if gas in MOLECULE_SIGNATURES]
    if request.quantum_result and request.quantum_result.formula in MOLECULE_SIGNATURES and request.quantum_result.formula not in dominant:
        dominant.insert(0, request.quantum_result.formula)
    for candidate in request.chemistry_candidates:
        if candidate.formula in MOLECULE_SIGNATURES and candidate.formula not in dominant and len(dominant) < 4:
            dominant.append(candidate.formula)
    return dominant[:4] or ["N2"]


def _mode_scalars(chemistry_modes: list[str]) -> tuple[float, float]:
    amplitude = 1.0
    baseline = 0.0
    for mode in chemistry_modes:
        adjustment = SPECTRUM_MODE_ADJUSTMENTS.get(mode)
        if adjustment:
            amplitude *= adjustment["amplitude"]
            baseline += adjustment["baseline"]
    return amplitude, baseline


def _apply_clarity_scalars(
    amplitude_scale: float,
    baseline_shift: float,
    atmospheric_clarity_mode: str,
    spectral_visibility_score: float,
) -> tuple[float, float]:
    if atmospheric_clarity_mode == "feature-flat":
        return amplitude_scale * 0.55, baseline_shift - 0.002
    if atmospheric_clarity_mode == "cloud-muted":
        return amplitude_scale * 0.72, baseline_shift - 0.001
    if atmospheric_clarity_mode == "hazy":
        return amplitude_scale * 0.88, baseline_shift
    return amplitude_scale * (0.96 + spectral_visibility_score * 0.12), baseline_shift


def _cloud_suppression_factor(request: SpectrumRequest) -> float:
    if request.state is not None:
        tau_cloud = request.state.tau_cloud
    elif request.scientific_profile is not None:
        # Compatibility path until the whole pipeline consumes tau_cloud directly.
        tau_cloud = request.scientific_profile.cloud_haze_factor
    else:
        tau_cloud = 0.0
    return max(0.2, min(1.0 / (1.0 + tau_cloud), 1.0))


def _geometry_factor(request: SpectrumRequest) -> float:
    if request.state is None:
        return 0.25
    rp_rsun = request.state.radius_rearth * 0.0091577
    scale_height_rsun = request.state.scale_height_km / 695700.0
    raw = (2.0 * rp_rsun * scale_height_rsun) / max(request.state.stellar_radius_rsun**2, 0.05)
    return max(0.02, min(raw * 400000.0, 1.8))


def _observation_proxies(request: SpectrumRequest, geometry_factor: float) -> dict[str, float]:
    if request.state is not None:
        star_type = request.state.star_type
        uv_activity = request.state.uv_activity
    else:
        star_type = request.profile.star_type
        uv_activity = "moderate"
    stellar_variability = _stellar_variability_proxy(star_type, uv_activity)
    spectral_resolution = {"M-type": 70.0, "K-type": 85.0, "G-type": 100.0}.get(star_type, 80.0)
    signal_to_noise = max(3.5, min(8.0 + 6.0 * geometry_factor - 5.0 * stellar_variability, 24.0))
    noise_floor = max(0.0012, min(0.0065, 0.0055 - 0.00012 * signal_to_noise + 0.006 * stellar_variability))
    return {
        "spectral_resolution_proxy": spectral_resolution,
        "signal_to_noise_proxy": signal_to_noise,
        "noise_floor_proxy": noise_floor,
        "stellar_variability_proxy": stellar_variability,
    }


def _stellar_variability_proxy(star_type: str, uv_activity: str) -> float:
    base = {"M-type": 0.11, "K-type": 0.055, "G-type": 0.035}.get(star_type, 0.05)
    uv_factor = {"low": 0.8, "moderate": 1.0, "high": 1.35}[uv_activity]
    return max(0.01, min(base * uv_factor, 0.25))


def _molecule_abundance(request: SpectrumRequest, molecule: str) -> float:
    if request.abundance_proxies:
        return request.abundance_proxies.get(molecule, request.profile.atmosphere.gas_fractions.get(molecule, 0.01))
    return request.profile.atmosphere.gas_fractions.get(molecule, 0.01)


def _molecule_absorption(
    molecule: str,
    wavelength: float,
    abundance: float,
    amplitude_scale: float,
    geometry_factor: float,
    cloud_suppression: float,
) -> float:
    signature = MOLECULE_SIGNATURES.get(molecule)
    if not signature:
        return 0.0

    total = 0.0
    for band in signature["bands"]:
        gaussian = math.exp(-((wavelength - band["center"]) ** 2) / max(2 * (band["width"] ** 2), 1e-6))
        total += band["strength"] * gaussian

    molecule_weight = math.pow(max(abundance, 1e-5), 0.55)
    return total * molecule_weight * amplitude_scale * geometry_factor * cloud_suppression


def _observed_feature_amplitude(
    intrinsic_amplitude: float,
    observation: dict[str, float],
    molecule: str,
) -> float:
    signature = MOLECULE_SIGNATURES.get(molecule, {})
    sharpness = max((band["strength"] / max(band["width"], 0.03)) for band in signature.get("bands", [{"strength": 0.05, "width": 0.1}]))
    band_resolution_proxy = 45.0 + sharpness * 22.0
    resolution_factor = math.sqrt(
        observation["spectral_resolution_proxy"] / (observation["spectral_resolution_proxy"] + band_resolution_proxy)
    )
    stellar_factor = 1.0 / (1.0 + observation["stellar_variability_proxy"] / 0.08)
    snr_factor = 1.0 - math.exp(-observation["signal_to_noise_proxy"] / 8.0)
    return intrinsic_amplitude * resolution_factor * stellar_factor * snr_factor


def _instrument_effect(wavelength: float, radiation_level: float, pressure_bar: float, observation: dict[str, float]) -> float:
    ripple = 0.004 * math.sin(wavelength * 12.0)
    pressure_smoothing = min(0.02, pressure_bar * 0.0015)
    radiation_noise = min(0.01, radiation_level * 0.0012)
    noise_floor = observation["noise_floor_proxy"]
    variability_noise = observation["stellar_variability_proxy"] * 0.01 * math.cos(wavelength * 5.0)
    return ripple * 0.6 + pressure_smoothing + radiation_noise + noise_floor + variability_noise


def _flatten_if_needed(
    absorption_values: list[float],
    atmospheric_clarity_mode: str,
    observation_confidence_mode: str,
) -> list[float]:
    if atmospheric_clarity_mode not in {"feature-flat", "cloud-muted"} and observation_confidence_mode not in {"ambiguous", "null-signal"}:
        return absorption_values

    mean_absorption = sum(absorption_values) / max(len(absorption_values), 1)
    if observation_confidence_mode == "null-signal":
        flatten_strength = 0.72
    elif atmospheric_clarity_mode == "feature-flat":
        flatten_strength = 0.58
    else:
        flatten_strength = 0.34

    return [
        round((value * (1.0 - flatten_strength)) + (mean_absorption * flatten_strength), 4)
        for value in absorption_values
    ]


def _extract_features(
    dominant_molecules: list[str],
    quantum_result: QuantumEvaluationResult | None,
    request: SpectrumRequest,
    amplitude_scale: float,
    geometry_factor: float,
    cloud_suppression: float,
    observation: dict[str, float],
) -> list[SpectrumFeature]:
    feature_molecules: list[str] = []
    if quantum_result and quantum_result.formula in MOLECULE_SIGNATURES:
        feature_molecules.append(quantum_result.formula)
    for molecule in dominant_molecules:
        if molecule not in feature_molecules:
            feature_molecules.append(molecule)

    features: list[SpectrumFeature] = []
    for molecule in feature_molecules[:3]:
        signature = MOLECULE_SIGNATURES.get(molecule)
        if not signature:
            continue
        strongest_band = max(signature["bands"], key=lambda band: band["strength"])
        abundance = _molecule_abundance(request, molecule)
        intrinsic_strength = (
            strongest_band["strength"]
            * math.pow(max(abundance, 1e-5), 0.55)
            * amplitude_scale
            * geometry_factor
            * cloud_suppression
        )
        strength = _observed_feature_amplitude(intrinsic_strength, observation, molecule) / max(observation["noise_floor_proxy"], 1e-4)
        features.append(
            SpectrumFeature(
                wavelength_um=strongest_band["center"],
                label=signature["label"],
                molecule=molecule,
                strength=round(min(strength, 1.0), 3),
            )
        )
    return features


def _limit_features_for_observation_mode(
    features: list[SpectrumFeature],
    observation_confidence_mode: str,
) -> list[SpectrumFeature]:
    if observation_confidence_mode == "null-signal":
        return features[:1]
    if observation_confidence_mode == "ambiguous":
        return features[:2]
    return features


def _spectrum_confidence(dominant_molecules: list[str], scientific_profile: ScientificProxyProfile | None, observation: dict[str, float]) -> float:
    base = 0.62 + min(len(dominant_molecules), 4) * 0.04
    if scientific_profile is not None:
        base += scientific_profile.spectral_visibility_score * 0.08
        if scientific_profile.observation_confidence_mode == "ambiguous":
            base -= 0.1
        if scientific_profile.observation_confidence_mode == "null-signal":
            base -= 0.2
    base += (1.0 - math.exp(-observation["signal_to_noise_proxy"] / 10.0)) * 0.08
    base -= observation["stellar_variability_proxy"] * 0.15
    base -= observation["noise_floor_proxy"] * 8.0
    return round(max(0.0, min(base, 0.96)), 3)


def _build_summary(
    dominant_molecules: list[str],
    quantum_result: QuantumEvaluationResult | None,
    chemistry_modes: list[str],
    confidence_score: float,
    atmospheric_clarity_mode: str,
    observation_confidence_mode: str,
    observation: dict[str, float],
) -> str:
    selected_formula = quantum_result.formula if quantum_result else dominant_molecules[0]
    modes_text = ", ".join(chemistry_modes[:2]) if chemistry_modes else "balanced atmosphere"
    dominant_text = ", ".join(dominant_molecules[:3])
    observation_text = observation_confidence_mode.replace("-", " ")
    return (
        f"Synthetic transmission spectrum emphasizes {selected_formula} within a {modes_text} context. "
        f"Atmospheric clarity is {atmospheric_clarity_mode}, with a {observation_text} observational posture. "
        f"Dominant visible contributors: {dominant_text}. "
        f"Resolution {observation['spectral_resolution_proxy']:.0f}, SNR {observation['signal_to_noise_proxy']:.1f}, confidence {confidence_score:.2f}."
    )


def _infer_modes_from_candidates(candidates: list[QuantumCandidateInput]) -> list[str]:
    modes: list[str] = []
    for candidate in candidates:
        for mode in candidate.chemistry_modes:
            if mode not in modes:
                modes.append(mode)
    return modes
