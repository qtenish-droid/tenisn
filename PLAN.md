# TENISN Plan

Goal: Build TENISN — a local-first AI Development OS (Electron + Python backend) with local model runtime, multi-agent orchestration, workflow builder, terminal & browser automation, and production-ready Windows installer.

Phases:

1) Repository bootstrap (this commit)
   - Create repo with skeleton files: Electron main, preload, renderer placeholder, FastAPI backend, plan, logo (SVG), installer conversion script.

2) Core runtime & IPC
   - Implement secure Electron main with contextIsolation, preload exposing minimal APIs, and a safe IPC contract.
   - Implement backend process manager in main to start/stop the FastAPI service and monitor health.

3) Local backend MVP
   - FastAPI service exposing: health, model-manager, agent-orchestrator, workflow-runner, memory API (SQLite + vector DB hooks), terminal execution endpoints (permissioned), browser automation endpoints (Playwright integration).
   - Local DB: SQLite for metadata, Chroma/Lance optional integration for vectors.

4) Model runtime & hardware detection
   - Hardware probe on first-run: CPU, RAM, GPU, CUDA/ROCm detection, disk space.
   - Model manager: discover, install, remove, optimize models (ollama / llama.cpp / gguf flows). Recommend quantization.

5) Workflow & multi-agent orchestration
   - Node-based visual workflow editor in renderer (drag/drop, connect nodes). Persist workflows to backend.
   - Agent system with task queues, priorities, retry, validation nodes, and logs.

6) Terminal & Browser Automation
   - Terminal: spawn shells with streamable output, permission checks, dangerous-command detection, rollback snapshots.
   - Browser: Playwright service endpoints, isolated profiles, screenshot and DOM analysis tools.

7) Security, Permissions & Git integration
   - Workspace-scoped permissions, approval dialogs, audit logs, encrypted credentials (OS vaults), git snapshot/rollback support.

8) Packaging & Installer
   - Windows installer (Inno Setup / nsis / Squirrel / Wix) to install app, register shortcuts, install runtime deps, optionally install starter models, and run hardware probe.
   - Code signing and auto-update integration.

9) Polishing & Monetization
   - Marketplace + sync (cloud-only features), subscription gating for cloud services only. Local AI remains free.

Deliverables for initial milestone (v0.1):
- Installable Electron app scaffold
- Local FastAPI backend with health and placeholder endpoints
- Secure IPC + preload
- Scalable SVG logo + conversion script for icons
- Detailed PLAN.md and contribution instructions

Next actions (short-term):
- Implement backend health and model-manager endpoints
- Create Electron UI skeleton and connect to backend health
- Add hardware probe on first-run and save recommendations to settings
- Prepare NSIS/Inno Setup installer template

Contribution: use branches for features, open PRs for major changes.
