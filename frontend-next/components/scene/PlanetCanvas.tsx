"use client";

import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Float, OrbitControls, Sparkles, Stars } from "@react-three/drei";
import * as THREE from "three";

import { QualityMode } from "@/lib/types/simulation";

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
  cloudMotionSpeed?: number;
  particleDensity?: number;
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

function AtmosphereRim({ color }: { color: string }) {
  const materialRef = useRef<THREE.ShaderMaterial>(null);

  const material = useMemo(
    () =>
      new THREE.ShaderMaterial({
        uniforms: {
          glowColor: { value: new THREE.Color(color) },
          coefficient: { value: 0.38 },
          power: { value: 2.6 }
        },
        vertexShader: `
          varying vec3 vNormal;
          void main() {
            vNormal = normalize(normalMatrix * normal);
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
          }
        `,
        fragmentShader: `
          uniform vec3 glowColor;
          uniform float coefficient;
          uniform float power;
          varying vec3 vNormal;
          void main() {
            float intensity = pow(coefficient - dot(vNormal, vec3(0.0, 0.0, 1.0)), power);
            gl_FragColor = vec4(glowColor, intensity * 0.85);
          }
        `,
        transparent: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        side: THREE.BackSide
      }),
    [color]
  );

  useFrame(() => {
    if (materialRef.current) {
      materialRef.current.uniforms.glowColor.value.set(color);
    }
  });

  return <primitive object={material} ref={materialRef} attach="material" />;
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
  cloudMotionSpeed = 0.3,
}: PlanetCanvasProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const ringRef = useRef<THREE.Mesh>(null);
  const shellRef = useRef<THREE.Mesh>(null);
  const haloRef = useRef<THREE.Points>(null);
  const surfaceTexture = useMemo(
    () => createSurfaceTexture(colors, surfaceVariationIntensity),
    [colors, surfaceVariationIntensity]
  );
  const cloudTexture = useMemo(() => createCloudTexture(cloudOpacity), [cloudOpacity]);
  const geometryDetail = qualityMode === "Cinematic" ? 96 : qualityMode === "Balanced" ? 72 : 48;

  const material = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: new THREE.Color(colors[1]),
        map: surfaceTexture,
        roughness: 0.92,
        metalness: 0.05,
        emissive: new THREE.Color(colors[2]),
        emissiveIntensity: 0.12
      }),
    [colors, surfaceTexture]
  );

  const cloudMaterial = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: new THREE.Color(cloudTint),
        map: cloudTexture,
        transparent: true,
        opacity: qualityMode === "Safe" ? cloudOpacity * 0.65 : cloudOpacity,
        roughness: 1,
        metalness: 0,
        emissive: new THREE.Color(glowColor),
        emissiveIntensity: 0.1
      }),
    [cloudOpacity, cloudTexture, cloudTint, glowColor, qualityMode]
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
    }
    if (shellRef.current) {
      shellRef.current.rotation.y -= delta * (0.012 + cloudMotionSpeed * 0.05);
      shellRef.current.rotation.z += delta * (0.006 + cloudMotionSpeed * 0.03);
    }
    if (ringRef.current) {
      ringRef.current.rotation.z += delta * 0.045;
    }
    if (haloRef.current) {
      haloRef.current.rotation.y += delta * 0.014;
    }
  });

  return (
    <group position={[0, 0, 0]}>
      <mesh ref={meshRef} material={material}>
        <sphereGeometry args={[1.52, geometryDetail, geometryDetail]} />
      </mesh>
      <mesh scale={1.05 + atmosphereRimWidth * 0.16}>
        <sphereGeometry args={[1.54, 64, 64]} />
        <AtmosphereRim color={glowColor} />
      </mesh>
      <mesh ref={shellRef} material={cloudMaterial} scale={1.03}>
        <sphereGeometry args={[1.56, Math.max(24, geometryDetail * 0.75), Math.max(24, geometryDetail * 0.75)]} />
      </mesh>
      <mesh scale={1.12 + atmosphereThicknessVisual * 0.14}>
        <sphereGeometry args={[1.58, 64, 64]} />
        <meshBasicMaterial color={glowColor} transparent opacity={0.05 + atmosphereGlowIntensity * 0.12} />
      </mesh>
      <mesh scale={1.18 + atmosphereThicknessVisual * 0.22}>
        <sphereGeometry args={[1.62, 64, 64]} />
        <meshBasicMaterial color={glowColor} transparent opacity={0.025 + atmosphereGlowIntensity * 0.08} />
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
  const starCountBase = qualityMode === "Cinematic" ? 3200 : qualityMode === "Balanced" ? 2200 : 1400;
  const sparkleBase = qualityMode === "Cinematic" ? 80 : qualityMode === "Balanced" ? 48 : 18;
  const starCount = Math.round(starCountBase * starScale);
  const sparkleCount = Math.round(sparkleBase * Math.max(0.65, starScale) * particleScale);
  const fov = props.cameraFov ?? 34;

  return (
    <div className="absolute inset-0">
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_52%,rgba(255,255,255,0.05),transparent_22%),linear-gradient(180deg,rgba(2,6,23,0.16),rgba(2,6,23,0.72))]"
      />
      <div className="pointer-events-none absolute inset-0 orbit-grid opacity-[0.14]" />
      <Canvas camera={{ position: [0, 0.04, props.cameraDistance], fov }}>
        <fog attach="fog" args={["#040816", 6, 12]} />
        <color attach="background" args={["#030711"]} />
        <ambientLight intensity={qualityMode === "Safe" ? 0.46 : 0.48 + (props.terminatorContrast ?? 0.5) * 0.18} color={props.fillLightColor} />
        <hemisphereLight intensity={0.58} groundColor="#020617" color={props.fillLightColor} />
        <directionalLight position={[5.4, 2.5, 2.4]} intensity={1.7 + (props.terminatorContrast ?? 0.5) * 1.0} color={props.hostStarColor} />
        <directionalLight position={[-5.4, -2.3, -3.2]} intensity={0.18 + (1 - (props.terminatorContrast ?? 0.5)) * 0.28} color={props.fillLightColor} />
        <pointLight position={[-2.5, -0.6, 2.4]} intensity={0.95} color={props.glowColor} />
        <Stars radius={110} depth={55} count={starCount} factor={3.2} saturation={0} fade speed={0.35} />
        <Sparkles count={sparkleCount} scale={[7.5, 4.4, 6]} size={2.4} speed={0.16} color={props.glowColor} />
        <Float speed={0.7} rotationIntensity={0.08} floatIntensity={0.2}>
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
      <div
        className="pointer-events-none absolute left-1/2 top-[13%] h-44 w-44 -translate-x-1/2 rounded-full opacity-70 blur-[110px]"
        style={{ backgroundColor: props.hostStarColor }}
      />
      <div
        className="pointer-events-none absolute left-[18%] top-[10%] h-56 w-56 rounded-full opacity-40 blur-[140px]"
        style={{ backgroundColor: props.glowColor }}
      />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-[32vh] bg-[linear-gradient(180deg,transparent_0%,rgba(2,6,23,0.82)_100%)]" />
      <div className="pointer-events-none absolute bottom-7 left-1/2 flex -translate-x-1/2 items-center gap-3">
        <span className="hud-pill">Interactive Orbital View</span>
        <span className="hud-pill">Drag To Rotate</span>
      </div>
    </div>
  );
}
