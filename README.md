# TENISN

Tenisn — Local-first AI Development Operating System.

This repo contains an Electron shell and a local FastAPI backend.

New endpoints added:
- GET /api/hardware/probe — hardware detection (CPU, RAM, disk, GPUs)
- GET /api/models/recommend — model recommendations based on hardware
- GET /api/models/list — list installed models (persisted in SQLite)
- POST /api/models/install — queue install of a model (persists to SQLite)
- POST /api/terminal/exec — terminal execution with dry-run and dangerous-command detection

Run backend locally:
1. python -m venv .venv
2. .\.venv\Scripts\activate
3. pip install -r backend/requirements.txt
4. python -m backend.main

The Electron app (src/electron) will spawn the backend on start. Update: hardware probe, model-manager placeholders, database persistence, and terminal endpoint were added.
