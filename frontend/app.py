from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


API_BASE_URL = "http://localhost:8000/api/v1"
DEMO_PRESETS = {
    "Temperate Water World": {
        "description": "Safe jury preset with balanced chemistry and a strong H2O / CO2 spectral story.",
        "payload": {
            "preset_name": "temperate_rocky",
            "star_type": "K-type",
            "orbit_zone": "temperate",
            "max_candidates": 3,
            "quantum_runtime_mode": "demo_balanced",
        },
    },
    "Hot Dense Carbon World": {
        "description": "High-contrast carbon-heavy case with dramatic CO2 and SO2 style signatures.",
        "payload": {
            "preset_name": "hot_dense",
            "star_type": "G-type",
            "orbit_zone": "hot",
            "max_candidates": 3,
            "quantum_runtime_mode": "cached_only",
        },
    },
    "Cold Methane Frontier": {
        "description": "A colder, methane-friendly atmosphere that still demos safely through fallback mode.",
        "payload": {
            "star_type": "M-type",
            "orbit_zone": "cold",
            "seed": 42,
            "max_candidates": 3,
            "quantum_runtime_mode": "fallback_only",
        },
    },
}
STAGE_TITLES = [
    "Planet Birth",
    "Atmospheric Validation",
    "Chemistry Emergence",
    "Quantum Evaluation",
    "Spectrum Reveal",
    "Final Discovery",
]


