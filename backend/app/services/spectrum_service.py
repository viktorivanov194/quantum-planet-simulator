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
    quantum_boost = _quantum_influence(request.quantum_result)

    absorption_values = []
    for wavelength in WAVELENGTH_GRID:
        absorption = 0.02 + baseline_shift
        for molecule in dominant_molecules:
            fraction = request.profile.atmosphere.gas_fractions.get(molecule, 0.02)
            absorption += _molecule_absorption(molecule, wavelength, fraction, amplitude_scale, quantum_boost, request.quantum_result)
        absorption += _instrument_effect(wavelength, request.profile.radiation_level, request.profile.atmosphere.pressure_bar)
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
    features = _extract_features(dominant_molecules, request.quantum_result, request.profile.atmosphere.gas_fractions, amplitude_scale)
    features = _limit_features_for_observation_mode(
        features,
        request.scientific_profile.observation_confidence_mode if request.scientific_profile else "strong-feature",
    )
    confidence_score = _spectrum_confidence(request.quantum_result, dominant_molecules, request.scientific_profile)
    summary_text = _build_summary(
        dominant_molecules,
        request.quantum_result,
        chemistry_modes,
        confidence_score,
        request.scientific_profile.atmospheric_clarity_mode if request.scientific_profile else "clear",
        request.scientific_profile.observation_confidence_mode if request.scientific_profile else "strong-feature",
    )

    metadata = SpectrumMetadata(
        dominant_molecules=dominant_molecules,
        summary_text=summary_text,
        confidence_score=confidence_score,
        generator="synthetic_signature_blend",
        selected_formula=request.quantum_result.formula if request.quantum_result else None,
        atmospheric_clarity_mode=request.scientific_profile.atmospheric_clarity_mode if request.scientific_profile else "clear",
        observation_confidence_mode=request.scientific_profile.observation_confidence_mode if request.scientific_profile else "strong-feature",
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


def _quantum_influence(quantum_result: QuantumEvaluationResult | None) -> float:
    if quantum_result is None:
        return 1.0
    stability = quantum_result.stability_score
    confidence = quantum_result.confidence_score or 0.5
    source_multiplier = {"live": 1.08, "cached": 1.03, "fallback": 0.97}.get(quantum_result.source, 1.0)
    return max(0.85, min(1.2, (0.8 + stability * 0.25 + confidence * 0.1) * source_multiplier))


def _molecule_absorption(
    molecule: str,
    wavelength: float,
    fraction: float,
    amplitude_scale: float,
    quantum_boost: float,
    quantum_result: QuantumEvaluationResult | None,
) -> float:
    signature = MOLECULE_SIGNATURES.get(molecule)
    if not signature:
        return 0.0

    total = 0.0
    for band in signature["bands"]:
        gaussian = math.exp(-((wavelength - band["center"]) ** 2) / max(2 * (band["width"] ** 2), 1e-6))
        total += band["strength"] * gaussian

    molecule_weight = 0.35 + min(fraction, 0.8)
    if quantum_result and quantum_result.formula == molecule:
        molecule_weight *= quantum_boost
    return total * molecule_weight * amplitude_scale


def _instrument_effect(wavelength: float, radiation_level: float, pressure_bar: float) -> float:
    ripple = 0.004 * math.sin(wavelength * 12.0)
    pressure_smoothing = min(0.02, pressure_bar * 0.0015)
    radiation_noise = min(0.01, radiation_level * 0.0012)
    return ripple + pressure_smoothing + radiation_noise


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
    gas_fractions: dict[str, float],
    amplitude_scale: float,
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
        strength = strongest_band["strength"] * (0.35 + gas_fractions.get(molecule, 0.03)) * amplitude_scale
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


def _spectrum_confidence(
    quantum_result: QuantumEvaluationResult | None,
    dominant_molecules: list[str],
    scientific_profile: ScientificProxyProfile | None,
) -> float:
    base = 0.62 + min(len(dominant_molecules), 4) * 0.04
    if quantum_result is not None:
        base += (quantum_result.confidence_score or 0.5) * 0.18
        if quantum_result.source == "live":
            base += 0.04
    if scientific_profile is not None:
        base += scientific_profile.spectral_visibility_score * 0.08
        if scientific_profile.observation_confidence_mode == "ambiguous":
            base -= 0.1
        if scientific_profile.observation_confidence_mode == "null-signal":
            base -= 0.2
    return round(max(0.0, min(base, 0.96)), 3)


def _build_summary(
    dominant_molecules: list[str],
    quantum_result: QuantumEvaluationResult | None,
    chemistry_modes: list[str],
    confidence_score: float,
    atmospheric_clarity_mode: str,
    observation_confidence_mode: str,
) -> str:
    selected_formula = quantum_result.formula if quantum_result else dominant_molecules[0]
    modes_text = ", ".join(chemistry_modes[:2]) if chemistry_modes else "balanced atmosphere"
    dominant_text = ", ".join(dominant_molecules[:3])
    observation_text = observation_confidence_mode.replace("-", " ")
    return (
        f"Synthetic transmission spectrum emphasizes {selected_formula} within a {modes_text} context. "
        f"Atmospheric clarity is {atmospheric_clarity_mode}, with a {observation_text} observational posture. "
        f"Dominant visible contributors: {dominant_text}. Confidence {confidence_score:.2f}."
    )


def _infer_modes_from_candidates(candidates: list[QuantumCandidateInput]) -> list[str]:
    modes: list[str] = []
    for candidate in candidates:
        for mode in candidate.chemistry_modes:
            if mode not in modes:
                modes.append(mode)
    return modes
