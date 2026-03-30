"use client";

import { motion } from "framer-motion";

import { StageStrip } from "@/components/layout/StageStrip";
import { ExperienceMode, SimulationPreset, StageDefinition, StageId } from "@/lib/types/simulation";

interface HeroSceneProps {
  preset: SimulationPreset;
  mode: ExperienceMode;
  builderSummary: string;
  stages: StageDefinition[];
  activeStage: StageId | null;
  onLaunch: () => void;
  isLoading: boolean;
}

export function HeroScene({
  preset,
  mode,
  builderSummary,
  stages,
  activeStage,
  onLaunch,
  isLoading
}: HeroSceneProps) {
  const isBuilder = mode === "builder";

  return (
    <motion.section
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8 }}
      className="pointer-events-auto max-w-2xl space-y-5"
    >
      <div className="section-kicker">Quantum Planet Simulator</div>
      <h1 className="max-w-4xl text-5xl font-semibold tracking-[-0.07em] text-white sm:text-6xl xl:text-7xl">
        {isBuilder ? "Shape a living world in full orbital view." : "Watch a living world emerge in full orbital view."}
      </h1>
      <p className="max-w-xl text-base leading-8 text-slate-300 sm:text-lg">
        {isBuilder
          ? "Tune star, orbit, atmosphere, and chemistry controls inside a scientific control deck while the world stays alive at center stage."
          : "A fullscreen cinematic interface for plausible exoplanet generation, atmosphere analysis, chemistry emergence, one lightweight quantum check, and a premium discovery reveal."}
      </p>
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={onLaunch}
          disabled={isLoading}
          className="rounded-full bg-gradient-to-r from-sky-300 via-cyan-300 to-amber-200 px-7 py-3 text-sm font-semibold uppercase tracking-[0.22em] text-slate-950 transition hover:scale-[1.02] disabled:cursor-wait disabled:opacity-70"
        >
          {isLoading ? "Simulation Live" : isBuilder ? "Build And Analyze Planet" : "Launch Simulation"}
        </button>
        <div className="hud-pill">{isBuilder ? "Mode: Planet Builder" : `Preset: ${preset.title}`}</div>
      </div>
      <div className="flex flex-wrap gap-2">
        <span className="hud-pill">Interactive Rotation</span>
        <span className="hud-pill">Planet-centered Analysis</span>
        {isBuilder ? <span className="hud-pill">Live Preview</span> : null}
      </div>
      <div className="max-w-lg rounded-[1.6rem] border border-white/10 bg-black/30 px-5 py-4 backdrop-blur-2xl">
        <div className="text-[11px] uppercase tracking-[0.25em] text-sky-200/70">Current Scenario</div>
        <div className="mt-2 text-2xl font-medium text-white">{isBuilder ? "Interactive Planet Builder" : preset.title}</div>
        <div className="mt-2 text-sm leading-7 text-slate-300">{isBuilder ? builderSummary : preset.description}</div>
      </div>
      <div className="hidden lg:block">
        <StageStrip stages={stages} activeStage={activeStage} />
      </div>
    </motion.section>
  );
}
