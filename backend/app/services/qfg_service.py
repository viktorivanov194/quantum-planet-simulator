from __future__ import annotations

from math import sin, sqrt, tau

from app.models.planet import PlanetProfile
from app.models.qfg import QFGObservablePoint, QFGSimulationConfig, QFGSimulationResult


def run_qfg_field_simulation(
    config: QFGSimulationConfig,
    profile: PlanetProfile | None = None,
) -> QFGSimulationResult | None:
    if not config.enabled:
        return None

    size = config.grid_size
    center = (size - 1) / 2.0
    planet_scale = _planet_scale(profile)
    coherence_seed = _coherence_seed(profile)

    psi_re = [[0.0 for _ in range(size)] for _ in range(size)]
    psi_im = [[0.0 for _ in range(size)] for _ in range(size)]
    phi = [[0.0 for _ in range(size)] for _ in range(size)]

    for y in range(size):
        for x in range(size):
            dx = (x - center) / max(center, 1.0)
            dy = (y - center) / max(center, 1.0)
            radius2 = dx * dx + dy * dy
            envelope = planet_scale * max(0.0, 1.0 - radius2)
            ring = max(0.0, 1.0 - abs(sqrt(radius2) - 0.45) * 2.2)
            psi_re[y][x] = envelope * (0.58 + 0.22 * coherence_seed) + 0.06 * ring
            psi_im[y][x] = 0.02 * (dx - dy)
            phi[y][x] = 0.25 * envelope + 0.08 * ring

    observables: list[QFGObservablePoint] = []
    best_resonance = 0.0
    best_mode_variance = 0.0
    last_energy = 0.0
    last_coherence = 0.0
    density_peak = 0.0
    density_mean = 0.0
    phi_alignment = 0.0

    for step in range(config.steps):
        drive_term = _drive_value(config=config, step=step)
        next_re = [[0.0 for _ in range(size)] for _ in range(size)]
        next_im = [[0.0 for _ in range(size)] for _ in range(size)]
        next_phi = [[0.0 for _ in range(size)] for _ in range(size)]

        total_energy = 0.0
        density_sum = 0.0
        coherence_acc = 0.0
        mode_sum = 0.0
        phi_align_sum = 0.0
        cells = 0

        for y in range(size):
            for x in range(size):
                rho = psi_re[y][x] * psi_re[y][x] + psi_im[y][x] * psi_im[y][x]
                lap_re = _laplacian(psi_re, x, y)
                lap_im = _laplacian(psi_im, x, y)
                lap_phi = _laplacian(phi, x, y)
                potential = config.lambda_vacuum * (rho - config.rho0)
                geometry_feedback = config.coupling_beta * phi[y][x]
                damping = config.damping

                updated_re = psi_re[y][x] + config.dt * (-lap_im - potential * psi_im[y][x] - damping * psi_re[y][x])
                updated_im = psi_im[y][x] + config.dt * (lap_re + (potential + geometry_feedback) * psi_re[y][x] - damping * psi_im[y][x])
                updated_re += config.dt * drive_term * (0.65 + 0.35 * rho)

                next_rho = updated_re * updated_re + updated_im * updated_im
                updated_phi = phi[y][x] + config.dt * (
                    config.alpha * (next_rho - config.rho0) + 0.18 * lap_phi - damping * 0.4 * phi[y][x]
                )

                next_re[y][x] = updated_re
                next_im[y][x] = updated_im
                next_phi[y][x] = updated_phi

                gradient_energy = abs(lap_re) + abs(lap_im) + abs(lap_phi)
                local_energy = 0.5 * gradient_energy + config.lambda_vacuum * (next_rho - config.rho0) ** 2 + abs(updated_phi) * 0.16
                total_energy += local_energy
                density_sum += next_rho
                coherence_acc += max(0.0, 1.0 - abs(next_rho - config.rho0) / max(config.rho0, 0.25))
                mode_sum += abs(next_rho - config.rho0)
                phi_align_sum += max(0.0, 1.0 - min(abs(updated_phi - next_rho * 0.45), 1.0))
                cells += 1

                if next_rho > density_peak:
                    density_peak = next_rho

        psi_re = next_re
        psi_im = next_im
        phi = next_phi

        density_mean = density_sum / max(cells, 1)
        coherence = _clamp(coherence_acc / max(cells, 1), 0.0, 1.0)
        mode_variance = mode_sum / max(cells, 1)
        resonance_signal = abs(drive_term) * (0.6 + 0.4 * coherence) / (1.0 + mode_variance)
        phi_alignment = _clamp(phi_align_sum / max(cells, 1), 0.0, 1.0)

        best_resonance = max(best_resonance, resonance_signal)
        best_mode_variance = max(best_mode_variance, mode_variance)
        last_energy = total_energy / max(cells, 1)
        last_coherence = coherence

        observables.append(
            QFGObservablePoint(
                step=step,
                total_energy=round(last_energy, 6),
                coherence=round(coherence, 6),
                mode_variance=round(mode_variance, 6),
                resonance_signal=round(resonance_signal, 6),
            )
        )

    resonance_delta = abs(config.drive.frequency_1 - config.drive.frequency_2) if config.drive.enabled else 0.0
    resonance_detected = bool(config.drive.enabled and best_resonance > 0.085 and last_coherence > 0.55)
    stability_score = _clamp(
        0.40 * last_coherence + 0.25 * phi_alignment + 0.20 * (1.0 / (1.0 + last_energy)) + 0.15 * (1.0 / (1.0 + best_mode_variance)),
        0.0,
        1.0,
    )
    dominant_mode_hint = _classify_mode(density_peak=density_peak, coherence=last_coherence, resonance=best_resonance)

    notes = [
        "QFG MVP field layer executed on a lightweight 2D lattice.",
        "The scalar field acts as a BSM-SG-inspired coherence substrate rather than a claim of complete physical closure.",
        "Resonance scoring tracks dual-drive forcing, density locking, and phi-rho alignment.",
    ]
    if resonance_detected:
        notes.append("A resonance-like regime appeared under the current dual-drive settings.")
    if profile is not None:
        notes.append(f"Planet coupling seeded from radius={profile.radius_rearth:.2f} R⊕, mass={profile.mass_mearth:.2f} M⊕.")

    return QFGSimulationResult(
        grid_size=size,
        steps=config.steps,
        dt=config.dt,
        coupling_beta=config.coupling_beta,
        resonance_detected=resonance_detected,
        resonance_frequency_delta=round(resonance_delta, 6),
        stability_score=round(stability_score, 3),
        coherence_score=round(last_coherence, 3),
        density_peak=round(density_peak, 6),
        density_mean=round(density_mean, 6),
        phi_alignment_score=round(phi_alignment, 3),
        dominant_mode_hint=dominant_mode_hint,
        notes=notes,
        observables=observables,
    )


