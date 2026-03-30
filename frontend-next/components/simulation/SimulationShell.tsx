"use client";

import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

import { BuilderDeck } from "@/components/builder/BuilderDeck";
import { HeroScene } from "@/components/hero/HeroScene";
import { StageStrip } from "@/components/layout/StageStrip";
import { PresetSwitcher } from "@/components/presets/PresetSwitcher";
import { PlanetCanvas } from "@/components/scene/PlanetCanvas";
import { runSimulation } from "@/lib/api/simulation-client";
import { simulationPresets, stageDefinitions, stageExecutionTimeline } from "@/lib/config/presets";
import {
  BuilderConfig,
  BuilderGasKey,
  BuilderMode,
  ExperienceMode,
  PresetKey,
  QualityMode,
  RuntimeMode,
  SimulationResponse,
  StageId,
} from "@/lib/types/simulation";

const stageOrder: StageId[] = stageDefinitions.map((stage) => stage.id);
const STAGE_REVEAL_DURATION_MS: Record<StageId, number> = {
  "planet-birth": 3200,
  "atmospheric-validation": 2100,
  "chemistry-emergence": 2100,
  "quantum-evaluation": 2200,
  "spectrum-reveal": 2200,
  "final-discovery": 1200,
};
const DEFAULT_BUILDER_CONFIG: BuilderConfig = {
  star_type: "K-type",
  orbit_zone: "temperate",
  radius_rearth: 1.14,
  mass_mearth: 1.5,
  equilibrium_temperature_k: 294,
  radiation_level: 0.94,
  pressure_bar: 1.08,
  gas_fractions: {
    N2: 0.62,
    O2: 0.18,
    CO2: 0.07,
    CH4: 0.03,
    H2O: 0.08,
    NH3: 0.0,
    HCN: 0.0,
    SO2: 0.0,
    CO: 0.02,
  },
  quantum_runtime_mode: "demo_balanced",
  seed: null,
};

