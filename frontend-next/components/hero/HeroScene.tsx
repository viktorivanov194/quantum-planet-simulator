"use client";

import { motion } from "framer-motion";

import { StageStrip } from "@/components/layout/StageStrip";
import { SimulationPreset, StageDefinition, StageId } from "@/lib/types/simulation";

interface HeroSceneProps {
  preset: SimulationPreset;
  stages: StageDefinition[];
  activeStage: StageId | null;
  onLaunch: () => void;
  isLoading: boolean;
}

export function HeroScene({
  preset,
  stages,
  activeStage,
  onLaunch,
  isLoading
}: HeroSceneProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8 }}
      className="pointer-events-auto max-w-2xl space-y-5"
    >
      <div className="section-kicker">Quantum Planet Simulator</div>
      <h1 className="max-w-4xl text-5xl font-semibold tracking-[-0.07em] text-white sm:text-6xl xl:text-7xl">
        Watch a living world emerge in full orbital view.
      </h1>
      <p className="max-w-xl text-base leading-8 text-slate-300 sm:text-lg">
        A fullscreen cinematic interface for plausible exoplanet generation, atmosphere analysis, chemistry emergence,
        one lightweight quantum check, and a premium discovery reveal.
      </p>
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={onLaunch}
          disabled={isLoading}
          className="rounded-full bg-gradient-to-r from-sky-300 via-cyan-300 to-amber-200 px-7 py-3 text-sm font-semibold uppercase tracking-[0.22em] text-slate-950 transition hover:scale-[1.02] disabled:cursor-wait disabled:opacity-70"
        >
          {isLoading ? "Simulation Live" : "Launch Simulation"}
        </button>
        <div className="hud-pill">Preset: {preset.title}</div>
      </div>
      <div className="flex flex-wrap gap-2">
        <span className="hud-pill">Interactive Rotation</span>
        <span className="hud-pill">Planet-centered Analysis</span>
      </div>
      <div className="max-w-lg rounded-[1.6rem] border border-white/10 bg-black/30 px-5 py-4 backdrop-blur-2xl">
        <div className="text-[11px] uppercase tracking-[0.25em] text-sky-200/70">Current Scenario</div>
        <div className="mt-2 text-2xl font-medium text-white">{preset.title}</div>
        <div className="mt-2 text-sm leading-7 text-slate-300">{preset.description}</div>
      </div>
      <div className="hidden lg:block">
        <StageStrip stages={stages} activeStage={activeStage} />
      </div>
    </motion.section>
  );
}
