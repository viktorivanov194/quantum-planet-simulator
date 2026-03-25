"use client";

import { motion } from "framer-motion";

import { StageDefinition, StageId } from "@/lib/types/simulation";

interface StageStripProps {
  stages: StageDefinition[];
  activeStage: StageId | null;
}

export function StageStrip({ stages, activeStage }: StageStripProps) {
  return (
    <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-6">
      {stages.map((stage, index) => {
        const isActive = stage.id === activeStage;

        return (
          <motion.div
            key={stage.id}
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.08 * index, duration: 0.4 }}
            className={[
              "rounded-full border px-4 py-3 text-center text-xs uppercase tracking-[0.22em] transition",
              isActive
                ? "border-sky-300/60 bg-sky-300/15 text-white shadow-glow"
                : "border-white/10 bg-white/5 text-slate-300"
            ].join(" ")}
          >
            {stage.title}
          </motion.div>
        );
      })}
    </div>
  );
}
