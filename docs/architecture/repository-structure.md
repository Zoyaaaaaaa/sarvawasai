# Repository Structure

This document reflects the current workspace layout.

## Top Level

- `backend/`: FastAPI backend service, API routes, ML pipeline code, templates, and backend-scoped data/config/assets.
- `frontend/`: Vite + React web client.
- `docs/`: Architecture and operations documentation.

## Backend Layout

- `backend/app/`: Main backend source tree.
- `backend/app/core/`: Shared backend runtime utilities (including path resolution helpers).
- `backend/app/routes/`: FastAPI route modules.
- `backend/app/services/`: Service-layer modules.
- `backend/app/ml_pipeline/`: ML pipeline and model loading logic.
- `backend/app/templates/`: PDF/document templates and rendering assets.
- `backend/app/models/`: Legacy model artifacts still referenced by compatibility fallbacks.
- `backend/data/`: Canonical backend-scoped data storage.
	- `backend/data/artifacts/`: Runtime model binaries and scalers.
	- `backend/data/raw/`: Raw input datasets.
	- `backend/data/processed/`: Processed datasets and derived tables.
- `backend/config/`: Runtime configuration payloads.
- `backend/assets/`: Static backend assets.
- `backend/blockchain/`: Reserved blockchain integration folder (currently empty).

## Frontend Layout

- `frontend/src/app/`: App composition layer (routing and providers).
- `frontend/src/features/`: Feature-oriented modules (incremental migration target).
- `frontend/src/shared/`: Shared utilities and cross-cutting modules.
- `frontend/src/components/`: Reusable UI components.
- `frontend/src/pages/`: Route-level screens.
- `frontend/src/lib/` and `frontend/src/context/`: Compatibility shims for older imports.
- `frontend/public/`: Static public assets.

## Generated and Local-Only Directories

- `frontend/dist/`: Frontend production build output.
- `frontend/node_modules/`: Frontend dependency installation directory.
- `backend/app/.venv/`: Local virtual environment inside backend app tree.

These directories are environment/build outputs and should stay excluded from version control.
