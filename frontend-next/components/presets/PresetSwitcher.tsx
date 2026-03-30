"use client";

import { motion } from "framer-motion";

import { ExperienceMode, SimulationPreset } from "@/lib/types/simulation";

interface PresetSwitcherProps {
  mode: ExperienceMode;
  presets: SimulationPreset[];
  activePreset: SimulationPreset["key"];
  onModeChange: (mode: ExperienceMode) => void;
  onSelect: (key: SimulationPreset["key"]) => void;
}

export function PresetSwitcher({
  mode,
  presets,
  activePreset,
  onModeChange,
  onSelect
}: PresetSwitcherProps) {
  return (
    <section className="pointer-events-auto space-y-3">
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => onModeChange("presets")}
          className={["preset-pill flex-1 justify-center text-center", mode === "presets" ? "preset-pill-active" : "hover:border-white/20 hover:bg-white/[0.08]"].join(" ")}
        >
          Preset Missions
        </button>
        <button
          type="button"
          onClick={() => onModeChange("builder")}
          className={["preset-pill flex-1 justify-center text-center", mode === "builder" ? "preset-pill-active" : "hover:border-white/20 hover:bg-white/[0.08]"].join(" ")}
        >
          Planet Builder
        </button>
      </div>
      {mode === "presets" ? (
        <div className="flex flex-wrap gap-2">
          {presets.map((preset, index) => {
        const isActive = preset.key === activePreset;

        return (
          <motion.button
            key={preset.key}
            type="button"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 * index, duration: 0.45 }}
            onClick={() => onSelect(preset.key)}
            aria-pressed={isActive}
            className={[
              "preset-pill text-left",
              isActive ? "preset-pill-active" : "hover:border-white/20 hover:bg-white/[0.08]"
            ].join(" ")}
          >
            {preset.title}
          </motion.button>
        );
          })}
        </div>
      ) : null}
    </section>
  );
}
