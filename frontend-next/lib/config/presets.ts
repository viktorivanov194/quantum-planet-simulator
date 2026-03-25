import { SimulationPreset, StageDefinition } from "@/lib/types/simulation";

export const simulationPresets: SimulationPreset[] = [
  {
    key: "Temperate Water World",
    title: "Temperate Water World",
    description: "Balanced oxidizing chemistry with a strong H2O / CO2 discovery narrative.",
    accent: "from-cyan-300 via-sky-300 to-amber-200",
    planetColors: ["#fff0bc", "#7fd8ff", "#1f5c93"],
    atmosphereGlow: "#7fd8ff",
    hasRing: true,
    hostStarColor: "#fff2be",
    fillLightColor: "#6cbcff",
    cloudTint: "#f7fdff",
    cloudOpacity: 0.12,
    cameraDistance: 4.75,
    autoRotateSpeed: 0.24,
    starDensity: 1,
    payload: {
      preset_name: "temperate_rocky",
      star_type: "K-type",
      orbit_zone: "temperate",
      max_candidates: 3,
      quantum_runtime_mode: "demo_balanced"
    }
  },
  {
    key: "Hot Dense Carbon World",
    title: "Hot Dense Carbon World",
    description: "A hotter, denser atmosphere built for dramatic carbon-dominant spectral output.",
    accent: "from-orange-300 via-amber-200 to-red-300",
    planetColors: ["#ffe5bb", "#ff944d", "#541d10"],
    atmosphereGlow: "#ffac6f",
    hasRing: true,
    hostStarColor: "#ffd087",
    fillLightColor: "#9d4b2e",
    cloudTint: "#fff1dd",
    cloudOpacity: 0.08,
    cameraDistance: 4.55,
    autoRotateSpeed: 0.19,
    starDensity: 0.82,
    payload: {
      preset_name: "hot_dense",
      star_type: "G-type",
      orbit_zone: "hot",
      max_candidates: 3,
      quantum_runtime_mode: "cached_only"
    }
  },
  {
    key: "Cold Methane Frontier",
    title: "Cold Methane Frontier",
    description: "A colder methane-friendly world with a resilient fallback-safe demo path.",
    accent: "from-blue-200 via-cyan-200 to-violet-300",
    planetColors: ["#eef7ff", "#7acfff", "#1a3d6b"],
    atmosphereGlow: "#9ddcff",
    hasRing: false,
    hostStarColor: "#d6f2ff",
    fillLightColor: "#496ed0",
    cloudTint: "#eef9ff",
    cloudOpacity: 0.16,
    cameraDistance: 4.95,
    autoRotateSpeed: 0.31,
    starDensity: 1.18,
    payload: {
      star_type: "M-type",
      orbit_zone: "cold",
      seed: 42,
      max_candidates: 3,
      quantum_runtime_mode: "fallback_only"
    }
  }
];

export const stageDefinitions: StageDefinition[] = [
  {
    id: "planet-birth",
    title: "Planet Birth",
    eyebrow: "Stage 01",
    description: "A plausible world is assembled from orbital context, atmospheric assumptions, and fast physical rules."
  },
  {
    id: "atmospheric-validation",
    title: "Atmospheric Validation",
    eyebrow: "Stage 02",
    description: "Guardrails evaluate whether the generated profile stays within the MVP plausibility envelope."
  },
  {
    id: "chemistry-emergence",
    title: "Chemistry Emergence",
    eyebrow: "Stage 03",
    description: "Atmospheric context is translated into an explainable shortlist of candidate molecular signatures."
  },
  {
    id: "quantum-evaluation",
    title: "Quantum Evaluation",
    eyebrow: "Stage 04",
    description: "One molecule enters the evaluation chamber while the rest remain in reserve."
  },
  {
    id: "spectrum-reveal",
    title: "Spectrum Reveal",
    eyebrow: "Stage 05",
    description: "A synthetic transmission signature emerges from the selected chemistry and quantum context."
  },
  {
    id: "final-discovery",
    title: "Final Discovery",
    eyebrow: "Stage 06",
    description: "The system resolves into a presentation-ready scientific narrative with confidence and caveats."
  }
];
