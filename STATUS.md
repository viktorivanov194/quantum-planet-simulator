# Quantum Planet Simulator Status

## Current State

Project currently has:

- Python backend pipeline already implemented and kept unchanged in the latest frontend passes:
  - planet generation
  - validation guardrails
  - chemistry candidate engine
  - cache-first quantum evaluation
  - synthetic spectrum engine
  - final discovery report
- Legacy Streamlit demo exists in `frontend/`
- New cinematic Next.js frontend exists in `frontend-next/`

## Latest Frontend State

The active frontend direction is `frontend-next/` and it is now scene-first, not dashboard-first.

Implemented there:

- fullscreen immersive planet scene
- reusable `PlanetCanvas` based on `react-three-fiber`
- drag rotation + autorotate + damping/inertia feel
- preset-driven look for:
  - Temperate Water World
  - Hot Dense Carbon World
  - Cold Methane Frontier
- quality modes:
  - Cinematic
  - Balanced
  - Safe
- procedural surface variation
- cloud layer motion
- atmospheric rim glow
- preset-driven lighting mood
- floating atmosphere overlay
- chemistry candidate floating chips
- quantum chamber overlay
- spectrum instrumentation overlay
- final discovery overlay card

## Files Most Recently Shaped

- `frontend-next/components/scene/PlanetCanvas.tsx`
- `frontend-next/components/simulation/SimulationShell.tsx`
- `frontend-next/components/hero/HeroScene.tsx`
- `frontend-next/components/presets/PresetSwitcher.tsx`
- `frontend-next/lib/config/presets.ts`
- `frontend-next/lib/types/simulation.ts`
- `frontend-next/app/globals.css`

## What Works

- `frontend-next` builds successfully with `npm run build`
- backend API integration remains through the existing `/simulation/run` endpoint
- no backend architecture changes were made during the cinematic frontend work

## Most Logical Next Steps

1. Make the overlay system truly stage-aware.
   - Atmosphere, chemistry, quantum, spectrum, and discovery should reveal progressively based on the active simulation stage, not all as one final block.

2. Improve chemistry motion language.
   - Candidate chips should orbit or drift more naturally around the planet before selected candidates lock in.

3. Upgrade the spectrum reveal choreography.
   - Add a sweep/scan animation and stronger highlighted-band timing.

4. Refine final discovery lockup.
   - Final report should feel like the climactic conclusion while keeping the planet visible behind it.

5. Optional polish pass.
   - spacing
   - mobile behavior
   - copy refinement
   - small performance trimming if needed

## Local Runtime Status

As of this snapshot, local dev processes were intentionally stopped:

- Next.js on `127.0.0.1:3000`
- FastAPI on `127.0.0.1:8000`
- Streamlit on `8501`

## How To Resume

Backend:

```bash
source .venv/bin/activate
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Next frontend:

```bash
cd frontend-next
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Optional legacy Streamlit demo:

```bash
source .venv/bin/activate
streamlit run frontend/app.py
```
