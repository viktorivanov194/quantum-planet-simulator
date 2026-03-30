"use client";

import { motion } from "framer-motion";

import { BuilderConfig, BuilderGasKey, BuilderMode, RuntimeMode } from "@/lib/types/simulation";

const GUIDED_GASES: BuilderGasKey[] = ["N2", "O2", "CO2", "CH4", "H2O"];
const ADVANCED_GASES: BuilderGasKey[] = ["N2", "O2", "CO2", "CH4", "H2O", "NH3", "HCN", "SO2", "CO"];

interface BuilderDeckProps {
  builderMode: BuilderMode;
  config: BuilderConfig;
  normalizedGasFractions: Record<BuilderGasKey, number>;
  validationTone: string;
  livePreviewSummary: string;
  onModeChange: (mode: BuilderMode) => void;
  onChange: <K extends keyof BuilderConfig>(key: K, value: BuilderConfig[K]) => void;
  onGasChange: (gas: BuilderGasKey, value: number) => void;
}

export function BuilderDeck({
  builderMode,
  config,
  normalizedGasFractions,
  validationTone,
  livePreviewSummary,
  onModeChange,
  onChange,
  onGasChange,
}: BuilderDeckProps) {
  const gases = builderMode === "guided" ? GUIDED_GASES : ADVANCED_GASES;

  return (
    <motion.section
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      className="overlay-shell p-4 sm:p-5"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="section-kicker">Planet Builder</div>
          <div className="text-xl font-semibold text-white">Scientific Control Deck</div>
        </div>
        <div
          className={[
            "hud-pill",
            validationTone === "critical"
              ? "border-rose-300/30 text-rose-100"
              : validationTone === "watch" || validationTone === "caution"
                ? "border-amber-300/30 text-amber-100"
                : "border-sky-300/30 text-sky-100",
          ].join(" ")}
        >
          {validationTone}
        </div>
      </div>

      <div className="mt-4 flex gap-2">
        <ModeButton label="Guided Builder" active={builderMode === "guided"} onClick={() => onModeChange("guided")} />
        <ModeButton label="Advanced Builder" active={builderMode === "advanced"} onClick={() => onModeChange("advanced")} />
      </div>

      <div className="mt-4 rounded-[1.4rem] border border-white/10 bg-black/20 px-4 py-3 text-sm leading-7 text-slate-300">
        {livePreviewSummary}
      </div>

      <div className="mt-5 grid gap-3">
        <div className="grid gap-3 sm:grid-cols-2">
          <SelectControl
            label="Host Star"
            value={config.star_type}
            options={["M-type", "K-type", "G-type"]}
            onChange={(value) => onChange("star_type", value)}
          />
          <SelectControl
            label="Orbit Zone"
            value={config.orbit_zone}
            options={["cold", "temperate", "hot"]}
            onChange={(value) => onChange("orbit_zone", value)}
          />
        </div>

        <SliderControl
          label="Radius"
          suffix="R⊕"
          min={0.5}
          max={2.5}
          step={0.01}
          value={config.radius_rearth}
          onChange={(value) => onChange("radius_rearth", value)}
        />

        {builderMode === "advanced" ? (
          <SliderControl
            label="Mass"
            suffix="M⊕"
            min={0.1}
            max={12}
            step={0.01}
            value={config.mass_mearth}
            onChange={(value) => onChange("mass_mearth", value)}
          />
        ) : null}

        <SliderControl
          label="Equilibrium Temperature"
          suffix="K"
          min={120}
          max={700}
          step={1}
          value={config.equilibrium_temperature_k}
          onChange={(value) => onChange("equilibrium_temperature_k", value)}
        />

        <div className="grid gap-3 sm:grid-cols-2">
          <SliderControl
            label="Radiation"
            suffix=""
            min={0}
            max={5}
            step={0.01}
            value={config.radiation_level}
            onChange={(value) => onChange("radiation_level", value)}
          />
          <SliderControl
            label="Pressure"
            suffix="bar"
            min={0.05}
            max={20}
            step={0.01}
            value={config.pressure_bar}
            onChange={(value) => onChange("pressure_bar", value)}
          />
        </div>

        {builderMode === "advanced" ? (
          <div className="grid gap-3 sm:grid-cols-2">
            <SelectControl
              label="Quantum Runtime"
              value={config.quantum_runtime_mode}
              options={["demo_balanced", "cached_only", "fallback_only"]}
              onChange={(value) => onChange("quantum_runtime_mode", value as RuntimeMode)}
            />
            <NumberControl
              label="Seed Lock"
              placeholder="Optional"
              value={config.seed ?? ""}
              onChange={(value) => onChange("seed", value === "" ? null : Number(value))}
            />
          </div>
        ) : null}
      </div>

      <div className="mt-5">
        <div className="mb-3 text-[11px] uppercase tracking-[0.24em] text-sky-200/70">Atmospheric Mix</div>
        <div className="grid gap-3">
          {gases.map((gas) => (
            <SliderControl
              key={gas}
              label={gas}
              suffix="%"
              min={0}
              max={100}
              step={1}
              value={Math.round(normalizedGasFractions[gas] * 100)}
              onChange={(value) => onGasChange(gas, value / 100)}
            />
          ))}
        </div>
      </div>
    </motion.section>
  );
}

function ModeButton({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "preset-pill flex-1 justify-center text-center text-[11px]",
        active ? "preset-pill-active" : "hover:border-white/20 hover:bg-white/[0.08]",
      ].join(" ")}
    >
      {label}
    </button>
  );
}

function SelectControl({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="builder-control">
      <span className="builder-label">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="builder-select"
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

function NumberControl({
  label,
  value,
  placeholder,
  onChange,
}: {
  label: string;
  value: string | number;
  placeholder?: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="builder-control">
      <span className="builder-label">{label}</span>
      <input
        value={value}
        type="number"
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
        className="builder-input"
      />
    </label>
  );
}

function SliderControl({
  label,
  value,
  min,
  max,
  step,
  suffix,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  suffix: string;
  onChange: (value: number) => void;
}) {
  return (
    <label className="builder-control">
      <div className="mb-2 flex items-center justify-between gap-3">
        <span className="builder-label">{label}</span>
        <span className="text-xs uppercase tracking-[0.18em] text-slate-300">
          {value.toFixed(step < 1 ? 2 : 0)}{suffix}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="builder-slider"
      />
    </label>
  );
}
