# Frontend Structure

## App Layer

- src/app/: routing and provider composition
- src/app/providers/: application-level React providers

## Domain and Shared Layers

- src/features/: feature-oriented modules (incremental migration target)
- src/shared/lib/: cross-cutting shared utilities

## Compatibility

Existing imports from src/lib and src/context remain valid through shim files while migration continues.