export function SimulationShell() {
  const [experienceMode, setExperienceMode] = useState<ExperienceMode>("presets");
  const [builderMode, setBuilderMode] = useState<BuilderMode>("guided");
  const [selectedPresetKey, setSelectedPresetKey] = useState<PresetKey>("Temperate Water World");
  const [builderConfig, setBuilderConfig] = useState<BuilderConfig>(DEFAULT_BUILDER_CONFIG);
  const [qualityMode, setQualityMode] = useState<QualityMode>("Balanced");
  const [activeStage, setActiveStage] = useState<StageId | null>(null);
  const [result, setResult] = useState<SimulationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [presentationStage, setPresentationStage] = useState<StageId | null>(null);
  const [manualStage, setManualStage] = useState<StageId | null>(null);
  const [executionLogs, setExecutionLogs] = useState<string[]>([]);
  const [completedStages, setCompletedStages] = useState<StageId[]>([]);
  const [isStagePlaybackActive, setIsStagePlaybackActive] = useState(false);
  const [stageMessageCount, setStageMessageCount] = useState(0);

  const selectedPreset = simulationPresets.find((preset) => preset.key === selectedPresetKey) ?? simulationPresets[0];
  const normalizedGasFractions = useMemo(() => normalizeGasFractions(builderConfig.gas_fractions), [builderConfig.gas_fractions]);
  const builderPreview = useMemo(
    () => deriveBuilderPreview({ ...builderConfig, gas_fractions: normalizedGasFractions }),
    [builderConfig, normalizedGasFractions]
  );
  const previewVisualProfile = !result || experienceMode === "builder" ? builderPreview.visual : result?.visual_physics_profile;
  const visualProfile = previewVisualProfile;
  const activeStageIndex = activeStage ? stageOrder.indexOf(activeStage) : -1;
  const progressValue = activeStageIndex >= 0 ? ((activeStageIndex + 1) / stageOrder.length) * 100 : 0;
  const stageNarrative = useMemo(
    () => stageDefinitions.find((stage) => stage.id === activeStage)?.description ?? "Pipeline standing by.",
    [activeStage]
  );
  const effectiveStage = manualStage ?? presentationStage ?? activeStage;
  const effectiveStageIndex = effectiveStage ? stageOrder.indexOf(effectiveStage) : -1;
  const sceneStage = isLoading ? activeStage : effectiveStage;
  const sceneStageProgress = clamp(stageMessageCount / 3, 0, 1);
  const heroBuilderSummary = builderPreview.summary;
  const hasSessionOutput = Boolean(result) || isLoading || Boolean(error);

  const launchSimulation = async () => {
    setError(null);
    setResult(null);
    setPresentationStage(null);
    setManualStage(null);
    setExecutionLogs([]);
    setCompletedStages([]);
    setIsStagePlaybackActive(false);
    setStageMessageCount(0);
    setIsLoading(true);

    try {
      let resolvedSimulation: SimulationResponse | null = null;
      let resolvedError: unknown = null;

      const requestPromise = runSimulation(
        experienceMode === "builder" ? buildBuilderPayload(builderConfig, normalizedGasFractions) : selectedPreset.payload
      ).then((simulation) => {
        resolvedSimulation = simulation;
        return simulation;
      }).catch((requestError) => {
        resolvedError = requestError;
        throw requestError;
      });

      for (const [index, stage] of stageExecutionTimeline.entries()) {
        setActiveStage(stage.id);
        for (const [messageIndex, message] of stage.messages.entries()) {
          setStageMessageCount(messageIndex + 1);
          setExecutionLogs((current) => [...current.slice(-7), message]);
          await wait(messageIndex === 0 ? 280 : 220);
        }
        setCompletedStages((current) => [...current, stage.id]);
        await wait(index === stageExecutionTimeline.length - 1 ? 360 : 220);
      }

      if (!resolvedSimulation && !resolvedError) {
        setActiveStage("final-discovery");
        setExecutionLogs((current) => [...current.slice(-7), "Backend pipeline finalizing response payload"]);
      }

      const simulation = await requestPromise;
      setResult(simulation);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Simulation failed.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!result) {
      setPresentationStage(null);
      setManualStage(null);
      setIsStagePlaybackActive(false);
      setStageMessageCount(0);
      return;
    }
    let cancelled = false;
    setManualStage(null);
    setPresentationStage(stageOrder[0]);
    setIsStagePlaybackActive(true);
    setStageMessageCount(0);

    const runPlayback = async () => {
      for (const stage of stageExecutionTimeline) {
        if (cancelled) {
          return;
        }
        setPresentationStage(stage.id);
        const stageDuration = STAGE_REVEAL_DURATION_MS[stage.id];
        const perMessageDelay = Math.max(180, Math.round(stageDuration / (stage.messages.length + 0.75)));
        const tailDelay = Math.max(120, stageDuration - perMessageDelay * stage.messages.length);
        for (let index = 0; index < stage.messages.length; index += 1) {
          if (cancelled) {
            return;
          }
          setStageMessageCount(index + 1);
          await wait(perMessageDelay);
        }
        await wait(tailDelay);
      }
      if (!cancelled) {
        setIsStagePlaybackActive(false);
        setManualStage(stageOrder[stageOrder.length - 1]);
        setStageMessageCount(3);
      }
    };

    runPlayback();
    return () => {
      cancelled = true;
    };
  }, [result]);

  const updateBuilderValue = <K extends keyof BuilderConfig>(key: K, value: BuilderConfig[K]) => {
    setBuilderConfig((current) => {
      const next = { ...current, [key]: value };
      if (key === "radius_rearth" && builderMode === "guided") {
        next.mass_mearth = estimateMassFromRadius(Number(value));
      }
      if (key === "orbit_zone" && builderMode === "guided") {
        next.equilibrium_temperature_k = zoneDefaultTemperature(String(value));
      }
      return next;
    });
    setResult(null);
    setPresentationStage(null);
    setActiveStage(null);
    setManualStage(null);
  };

  const updateBuilderGas = (gas: BuilderGasKey, value: number) => {
    setBuilderConfig((current) => ({
      ...current,
      gas_fractions: {
        ...current.gas_fractions,
        [gas]: value,
      },
    }));
    setResult(null);
    setPresentationStage(null);
    setActiveStage(null);
    setManualStage(null);
  };

  return (
    <main className="relative min-h-screen overflow-x-hidden overflow-y-auto bg-space-shell">
      <div className="fixed inset-0">
        <PlanetCanvas
          colors={(visualProfile?.surface_palette?.slice(0, 3) as [string, string, string]) ?? selectedPreset.planetColors}
          glowColor={visualProfile?.atmosphere_glow_color ?? selectedPreset.atmosphereGlow}
          hasRing={selectedPreset.hasRing}
          qualityMode={qualityMode}
          hostStarColor={visualProfile?.host_star_light_color ?? selectedPreset.hostStarColor}
          fillLightColor={visualProfile?.fill_light_color ?? selectedPreset.fillLightColor}
          cloudTint={visualProfile?.cloud_tint ?? selectedPreset.cloudTint}
          cloudOpacity={visualProfile?.cloud_opacity ?? selectedPreset.cloudOpacity}
          cameraDistance={visualProfile?.camera_distance ?? selectedPreset.cameraDistance}
          cameraFov={visualProfile?.camera_fov ?? 34}
          autoRotateSpeed={visualProfile?.auto_rotate_speed ?? selectedPreset.autoRotateSpeed}
          starDensity={visualProfile?.starfield_density ?? selectedPreset.starDensity}
          surfaceVariationIntensity={visualProfile?.surface_variation_intensity ?? 0.5}
          terminatorContrast={visualProfile?.terminator_contrast ?? 0.55}
          atmosphereGlowIntensity={visualProfile?.atmosphere_glow_intensity ?? 0.55}
          atmosphereRimWidth={visualProfile?.atmosphere_rim_width ?? 0.5}
          atmosphereThicknessVisual={visualProfile?.atmosphere_thickness_visual ?? 0.5}
          hazeIntensity={visualProfile?.haze_intensity ?? 0.2}
          cloudMotionSpeed={visualProfile?.cloud_motion_speed ?? 0.3}
          particleDensity={visualProfile?.particle_density ?? 1.0}
          radiationLevel={result?.profile.radiation_level ?? builderConfig.radiation_level}
          quantumChamberIntensity={visualProfile?.quantum_chamber_intensity ?? 0.5}
          spectrumAccentPalette={visualProfile?.spectrum_accent_palette ?? [selectedPreset.atmosphereGlow]}
          sceneStage={sceneStage}
          stageProgress={sceneStageProgress}
          isSequenceActive={isLoading || isStagePlaybackActive}
        />
      </div>

      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_50%_55%,transparent_0%,rgba(2,6,23,0.18)_42%,rgba(2,6,23,0.8)_100%)]" />

      <div className="relative z-10 flex min-h-screen flex-col p-4 sm:p-6 lg:p-8">
        <div className="flex items-start justify-between gap-4">
          <div className="hud-pill">QPS / Fullscreen Planet View</div>
          <div className="pointer-events-auto flex flex-wrap items-center gap-2">
            {(["Cinematic", "Balanced", "Safe"] as QualityMode[]).map((mode) => (
              <button
                key={mode}
                type="button"
                onClick={() => setQualityMode(mode)}
                className={[
                  "quality-pill",
                  qualityMode === mode ? "quality-pill-active" : "hover:border-white/20 hover:bg-white/[0.08]"
                ].join(" ")}
              >
                {mode}
              </button>
            ))}
          </div>
        </div>

        {!hasSessionOutput ? (
          <div className="mt-auto grid items-end gap-6 pb-20 lg:grid-cols-[1.05fr_0.95fr] lg:pb-24">
            <HeroScene
              preset={selectedPreset}
              mode={experienceMode}
              builderSummary={heroBuilderSummary}
              stages={stageDefinitions}
              activeStage={effectiveStage}
              onLaunch={launchSimulation}
              isLoading={isLoading}
            />

            <div className="pointer-events-auto justify-self-end lg:w-full lg:max-w-[25rem]">
              <div className="overlay-shell p-4 sm:p-5">
                <div className="section-kicker">Preset Orbit</div>
                <PresetSwitcher
                  mode={experienceMode}
                  presets={simulationPresets}
                  activePreset={selectedPreset.key}
                  onModeChange={setExperienceMode}
                  onSelect={setSelectedPresetKey}
                />
                {experienceMode === "presets" ? (
                  <div className="mt-4 text-sm leading-7 text-slate-300">{selectedPreset.description}</div>
                ) : (
                  <div className="mt-4">
                    <BuilderDeck
                      builderMode={builderMode}
                      config={builderConfig}
                      normalizedGasFractions={normalizedGasFractions}
                      validationTone={builderPreview.validationTone}
                      livePreviewSummary={builderPreview.summary}
                      onModeChange={setBuilderMode}
                      onChange={updateBuilderValue}
                      onGasChange={updateBuilderGas}
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="mt-6 flex flex-col gap-4 pb-28 lg:pb-36">
            <div className="flex items-start justify-between gap-4">
            <div className="pointer-events-auto max-w-xl">
              <div className="overlay-shell p-4 sm:p-5">
                <div className="section-kicker">Active Mission</div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="hud-pill">{experienceMode === "builder" ? "Planet Builder" : selectedPreset.title}</span>
                  <span className="hud-pill">{qualityMode}</span>
                  {effectiveStage ? <span className="hud-pill">{effectiveStage.replace("-", " ")}</span> : null}
                </div>
                <div className="mt-3 text-sm leading-7 text-slate-300">
                  {experienceMode === "builder" ? heroBuilderSummary : selectedPreset.description}
                </div>
              </div>
            </div>

              {!result && !error ? (
                <div className="pointer-events-auto justify-self-end lg:w-full lg:max-w-[25rem]">
                  <div className="overlay-shell p-4 sm:p-5">
                    <div className="section-kicker">Scenario</div>
                    <PresetSwitcher
                      mode={experienceMode}
                      presets={simulationPresets}
                      activePreset={selectedPreset.key}
                      onModeChange={setExperienceMode}
                      onSelect={setSelectedPresetKey}
                    />
                  </div>
                </div>
              ) : null}
            </div>

            <div className="flex items-start justify-between gap-4">
              <div className="hidden max-w-4xl lg:block">
                <StageStrip
                  stages={stageDefinitions}
                  activeStage={effectiveStage}
                  onSelect={
                    result && !isStagePlaybackActive
                      ? (stage) => {
                          setManualStage(stage);
                        }
                      : undefined
                  }
                />
              </div>

              <div className="pointer-events-auto w-full max-w-2xl">
                <AnimatePresence mode="wait">
                  {error ? (
                    <OverlayCard
                      key="error"
                      eyebrow="Connection Error"
                      title="Mission control lost contact with the backend."
                      body="Keep the Python API on 127.0.0.1:8000 live and relaunch the current scenario."
                      accent="amber"
                      footer={error}
                    />
                  ) : isLoading ? (
                    <LoadingOverlay
                      key="loading"
                      activeStage={activeStage}
                      progressValue={progressValue}
                      activeStageIndex={activeStageIndex}
                      stageNarrative={stageNarrative}
                      executionLogs={executionLogs}
                      completedStages={completedStages}
                    />
                  ) : result ? (
                    <ResultOverlay
                      key="result"
                      result={result}
                      stage={effectiveStage ?? "planet-birth"}
                      qualityMode={qualityMode}
                      isStagePlaybackActive={isStagePlaybackActive}
                      stageMessageCount={stageMessageCount}
                      onStageChange={setManualStage}
                      onRunAgain={launchSimulation}
                      onReset={() => {
                        setResult(null);
                        setPresentationStage(null);
                        setManualStage(null);
                        setActiveStage(null);
                        setIsStagePlaybackActive(false);
                        setStageMessageCount(0);
                      }}
                    />
                  ) : (
                    <OverlayCard
                      key="standby"
                      eyebrow="Launch Sequence"
                      title="The planet is idle, alive, and waiting for a mission profile."
                      body="Choose a cinematic preset, keep the world in view, and trigger the staged simulation without leaving orbital perspective."
                    />
                  )}
                </AnimatePresence>
              </div>
            </div>
          </div>
        )}

        {!hasSessionOutput ? (
          <div className="mt-auto flex items-end justify-between gap-4 pb-24">
            <div className="hidden max-w-4xl lg:block">
              <StageStrip
                stages={stageDefinitions}
                activeStage={effectiveStage}
                onSelect={
                  result && !isStagePlaybackActive
                    ? (stage) => {
                        setManualStage(stage);
                      }
                    : undefined
                }
              />
            </div>

            <div className="pointer-events-auto w-full max-w-2xl">
              <AnimatePresence mode="wait">
                {error ? (
                  <OverlayCard
                    key="error"
                    eyebrow="Connection Error"
                    title="Mission control lost contact with the backend."
                    body="Keep the Python API on 127.0.0.1:8000 live and relaunch the current scenario."
                    accent="amber"
                    footer={error}
                  />
                ) : isLoading ? (
                  <LoadingOverlay
                    key="loading"
                    activeStage={activeStage}
                    progressValue={progressValue}
                    activeStageIndex={activeStageIndex}
                    stageNarrative={stageNarrative}
                    executionLogs={executionLogs}
                    completedStages={completedStages}
                  />
                ) : result ? (
                  <ResultOverlay
                    key="result"
                    result={result}
                    stage={effectiveStage ?? "planet-birth"}
                    qualityMode={qualityMode}
                    isStagePlaybackActive={isStagePlaybackActive}
                    stageMessageCount={stageMessageCount}
                    onStageChange={setManualStage}
                    onRunAgain={launchSimulation}
                    onReset={() => {
                      setResult(null);
                      setPresentationStage(null);
                      setManualStage(null);
                      setActiveStage(null);
                      setIsStagePlaybackActive(false);
                      setStageMessageCount(0);
                    }}
                  />
                ) : (
                  <OverlayCard
                    key="standby"
                    eyebrow="Launch Sequence"
                    title="The planet is idle, alive, and waiting for a mission profile."
                    body="Choose a cinematic preset, keep the world in view, and trigger the staged simulation without leaving orbital perspective."
                  />
                )}
              </AnimatePresence>
            </div>
          </div>
        ) : null}
        <div className="absolute bottom-3 left-1/2 hidden w-[min(1080px,calc(100vw-2rem))] -translate-x-1/2 lg:block">
          <div className="mx-auto max-w-5xl rounded-full border border-white/10 bg-black/25 px-3 py-2 backdrop-blur-xl">
            <div className="flex items-center justify-between gap-2">
              {stageDefinitions.map((stage, index) => {
                const isActive = effectiveStage === stage.id;
                const isResolved = effectiveStageIndex > index;

                return (
                  <button
                    key={stage.id}
                    type="button"
                    onClick={() => result && !isStagePlaybackActive && setManualStage(stage.id)}
                    className="pointer-events-auto flex min-w-0 flex-1 items-center gap-2 text-left"
                  >
                    <div
                      className={[
                        "h-2 w-2 shrink-0 rounded-full transition",
                        isActive
                          ? "bg-white shadow-glow"
                          : isResolved
                            ? "bg-emerald-300"
                            : "bg-white/20"
                      ].join(" ")}
                    />
                    <div
                      className={[
                        "truncate text-[10px] uppercase tracking-[0.22em] transition",
                        isActive ? "text-white" : isResolved ? "text-emerald-100" : "text-slate-500"
                      ].join(" ")}
                    >
                      {stage.title}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

function OverlayCard({
  eyebrow,
  title,
  body,
  footer,
  accent = "sky"
}: {
  eyebrow: string;
  title: string;
  body: string;
  footer?: string;
  accent?: "sky" | "amber";
}) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 16 }}
      className={[
        "overlay-shell p-5 sm:p-6",
        accent === "amber" ? "border-amber-200/20" : "border-white/10"
      ].join(" ")}
    >
      <div className="section-kicker">{eyebrow}</div>
      <h2 className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">{title}</h2>
      <p className="overlay-copy mt-4">{body}</p>
      {footer ? <div className="mt-4 text-sm text-amber-200">{footer}</div> : null}
    </motion.section>
  );
}

function LoadingOverlay({
  activeStage,
  progressValue,
  activeStageIndex,
  stageNarrative,
  executionLogs,
  completedStages,
}: {
  activeStage: StageId | null;
  progressValue: number;
  activeStageIndex: number;
  stageNarrative: string;
  executionLogs: string[];
  completedStages: StageId[];
}) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 16 }}
      className="overlay-shell p-5 sm:p-6"
    >
      <div className="section-kicker">Simulation Sequence</div>
      <h2 className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">
        {activeStage
          ? stageDefinitions.find((stage) => stage.id === activeStage)?.title
          : "Preparing orbital synthesis"}
      </h2>
      <p className="overlay-copy mt-4">{stageNarrative}</p>
      <div className="mt-5 progress-rail">
        <motion.div
          className="progress-fill"
          animate={{ width: `${progressValue}%` }}
          transition={{ duration: 0.45, ease: "easeOut" }}
        />
      </div>
      <div className="mt-3 flex items-center justify-between text-[11px] uppercase tracking-[0.24em] text-slate-400">
        <span>Pipeline Active</span>
        <span>{Math.max(activeStageIndex + 1, 0)} / {stageOrder.length}</span>
      </div>
      <div className="mt-5 flex flex-wrap gap-2">
        {stageDefinitions.map((stage, index) => {
          const isCurrent = activeStage === stage.id;
          const isComplete = completedStages.includes(stage.id) || activeStageIndex > index;
          return (
            <span
              key={stage.id}
              className={[
                "rounded-full px-3 py-2 text-[11px] uppercase tracking-[0.24em]",
                isCurrent
                  ? "bg-sky-300/15 text-white shadow-glow"
                  : isComplete
                    ? "bg-emerald-300/12 text-emerald-100"
                    : "bg-white/[0.05] text-slate-400"
              ].join(" ")}
            >
              {stage.title}
            </span>
          );
        })}
      </div>
      <div className="mt-5 rounded-3xl border border-white/10 bg-black/20 p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="text-[11px] uppercase tracking-[0.24em] text-sky-200/70">Execution Log</div>
          <div className="text-[11px] uppercase tracking-[0.24em] text-slate-500">
            {completedStages.length} completed
          </div>
        </div>
        <div className="mt-3 space-y-2">
          {executionLogs.length ? (
            executionLogs.map((message, index) => {
              const isLatest = index === executionLogs.length - 1;
              return (
                <motion.div
                  key={`${message}-${index}`}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={[
                    "rounded-2xl border px-3 py-2 text-sm",
                    isLatest
                      ? "border-sky-300/25 bg-sky-300/8 text-slate-100"
                      : "border-white/8 bg-white/[0.03] text-slate-400"
                  ].join(" ")}
                >
                  {message}
                </motion.div>
              );
            })
          ) : (
            <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-3 py-2 text-sm text-slate-400">
              Waiting for mission execution timeline to initialize.
            </div>
          )}
        </div>
      </div>
    </motion.section>
  );
}

