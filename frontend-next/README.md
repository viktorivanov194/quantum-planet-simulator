# Quantum Planet Simulator Frontend

Initial Next.js cinematic frontend scaffold for the existing Python backend.

## Planned Structure

```text
frontend-next/
  app/
    layout.tsx
    page.tsx
    globals.css
  components/
    hero/
    layout/
    presets/
    scene/
    simulation/
  lib/
    api/
    config/
    types/
  package.json
  tailwind.config.ts
  tsconfig.json
```

## Intended Local Run

1. Install Node.js 18+ and npm.
2. From `frontend-next/`, run:

```bash
npm install
npm run dev
```

3. Ensure the backend API is running on `http://127.0.0.1:8000`.

## Current Scope

- App Router scaffold
- Tailwind setup
- Preset switching
- Cinematic hero section
- Reusable 3D planet component with drag interaction
- Staged simulation shell
- Basic `/simulation/run` API integration

## Next Steps

1. Build richer per-stage content panels for validation, chemistry, quantum, and spectrum.
2. Add animated atmosphere composition visuals.
3. Add premium spectrum chart reveal with highlighted signatures.
4. Complete the final discovery card with backend report details and stage-specific motion choreography.
