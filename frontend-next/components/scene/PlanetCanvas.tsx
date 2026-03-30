"use client";

import { useMemo, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Float, OrbitControls, Sparkles, Stars } from "@react-three/drei";
import { motion } from "framer-motion";
import * as THREE from "three";

import { createAtmosphereMaterial } from "@/components/scene/shaders/atmosphere";
import { createCloudShellMaterial } from "@/components/scene/shaders/clouds";
import { QualityMode, StageId } from "@/lib/types/simulation";

interface PlanetCanvasProps {
  colors: [string, string, string];
  glowColor: string;
  hasRing?: boolean;
  qualityMode?: QualityMode;
  hostStarColor: string;
  fillLightColor: string;
  cloudTint: string;
  cloudOpacity: number;
  cameraDistance: number;
  cameraFov?: number;
  autoRotateSpeed: number;
  starDensity: number;
  surfaceVariationIntensity?: number;
  terminatorContrast?: number;
  atmosphereGlowIntensity?: number;
  atmosphereRimWidth?: number;
  atmosphereThicknessVisual?: number;
  hazeIntensity?: number;
  cloudMotionSpeed?: number;
  particleDensity?: number;
  sceneStage?: StageId | null;
  stageProgress?: number;
  isSequenceActive?: boolean;
  radiationLevel?: number;
  quantumChamberIntensity?: number;
  spectrumAccentPalette?: string[];
}