function ResultOverlay({
  result,
  stage,
  qualityMode,
  isStagePlaybackActive,
  stageMessageCount,
  onStageChange,
  onRunAgain,
  onReset,
}: {
  result: SimulationResponse;
  stage: StageId;
  qualityMode: QualityMode;
  isStagePlaybackActive: boolean;
  stageMessageCount: number;
  onStageChange: (stage: StageId) => void;
  onRunAgain: () => void;
  onReset: () => void;
}) {
  const quantumSource = result.quantum?.source ?? "fallback";
  const confidence = result.final_report?.confidence_score ?? result.quantum?.confidence_score ?? 0.72;
  const tone = result.visual_physics_profile.validation_overlay_tone;
  const disclaimers = result.scientific_proxy_profile.scientific_disclaimers.slice(0, 2);
  const observationMode = result.scientific_proxy_profile.observation_confidence_mode.replace("-", " ");
  const isDiscoveryStage = stage === "final-discovery";
  const visibleStageMessages = getVisibleStageMessages(stage, stageMessageCount);

  return (
    <div className="space-y-4">
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="overlay-shell p-4"
      >
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="section-kicker mb-1">Mission Control</div>
            <div className="text-sm text-slate-300">
              {isStagePlaybackActive
                ? "Scientific playback is unfolding stage by stage while the planet remains in view."
                : "Review any stage from the strip below and relaunch without refreshing the scene."}
            </div>
          </div>
          <div className="flex gap-2">
            <button type="button" onClick={onRunAgain} className="preset-pill preset-pill-active">
              Run Again
            </button>
            <button type="button" onClick={onReset} className="preset-pill hover:border-white/20 hover:bg-white/[0.08]">
              Clear Results
            </button>
          </div>
        </div>
      </motion.section>
      {isStagePlaybackActive ? (
        <PlaybackOverlayPanel
          stage={stage}
          messages={visibleStageMessages}
          progressLabel={`${Math.min(stageMessageCount, 3)} / 3`}
        />
      ) : (
        <>
          <StageReviewPanel result={result} stage={stage} onStageChange={onStageChange} />
          <AnimatePresence>
            {isDiscoveryStage ? (
              <motion.section
                initial={{ opacity: 0, y: 28, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 16 }}
                className={[
                  "overlay-shell relative max-h-[44vh] overflow-hidden p-5 sm:p-6 lg:overflow-y-auto",
                  tone === "critical" ? "border-rose-300/25" : tone === "watch" ? "border-amber-300/25" : "border-sky-300/20"
                ].join(" ")}
              >
                <div className="absolute inset-0 bg-[linear-gradient(120deg,transparent_0%,rgba(255,255,255,0.06)_45%,transparent_70%)] animate-sheen" />
                <div className="relative">
                  <div className="section-kicker">Final Discovery</div>
                  <h2 className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">
                    {result.final_report?.discovery_headline ?? "Discovery report available from the backend pipeline."}
                  </h2>
                  <p className="overlay-copy mt-4">
                    {result.final_report?.discovery_summary ??
                      "The cinematic shell is connected. The backend already returns a final narrative report that can power the rest of the reveal."}
                  </p>
                  <div className="mt-5 flex flex-wrap gap-2">
                    <span className="hud-pill">{result.profile.planet_name}</span>
                    <span className="hud-pill">{result.quantum?.formula ?? "N/A"}</span>
                    <span className="hud-pill">Confidence {(confidence * 100).toFixed(0)}%</span>
                    <span className="hud-pill">{observationMode}</span>
                    <span className="hud-pill">{tone} analysis</span>
                    <span
                      className={[
                        "hud-pill",
                        quantumSource === "live"
                          ? "border-emerald-300/30 text-emerald-100"
                          : quantumSource === "cached"
                            ? "border-sky-300/30 text-sky-100"
                            : "border-amber-300/30 text-amber-100"
                      ].join(" ")}
                    >
                      Quantum {quantumSource}
                    </span>
                  </div>
                  <div className="mt-5 space-y-3">
                    {(result.final_report?.key_highlights ?? []).slice(0, 3).map((highlight) => (
                      <div
                        key={highlight}
                        className="rounded-2xl border border-white/10 bg-slate-950/35 px-4 py-3 text-sm text-slate-300"
                      >
                        {highlight}
                      </div>
                    ))}
                  </div>
                  <div className="mt-5 flex items-center justify-between gap-4">
                    <div>
                      <div className="text-[11px] uppercase tracking-[0.24em] text-sky-200/70">Novelty Tagline</div>
                      <div className="mt-2 text-lg font-medium text-white">
                        {result.final_report?.novelty_tagline ?? "Synthetic evidence assembled for a stable reveal."}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-[11px] uppercase tracking-[0.24em] text-slate-400">Selected Signal</div>
                      <div className="mt-2 text-3xl font-semibold text-white">{result.quantum?.formula ?? "N/A"}</div>
                    </div>
                  </div>
                  <div className="mt-4 grid gap-2">
                    {disclaimers.map((disclaimer) => (
                      <div key={disclaimer} className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-xs leading-6 text-slate-400">
                        {disclaimer}
                      </div>
                    ))}
                  </div>
                </div>
              </motion.section>
            ) : null}
          </AnimatePresence>
        </>
      )}

      <PlanetStageExperience
        result={result}
        stage={stage}
        revealCount={stageMessageCount}
        isActive={isStagePlaybackActive}
        qualityMode={qualityMode}
      />
    </div>
  );
}

