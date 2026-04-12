# Backend Structure

## Runtime

- app/: FastAPI application source
- app/routes/: API routers
- app/core/: shared backend runtime utilities
- app/services/: business logic modules

## Production Data Layout

- data/artifacts/: model binaries used at runtime
- data/raw/: canonical raw datasets used by APIs and offline jobs
- data/processed/: processed datasets used for training and analysis
- config/: runtime templates and static config payloads
- assets/: image/static assets consumed by APIs

## Compatibility

Legacy files are still supported through resolver fallbacks to avoid runtime breakage while migration completes.