def _drive_value(config: QFGSimulationConfig, step: int) -> float:
    if not config.drive.enabled:
        return 0.0
    t = step * config.dt
    return (
        config.drive.amplitude_1 * sin(tau * config.drive.frequency_1 * t)
        + config.drive.amplitude_2 * sin(tau * config.drive.frequency_2 * t + config.drive.phase_offset)
    )


def _laplacian(field: list[list[float]], x: int, y: int) -> float:
    width = len(field[0])
    height = len(field)
    center = field[y][x]
    left = field[y][x - 1] if x > 0 else center
    right = field[y][x + 1] if x < width - 1 else center
    up = field[y - 1][x] if y > 0 else center
    down = field[y + 1][x] if y < height - 1 else center
    return left + right + up + down - 4.0 * center


def _planet_scale(profile: PlanetProfile | None) -> float:
    if profile is None:
        return 0.75
    radius_factor = min(max(profile.radius_rearth / 1.5, 0.45), 1.65)
    mass_factor = min(max(profile.mass_mearth / 2.0, 0.35), 1.8)
    return min(1.4, 0.42 + 0.28 * radius_factor + 0.22 * mass_factor)


def _coherence_seed(profile: PlanetProfile | None) -> float:
    if profile is None:
        return 0.55
    radiation_penalty = min(profile.radiation_level / 5.0, 0.35)
    pressure_boost = min(profile.atmosphere.pressure_bar / 6.0, 0.2)
    temp_balance = 1.0 - min(abs(profile.atmosphere.temperature_k - 295.0) / 420.0, 0.55)
    return _clamp(0.45 + pressure_boost + 0.25 * temp_balance - radiation_penalty, 0.2, 0.95)


def _classify_mode(density_peak: float, coherence: float, resonance: float) -> str:
    if resonance > 0.11 and coherence > 0.72:
        return "dual-drive locked"
    if density_peak > 1.0 and coherence > 0.62:
        return "topological-core candidate"
    if coherence < 0.45:
        return "decohering"
    return "broadband"


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