function PlaybackOverlayPanel({
  stage,
  messages,
  progressLabel,
}: {
  stage: StageId;
  messages: string[];
  progressLabel: string;
}) {
  const stageDefinition = stageDefinitions.find((item) => item.id === stage);

  return (
    <motion.section
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      className="overlay-shell p-4 sm:p-5"
    >
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="section-kicker">{stageDefinition?.eyebrow ?? "Stage"}</div>
          <div className="text-xl font-semibold text-white">{stageDefinition?.title ?? "Simulation Stage"}</div>
        </div>
        <div className="hud-pill">{progressLabel}</div>
      </div>
      <p className="mt-3 text-sm leading-7 text-slate-300">
        {stageDefinition?.description ?? "Stage reveal in progress."}
      </p>
      <div className="mt-4 space-y-2">
        {messages.map((message, index) => (
          <motion.div
            key={`${message}-${index}`}
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            className={[
              "rounded-2xl border px-4 py-3 text-sm",
              index === messages.length - 1
                ? "border-sky-300/25 bg-sky-300/8 text-slate-100"
                : "border-white/8 bg-white/[0.03] text-slate-400"
            ].join(" ")}
          >
            {message}
          </motion.div>
        ))}
      </div>
    </motion.section>
  );
}

function StageReviewPanel({
  result,
  stage,
  onStageChange,
}: {
  result: SimulationResponse;
  stage: StageId;
  onStageChange: (stage: StageId) => void;
}) {
  const currentIndex = stageOrder.indexOf(stage);
  const review = getStageReview(result, stage);

  return (
    <motion.section
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      className="overlay-shell max-h-[48vh] overflow-y-auto p-4 sm:p-5"
    >
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="section-kicker mb-1">Stage Review</div>
          <div className="text-lg font-semibold text-white">{review.title}</div>
        </div>
        <div className="hud-pill">{stage.replace("-", " ")}</div>
      </div>
      <p className="mt-3 text-sm leading-7 text-slate-300">{review.summary}</p>
      <div className="mt-4 grid gap-2">
        {review.lines.map((line) => (
          <div key={line} className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-slate-300">
            {line}
          </div>
        ))}
      </div>
      <div className="mt-4 flex items-center justify-between gap-3">
        <button
          type="button"
          disabled={currentIndex <= 0}
          onClick={() => onStageChange(stageOrder[Math.max(0, currentIndex - 1)])}
          className="preset-pill disabled:cursor-not-allowed disabled:opacity-40"
        >
          Previous
        </button>
        <div className="text-[11px] uppercase tracking-[0.22em] text-slate-400">
          {currentIndex + 1} / {stageOrder.length}
        </div>
        <button
          type="button"
          disabled={currentIndex >= stageOrder.length - 1}
          onClick={() => onStageChange(stageOrder[Math.min(stageOrder.length - 1, currentIndex + 1)])}
          className="preset-pill disabled:cursor-not-allowed disabled:opacity-40"
        >
          Next
        </button>
      </div>
    </motion.section>
  );
}

function getVisibleStageMessages(stage: StageId, count: number) {
  const timeline = stageExecutionTimeline.find((item) => item.id === stage);
  if (!timeline) {
    return [];
  }
  return timeline.messages.slice(0, Math.max(1, Math.min(timeline.messages.length, count)));
}

function PlanetStageExperience({
  result,
  stage,
  revealCount,
  isActive,
  qualityMode,
}: {
  result: SimulationResponse;
  stage: StageId;
  revealCount: number;
  isActive: boolean;
  qualityMode: QualityMode;
}) {
  if (!isActive) {
    return null;
  }

  if (stage === "planet-birth") {
    return <PlanetBirthOverlay result={result} revealCount={revealCount} />;
  }
  if (stage === "atmospheric-validation") {
    return <AtmosphereOverlay result={result} revealCount={revealCount} />;
  }
  if (stage === "chemistry-emergence") {
    return <ChemistryOrbitOverlay result={result} revealCount={revealCount} />;
  }
  if (stage === "quantum-evaluation") {
    return <QuantumChamberOverlay result={result} revealCount={revealCount} qualityMode={qualityMode} />;
  }
  if (stage === "spectrum-reveal") {
    return <SpectrumOverlay result={result} revealCount={revealCount} qualityMode={qualityMode} />;
  }
  return <DiscoveryStageHalo result={result} />;
}

