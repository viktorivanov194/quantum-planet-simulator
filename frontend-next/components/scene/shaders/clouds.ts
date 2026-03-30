import * as THREE from "three";

export function createCloudShellMaterial({
  cloudMap,
  cloudTint,
  glowColor,
  opacity,
  hazeIntensity,
  thickness,
  driftScale,
  secondaryDriftScale,
  coverageBias,
}: {
  cloudMap: THREE.Texture | null;
  cloudTint: string;
  glowColor: string;
  opacity: number;
  hazeIntensity: number;
  thickness: number;
  driftScale: number;
  secondaryDriftScale: number;
  coverageBias: number;
}) {
  return new THREE.ShaderMaterial({
    uniforms: {
      cloudMap: { value: cloudMap },
      cloudTint: { value: new THREE.Color(cloudTint) },
      glowColor: { value: new THREE.Color(glowColor) },
      opacity: { value: opacity },
      hazeIntensity: { value: hazeIntensity },
      thickness: { value: thickness },
      driftScale: { value: driftScale },
      secondaryDriftScale: { value: secondaryDriftScale },
      coverageBias: { value: coverageBias },
      time: { value: 0 },
      starDirection: { value: new THREE.Vector3(5.4, 2.5, 2.4).normalize() },
    },
    vertexShader: `
      varying vec2 vUv;
      varying vec3 vWorldPosition;
      varying vec3 vWorldNormal;

      void main() {
        vUv = uv;
        vec4 worldPosition = modelMatrix * vec4(position, 1.0);
        vWorldPosition = worldPosition.xyz;
        vWorldNormal = normalize(mat3(modelMatrix) * normal);
        gl_Position = projectionMatrix * viewMatrix * worldPosition;
      }
    `,
    fragmentShader: `
      uniform sampler2D cloudMap;
      uniform vec3 cloudTint;
      uniform vec3 glowColor;
      uniform vec3 starDirection;
      uniform float opacity;
      uniform float hazeIntensity;
      uniform float thickness;
      uniform float driftScale;
      uniform float secondaryDriftScale;
      uniform float coverageBias;
      uniform float time;

      varying vec2 vUv;
      varying vec3 vWorldPosition;
      varying vec3 vWorldNormal;

      void main() {
        vec2 driftA = vUv * vec2(1.0 * driftScale, 0.92 * driftScale) + vec2(time * 0.0025 * driftScale, time * 0.0011 * driftScale);
        vec2 driftB = vUv * vec2(1.8 * secondaryDriftScale, 1.35 * secondaryDriftScale) - vec2(time * 0.0013 * secondaryDriftScale, time * 0.0022 * secondaryDriftScale);

        float layerA = texture2D(cloudMap, fract(driftA)).r;
        float layerB = texture2D(cloudMap, fract(driftB)).r;
        float density = mix(layerA, layerB, 0.45);

        float coverage = smoothstep(0.38 - hazeIntensity * 0.12 + coverageBias, 0.88 - thickness * 0.08 + coverageBias * 0.3, density);
        vec3 viewDirection = normalize(cameraPosition - vWorldPosition);
        float rim = pow(1.0 - max(dot(normalize(vWorldNormal), viewDirection), 0.0), 1.8);
        float starFacing = pow(max(dot(normalize(vWorldNormal), starDirection), 0.0), 1.3);

        vec3 finalColor = mix(cloudTint, glowColor, starFacing * 0.18 + rim * 0.12);
        float finalAlpha = coverage * opacity * (0.55 + rim * 0.45);

        if (finalAlpha < 0.02) {
          discard;
        }

        gl_FragColor = vec4(finalColor, finalAlpha);
      }
    `,
    transparent: true,
    depthWrite: false,
    side: THREE.FrontSide,
  });
}
