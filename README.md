# Sarvawas AI

Monorepo containing the Sarvawas backend API, frontend app, and ML/data workflows.

## Production-Oriented Layout

- `backend/`: FastAPI service and backend tests
- `frontend/`: Vite + React web client
- `data/`: shared datasets, model bundles, and snapshots
- `investor_similarity/`: similarity engine package and examples
- `ml_training/`: training, evaluation, and packaging workflows
- `docs/`: architecture and operations docs
- `tools/`: utility scripts
- `configs/`: shared deployment/config templates

Reference details:

- `docs/architecture/repository-structure.md`
- `docs/operations/local-development.md`

## Run Backend

```powershell
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Run Frontend

```powershell
cd frontend
npm install
npm run dev
```

## Data Organization

Loose legacy CSV assets were moved under:

- `data/raw/legacy/buyer_investor_matches.csv`
- `data/raw/legacy/homebuyer_profiles_mumbai.csv`
- `data/raw/legacy/survey_responses.csv`