function createSurfaceTexture(colors: [string, string, string], variationIntensity: number) {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 512;
  const context = canvas.getContext("2d");

  if (!context) {
    return null;
  }

  const baseGradient = context.createLinearGradient(0, 0, 512, 512);
  baseGradient.addColorStop(0, colors[0]);
  baseGradient.addColorStop(0.45, colors[1]);
  baseGradient.addColorStop(1, colors[2]);
  context.fillStyle = baseGradient;
  context.fillRect(0, 0, 512, 512);

  for (let index = 0; index < 32 + Math.round(24 * variationIntensity); index += 1) {
    const x = Math.random() * 512;
    const y = Math.random() * 512;
    const radius = 20 + Math.random() * 90;
    const alpha = 0.02 + Math.random() * (0.04 + 0.08 * variationIntensity);
    context.fillStyle = `rgba(255,255,255,${alpha})`;
    context.beginPath();
    context.ellipse(x, y, radius, radius * (0.4 + Math.random() * 0.7), Math.random() * Math.PI, 0, Math.PI * 2);
    context.fill();
  }

  for (let index = 0; index < 12 + Math.round(10 * variationIntensity); index += 1) {
    context.strokeStyle = `rgba(15,23,42,${0.08 + Math.random() * 0.08})`;
    context.lineWidth = 5 + Math.random() * (12 + 14 * variationIntensity);
    context.beginPath();
    context.moveTo(-20, Math.random() * 512);
    context.bezierCurveTo(140, Math.random() * 512, 300, Math.random() * 512, 540, Math.random() * 512);
    context.stroke();
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  return texture;
}

function createRoughnessTexture(variationIntensity: number) {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 512;
  const context = canvas.getContext("2d");

  if (!context) {
    return null;
  }

  context.fillStyle = "rgb(190,190,190)";
  context.fillRect(0, 0, 512, 512);

  for (let index = 0; index < 46 + Math.round(20 * variationIntensity); index += 1) {
    const tone = 70 + Math.floor(Math.random() * 120);
    context.fillStyle = `rgba(${tone},${tone},${tone},${0.08 + Math.random() * 0.12})`;
    context.beginPath();
    context.ellipse(
      Math.random() * 512,
      Math.random() * 512,
      16 + Math.random() * 80,
      10 + Math.random() * 52,
      Math.random() * Math.PI,
      0,
      Math.PI * 2
    );
    context.fill();
  }

  for (let index = 0; index < 18; index += 1) {
    context.strokeStyle = `rgba(30,30,30,${0.05 + Math.random() * 0.08})`;
    context.lineWidth = 2 + Math.random() * 5;
    context.beginPath();
    context.moveTo(-20, Math.random() * 512);
    context.bezierCurveTo(120, Math.random() * 512, 300, Math.random() * 512, 540, Math.random() * 512);
    context.stroke();
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  return texture;
}

function createCloudTexture(cloudIntensity: number) {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 512;
  const context = canvas.getContext("2d");

  if (!context) {
    return null;
  }

  context.clearRect(0, 0, 512, 512);

  for (let index = 0; index < 20 + Math.round(20 * cloudIntensity); index += 1) {
    const gradient = context.createRadialGradient(
      Math.random() * 512,
      Math.random() * 512,
      10,
      Math.random() * 512,
      Math.random() * 512,
      90 + Math.random() * 70
    );
    gradient.addColorStop(0, `rgba(255,255,255,${0.08 + 0.18 * cloudIntensity})`);
    gradient.addColorStop(1, "rgba(255,255,255,0)");
    context.fillStyle = gradient;
    context.fillRect(0, 0, 512, 512);
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  return texture;
}

function AtmosphereRim({
  color,
  starColor,
  thickness,
  glowIntensity,
  hazeIntensity,
  density,
}: {
  color: string;
  starColor: string;
  thickness: number;
  glowIntensity: number;
  hazeIntensity: number;
  density: number;
}) {
  const materialRef = useRef<THREE.ShaderMaterial>(null);

  const material = useMemo(
    () => createAtmosphereMaterial({ glowColor: color, starColor, thickness, glowIntensity, hazeIntensity, density }),
    [color, density, glowIntensity, hazeIntensity, starColor, thickness]
  );

  useFrame((state) => {
    if (materialRef.current) {
      materialRef.current.uniforms.glowColor.value.set(color);
      materialRef.current.uniforms.starColor.value.set(starColor);
      materialRef.current.uniforms.thickness.value = thickness;
      materialRef.current.uniforms.glowIntensity.value = glowIntensity;
      materialRef.current.uniforms.hazeIntensity.value = hazeIntensity;
      materialRef.current.uniforms.density.value = density;
      materialRef.current.uniforms.time.value = state.clock.getElapsedTime();
    }
  });

  return <primitive object={material} ref={materialRef} attach="material" />;
}

function CameraRig({
  distance,
  fov,
  stage,
  progress,
  isSequenceActive,
}: {
  distance: number;
  fov: number;
  stage?: StageId | null;
  progress: number;
  isSequenceActive: boolean;
}) {
  const { camera, clock } = useThree();

  useFrame((_, delta) => {
    const elapsed = clock.getElapsedTime();
    const drift = isSequenceActive ? 0.9 : 0.28;
    const birthBoost = stage === "planet-birth" ? 1 - progress : 0;
    const atmosphereBias = stage === "atmospheric-validation" ? 0.16 : 0;
    const chemistryBias = stage === "chemistry-emergence" ? 0.08 : 0;
    const quantumBias = stage === "quantum-evaluation" ? -0.22 : 0;
    const spectrumBias = stage === "spectrum-reveal" ? 0.12 : 0;
    const discoveryBias = stage === "final-discovery" ? 0.18 : 0;
    const targetZ =
      distance +
      birthBoost * 0.62 +
      atmosphereBias +
      chemistryBias +
      quantumBias +
      spectrumBias +
      discoveryBias +
      Math.sin(elapsed * 0.16) * 0.034 * drift;
    const targetX = Math.sin(elapsed * 0.075) * (0.11 + atmosphereBias * 0.22 + chemistryBias * 0.18) * drift;
    const targetY = 0.03 + Math.cos(elapsed * 0.12) * (0.072 + spectrumBias * 0.22 + discoveryBias * 0.14) * drift;
    const targetFov =
      fov +
      birthBoost * 1.4 +
      (stage === "quantum-evaluation" ? -0.8 : 0) +
      (stage === "final-discovery" ? 0.4 : 0) +
      Math.sin(elapsed * 0.1) * 0.26 * drift;
    const perspectiveCamera = camera as THREE.PerspectiveCamera;

    camera.position.x = THREE.MathUtils.lerp(camera.position.x, targetX, delta * 1.6);
    camera.position.y = THREE.MathUtils.lerp(camera.position.y, targetY, delta * 1.6);
    camera.position.z = THREE.MathUtils.lerp(camera.position.z, targetZ, delta * 1.6);
    perspectiveCamera.fov = THREE.MathUtils.lerp(perspectiveCamera.fov, targetFov, delta * 1.4);
    camera.lookAt(0, 0, 0);
    camera.updateProjectionMatrix();
  });

  return null;
}

function StageFieldOverlays({
  stage,
  progress,
  glowColor,
  hostStarColor,
  accent,
  quantumChamberIntensity,
}: {
  stage?: StageId | null;
  progress: number;
  glowColor: string;
  hostStarColor: string;
  accent: string;
  quantumChamberIntensity: number;
}) {
  if (!stage) {
    return null;
  }

  if (stage === "planet-birth") {
    return (
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(2,6,23,0.12),rgba(2,6,23,0.76)_58%,rgba(2,6,23,0.96)_100%)]" />
        <motion.div
          className="absolute left-1/2 top-1/2 h-[34rem] w-24 -translate-x-1/2 -translate-y-1/2 rounded-full blur-[56px]"
          style={{ background: `linear-gradient(180deg, transparent 0%, ${hexToRgba(hostStarColor, 0.72)} 50%, transparent 100%)` }}
          initial={{ opacity: 0, x: "-190%" }}
          animate={{ opacity: [0, 1, 0], x: ["-220%", "0%", "220%"] }}
          transition={{ duration: 3.8, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute left-1/2 top-1/2 h-[30rem] w-[30rem] -translate-x-1/2 -translate-y-1/2 rounded-full blur-[130px]"
          style={{ backgroundColor: hexToRgba(glowColor, 0.18) }}
          animate={{ opacity: [0.16, 0.42, 0.24], scale: [0.72, 1.06, 1] }}
          transition={{ duration: 3.6, ease: "easeInOut" }}
        />
      </div>
    );
  }

  if (stage === "atmospheric-validation") {
    return (
      <div className="pointer-events-none absolute inset-0">
        <motion.div
          className="analysis-ring h-[24rem] w-[24rem]"
          style={{ borderColor: hexToRgba(glowColor, 0.3), opacity: 0.75 }}
          initial={{ scale: 0.55, opacity: 0 }}
          animate={{ scale: 0.84 + progress * 0.2, opacity: 0.75 }}
          transition={{ duration: 1.25, ease: "easeOut" }}
        />
        <motion.div
          className="analysis-ring h-[31rem] w-[31rem]"
          style={{ borderColor: hexToRgba(glowColor, 0.18), opacity: 0.42 }}
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 0.78 + progress * 0.24, opacity: 0.42 }}
          transition={{ duration: 1.65, ease: "easeOut" }}
        />
        <motion.div
          className="absolute left-1/2 top-1/2 h-[34rem] w-[34rem] -translate-x-1/2 -translate-y-1/2 rounded-full blur-[120px]"
          style={{ backgroundColor: hexToRgba(glowColor, 0.12 + progress * 0.08) }}
          animate={{ opacity: [0.24, 0.38, 0.28], scale: [0.86, 1.02, 1] }}
          transition={{ duration: 2.8, repeat: Infinity, ease: "easeInOut" }}
        />
      </div>
    );
  }

  if (stage === "chemistry-emergence") {
    return (
      <div className="pointer-events-none absolute inset-0">
        <motion.div
          className="analysis-ring h-[23rem] w-[23rem] opacity-40"
          style={{ borderColor: hexToRgba(glowColor, 0.16), borderStyle: "dashed" }}
          animate={{ rotate: 360 }}
          transition={{ duration: 22, repeat: Infinity, ease: "linear" }}
        />
        <motion.div
          className="analysis-ring h-[29rem] w-[29rem] opacity-24"
          style={{ borderColor: hexToRgba(accent, 0.18), borderStyle: "dashed" }}
          animate={{ rotate: -360 }}
          transition={{ duration: 28, repeat: Infinity, ease: "linear" }}
        />
      </div>
    );
  }

  if (stage === "quantum-evaluation") {
    return (
      <div className="pointer-events-none absolute inset-0">
        <div
          className="absolute inset-[12%] rounded-[3rem] border border-white/6"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)",
            backgroundSize: "40px 40px, 40px 40px",
          }}
        />
        <motion.div
          className="analysis-ring h-[28rem] w-[28rem] opacity-40"
          style={{ borderColor: hexToRgba(accent, 0.22) }}
          animate={{ rotate: 360, scale: [0.98, 1.02, 0.98] }}
          transition={{ rotate: { duration: 30, repeat: Infinity, ease: "linear" }, scale: { duration: 3.4, repeat: Infinity, ease: "easeInOut" } }}
        />
        <motion.div
          className="absolute left-1/2 top-1/2 h-[22rem] w-[22rem] -translate-x-1/2 -translate-y-1/2 rounded-full blur-[110px]"
          style={{ backgroundColor: hexToRgba(accent, 0.12 + quantumChamberIntensity * 0.1) }}
          animate={{ opacity: [0.18, 0.32, 0.2] }}
          transition={{ duration: 2.6, repeat: Infinity, ease: "easeInOut" }}
        />
      </div>
    );
  }

  if (stage === "spectrum-reveal") {
    return (
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_48%,rgba(2,6,23,0.06),rgba(2,6,23,0.62)_58%,rgba(2,6,23,0.88)_100%)]" />
        <motion.div
          className="absolute inset-y-[14%] left-[-16%] w-[20%] rounded-[4rem] bg-[linear-gradient(90deg,transparent_0%,rgba(125,211,252,0.18)_55%,transparent_100%)] blur-[8px]"
          initial={{ x: "-18%" }}
          animate={{ x: "760%" }}
          transition={{ duration: 3.2, ease: "easeInOut" }}
        />
      </div>
    );
  }

  if (stage === "final-discovery") {
    return (
      <div className="pointer-events-none absolute inset-0">
        <motion.div
          className="absolute left-1/2 top-1/2 h-[38rem] w-[38rem] -translate-x-1/2 -translate-y-1/2 rounded-full blur-[130px]"
          style={{ backgroundColor: hexToRgba(accent, 0.18) }}
          animate={{ opacity: [0.12, 0.22, 0.14] }}
          transition={{ duration: 5.2, repeat: Infinity, ease: "easeInOut" }}
        />
      </div>
    );
  }

  return null;
}