function PlanetBirthOverlay({
  result,
  revealCount,
}: {
  result: SimulationResponse;
  revealCount: number;
}) {
  const visual = result.visual_physics_profile;
  const items = [
    `Stabilizing ${result.profile.planet_name}`,
    `Radius ${result.profile.radius_rearth.toFixed(2)} R⊕ • Mass ${result.profile.mass_mearth.toFixed(2)} M⊕`,
    `${result.profile.star_type} illumination locked • ${result.profile.orbit_zone} orbit`
  ].slice(0, Math.max(1, revealCount));

  return (
    <motion.section
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      className="pointer-events-none absolute left-1/2 top-[20%] hidden w-[min(540px,calc(100vw-4rem))] -translate-x-1/2 lg:block"
    >
      <div
        className="rounded-[2rem] border border-white/10 bg-black/28 px-6 py-5 text-center backdrop-blur-xl"
        style={{ boxShadow: `0 0 32px ${hexToRgba(visual.host_star_light_color, 0.12)}` }}
      >
        <div className="section-kicker">Planet Initialization</div>
        <div className="mt-2 text-3xl font-semibold tracking-tight text-white">Worldframe Stabilizing</div>
        <div className="mt-5 space-y-2">
          {items.map((item, index) => (
            <motion.div
              key={item}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.08 }}
              className="rounded-2xl border border-white/8 bg-white/[0.04] px-4 py-3 text-sm text-slate-200"
            >
              {item}
            </motion.div>
          ))}
        </div>
      </div>
    </motion.section>
  );
}

function getStageReview(result: SimulationResponse, stage: StageId) {
  if (stage === "planet-birth") {
    return {
      title: "Planet Initialization",
      summary: `${result.profile.planet_name} emerges as a ${result.profile.orbit_zone} world around a ${result.profile.star_type} star.`,
      lines: [
        `Radius ${result.profile.radius_rearth.toFixed(2)} R⊕ • Mass ${result.profile.mass_mearth.toFixed(2)} M⊕`,
        `Equilibrium temperature ${result.profile.equilibrium_temperature_k.toFixed(0)} K • Radiation ${result.profile.radiation_level.toFixed(2)}`,
        `Pressure ${result.profile.atmosphere.pressure_bar.toFixed(2)} bar • Dominant gases ${result.profile.atmosphere.dominant_gases.slice(0, 3).join(", ")}`,
      ],
    };
  }
  if (stage === "atmospheric-validation") {
    return {
      title: "Atmospheric Model",
      summary: `Plausibility score ${result.validation.score.toFixed(2)} with ${result.scientific_proxy_profile.atmospheric_clarity_mode.replace("-", " ")} atmospheric clarity.`,
      lines: result.validation.issues.length
        ? result.validation.issues.slice(0, 3).map((issue) => issue.message)
        : [
            `Scale height proxy ${result.scientific_proxy_profile.scale_height_proxy.toFixed(2)}x Earth baseline`,
            `Cloud / haze factor ${(result.scientific_proxy_profile.cloud_haze_factor * 100).toFixed(0)}%`,
            `Spectral visibility ${(result.scientific_proxy_profile.spectral_visibility_score * 100).toFixed(0)}%`,
          ],
    };
  }
  if (stage === "chemistry-emergence") {
    return {
      title: "Chemistry Engine",
      summary: `Rule-based chemistry shortlist resolved to ${result.chemistry.chemistry_mode_summary}.`,
      lines: result.chemistry.candidates.slice(0, 3).map(
        (candidate) => `${candidate.formula} • score ${candidate.classical_score.toFixed(2)} • ${candidate.tag}`
      ),
    };
  }
  if (stage === "quantum-evaluation") {
    return {
      title: "Quantum Evaluation",
      summary: `${result.quantum?.formula ?? "No candidate"} evaluated with ${result.quantum?.source ?? "fallback"} source.`,
      lines: [
        `Ground-state proxy ${result.quantum?.ground_state_energy_proxy.toFixed(3) ?? "n/a"}`,
        `Stability ${(100 * (result.quantum?.stability_score ?? 0)).toFixed(0)}% • Confidence ${(100 * (result.quantum?.confidence_score ?? 0)).toFixed(0)}%`,
        `Baseline agreement ${(100 * (result.quantum?.baseline_agreement_score ?? 0)).toFixed(0)}% • ${result.quantum?.verification_mode?.replace(/_/g, " ") ?? "proxy verification"}`,
      ],
    };
  }
  if (stage === "spectrum-reveal") {
    return {
      title: "Spectrum Simulation",
      summary: result.spectrum?.summary_text ?? "Synthetic transmission spectrum available.",
      lines:
        result.spectrum?.highlighted_features.slice(0, 3).map(
          (feature) => `${feature.label} at ${feature.wavelength_um.toFixed(2)} μm • strength ${feature.strength.toFixed(2)}`
        ) ?? [],
    };
  }
  return {
    title: "Discovery Report",
    summary: result.final_report?.discovery_summary ?? result.report_summary,
    lines: [
      ...(result.final_report?.key_highlights ?? []).slice(0, 3),
      `Confidence ${(100 * (result.final_report?.confidence_score ?? 0)).toFixed(0)}%`,
    ],
  };
}

