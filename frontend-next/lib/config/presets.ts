import { SimulationPreset, StageDefinition, StageExecutionDefinition } from "@/lib/types/simulation";

export const simulationPresets: SimulationPreset[] = [
  {
    key: "Temperate Water World",
    title: "Temperate Water World",
    description: "Archive-calibrated temperate world with a clear water-rich observational posture and balanced oxidizing chemistry.",
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
      preset_name: "temperate_water_world",
      max_candidates: 3,
      quantum_runtime_mode: "demo_balanced"
    }
  },
  {
    key: "Hot Dense Carbon World",
    title: "Hot Dense Carbon World",
    description: "A hot dense carbon-heavy atmosphere inspired by high-contrast JWST-style molecular signatures.",
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
      preset_name: "hot_dense_carbon_world",
      max_candidates: 3,
      quantum_runtime_mode: "cached_only"
    }
  },
  {
    key: "Cold Methane Frontier",
    title: "Cold Methane Frontier",
    description: "A colder methane-friendly frontier built to demonstrate weaker or more ambiguous observation modes safely.",
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
      preset_name: "cold_methane_frontier",
      max_candidates: 3,
      quantum_runtime_mode: "fallback_only"
    }
  }
];

export const stageDefinitions: StageDefinition[] = [
  {
    id: "planet-birth",
    title: "Planet Initialization",
    eyebrow: "Stage 01",
    description: "Planetary physics are initialized and bulk parameters are stabilized into a plausible generated world."
  },
  {
    id: "atmospheric-validation",
    title: "Atmospheric Model",
    eyebrow: "Stage 02",
    description: "The system derives scale-height, haze, and observability proxies from pressure, temperature, gravity, and composition."
  },
  {
    id: "chemistry-emergence",
    title: "Chemistry Engine",
    eyebrow: "Stage 03",
    description: "Atmospheric context is translated into an explainable shortlist of plausible molecular candidates."
  },
  {
    id: "quantum-evaluation",
    title: "Quantum Evaluation",
    eyebrow: "Stage 04",
    description: "One molecule enters the evaluation chamber while the rest remain in reserve."
  },
  {
    id: "spectrum-reveal",
    title: "Spectrum Simulation",
    eyebrow: "Stage 05",
    description: "A synthetic transmission spectrum is assembled and annotated with candidate absorption features."
  },
  {
    id: "final-discovery",
    title: "Discovery Report",
    eyebrow: "Stage 06",
    description: "The simulation resolves into a presentation-ready scientific conclusion with confidence and caveats."
  }
];

export const stageExecutionTimeline: StageExecutionDefinition[] = [
  {
    id: "planet-birth",
    messages: [
      "Generate planet physics envelope",
      "Stabilize mass, radius, and orbital parameters",
      "Lock plausible atmospheric starting state"
    ]
  },
  {
    id: "atmospheric-validation",
    messages: [
      "Compute scale-height proxy",
      "Evaluate haze and cloud regime",
      "Estimate spectral observability"
    ]
  },
  {
    id: "chemistry-emergence",
    messages: [
      "Test candidate molecules against atmospheric regime",
      "Shortlist plausible molecular signatures",
      "Select molecule for quantum evaluation"
    ]
  },
  {
    id: "quantum-evaluation",
    messages: [
      "Construct molecular Hamiltonian proxy",
      "Run ground-state evaluation path",
      "Compare classical baseline when available"
    ]
  },
  {
    id: "spectrum-reveal",
    messages: [
      "Build synthetic transmission spectrum",
      "Blend molecular feature signatures",
      "Highlight dominant absorption bands"
    ]
  },
  {
    id: "final-discovery",
    messages: [
      "Assemble scientific narrative",
      "Resolve confidence and caution notes",
      "Finalize discovery report"
    ]
  }
];