function AccretionField({
  glowColor,
  progress,
  qualityMode,
}: {
  glowColor: string;
  progress: number;
  qualityMode: QualityMode;
}) {
  const pointsRef = useRef<THREE.Points>(null);
  const geometry = useMemo(() => {
    const pointCount = qualityMode === "Cinematic" ? 220 : qualityMode === "Balanced" ? 160 : 90;
    const positions = new Float32Array(pointCount * 3);
    for (let index = 0; index < positions.length; index += 3) {
      const radius = 2.5 + Math.random() * 1.6;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      positions[index] = radius * Math.sin(phi) * Math.cos(theta);
      positions[index + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[index + 2] = radius * Math.cos(phi);
    }
    const nextGeometry = new THREE.BufferGeometry();
    nextGeometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    return nextGeometry;
  }, [qualityMode]);

  useFrame((_, delta) => {
    if (!pointsRef.current) {
      return;
    }
    pointsRef.current.rotation.y += delta * 0.2;
    pointsRef.current.rotation.z -= delta * 0.08;
    const scale = 1.2 - progress * 0.35;
    pointsRef.current.scale.setScalar(scale);
    const material = pointsRef.current.material as THREE.PointsMaterial;
    material.opacity = Math.max(0, 0.42 * (1 - progress));
  });

  return (
    <points ref={pointsRef} geometry={geometry}>
      <pointsMaterial color={glowColor} size={0.04} transparent opacity={0.38} />
    </points>
  );
}

function NebulaBackdrop({
  glowColor,
  hostStarColor,
  fillLightColor,
  stageProgress,
}: {
  glowColor: string;
  hostStarColor: string;
  fillLightColor: string;
  stageProgress: number;
}) {
  return (
    <>
      <div
        className="pointer-events-none absolute inset-0 opacity-100"
        style={{
          background: `radial-gradient(circle at 24% 30%, ${hexToRgba(fillLightColor, 0.08)}, transparent 32%),
            radial-gradient(circle at 78% 16%, ${hexToRgba(hostStarColor, 0.09)}, transparent 26%),
            radial-gradient(circle at 62% 74%, ${hexToRgba(glowColor, 0.05)}, transparent 34%),
            linear-gradient(180deg, rgba(2,6,23,0.06), rgba(2,6,23,0.24))`
        }}
      />
      <motion.div
        className="pointer-events-none absolute -left-[10%] top-[14%] h-[38rem] w-[38rem] rounded-full blur-[170px]"
        style={{ backgroundColor: hexToRgba(glowColor, 0.045) }}
        animate={{ x: [0, 16, -10, 0], y: [0, -10, 8, 0], scale: [1, 1.02, 0.99, 1] }}
        transition={{ duration: 42, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="pointer-events-none absolute right-[-8%] top-[4%] h-[34rem] w-[34rem] rounded-full blur-[150px]"
        style={{ backgroundColor: hexToRgba(hostStarColor, 0.055 + stageProgress * 0.015) }}
        animate={{ x: [0, -14, 6, 0], y: [0, 10, -8, 0], scale: [1, 0.985, 1.03, 1] }}
        transition={{ duration: 38, repeat: Infinity, ease: "easeInOut" }}
      />
    </>
  );
}

function ForegroundDust({
  glowColor,
  count,
}: {
  glowColor: string;
  count: number;
}) {
  return (
    <Sparkles
      count={count}
      scale={[10, 6.4, 8]}
      size={1.6}
      speed={0.08}
      color={glowColor}
      opacity={0.18}
    />
  );
}

function AuroraParticles({
  glowColor,
  radiationLevel,
  qualityMode,
}: {
  glowColor: string;
  radiationLevel: number;
  qualityMode: QualityMode;
}) {
  const count =
    qualityMode === "Cinematic" ? 52 : qualityMode === "Balanced" ? 28 : 12;

  return (
    <>
      <Sparkles
        count={count}
        scale={[3.1, 0.34, 3.1]}
        position={[0, 1.72, 0]}
        size={1.05}
        speed={0.1 + radiationLevel * 0.028}
        color={glowColor}
        opacity={0.08 + Math.min(0.12, radiationLevel * 0.018)}
      />
      <Sparkles
        count={count}
        scale={[2.9, 0.28, 2.9]}
        position={[0, -1.72, 0]}
        size={0.9}
        speed={0.09 + radiationLevel * 0.022}
        color="#c4f1ff"
        opacity={0.055 + Math.min(0.09, radiationLevel * 0.014)}
      />
    </>
  );
}

function PlanetMesh({
  colors,
  glowColor,
  hasRing = true,
  qualityMode = "Balanced",
  cloudTint,
  cloudOpacity,
  surfaceVariationIntensity = 0.5,
  atmosphereGlowIntensity = 0.55,
  atmosphereRimWidth = 0.5,
  atmosphereThicknessVisual = 0.5,
  hazeIntensity = 0.2,
  cloudMotionSpeed = 0.3,
  sceneStage = null,
  stageProgress = 1,
  hostStarColor,
}: PlanetCanvasProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const ringRef = useRef<THREE.Mesh>(null);
  const shellRef = useRef<THREE.Mesh>(null);
  const upperShellRef = useRef<THREE.Mesh>(null);
  const haloRef = useRef<THREE.Points>(null);
  const surfaceTexture = useMemo(
    () => createSurfaceTexture(colors, surfaceVariationIntensity),
    [colors, surfaceVariationIntensity]
  );
  const roughnessTexture = useMemo(
    () => createRoughnessTexture(surfaceVariationIntensity),
    [surfaceVariationIntensity]
  );
  const cloudTexture = useMemo(() => createCloudTexture(cloudOpacity), [cloudOpacity]);
  const upperCloudTexture = useMemo(() => createCloudTexture(cloudOpacity * 0.72), [cloudOpacity]);
  const geometryDetail = qualityMode === "Cinematic" ? 96 : qualityMode === "Balanced" ? 72 : 48;
  const birthProgress = sceneStage === "planet-birth" ? stageProgress : 1;
  const birthDarkness = sceneStage === "planet-birth" ? 1 - stageProgress : 0;
  const atmosphereProgress =
    sceneStage === "planet-birth"
      ? Math.min(1, 0.25 + stageProgress * 0.45)
      : sceneStage === "atmospheric-validation"
        ? Math.min(1, 0.32 + stageProgress * 0.68)
        : 1;
  const chemistryPulse = sceneStage === "chemistry-emergence" ? 1 : 0;
  const cloudPhase = sceneStage === "atmospheric-validation" ? stageProgress : 1;

  const material = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: new THREE.Color(colors[1]),
        map: surfaceTexture,
        roughness: 0.84,
        roughnessMap: roughnessTexture,
        metalness: 0.05,
        bumpMap: roughnessTexture,
        bumpScale: 0.035 + surfaceVariationIntensity * 0.045,
        emissive: new THREE.Color(colors[2]),
        emissiveIntensity: 0.12
      }),
    [colors, roughnessTexture, surfaceTexture, surfaceVariationIntensity]
  );

  const cloudMaterial = useMemo(
    () =>
      createCloudShellMaterial({
        cloudMap: cloudTexture,
        cloudTint,
        glowColor,
        opacity: qualityMode === "Safe" ? cloudOpacity * 0.65 : cloudOpacity,
        hazeIntensity,
        thickness: atmosphereThicknessVisual,
        driftScale: 1.0,
        secondaryDriftScale: 1.2,
        coverageBias: 0.0,
      }),
    [atmosphereThicknessVisual, cloudOpacity, cloudTexture, cloudTint, glowColor, hazeIntensity, qualityMode]
  );
  const upperCloudMaterial = useMemo(
    () =>
      createCloudShellMaterial({
        cloudMap: upperCloudTexture,
        cloudTint: "#f8fdff",
        glowColor,
        opacity: (qualityMode === "Safe" ? cloudOpacity * 0.65 : cloudOpacity) * 0.42,
        hazeIntensity: hazeIntensity * 0.7,
        thickness: atmosphereThicknessVisual * 0.72,
        driftScale: 1.34,
        secondaryDriftScale: 1.7,
        coverageBias: 0.08,
      }),
    [atmosphereThicknessVisual, cloudOpacity, glowColor, hazeIntensity, qualityMode, upperCloudTexture]
  );

  const haloParticles = useMemo(() => {
    const geometry = new THREE.BufferGeometry();
    const count = qualityMode === "Cinematic" ? 240 : qualityMode === "Balanced" ? 180 : 96;
    const positions = new Float32Array(count * 3);

    for (let index = 0; index < positions.length; index += 3) {
      const radius = 1.8 + Math.random() * 1.1;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);

      positions[index] = radius * Math.sin(phi) * Math.cos(theta);
      positions[index + 1] = radius * Math.sin(phi) * Math.sin(theta) * 0.55;
      positions[index + 2] = radius * Math.cos(phi);
    }

    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    return geometry;
  }, [qualityMode]);

  useFrame((_, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += delta * 0.12;
      meshRef.current.rotation.x = Math.sin(meshRef.current.rotation.y * 0.35) * 0.035;
      meshRef.current.scale.setScalar(0.58 + birthProgress * 0.42);
    }
    if (shellRef.current) {
      shellRef.current.rotation.y -= delta * (0.006 + cloudMotionSpeed * 0.05 * cloudPhase);
      shellRef.current.rotation.z += delta * (0.003 + cloudMotionSpeed * 0.03 * cloudPhase);
      shellRef.current.scale.setScalar(1.01 + atmosphereProgress * 0.02);
      if (shellRef.current.material instanceof THREE.ShaderMaterial) {
        shellRef.current.material.uniforms.opacity.value = (qualityMode === "Safe" ? cloudOpacity * 0.65 : cloudOpacity) * atmosphereProgress;
        shellRef.current.material.uniforms.hazeIntensity.value = hazeIntensity;
        shellRef.current.material.uniforms.thickness.value = atmosphereThicknessVisual;
        shellRef.current.material.uniforms.time.value += delta * (0.55 + cloudMotionSpeed * 1.4);
        shellRef.current.material.uniforms.cloudTint.value.set(cloudTint);
        shellRef.current.material.uniforms.glowColor.value.set(glowColor);
      }
    }
    if (upperShellRef.current) {
      upperShellRef.current.rotation.y += delta * (0.004 + cloudMotionSpeed * 0.08 * cloudPhase);
      upperShellRef.current.rotation.x += delta * 0.0015;
      upperShellRef.current.scale.setScalar(1.025 + atmosphereProgress * 0.028);
      if (upperShellRef.current.material instanceof THREE.ShaderMaterial) {
        upperShellRef.current.material.uniforms.opacity.value = (qualityMode === "Safe" ? cloudOpacity * 0.65 : cloudOpacity) * 0.3 * atmosphereProgress;
        upperShellRef.current.material.uniforms.hazeIntensity.value = hazeIntensity * 0.75;
        upperShellRef.current.material.uniforms.thickness.value = atmosphereThicknessVisual * 0.7;
        upperShellRef.current.material.uniforms.time.value += delta * (0.95 + cloudMotionSpeed * 1.9);
        upperShellRef.current.material.uniforms.glowColor.value.set(glowColor);
      }
    }
    if (ringRef.current) {
      ringRef.current.rotation.z += delta * 0.045;
    }
    if (haloRef.current) {
      haloRef.current.rotation.y += delta * 0.014;
      haloRef.current.scale.setScalar(0.96 + chemistryPulse * 0.04 + (1 - birthProgress) * 0.08);
    }
    if (meshRef.current?.material instanceof THREE.MeshStandardMaterial) {
      meshRef.current.material.emissiveIntensity = 0.015 + atmosphereProgress * 0.08 + chemistryPulse * 0.03 + birthProgress * 0.02;
      meshRef.current.material.opacity = 0.42 + birthProgress * 0.58;
      meshRef.current.material.transparent = true;
    }
  });

  return (
    <group position={[0, 0, 0]}>
      {sceneStage === "planet-birth" ? <AccretionField glowColor={glowColor} progress={birthProgress} qualityMode={qualityMode} /> : null}
      <mesh ref={meshRef} material={material}>
        <sphereGeometry args={[1.52, geometryDetail, geometryDetail]} />
      </mesh>
      <mesh scale={1.02 + (1.05 + atmosphereRimWidth * 0.16 - 1.02) * atmosphereProgress}>
        <sphereGeometry args={[1.54, 64, 64]} />
        <AtmosphereRim
          color={glowColor}
          starColor={hostStarColor}
          thickness={atmosphereRimWidth + atmosphereThicknessVisual * 0.6}
          glowIntensity={atmosphereGlowIntensity * 0.85 * atmosphereProgress}
          hazeIntensity={hazeIntensity}
          density={0.72}
        />
      </mesh>
      <mesh scale={1.08 + (1.12 + atmosphereThicknessVisual * 0.18 - 1.08) * atmosphereProgress}>
        <sphereGeometry args={[1.6, 64, 64]} />
        <AtmosphereRim
          color={glowColor}
          starColor={hostStarColor}
          thickness={atmosphereRimWidth * 0.8 + atmosphereThicknessVisual * 0.45}
          glowIntensity={atmosphereGlowIntensity * 0.38 * atmosphereProgress}
          hazeIntensity={hazeIntensity * 1.1}
          density={0.32}
        />
      </mesh>
      <mesh ref={shellRef} material={cloudMaterial} scale={1.03}>
        <sphereGeometry args={[1.56, Math.max(24, geometryDetail * 0.75), Math.max(24, geometryDetail * 0.75)]} />
      </mesh>
      <mesh ref={upperShellRef} material={upperCloudMaterial} scale={1.04}>
        <sphereGeometry args={[1.585, Math.max(24, geometryDetail * 0.7), Math.max(24, geometryDetail * 0.7)]} />
      </mesh>
      <mesh scale={1.05 + (1.12 + atmosphereThicknessVisual * 0.14 - 1.05) * atmosphereProgress}>
        <sphereGeometry args={[1.58, 64, 64]} />
        <meshBasicMaterial color={glowColor} transparent opacity={(0.05 + atmosphereGlowIntensity * 0.12) * atmosphereProgress} />
      </mesh>
      <mesh scale={1.08 + (1.18 + atmosphereThicknessVisual * 0.22 - 1.08) * atmosphereProgress}>
        <sphereGeometry args={[1.62, 64, 64]} />
        <meshBasicMaterial color={glowColor} transparent opacity={(0.025 + atmosphereGlowIntensity * 0.08) * atmosphereProgress} />
      </mesh>
      {hasRing ? (
        <mesh ref={ringRef} rotation={[1.1, 0.18, -0.32]}>
          <torusGeometry args={[2.18, 0.03, 20, 180]} />
          <meshBasicMaterial color={colors[0]} transparent opacity={0.36} />
        </mesh>
      ) : null}
      <points ref={haloRef} geometry={haloParticles}>
        <pointsMaterial color={glowColor} size={0.04} transparent opacity={0.45} />
      </points>
    </group>
  );
}