function AtmosphereOverlay({ result, revealCount }: { result: SimulationResponse; revealCount: number }) {
  const visual = result.visual_physics_profile;
  const scientific = result.scientific_proxy_profile;
  const gases = Object.entries(result.profile.atmosphere.gas_fractions)
    .sort(([, left], [, right]) => right - left)
    .slice(0, Math.max(1, Math.min(4, revealCount + 1)));
  const tone = visual.validation_overlay_tone;
  const chemistryModes = result.chemistry.chemistry_modes.slice(0, 3);
  const clarityMode = scientific.atmospheric_clarity_mode.replace("-", " ");
  const observationMode = scientific.observation_confidence_mode.replace("-", " ");

  return (
    <motion.section
      initial={{ opacity: 0, x: -24 }}
      animate={{ opacity: 1, x: 0 }}
      className="pointer-events-auto absolute left-6 top-[22%] hidden w-[272px] lg:block"
    >
      <div
        className={[
          "overlay-shell p-5",
          tone === "critical" ? "border-rose-300/25" : tone === "watch" ? "border-amber-300/25" : "border-sky-300/20"
        ].join(" ")}
      >
        <div className="section-kicker">Atmospheric Validation</div>
        <div className="text-xl font-semibold text-white">Composition Envelope</div>
        <div className="mt-5 grid place-items-center">
          <div
            className="relative grid place-items-center rounded-full bg-black/30"
            style={{
              width: `${136 + visual.atmosphere_thickness_visual * 44}px`,
              height: `${136 + visual.atmosphere_thickness_visual * 44}px`,
              border: `1px solid ${hexToRgba(visual.atmosphere_glow_color, 0.28)}`,
              boxShadow: `0 0 ${18 + visual.haze_intensity * 26}px ${hexToRgba(visual.atmosphere_glow_color, 0.22)}`
            }}
          >
            <div
              className="absolute inset-3 rounded-full"
              style={{
                background: `conic-gradient(${visual.atmosphere_glow_color} 0 ${gasSpan(gases, 0)}deg, #fbbf24 ${gasSpan(
                  gases,
                  0
                )}deg ${gasSpan(gases, 1)}deg, #86efac ${gasSpan(gases, 1)}deg ${gasSpan(
                  gases,
                  2
                )}deg, #c4b5fd ${gasSpan(gases, 2)}deg 360deg)`
              }}
            />
            <div className="absolute inset-7 rounded-full bg-slate-950/95" />
            <div className="relative text-center">
              <div className="text-[11px] uppercase tracking-[0.24em] text-slate-400">Visibility</div>
              <div className="mt-1 text-2xl font-semibold text-white">
                {(scientific.spectral_visibility_score * 100).toFixed(0)}%
              </div>
            </div>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <span className="hud-pill">Scale {scientific.scale_height_proxy.toFixed(2)}x</span>
          <span className="hud-pill">Haze {(scientific.cloud_haze_factor * 100).toFixed(0)}%</span>
          <span className="hud-pill">{clarityMode}</span>
          <span className="hud-pill">{observationMode}</span>
        </div>
        <div className="mt-5 space-y-3">
          {gases.map(([gas, fraction], index) => (
            <div key={gas} className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3">
              <div className="flex items-center justify-between text-sm text-slate-200">
                <span>{gas}</span>
                <span>{(fraction * 100).toFixed(0)}%</span>
              </div>
              <div className="mt-2 h-1.5 rounded-full bg-white/10">
                <motion.div
                  className="h-full rounded-full"
                  style={{ background: `linear-gradient(90deg, ${visual.atmosphere_glow_color}, ${visual.spectrum_accent_palette[1] ?? "#fde68a"})` }}
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.max(8, fraction * 100)}%` }}
                  transition={{ duration: 0.6, delay: 0.08 * index }}
                />
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {chemistryModes.map((mode) => (
            <span key={mode} className="floating-chip text-[10px]">
              {mode}
            </span>
          ))}
        </div>
        {scientific.observation_risk_notes[0] ? (
          <div className="mt-4 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-xs leading-6 text-slate-400">
            {scientific.observation_risk_notes[0]}
          </div>
        ) : null}
      </div>
    </motion.section>
  );
}

function ChemistryOrbitOverlay({ result, revealCount }: { result: SimulationResponse; revealCount: number }) {
  const visual = result.visual_physics_profile;
  const scientific = result.scientific_proxy_profile;
  const candidates = result.chemistry.candidates.slice(0, Math.max(1, Math.min(5, revealCount + 2)));
  const selected = new Set(result.chemistry.selected_for_quantum.map((candidate) => candidate.formula));
  const lockedFormula = result.selected_candidate?.formula ?? result.quantum?.formula ?? null;
  const placements = [
    "left-[16%] top-[22%]",
    "left-[24%] top-[48%]",
    "right-[21%] top-[26%]",
    "right-[14%] top-[46%]",
    "left-[48%] top-[18%]"
  ];

  return (
    <div className="pointer-events-none absolute inset-0 hidden lg:block">
      {candidates.map((candidate, index) => (
        <motion.div
          key={candidate.formula}
          initial={{ opacity: 0, scale: 0.88, y: 12 }}
          animate={{
            opacity: 1,
            scale: selected.has(candidate.formula) && revealCount >= 3 ? 1.08 : 1,
            y: [0, -4 - visual.cloud_motion_speed * 10, 0]
          }}
          transition={{ delay: 0.1 * index, duration: 3.2 + index * 0.35, repeat: Infinity, ease: "easeInOut" }}
          className={["absolute", placements[index] ?? "left-1/2 top-1/2"].join(" ")}
        >
          <div
            className={[
              "floating-chip pointer-events-auto",
              selected.has(candidate.formula) ? "floating-chip-selected" : ""
            ].join(" ")}
            style={selected.has(candidate.formula) ? { boxShadow: `0 0 ${18 + visual.quantum_chamber_intensity * 22}px ${hexToRgba(visual.atmosphere_glow_color, 0.34)}` } : undefined}
          >
            <div className="text-[10px] tracking-[0.22em] text-slate-400">
              {selected.has(candidate.formula) && revealCount >= 3 ? "Locked Candidate" : "Candidate"}
            </div>
            <div className="mt-1 text-lg font-semibold text-white">{candidate.formula}</div>
            <div className="mt-1 text-[10px] uppercase tracking-[0.22em] text-slate-500">
              {lockedFormula === candidate.formula && revealCount >= 3 ? "locked for quantum" : candidate.tag}
            </div>
          </div>
        </motion.div>
      ))}
      <div className="pointer-events-auto absolute right-6 top-[56%] hidden w-[248px] xl:block">
        <div className="overlay-shell p-4">
          <div className="section-kicker">Chemistry State</div>
          <div className="grid gap-2">
            <ProxyMeter label="Oxidation" value={Math.abs(scientific.oxidation_index_proxy) * 100} accent={visual.atmosphere_glow_color} />
            <ProxyMeter label="Carbon" value={scientific.carbon_richness_proxy * 100} accent={visual.spectrum_accent_palette[1] ?? "#fde68a"} />
            <ProxyMeter label="Nitrogen" value={scientific.nitrogen_richness_proxy * 100} accent={visual.spectrum_accent_palette[2] ?? "#c4b5fd"} />
          </div>
        </div>
      </div>
    </div>
  );
}

function QuantumChamberOverlay({
  result,
  revealCount,
  qualityMode,
}: {
  result: SimulationResponse;
  revealCount: number;
  qualityMode: QualityMode;
}) {
  const visual = result.visual_physics_profile;
  const confidence = (result.quantum?.confidence_score ?? 0.72) * 100;
  const stability = (result.quantum?.stability_score ?? 0.68) * 100;
  const agreement = (result.quantum?.baseline_agreement_score ?? 0.58) * 100;
  const source = result.quantum?.source ?? "fallback";
  const sourceTone = source === "live" ? "#86efac" : source === "cached" ? "#67d3ff" : "#fbbf24";
  const sourceHalo = source === "live" ? "#f8fafc" : source === "cached" ? visual.atmosphere_glow_color : "#f59e0b";
  const cinematicGlow = qualityMode === "Cinematic";

  return (
    <div className="pointer-events-none absolute inset-0 hidden lg:block">
      <motion.div
        className="absolute left-1/2 top-1/2 h-[8rem] w-[8rem] -translate-x-1/2 -translate-y-1/2 rounded-full blur-[55px]"
        style={{ backgroundColor: hexToRgba(sourceHalo, 0.16 + visual.quantum_chamber_intensity * 0.08) }}
        animate={{ scale: [1, 1.12, 1], opacity: [0.55, 0.82, 0.55] }}
        transition={{ duration: 2.6, repeat: Infinity, ease: "easeInOut" }}
      />
      <div className="analysis-ring h-[360px] w-[360px] opacity-60" style={{ borderColor: hexToRgba(sourceTone, 0.35), boxShadow: `0 0 24px ${hexToRgba(sourceTone, 0.2)}` }} />
      <motion.div
        className="analysis-ring h-[430px] w-[430px] opacity-35"
        style={{ borderColor: hexToRgba(sourceTone, 0.28) }}
        animate={{ rotate: 360 }}
        transition={{ duration: 30 - visual.quantum_ring_speed * 12, repeat: Infinity, ease: "linear" }}
      />
      <motion.div
        className="analysis-ring h-[520px] w-[520px] opacity-20"
        style={{ borderColor: hexToRgba(sourceTone, 0.18) }}
        animate={{ rotate: -360 }}
        transition={{ duration: 38 - visual.quantum_ring_speed * 14, repeat: Infinity, ease: "linear" }}
      />
      <motion.div
        className="analysis-ring h-[310px] w-[310px] opacity-45"
        style={{ borderColor: hexToRgba(sourceHalo, 0.22), borderStyle: "dashed" }}
        animate={{ rotate: 360, scale: [0.98, 1.02, 0.98] }}
        transition={{ rotate: { duration: 18, repeat: Infinity, ease: "linear" }, scale: { duration: 3.4, repeat: Infinity, ease: "easeInOut" } }}
      />
      <motion.section
        initial={{ opacity: 0, scale: 0.92 }}
        animate={{ opacity: 1, scale: 1 }}
        className="pointer-events-auto absolute left-1/2 top-[56%] w-[308px] -translate-x-1/2 -translate-y-1/2"
      >
        <div
          className="overlay-shell p-5 text-center"
          style={{
            boxShadow: `0 0 ${26 + visual.quantum_chamber_intensity * 30}px ${hexToRgba(sourceTone, cinematicGlow ? 0.28 : 0.22)}`
          }}
        >
          <div className="section-kicker">Quantum Evaluation</div>
          <div className="text-5xl font-semibold tracking-tight text-white">{result.quantum?.formula ?? "N/A"}</div>
          <div
            className={[
              "mx-auto mt-3 inline-flex rounded-full px-4 py-2 text-[11px] uppercase tracking-[0.24em]",
              source === "live"
                ? "bg-emerald-300/14 text-emerald-100"
                : source === "cached"
                  ? "bg-sky-300/14 text-sky-100"
                  : "bg-amber-300/14 text-amber-100"
            ].join(" ")}
          >
            {source} source
          </div>
          <div className="mt-5 space-y-4 text-left">
            {revealCount >= 1 ? <GaugeBar label="Stability" value={stability} accent={sourceTone} /> : null}
            {revealCount >= 2 ? <GaugeBar label="Confidence" value={confidence} accent={sourceTone} /> : null}
            {revealCount >= 3 ? <GaugeBar label="Baseline Agreement" value={agreement} accent={sourceTone} /> : null}
          </div>
          {revealCount >= 3 ? (
            <div className="mt-4 text-[11px] uppercase tracking-[0.22em] text-slate-400">
              {result.quantum?.verification_mode?.replace(/_/g, " ") ?? "proxy verification"}
            </div>
          ) : null}
        </div>
      </motion.section>
    </div>
  );
}

function SpectrumOverlay({
  result,
  revealCount,
  qualityMode,
}: {
  result: SimulationResponse;
  revealCount: number;
  qualityMode: QualityMode;
}) {
  if (!result.spectrum) {
    return null;
  }

  const visual = result.visual_physics_profile;
  const scientific = result.scientific_proxy_profile;
  const values = result.spectrum.absorption_values;
  const wavelengths = result.spectrum.wavelengths;
  const clarityLabel = (result.spectrum.metadata.atmospheric_clarity_mode ?? scientific.atmospheric_clarity_mode).replace("-", " ");
  const observationLabel = (result.spectrum.metadata.observation_confidence_mode ?? scientific.observation_confidence_mode).replace("-", " ");
  const min = Math.min(...values);
  const max = Math.max(...values);
  const width = 760;
  const height = 170;
  const revealWidth = `${Math.max(12, Math.min(100, revealCount * 34))}%`;
  const cinematicGlow = qualityMode === "Cinematic";

  const points = values
    .map((value, index) => {
      const x = (index / Math.max(values.length - 1, 1)) * width;
      const normalized = (value - min) / Math.max(max - min, 0.0001);
      const y = height - normalized * 110 - 24;
      return `${x},${y}`;
    })
    .join(" ");

  const area = `0,${height} ${points} ${width},${height}`;

  return (
    <motion.section
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      className="pointer-events-auto absolute bottom-5 left-1/2 w-[min(920px,calc(100vw-2rem))] -translate-x-1/2"
    >
      <div
        className="overlay-shell overflow-hidden border-sky-300/15 bg-black/40 p-5"
        style={cinematicGlow ? { boxShadow: `0 0 34px ${hexToRgba(visual.spectrum_accent_palette[0] ?? "#7dd3fc", 0.12)}` } : undefined}
      >
        <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(103,211,255,0.05),transparent_25%,transparent_70%,rgba(2,6,23,0.24))]" />
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="section-kicker">Spectrum Reveal</div>
            <div className="text-2xl font-semibold text-white">Transmission Scan</div>
            <div className="mt-2 max-w-2xl text-sm leading-7 text-slate-300">
              {result.spectrum.summary_text}
            </div>
          </div>
          <div className="hidden flex-wrap gap-2 lg:flex">
            <span className="floating-chip">{clarityLabel}</span>
            <span className="floating-chip">{observationLabel}</span>
            {result.spectrum.highlighted_features.slice(0, 3).map((feature) => (
              <span key={`${feature.label}-${feature.wavelength_um}`} className="floating-chip">
                {feature.label}
              </span>
            ))}
          </div>
        </div>
        <div className="relative mt-5 rounded-[1.5rem] border border-white/10 bg-black/35 p-4">
          <motion.div
            className="pointer-events-none absolute inset-y-4 top-4 w-[12%] rounded-[1rem] bg-[linear-gradient(90deg,transparent_0%,rgba(125,211,252,0.08)_50%,transparent_100%)]"
            initial={{ x: "-25%" }}
            animate={{ x: "820%" }}
            transition={{ duration: 1.8, ease: "easeInOut" }}
          />
          <div className="mb-3 h-0.5 overflow-hidden rounded-full bg-white/10">
            <motion.div
              className="h-full"
              style={{
                background: `linear-gradient(90deg, transparent, ${visual.spectrum_accent_palette[0] ?? "#7dd3fc"}, transparent)`
              }}
              initial={{ x: "-100%" }}
              animate={{ x: "220%" }}
              transition={{ duration: 1.4, ease: "easeInOut" }}
            />
          </div>
          <div className="overflow-hidden" style={{ width: revealWidth }}>
            <svg viewBox={`0 0 ${width} ${height}`} className="h-[180px] w-full min-w-[760px]">
            <defs>
              <linearGradient id="spectrumStroke" x1="0%" x2="100%">
                <stop offset="0%" stopColor={visual.spectrum_accent_palette[0] ?? "#7dd3fc"} />
                <stop offset="50%" stopColor={visual.spectrum_accent_palette[1] ?? "#fef08a"} />
                <stop offset="100%" stopColor={visual.spectrum_accent_palette[2] ?? "#c4b5fd"} />
              </linearGradient>
              <linearGradient id="spectrumFill" x1="0%" x2="0%" y1="0%" y2="100%">
                <stop offset="0%" stopColor={hexToRgba(visual.spectrum_accent_palette[0] ?? "#7dd3fc", 0.35)} />
                <stop offset="100%" stopColor={hexToRgba(visual.spectrum_accent_palette[0] ?? "#7dd3fc", 0.02)} />
              </linearGradient>
            </defs>
            {revealCount >= 1 ? <polygon points={area} fill="url(#spectrumFill)" /> : null}
            {revealCount >= 1 ? (
              <polyline
                fill="none"
                stroke="url(#spectrumStroke)"
                strokeWidth="3"
                strokeLinejoin="round"
                strokeLinecap="round"
                points={points}
              />
            ) : null}
            {result.spectrum.highlighted_features.slice(0, Math.max(0, Math.min(4, revealCount))).map((feature) => {
              const idx = nearestIndex(wavelengths, feature.wavelength_um);
              const x = (idx / Math.max(values.length - 1, 1)) * width;
              const normalized = (values[idx] - min) / Math.max(max - min, 0.0001);
              const y = height - normalized * 110 - 24;

              return (
                <g key={`${feature.label}-${feature.wavelength_um}`}>
                  <line x1={x} y1={height - 10} x2={x} y2={y - 8} stroke="rgba(255,255,255,0.24)" strokeDasharray="4 5" />
                  <circle cx={x} cy={y} r="5" fill="#f8fafc" />
                </g>
              );
            })}
            </svg>
          </div>
          <div className="mt-3 flex items-center justify-between text-[11px] uppercase tracking-[0.24em] text-slate-400">
            <span>{wavelengths[0]?.toFixed(2)} um</span>
            <span>Visibility {(scientific.spectral_visibility_score * 100).toFixed(0)}% • {(result.spectrum.metadata.confidence_score ?? 0.8).toFixed(2)}</span>
            <span>{wavelengths[wavelengths.length - 1]?.toFixed(2)} um</span>
          </div>
        </div>
      </div>
    </motion.section>
  );
}

function DiscoveryStageHalo({ result }: { result: SimulationResponse }) {
  const visual = result.visual_physics_profile;
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="pointer-events-none absolute inset-0 hidden lg:block"
    >
      <div
        className="absolute left-1/2 top-1/2 h-[36rem] w-[36rem] -translate-x-1/2 -translate-y-1/2 rounded-full blur-[120px]"
        style={{ backgroundColor: hexToRgba(visual.spectrum_accent_palette[0] ?? visual.atmosphere_glow_color, 0.16) }}
      />
    </motion.div>
  );
}

function GaugeBar({ label, value, accent }: { label: string; value: number; accent: string }) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-[11px] uppercase tracking-[0.24em] text-slate-300">
        <span>{label}</span>
        <span>{value.toFixed(0)}%</span>
      </div>
      <div className="h-2 rounded-full bg-white/10">
        <motion.div
          className="h-full rounded-full"
          style={{ background: `linear-gradient(90deg, ${accent}, rgba(255,255,255,0.92))` }}
          initial={{ width: 0 }}
          animate={{ width: `${Math.max(8, value)}%` }}
          transition={{ duration: 0.7 }}
        />
      </div>
    </div>
  );
}

function ProxyMeter({ label, value, accent }: { label: string; value: number; accent: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/20 px-3 py-3">
      <div className="mb-2 flex items-center justify-between text-[11px] uppercase tracking-[0.22em] text-slate-400">
        <span>{label}</span>
        <span>{value.toFixed(0)}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-white/10">
        <div className="h-full rounded-full" style={{ width: `${Math.max(8, value)}%`, backgroundColor: accent }} />
      </div>
    </div>
  );
}

function buildBuilderPayload(
  config: BuilderConfig,
  normalizedGasFractions: Record<BuilderGasKey, number>
): Record<string, string | number | boolean | null | Record<string, number | Record<string, number>>> {
  return {
    generation_mode: "manual",
    star_type: config.star_type,
    orbit_zone: config.orbit_zone,
    radius_rearth: round(config.radius_rearth, 3),
    mass_mearth: round(config.mass_mearth, 3),
    equilibrium_temperature_k: round(config.equilibrium_temperature_k, 1),
    radiation_level: round(config.radiation_level, 3),
    quantum_runtime_mode: config.quantum_runtime_mode,
    seed: config.seed ?? null,
    atmosphere: {
      pressure_bar: round(config.pressure_bar, 3),
      temperature_k: round(config.equilibrium_temperature_k, 1),
      gas_fractions: normalizedGasFractions,
    },
  };
}

function deriveBuilderPreview(config: BuilderConfig) {
  const warmth = clamp((config.equilibrium_temperature_k - 160) / 420, 0, 1);
  const haze = clamp((config.pressure_bar / 10) * 0.35 + config.gas_fractions.CH4 * 0.45 + config.gas_fractions.H2O * 0.2, 0.05, 0.95);
  const glowColor = config.gas_fractions.CH4 > 0.12
    ? "#9ab8ff"
    : config.gas_fractions.CO2 > 0.18
      ? "#ffb07d"
      : config.gas_fractions.H2O > 0.08
        ? "#7fdcff"
        : "#86e0d0";
  const surfacePalette = warmth > 0.66
    ? ["#ffe6bf", "#f38a4f", "#582011"]
    : config.orbit_zone === "cold"
      ? ["#edf7ff", "#7ccfff", "#1a3e6e"]
      : config.gas_fractions.H2O > 0.08
        ? ["#e1f7ff", "#84d7ff", "#245f96"]
        : ["#eef7ee", "#87cda1", "#2d5f57"];
  const visibility = clamp(
    0.52
      + config.gas_fractions.H2O * 0.16
      + config.gas_fractions.CO2 * 0.12
      - haze * 0.24
      - (config.radiation_level > 2.4 ? 0.05 : 0),
    0.18,
    0.94
  );
  const validationTone = deriveBuilderTone(config, normalizedSum(config.gas_fractions));
  const summary = `Live preview: ${config.star_type} star, ${config.orbit_zone} orbit, ${visibilityLabel(visibility)} visibility, ${validationTone} plausibility tone.`;

  return {
    validationTone,
    summary,
    visual: {
      surface_palette: surfacePalette as [string, string, string],
      surface_variation_intensity: round(clamp(0.34 + config.gas_fractions.CO2 * 0.28 + warmth * 0.24, 0.2, 0.95), 3),
      terminator_contrast: round(clamp(0.32 + warmth * 0.42 + config.radiation_level * 0.05, 0.24, 0.96), 3),
      host_star_light_color: hostStarColor(config.star_type),
      fill_light_color: warmth > 0.6 ? "#6b84d8" : "#73b0ff",
      atmosphere_glow_color: glowColor,
      atmosphere_glow_intensity: round(clamp(0.32 + visibility * 0.42, 0.2, 1), 3),
      atmosphere_rim_width: round(clamp(0.28 + config.pressure_bar * 0.03, 0.18, 0.92), 3),
      atmosphere_thickness_visual: round(clamp(0.24 + config.pressure_bar * 0.04, 0.18, 0.92), 3),
      cloud_tint: config.gas_fractions.CO2 > 0.16 ? "#fff2e1" : config.gas_fractions.CH4 > 0.1 ? "#eef0ff" : "#effcff",
      cloud_opacity: round(clamp(0.08 + haze * 0.34, 0.04, 0.72), 3),
      cloud_motion_speed: round(clamp(0.18 + warmth * 0.32, 0.08, 0.7), 3),
      haze_intensity: round(haze, 3),
      camera_distance: round(clamp(4.2 + config.radius_rearth * 0.45, 4.2, 5.8), 2),
      camera_fov: round(clamp(33 + config.radius_rearth * 2.8, 30, 42), 1),
      auto_rotate_speed: round(clamp(0.18 + visibility * 0.18, 0.12, 0.42), 3),
      starfield_density: round(clamp(0.76 + config.radiation_level * 0.08, 0.6, 1.6), 3),
      particle_density: round(clamp(0.7 + haze * 0.5 + config.radiation_level * 0.06, 0.6, 1.8), 3),
      spectrum_accent_palette:
        config.gas_fractions.H2O > 0.08
          ? ["#7dd3fc", "#67e8f9", "#dbeafe"]
          : config.gas_fractions.CH4 > 0.1
            ? ["#93c5fd", "#a78bfa", "#e9d5ff"]
            : config.gas_fractions.CO2 > 0.14
              ? ["#fde68a", "#fca5a5", "#fb7185"]
              : ["#7dd3fc", "#fde68a", "#c4b5fd"],
      quantum_chamber_intensity: round(clamp(0.4 + config.radiation_level * 0.08, 0.3, 0.9), 3),
      quantum_ring_speed: round(clamp(0.42 + config.radiation_level * 0.06, 0.28, 0.92), 3),
      validation_overlay_tone: validationTone,
    },
  };
}

function deriveBuilderTone(config: BuilderConfig, gasSum: number) {
  if (Math.abs(gasSum - 1) > 0.08 || config.pressure_bar < 0.05 || config.pressure_bar > 25) {
    return "critical";
  }
  if (
    Math.abs(gasSum - 1) > 0.02 ||
    config.equilibrium_temperature_k < 140 ||
    config.equilibrium_temperature_k > 720 ||
    config.radiation_level > 3.2
  ) {
    return "watch";
  }
  return "stable";
}

function normalizedSum(gases: Record<BuilderGasKey, number>) {
  return Object.values(gases).reduce((sum, value) => sum + value, 0);
}

function normalizeGasFractions(gases: Record<BuilderGasKey, number>) {
  const total = normalizedSum(gases);
  if (total <= 0) {
    return { ...DEFAULT_BUILDER_CONFIG.gas_fractions };
  }

  return Object.fromEntries(
    Object.entries(gases).map(([gas, value]) => [gas, round(Math.max(value, 0) / total, 4)])
  ) as Record<BuilderGasKey, number>;
}

function estimateMassFromRadius(radius: number) {
  return round(clamp(radius * radius * radius * 0.92, 0.1, 12), 3);
}

function zoneDefaultTemperature(orbitZone: string) {
  if (orbitZone === "cold") {
    return 190;
  }
  if (orbitZone === "hot") {
    return 448;
  }
  return 292;
}

function hostStarColor(starType: string) {
  if (starType === "M-type") {
    return "#ffb38d";
  }
  if (starType === "G-type") {
    return "#fff0bf";
  }
  return "#ffd6a3";
}

function visibilityLabel(visibility: number) {
  if (visibility < 0.34) {
    return "muted";
  }
  if (visibility < 0.64) {
    return "balanced";
  }
  return "high";
}

function round(value: number, digits: number) {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

function clamp(value: number, minimum: number, maximum: number) {
  return Math.max(minimum, Math.min(maximum, value));
}


function gasSpan(gases: [string, number][], untilIndex: number) {
  const total = gases
    .slice(0, untilIndex + 1)
    .reduce((sum, [, fraction]) => sum + fraction, 0);
  return total * 360;
}

function nearestIndex(values: number[], target: number) {
  let bestIndex = 0;
  let bestDistance = Number.POSITIVE_INFINITY;

  values.forEach((value, index) => {
    const distance = Math.abs(value - target);
    if (distance < bestDistance) {
      bestDistance = distance;
      bestIndex = index;
    }
  });

  return bestIndex;
}

function hexToRgba(hex: string, alpha: number) {
  const normalized = hex.replace("#", "");
  const safe = normalized.length === 3 ? normalized.split("").map((char) => `${char}${char}`).join("") : normalized;
  const red = Number.parseInt(safe.slice(0, 2), 16);
  const green = Number.parseInt(safe.slice(2, 4), 16);
  const blue = Number.parseInt(safe.slice(4, 6), 16);
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}

function wait(duration: number) {
  return new Promise((resolve) => {
    setTimeout(resolve, duration);
  });
}
