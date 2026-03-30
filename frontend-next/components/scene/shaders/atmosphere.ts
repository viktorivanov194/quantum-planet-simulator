import * as THREE from "three";

export function createAtmosphereMaterial({
  glowColor,
  starColor,
  thickness,
  glowIntensity,
  hazeIntensity,
  density,
}: {
  glowColor: string;
  starColor: string;
  thickness: number;
  glowIntensity: number;
  hazeIntensity: number;
  density: number;
}) {
  return new THREE.ShaderMaterial({
    uniforms: {
      glowColor: { value: new THREE.Color(glowColor) },
      starColor: { value: new THREE.Color(starColor) },
      thickness: { value: thickness },
      glowIntensity: { value: glowIntensity },
      hazeIntensity: { value: hazeIntensity },
      density: { value: density },
      starDirection: { value: new THREE.Vector3(5.4, 2.5, 2.4).normalize() },
      time: { value: 0 },
    },
    vertexShader: `
      varying vec3 vWorldPosition;
      varying vec3 vWorldNormal;

      void main() {
        vec4 worldPosition = modelMatrix * vec4(position, 1.0);
        vWorldPosition = worldPosition.xyz;
        vWorldNormal = normalize(mat3(modelMatrix) * normal);
        gl_Position = projectionMatrix * viewMatrix * worldPosition;
      }
    `,
    fragmentShader: `
      uniform vec3 glowColor;
      uniform vec3 starColor;
      uniform vec3 starDirection;
      uniform float thickness;
      uniform float glowIntensity;
      uniform float hazeIntensity;
      uniform float density;
      uniform float time;

      varying vec3 vWorldPosition;
      varying vec3 vWorldNormal;

      void main() {
        vec3 viewDirection = normalize(cameraPosition - vWorldPosition);
        vec3 normalDirection = normalize(vWorldNormal);

        float rimBase = 1.0 - max(dot(normalDirection, viewDirection), 0.0);
        float rim = pow(rimBase, 1.6 + thickness * 2.0);
        float starFacing = pow(max(dot(normalDirection, starDirection), 0.0), 1.35);
        float limbSoftness = smoothstep(0.06, 0.96, rim);
        float hazePulse = 0.92 + sin(time * 0.35) * 0.08;
        float hazeBody = smoothstep(0.0, 0.65 + hazeIntensity * 0.22, rim + hazeIntensity * 0.22);
        float nightLift = pow(1.0 - max(dot(normalDirection, starDirection), 0.0), 1.8) * 0.18 * hazeIntensity;

        vec3 dayScatter = mix(glowColor, starColor, starFacing * 0.52);
        vec3 scatteringColor = dayScatter + glowColor * nightLift;
        float alpha = limbSoftness * (0.12 + density * 0.1 + glowIntensity * 0.32) + hazeBody * hazeIntensity * 0.16 * hazePulse;

        gl_FragColor = vec4(scatteringColor, alpha);
      }
    `,
    transparent: true,
    depthWrite: false,
    side: THREE.BackSide,
    blending: THREE.AdditiveBlending,
  });
}