export function PlanetCanvas({
  qualityMode = "Balanced",
  ...props
}: PlanetCanvasProps) {
  const starScale = props.starDensity;
  const particleScale = props.particleDensity ?? 1.0;
  const starCountBase = qualityMode === "Cinematic" ? 3000 : qualityMode === "Balanced" ? 1800 : 950;
  const sparkleBase = qualityMode === "Cinematic" ? 56 : qualityMode === "Balanced" ? 30 : 8;
  const starCount = Math.round(starCountBase * starScale);
  const sparkleCount = Math.round(sparkleBase * Math.max(0.65, starScale) * particleScale);
  const midStarCount = Math.round(starCount * 0.1);
  const nearDustCount = Math.round((qualityMode === "Cinematic" ? 24 : qualityMode === "Balanced" ? 14 : 6) * Math.max(0.75, particleScale));
  const fov = props.cameraFov ?? 34;
  const stageProgress = props.stageProgress ?? 1;
  const allowBloomLikeGlow = qualityMode === "Cinematic";
  const highRadiation = (props.radiationLevel ?? 0) >= 1.8;
  const chamberGlow = props.quantumChamberIntensity ?? 0.5;
  const accent = props.spectrumAccentPalette?.[0] ?? props.glowColor;
  const birthDarkness = props.sceneStage === "planet-birth" ? 1 - stageProgress : 0;

  return (
    <div className="absolute inset-0">
      <NebulaBackdrop
        glowColor={props.glowColor}
        hostStarColor={props.hostStarColor}
        fillLightColor={props.fillLightColor}
        stageProgress={stageProgress}
      />
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_52%,rgba(255,255,255,0.05),transparent_22%),linear-gradient(180deg,rgba(2,6,23,0.16),rgba(2,6,23,0.72))]"
      />
      <div className="pointer-events-none absolute inset-0 orbit-grid opacity-[0.14]" />
      <Canvas camera={{ position: [0, 0.04, props.cameraDistance], fov }}>
        <fog attach="fog" args={["#040816", 6, 12]} />
        <color attach="background" args={["#030711"]} />
        <CameraRig
          distance={props.cameraDistance}
          fov={fov}
          stage={props.sceneStage}
          progress={props.stageProgress ?? 1}
          isSequenceActive={props.isSequenceActive ?? false}
        />
        <ambientLight intensity={qualityMode === "Safe" ? 0.46 : 0.48 + (props.terminatorContrast ?? 0.5) * 0.18} color={props.fillLightColor} />
        <hemisphereLight intensity={0.58} groundColor="#020617" color={props.fillLightColor} />
        <directionalLight position={[5.4, 2.5, 2.4]} intensity={1.7 + (props.terminatorContrast ?? 0.5) * 1.0} color={props.hostStarColor} />
        <directionalLight position={[-5.4, -2.3, -3.2]} intensity={0.18 + (1 - (props.terminatorContrast ?? 0.5)) * 0.28} color={props.fillLightColor} />
        <pointLight position={[-2.5, -0.6, 2.4]} intensity={(props.isSequenceActive ? 1.05 : 0.95) + Math.sin(Date.now() * 0.0014) * 0.03} color={props.glowColor} />
        <Stars radius={132} depth={72} count={starCount} factor={2.7} saturation={0} fade speed={0.18 + (stageProgress * 0.03)} />
        <Stars radius={80} depth={26} count={midStarCount} factor={4.1} saturation={0} fade speed={0.12} />
        <ForegroundDust glowColor={props.glowColor} count={nearDustCount} />
        {highRadiation ? <AuroraParticles glowColor={accent} radiationLevel={props.radiationLevel ?? 0} qualityMode={qualityMode} /> : null}
        <Sparkles count={sparkleCount} scale={[7.5, 4.4, 6]} size={1.55} speed={0.08 + ((props.stageProgress ?? 1) * 0.03)} color={props.glowColor} opacity={0.24} />
        <Float speed={0.42} rotationIntensity={0.032} floatIntensity={0.07}>
          <PlanetMesh {...props} qualityMode={qualityMode} />
        </Float>
        <OrbitControls
          enablePan={false}
          enableDamping
          dampingFactor={0.075}
          minDistance={props.cameraDistance - 0.9}
          maxDistance={props.cameraDistance + 0.7}
          minPolarAngle={Math.PI * 0.34}
          maxPolarAngle={Math.PI * 0.66}
          enableZoom={qualityMode !== "Safe"}
          autoRotate
          autoRotateSpeed={props.autoRotateSpeed}
          rotateSpeed={0.42}
        />
      </Canvas>
      <StageFieldOverlays
        stage={props.sceneStage}
        progress={stageProgress}
        glowColor={props.glowColor}
        hostStarColor={props.hostStarColor}
        accent={accent}
        quantumChamberIntensity={chamberGlow}
      />
      {props.sceneStage === "planet-birth" ? (
        <div
          className="pointer-events-none absolute inset-0"
          style={{ backgroundColor: `rgba(2, 6, 23, ${0.62 * birthDarkness})` }}
        />
      ) : null}
      <div
        className="pointer-events-none absolute left-1/2 top-[13%] h-44 w-44 -translate-x-1/2 rounded-full opacity-55 blur-[110px]"
        style={{ backgroundColor: props.hostStarColor }}
      />
      <div
        className="pointer-events-none absolute left-[18%] top-[10%] h-56 w-56 rounded-full opacity-22 blur-[150px]"
        style={{ backgroundColor: props.glowColor }}
      />
      {allowBloomLikeGlow ? (
        <>
          <div
            className="pointer-events-none absolute left-1/2 top-1/2 h-[30rem] w-[30rem] -translate-x-1/2 -translate-y-1/2 rounded-full blur-[150px]"
            style={{ backgroundColor: hexToRgba(props.glowColor, 0.08 + chamberGlow * 0.03) }}
          />
          <div
            className="pointer-events-none absolute bottom-[16%] left-1/2 h-28 w-[42rem] -translate-x-1/2 rounded-full blur-[90px]"
            style={{ backgroundColor: hexToRgba(accent, 0.07) }}
          />
        </>
      ) : null}
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-[32vh] bg-[linear-gradient(180deg,transparent_0%,rgba(2,6,23,0.82)_100%)]" />
      <div className="pointer-events-none absolute bottom-7 left-1/2 flex -translate-x-1/2 items-center gap-3">
        <span className="hud-pill">Interactive Orbital View</span>
        <span className="hud-pill">Drag To Rotate</span>
      </div>
    </div>
  );
}

function hexToRgba(hex: string, alpha: number) {
  const normalized = hex.replace("#", "");
  const safe = normalized.length === 3 ? normalized.split("").map((char) => `${char}${char}`).join("") : normalized;
  const red = Number.parseInt(safe.slice(0, 2), 16);
  const green = Number.parseInt(safe.slice(2, 4), 16);
  const blue = Number.parseInt(safe.slice(4, 6), 16);
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}
