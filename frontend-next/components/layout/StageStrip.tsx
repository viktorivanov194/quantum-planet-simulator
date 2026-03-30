"use client";

import { motion } from "framer-motion";

import { StageDefinition, StageId } from "@/lib/types/simulation";

interface StageStripProps {
  stages: StageDefinition[];
  activeStage: StageId | null;
  onSelect?: (stage: StageId) => void;
}

export function StageStrip({ stages, activeStage, onSelect }: StageStripProps) {
  return (
    <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-6">
      {stages.map((stage, index) => {
        const isActive = stage.id === activeStage;

        return (
          <motion.button
            key={stage.id}
            type="button"
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.08 * index, duration: 0.4 }}
            onClick={() => onSelect?.(stage.id)}
            className={[
              "rounded-full border px-4 py-3 text-center text-xs uppercase tracking-[0.22em] transition",
              onSelect ? "cursor-pointer hover:border-white/20 hover:bg-white/[0.08]" : "cursor-default",
              isActive
                ? "border-sky-300/60 bg-sky-300/15 text-white shadow-glow"
                : "border-white/10 bg-white/5 text-slate-300"
            ].join(" ")}
          >
            {stage.title}
          </motion.button>
        );
      })}
    </div>
  );
}