def main() -> None:
    st.set_page_config(page_title="Quantum Planet Simulator", layout="wide")
    inject_styles()
    render_hero()

    with st.sidebar:
        st.markdown("### Mission Control")
        preset_name = st.selectbox("Simulation preset", list(DEMO_PRESETS.keys()), index=0)
        preset = DEMO_PRESETS[preset_name]
        st.caption(preset["description"])
        custom_mode = st.toggle("Manual override", value=False)
        star_type = st.selectbox("Host star", ["M-type", "K-type", "G-type"], index=1, disabled=not custom_mode)
        orbit_zone = st.selectbox("Orbit regime", ["cold", "temperate", "hot"], index=1, disabled=not custom_mode)
        max_candidates = st.slider("Candidate depth", min_value=2, max_value=5, value=3, disabled=not custom_mode)
        quantum_runtime_mode = st.selectbox(
            "Quantum runtime",
            ["demo_balanced", "cached_only", "fallback_only"],
            index=0,
            disabled=not custom_mode,
        )
        run_pipeline = st.button("Launch Simulation", type="primary", use_container_width=True)

    if run_pipeline:
        payload = dict(preset["payload"])
        if custom_mode:
            payload.update(
                {
                    "star_type": star_type,
                    "orbit_zone": orbit_zone,
                    "max_candidates": max_candidates,
                    "quantum_runtime_mode": quantum_runtime_mode,
                }
            )
        try:
            with st.spinner("Synthesizing planet conditions, chemistry, quantum proxy, and spectral reveal..."):
                response = requests.post(f"{API_BASE_URL}/simulation/run", json=payload, timeout=30)
                response.raise_for_status()
                render_simulation_result(response.json(), preset_name)
        except requests.RequestException as exc:
            st.error("Mission link to the backend failed. Start FastAPI first, then relaunch the simulation.")
            st.caption(f"Request error: {exc}")
    else:
        render_placeholder()


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(65, 173, 255, 0.16), transparent 28%),
                radial-gradient(circle at 80% 10%, rgba(255, 175, 88, 0.16), transparent 22%),
                linear-gradient(180deg, #07111f 0%, #0d1726 45%, #081018 100%);
            color: #eef4ff;
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 4rem;
            max-width: 1200px;
        }
        .hero-shell, .glass-card, .discovery-card {
            border: 1px solid rgba(171, 208, 255, 0.16);
            background: linear-gradient(180deg, rgba(15, 24, 38, 0.88), rgba(8, 15, 26, 0.88));
            box-shadow: 0 30px 80px rgba(0, 0, 0, 0.28);
            backdrop-filter: blur(10px);
        }
        .hero-shell {
            border-radius: 28px;
            padding: 2rem 2rem 1.6rem 2rem;
            margin-bottom: 1.25rem;
            position: relative;
            overflow: hidden;
        }
        .hero-grid {
            display: grid;
            grid-template-columns: 1.3fr 0.9fr;
            gap: 1.5rem;
            align-items: center;
        }
        .hero-title {
            font-size: 4rem;
            line-height: 0.95;
            font-weight: 800;
            letter-spacing: -0.05em;
            margin: 0;
            color: #f6fbff;
        }
        .hero-subtitle {
            font-size: 1.1rem;
            color: #adc7e8;
            margin-top: 0.8rem;
            margin-bottom: 0.6rem;
        }
        .hero-tagline {
            font-size: 1.2rem;
            color: #fff3d8;
            max-width: 52rem;
        }
        .hero-visual {
            min-height: 260px;
            position: relative;
            border-radius: 24px;
            overflow: hidden;
            background:
                radial-gradient(circle at 50% 40%, rgba(126, 209, 255, 0.18), transparent 25%),
                radial-gradient(circle at 20% 20%, rgba(255, 206, 132, 0.14), transparent 18%),
                linear-gradient(180deg, rgba(9, 17, 31, 0.85), rgba(5, 10, 18, 0.92));
            border: 1px solid rgba(136, 188, 255, 0.14);
        }
        .hero-star {
            position: absolute;
            width: 4px;
            height: 4px;
            border-radius: 50%;
            background: rgba(255,255,255,0.7);
            box-shadow: 0 0 14px rgba(144, 214, 255, 0.32);
            animation: pulseStar 3.6s ease-in-out infinite;
        }
        .hero-core {
            position: absolute;
            right: 12%;
            top: 16%;
            width: 150px;
            height: 150px;
            border-radius: 50%;
            background: radial-gradient(circle at 32% 30%, #fff6d2, #8cd3ff 38%, #1d5685 72%, #0a1733 100%);
            box-shadow: inset -20px -30px 50px rgba(0,0,0,0.36), 0 0 60px rgba(103, 188, 255, 0.25);
            animation: floatOrb 8s ease-in-out infinite;
        }
        .hero-orbit {
            position: absolute;
            width: 210px;
            height: 210px;
            right: 5%;
            top: 6%;
            border-radius: 50%;
            border: 1px solid rgba(146, 203, 255, 0.18);
            animation: spinRing 16s linear infinite;
        }
        .hero-probe {
            position: absolute;
            width: 14px;
            height: 14px;
            right: 11%;
            top: 38%;
            border-radius: 50%;
            background: #ffe1aa;
            box-shadow: 0 0 18px rgba(255, 207, 120, 0.5);
        }
        .stage-strip {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 0.65rem;
            margin: 1rem 0 0.25rem 0;
        }
        .stage-pill {
            border-radius: 999px;
            padding: 0.6rem 0.85rem;
            font-size: 0.82rem;
            text-align: center;
            background: rgba(124, 174, 255, 0.08);
            border: 1px solid rgba(124, 174, 255, 0.18);
            color: #d8e9ff;
        }
        .section-title {
            font-size: 1.65rem;
            font-weight: 700;
            color: #f5fbff;
            margin: 0;
        }
        .section-kicker {
            color: #8eb6d8;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-size: 0.78rem;
            margin-bottom: 0.5rem;
        }
        .glass-card {
            border-radius: 24px;
            padding: 1.2rem;
            height: 100%;
        }
        .planet-scene {
            min-height: 300px;
            position: relative;
            overflow: hidden;
            border-radius: 28px;
            border: 1px solid rgba(168, 214, 255, 0.16);
            background:
                radial-gradient(circle at 30% 30%, rgba(255,255,255,0.18), transparent 18%),
                radial-gradient(circle at 60% 40%, rgba(255, 193, 84, 0.22), transparent 28%),
                radial-gradient(circle at center, rgba(62, 154, 255, 0.28), transparent 60%),
                linear-gradient(160deg, #09101a 10%, #0f1d32 65%, #08111a 100%);
            box-shadow: inset 0 0 80px rgba(0,0,0,0.35);
        }
        .planet-orb {
            width: 180px;
            height: 180px;
            border-radius: 50%;
            position: absolute;
            right: 12%;
            top: 18%;
            box-shadow:
                inset -18px -24px 48px rgba(0, 0, 0, 0.36),
                0 0 40px rgba(89, 191, 255, 0.24);
            animation: floatOrb 9s ease-in-out infinite;
        }
        .planet-ring {
            position: absolute;
            width: 220px;
            height: 60px;
            border-radius: 50%;
            border: 1px solid rgba(255,255,255,0.18);
            right: 3%;
            top: 39%;
            transform: rotate(-13deg);
            opacity: 0.6;
            animation: driftRing 7s ease-in-out infinite;
        }
        .planet-label {
            position: absolute;
            left: 7%;
            bottom: 14%;
            max-width: 46%;
        }
        .planet-name {
            font-size: 2rem;
            font-weight: 700;
            color: #f7fbff;
        }
        .planet-meta {
            color: #b7d2ee;
            font-size: 1rem;
        }
        .molecule-card {
            border-radius: 20px;
            padding: 1rem;
            border: 1px solid rgba(145, 192, 255, 0.15);
            background: linear-gradient(180deg, rgba(18, 29, 45, 0.9), rgba(8, 16, 28, 0.9));
            margin-bottom: 0.8rem;
        }
        .molecule-focus {
            border: 1px solid rgba(255, 208, 117, 0.36);
            box-shadow: 0 0 24px rgba(255, 197, 97, 0.14);
        }
        .molecule-formula {
            font-size: 1.45rem;
            font-weight: 700;
            color: #fff8eb;
        }
        .minor-copy {
            color: #a8c4df;
            font-size: 0.95rem;
        }
        .quantum-chamber {
            border-radius: 26px;
            padding: 1.2rem;
            background:
                radial-gradient(circle at top, rgba(83, 155, 255, 0.15), transparent 42%),
                linear-gradient(180deg, rgba(10, 17, 28, 0.96), rgba(5, 10, 18, 0.96));
            border: 1px solid rgba(124, 175, 255, 0.18);
            position: relative;
            overflow: hidden;
        }
        .quantum-chamber::after {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(180deg, transparent, rgba(103, 187, 255, 0.08), transparent);
            transform: translateY(-100%);
            animation: scanDrop 3.8s linear infinite;
            pointer-events: none;
        }
        .source-badge {
            display: inline-block;
            padding: 0.35rem 0.75rem;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.75rem;
        }
        .source-live { background: rgba(59, 210, 141, 0.14); color: #7cf3b8; border: 1px solid rgba(59, 210, 141, 0.25); }
        .source-cached { background: rgba(104, 162, 255, 0.14); color: #a9d0ff; border: 1px solid rgba(104, 162, 255, 0.25); }
        .source-fallback { background: rgba(255, 186, 117, 0.14); color: #ffd59e; border: 1px solid rgba(255, 186, 117, 0.25); }
        .reveal-shell {
            border-radius: 28px;
            padding: 1.4rem;
            background: linear-gradient(180deg, rgba(8, 18, 31, 0.95), rgba(7, 12, 20, 0.95));
            border: 1px solid rgba(145, 204, 255, 0.18);
            box-shadow: inset 0 0 60px rgba(107, 176, 255, 0.08);
        }
        .discovery-card {
            border-radius: 30px;
            padding: 1.6rem;
            background:
                radial-gradient(circle at top right, rgba(255, 196, 104, 0.16), transparent 28%),
                linear-gradient(180deg, rgba(11, 20, 34, 0.98), rgba(7, 13, 22, 0.98));
            position: relative;
            overflow: hidden;
        }
        .discovery-card::before {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(120deg, transparent 0%, rgba(255,255,255,0.06) 45%, transparent 70%);
            transform: translateX(-120%);
            animation: sheen 7s ease-in-out infinite;
        }
        .discovery-headline {
            font-size: 2rem;
            line-height: 1.1;
            font-weight: 800;
            color: #fff9ef;
        }
        .highlight-chip {
            border-radius: 999px;
            display: inline-block;
            padding: 0.45rem 0.7rem;
            margin: 0.2rem 0.25rem 0.2rem 0;
            background: rgba(116, 174, 255, 0.12);
            border: 1px solid rgba(116, 174, 255, 0.2);
            color: #d6e9ff;
            font-size: 0.88rem;
        }
        @keyframes floatOrb {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        @keyframes spinRing {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        @keyframes driftRing {
            0%, 100% { transform: rotate(-13deg) translateY(0px); }
            50% { transform: rotate(-9deg) translateY(-4px); }
        }
        @keyframes pulseStar {
            0%, 100% { opacity: 0.35; transform: scale(0.9); }
            50% { opacity: 1; transform: scale(1.2); }
        }
        @keyframes scanDrop {
            from { transform: translateY(-110%); }
            to { transform: translateY(110%); }
        }
        @keyframes sheen {
            0%, 100% { transform: translateX(-120%); }
            50% { transform: translateX(120%); }
        }
        @media (max-width: 900px) {
            .hero-grid {
                grid-template-columns: 1fr;
            }
            .stage-strip {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero-shell">
            <div class="hero-grid">
                <div>
                    <div class="hero-title">Quantum Planet Simulator</div>
                    <div class="hero-subtitle">Synthetic Exoplanet Discovery Experience</div>
                    <div class="hero-tagline">
                        Trace the birth of a plausible world, watch its chemistry emerge, push one candidate through a
                        quantum gate, and reveal the transmission signature that would define its story.
                    </div>
                </div>
                <div class="hero-visual">
                    <div class="hero-star" style="left:12%; top:22%;"></div>
                    <div class="hero-star" style="left:22%; top:62%; animation-delay:0.8s;"></div>
                    <div class="hero-star" style="left:58%; top:14%; animation-delay:1.6s;"></div>
                    <div class="hero-star" style="left:72%; top:72%; animation-delay:1.2s;"></div>
                    <div class="hero-star" style="left:84%; top:26%; animation-delay:2s;"></div>
                    <div class="hero-orbit"></div>
                    <div class="hero-core"></div>
                    <div class="hero-probe"></div>
                </div>
            </div>
            <div class="stage-strip">
                <div class="stage-pill">Planet Birth</div>
                <div class="stage-pill">Atmospheric Validation</div>
                <div class="stage-pill">Chemistry Emergence</div>
                <div class="stage-pill">Quantum Evaluation</div>
                <div class="stage-pill">Spectrum Reveal</div>
                <div class="stage-pill">Final Discovery</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_placeholder() -> None:
    col1, col2, col3 = st.columns(3)
    with col1:
        render_text_card(
            "Planet Birth",
            "Rule-based world generation tuned for fast, credible exoplanet scenarios.",
        )
    with col2:
        render_text_card(
            "Quantum Storyline",
            "Cache-first quantum scoring keeps the demo stable while preserving a scientific narrative.",
        )
    with col3:
        render_text_card(
            "Spectrum Reveal",
            "A synthetic but explainable transmission signature turns the analysis into a jury-friendly finale.",
        )
    st.info("Choose a preset from Mission Control and launch the simulation to begin the guided discovery flow.")


def render_simulation_result(data: dict, preset_name: str) -> None:
    report = data.get("final_report") or {}
    st.markdown(
        f"""
        <div class="glass-card" style="margin-bottom:1rem;">
            <div class="section-kicker">Simulation Active</div>
            <div class="section-title">{report.get("discovery_headline", data.get("report_summary", "Simulation completed."))}</div>
            <div class="minor-copy" style="margin-top:0.5rem;">Preset lock: {preset_name}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_planet_section(data["profile"])
    render_validation_section(data["validation"])
    render_chemistry_section(data["chemistry"])
    render_quantum_section(data.get("selected_candidate"), data.get("quantum"))
    render_spectrum_section(data.get("spectrum"))
    render_report_section(report)


def render_planet_section(profile: dict) -> None:
    render_section_header("Planet Birth", "A synthetic planet emerges from orbital context, atmospheric assumptions, and lightweight physical rules.")
    col1, col2 = st.columns([1.25, 1])

    with col1:
        planet_color = planet_gradient(profile["orbit_zone"])
        st.markdown(
            f"""
            <div class="planet-scene">
                <div class="planet-orb" style="background:{planet_color};"></div>
                <div class="planet-ring"></div>
                <div class="planet-label">
                    <div class="planet-name">{profile["planet_name"]}</div>
                    <div class="planet-meta">{profile["star_type"]} host star • {profile["orbit_zone"]} regime</div>
                    <div class="planet-meta">Generated as a cinematic proxy for a fast local scientific demo.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        atmosphere_df = pd.DataFrame(
            {
                "gas": list(profile["atmosphere"]["gas_fractions"].keys()),
                "fraction": list(profile["atmosphere"]["gas_fractions"].values()),
            }
        )
        atmosphere_fig = atmosphere_chart(atmosphere_df)
        st.plotly_chart(atmosphere_fig, use_container_width=True)
        render_metric_row(
            [
                ("Equilibrium", f'{profile["equilibrium_temperature_k"]:.1f} K'),
                ("Radiation", f'{profile["radiation_level"]:.2f}'),
            ]
        )
        render_metric_row(
            [
                ("Radius", f'{profile["radius_rearth"]:.2f} R⊕'),
                ("Mass", f'{profile["mass_mearth"]:.2f} M⊕'),
                ("Gravity", f'{profile["gravity_ms2"]:.2f} m/s²'),
            ]
        )
        render_text_card(
            "Planet Overview",
            f"Temperatures near {profile['equilibrium_temperature_k']:.0f} K and pressure around {profile['atmosphere']['pressure_bar']:.2f} bar create the stage for the chemistry pipeline.",
        )


def render_validation_section(validation: dict) -> None:
    render_section_header("Atmospheric Validation", "Guardrails evaluate whether the generated world remains plausible inside the MVP science envelope.")
    col1, col2 = st.columns([0.9, 1.4])
    with col1:
        render_text_card(
            "Plausibility Envelope",
            "Warnings are interpreted as cautionary scientific framing, not hard failure claims.",
        )
        st.metric("Validation Score", f'{validation["score"]:.2f}')
    with col2:
        if validation["issues"]:
            for issue in validation["issues"]:
                st.warning(f'{issue["code"]}: {issue["message"]}')
        else:
            st.success("No major atmospheric or planetary contradictions were flagged in the current scenario.")


def render_chemistry_section(chemistry: dict) -> None:
    render_section_header("Chemistry Emergence", "Atmospheric context is translated into a shortlist of signatures worth tracking across the rest of the pipeline.")
    col1, col2 = st.columns([0.9, 1.3])

    with col1:
        fig = chemistry_field_chart(chemistry["candidates"])
        st.plotly_chart(fig, use_container_width=True)
        render_text_card(
            "Selection Logic",
            "Shortlisted molecules inherit atmosphere mode signals first, then receive a second pass for quantum-worthiness.",
        )

    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### Candidate Field")
        for candidate in chemistry["candidates"]:
            focus = any(
                candidate["formula"] == selected["formula"]
                for selected in chemistry["selected_for_quantum"]
            )
            render_molecule_card(candidate, focus=focus)
        st.caption(f'Atmospheric mode interpretation: {chemistry["chemistry_mode_summary"]}')
        st.markdown("</div>", unsafe_allow_html=True)


def render_quantum_section(selected_candidate: dict | None, quantum: dict | None) -> None:
    render_section_header("Quantum Evaluation", "A single molecule enters the evaluation chamber while the rest of the shortlist stays in reserve.")
    if not quantum:
        st.info("The quantum chamber did not produce a result for this run. Chemistry and spectrum layers can still anchor the presentation.")
        return

    source_class = f'source-{quantum["source"]}'
    st.markdown(
        f"""
        <div class="quantum-chamber">
            <div class="source-badge {source_class}">{quantum["source"]}</div>
            <div class="section-title" style="font-size:1.8rem;">{selected_candidate["name"] if selected_candidate else quantum["name"]}</div>
            <div class="minor-copy">Formula {quantum["formula"]} • Ground-state proxy {quantum["ground_state_energy_proxy"]:.3f}</div>
            <div class="minor-copy" style="margin-top:0.45rem;">Evaluation chamber engaged with a lightweight local quantum proxy workflow.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.progress(int(max(0.0, min(1.0, quantum["stability_score"])) * 100), text=f'Stability score: {quantum["stability_score"]:.2f}')
        st.progress(int(max(0.0, min(1.0, quantum.get("confidence_score") or 0.0)) * 100), text=f'Confidence: {(quantum.get("confidence_score") or 0.0):.2f}')
    with col2:
        if quantum["source"] == "fallback":
            render_text_card("Quantum Status", "The live/cache path was unavailable, so the system switched to a safe fallback proxy without breaking the story.")
        elif quantum["source"] == "cached":
            render_text_card("Quantum Status", "The chamber resolved this candidate from the local cache, which is ideal for a stable stage demo.")
        else:
            render_text_card("Quantum Status", "A live local proxy evaluation completed successfully and reinforced the selected signature.")

    with st.expander("Evaluation chamber notes", expanded=False):
        for note in quantum["notes"]:
            st.write(f"- {note}")


def render_spectrum_section(spectrum: dict | None) -> None:
    render_section_header("Spectrum Reveal", "The analysis resolves into a cinematic transmission signature built from synthetic but explainable molecular bands.")
    if not spectrum:
        st.info("The spectrum layer did not return a result for this run.")
        return

    st.markdown('<div class="reveal-shell">', unsafe_allow_html=True)
    spectrum_df = pd.DataFrame(
        {"wavelength_um": spectrum["wavelengths"], "absorption": spectrum["absorption_values"]}
    )
    fig = px.line(
        spectrum_df,
        x="wavelength_um",
        y="absorption",
        markers=False,
        title="Transmission Signature",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#eaf4ff",
        margin=dict(l=10, r=10, t=60, b=20),
    )
    fig.update_traces(line=dict(width=4, color="#8bd0ff"))
    fig.add_trace(
        go.Scatter(
            x=spectrum_df["wavelength_um"],
            y=spectrum_df["absorption"],
            mode="lines",
            fill="tozeroy",
            line=dict(color="rgba(0,0,0,0)"),
            fillcolor="rgba(122, 207, 255, 0.16)",
            showlegend=False,
        )
    )
    for feature in spectrum["highlighted_features"]:
        fig.add_vline(x=feature["wavelength_um"], line_dash="dot", line_color="#ffd289", opacity=0.55)
        fig.add_annotation(
            x=feature["wavelength_um"],
            y=max(spectrum["absorption_values"]),
            text=feature["molecule"],
            showarrow=False,
            yshift=15,
            font=dict(color="#ffe7bc", size=11),
        )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1.2, 1])
    with col1:
        st.markdown("#### Highlighted Features")
        for feature in spectrum["highlighted_features"]:
            st.markdown(
                f'<span class="highlight-chip">{feature["label"]} • {feature["wavelength_um"]:.2f} μm • strength {feature["strength"]:.2f}</span>',
                unsafe_allow_html=True,
            )
    with col2:
        render_text_card(
            "Dominant Contributors",
            f'{", ".join(spectrum["dominant_molecules"])}. {spectrum["summary_text"]}',
        )


def render_report_section(report: dict) -> None:
    render_section_header("Final Discovery", "The simulation resolves into a presentable scientific claim with confidence framing and honest caveats.")
    if not report:
        st.info("No final discovery report is available for this run.")
        return

    st.markdown(
        f"""
        <div class="discovery-card">
            <div class="section-kicker">{report["title"]}</div>
            <div class="discovery-headline">{report["discovery_headline"]}</div>
            <div class="hero-subtitle" style="margin-bottom:0.9rem;">{report["subtitle"]}</div>
            <div class="hero-tagline" style="font-size:1.05rem; color:#dce8f8;">{report["discovery_summary"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        render_text_card("Key Highlights", "<br>".join(f"• {item}" for item in report["key_highlights"]))
    with col2:
        render_text_card("Caution Notes", "<br>".join(f"• {item}" for item in report["caution_notes"]))

    col3, col4 = st.columns([0.8, 1.2])
    with col3:
        st.metric("Discovery Confidence", f'{report["confidence_score"]:.2f}')
    with col4:
        render_text_card("Novelty Tagline", report["novelty_tagline"])

    with st.expander("Scientific narrative", expanded=False):
        st.write(report["planet_overview"])
        st.write(report["chemistry_overview"])
        st.write(report["quantum_overview"])
        st.write(report["spectrum_overview"])


def render_section_header(title: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="section-kicker">{title}</div>
        <div class="section-title">{title}</div>
        <div class="minor-copy" style="margin:0.35rem 0 1rem 0;">{description}</div>
        """,
        unsafe_allow_html=True,
    )


def render_text_card(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="glass-card">
            <div class="section-kicker">{title}</div>
            <div class="minor-copy">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_row(items: list[tuple[str, str]]) -> None:
    columns = st.columns(len(items))
    for column, (label, value) in zip(columns, items):
        column.metric(label, value)


def render_molecule_card(candidate: dict, focus: bool = False) -> None:
    focus_class = " molecule-focus" if focus else ""
    st.markdown(
        f"""
        <div class="molecule-card{focus_class}">
            <div class="molecule-formula">{candidate["formula"]}</div>
            <div class="minor-copy"><strong>{candidate["name"]}</strong> • score {candidate["classical_score"]:.2f} • {candidate["tag"]}</div>
            <div class="minor-copy" style="margin-top:0.5rem;">{candidate["rationale"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def chemistry_field_chart(candidates: list[dict]) -> go.Figure:
    top = candidates[:4]
    labels = [candidate["formula"] for candidate in top]
    values = [max(candidate["classical_score"], 0.05) for candidate in top]
    colors = ["#7fd3ff", "#9effd6", "#ffd28d", "#d3a6ff"]
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.62,
                textinfo="label",
                marker=dict(colors=colors[: len(labels)], line=dict(color="#07111f", width=2)),
            )
        ]
    )
    fig.update_layout(
        title="Molecular Field",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#eaf4ff",
        margin=dict(l=10, r=10, t=60, b=10),
        showlegend=False,
    )
    return fig


def atmosphere_chart(atmosphere_df: pd.DataFrame) -> go.Figure:
    colors = ["#9ed8ff", "#86f1cf", "#ffd599", "#d5b0ff", "#f7a6c6", "#9ab4ff"]
    fig = go.Figure(
        data=[
            go.Pie(
                labels=atmosphere_df["gas"],
                values=atmosphere_df["fraction"],
                hole=0.7,
                textinfo="label+percent",
                textfont=dict(color="#f3f8ff", size=12),
                marker=dict(colors=colors[: len(atmosphere_df)], line=dict(color="#07111f", width=2)),
            )
        ]
    )
    fig.update_layout(
        title="Atmospheric Composition Panel",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#eaf4ff",
        margin=dict(l=10, r=10, t=60, b=10),
        showlegend=False,
    )
    return fig


def planet_gradient(orbit_zone: str) -> str:
    if orbit_zone == "hot":
        return "radial-gradient(circle at 30% 30%, #ffefc0, #ff8b4a 35%, #61210d 70%, #1f0d0a 100%)"
    if orbit_zone == "cold":
        return "radial-gradient(circle at 30% 30%, #eff8ff, #8ad2ff 38%, #234c80 72%, #0a1730 100%)"
    return "radial-gradient(circle at 30% 30%, #fff8d8, #7fd1ff 34%, #2f7bb0 68%, #10253b 100%)"


if __name__ == "__main__":
    main()
