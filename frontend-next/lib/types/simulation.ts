export type PresetKey =
  | "Temperate Water World"
  | "Hot Dense Carbon World"
  | "Cold Methane Frontier";

export type QualityMode = "Cinematic" | "Balanced" | "Safe";
export type ExperienceMode = "presets" | "builder";
export type BuilderMode = "guided" | "advanced";
export type BuilderGasKey = "N2" | "O2" | "CO2" | "CH4" | "H2O" | "NH3" | "HCN" | "SO2" | "CO";
export type RuntimeMode = "cached_only" | "demo_balanced" | "fallback_only";

export type StageId =
  | "planet-birth"
  | "atmospheric-validation"
  | "chemistry-emergence"
  | "quantum-evaluation"
  | "spectrum-reveal"
  | "final-discovery";

export interface SimulationPreset {
  key: PresetKey;
  title: string;
  description: string;
  accent: string;
  planetColors: [string, string, string];
  atmosphereGlow: string;
  hasRing?: boolean;
  hostStarColor: string;
  fillLightColor: string;
  cloudTint: string;
  cloudOpacity: number;
  cameraDistance: number;
  autoRotateSpeed: number;
  starDensity: number;
  payload: Record<string, string | number>;
}

export interface StageDefinition {
  id: StageId;
  title: string;
  eyebrow: string;
  description: string;
}

export interface StageExecutionDefinition {
  id: StageId;
  messages: string[];
}

export interface BuilderConfig {
  star_type: string;
  orbit_zone: string;
  radius_rearth: number;
  mass_mearth: number;
  equilibrium_temperature_k: number;
  radiation_level: number;
  pressure_bar: number;
  gas_fractions: Record<BuilderGasKey, number>;
  quantum_runtime_mode: RuntimeMode;
  seed?: number | null;
}

export interface QuantumCandidateInput {
  name: string;
  formula: string;
  classical_score: number;
  tag: string;
  rationale: string;
  chemistry_modes: string[];
}

export interface QuantumEvaluationResult {
  name: string;
  formula: string;
  ground_state_energy_proxy: number;
  stability_score: number;
  source: "cached" | "live" | "fallback";
  notes: string[];
  confidence_score?: number | null;
  classical_reference_energy_proxy?: number | null;
  baseline_agreement_score?: number | null;
  verification_mode?: string | null;
}

export interface SpectrumFeature {
  wavelength_um: number;
  label: string;
  molecule: string;
  strength: number;
}

export interface SpectrumResponse {
  wavelengths: number[];
  absorption_values: number[];
  highlighted_features: SpectrumFeature[];
  dominant_molecules: string[];
  summary_text: string;
  metadata: {
    confidence_score?: number | null;
    selected_formula?: string | null;
    atmospheric_clarity_mode?: string;
    observation_confidence_mode?: string;
  };
}

export interface FinalDiscoveryReport {
  title: string;
  subtitle: string;
  discovery_headline: string;
  discovery_summary: string;
  planet_overview: string;
  chemistry_overview: string;
  quantum_overview: string;
  spectrum_overview: string;
  key_highlights: string[];
  caution_notes: string[];
  confidence_score: number;
  novelty_tagline: string;
}

export interface ScientificProxyProfile {
  mean_molecular_weight_proxy: number;
  scale_height_proxy: number;
  cloud_haze_factor: number;
  oxidation_index_proxy: number;
  carbon_richness_proxy: number;
  nitrogen_richness_proxy: number;
  spectral_visibility_score: number;
  atmospheric_clarity_mode: string;
  observation_confidence_mode: string;
  observation_risk_notes: string[];
  scientific_disclaimers: string[];
}

export interface VisualPhysicsProfile {
  surface_palette: string[];
  surface_variation_intensity: number;
  terminator_contrast: number;
  host_star_light_color: string;
  fill_light_color: string;
  atmosphere_glow_color: string;
  atmosphere_glow_intensity: number;
  atmosphere_rim_width: number;
  atmosphere_thickness_visual: number;
  cloud_tint: string;
  cloud_opacity: number;
  cloud_motion_speed: number;
  haze_intensity: number;
  camera_distance: number;
  camera_fov: number;
  auto_rotate_speed: number;
  starfield_density: number;
  particle_density: number;
  spectrum_accent_palette: string[];
  quantum_chamber_intensity: number;
  quantum_ring_speed: number;
  validation_overlay_tone: string;
}

export interface SimulationResponse {
  profile: {
    planet_name: string;
    star_type: string;
    orbit_zone: string;
    generation_mode: string;
    radius_rearth: number;
    mass_mearth: number;
    gravity_ms2: number;
    equilibrium_temperature_k: number;
    radiation_level: number;
    atmosphere: {
      gas_fractions: Record<string, number>;
      dominant_gases: string[];
      pressure_bar: number;
      temperature_k: number;
    };
    notes: string[];
  };
  validation: {
    is_valid: boolean;
    score: number;
    issues: Array<{
      code: string;
      message: string;
      severity: string;
    }>;
  };
  chemistry: {
    candidates: Array<{
      name: string;
      formula: string;
      classical_score: number;
      rationale: string;
      tag: string;
    }>;
    selected_for_quantum: QuantumCandidateInput[];
    chemistry_mode_summary: string;
    chemistry_modes: string[];
  };
  selected_candidate?: QuantumCandidateInput | null;
  quantum?: QuantumEvaluationResult | null;
  spectrum?: SpectrumResponse | null;
  scientific_proxy_profile: ScientificProxyProfile;
  visual_physics_profile: VisualPhysicsProfile;
  report_summary: string;
  final_report?: FinalDiscoveryReport | null;
}
