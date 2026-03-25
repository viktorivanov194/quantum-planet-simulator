"use client";

import { motion } from "framer-motion";

import { SimulationPreset } from "@/lib/types/simulation";

interface PresetSwitcherProps {
  presets: SimulationPreset[];
  activePreset: SimulationPreset["key"];
  onSelect: (key: SimulationPreset["key"]) => void;
}

export function PresetSwitcher({
  presets,
  activePreset,
  onSelect
}: PresetSwitcherProps) {
  return (
    <section className="pointer-events-auto flex flex-wrap gap-2">
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
    </section>
  );
}
