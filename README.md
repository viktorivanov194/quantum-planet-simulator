# Quantum Planet Simulator

Lightweight hackathon MVP skeleton for a hybrid exoplanet discovery workflow.

## Goals

- Generate a plausible exoplanet profile
- Validate the profile with lightweight rules and guardrails
- Suggest chemistry candidates for the environment
- Run a minimal quantum evaluation flow for a small molecule
- Generate a synthetic transmission spectrum
- Present a final discovery report

## Design Principles

- Keep everything CPU-first
- Favor cached and precomputed results over live heavy computation
- Support only small molecular systems
- Avoid large datasets, GPU requirements, and cloud-heavy setup
- Keep the code modular, readable, and easy to extend

## Project Structure

```text
backend/
  app/
    api/
      routes/
    core/
    models/
    services/
    main.py
frontend/
  app.py
data/
  cache/
requirements.txt
README.md
```

## Local Setup

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the FastAPI backend:

```bash
uvicorn app.main:app --app-dir backend --reload
```

4. Start the Streamlit frontend in a separate terminal:

```bash
streamlit run frontend/app.py
```

