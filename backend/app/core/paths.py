from pathlib import Path
from typing import Iterable

APP_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = APP_ROOT.parent
PROJECT_ROOT = BACKEND_ROOT.parent

BACKEND_DATA = BACKEND_ROOT / "data"
BACKEND_CONFIG = BACKEND_ROOT / "config"
BACKEND_ASSETS = BACKEND_ROOT / "assets"

ARTIFACTS_DIR = BACKEND_DATA / "artifacts"
RAW_DATA_DIR = BACKEND_DATA / "raw"
PROCESSED_DATA_DIR = BACKEND_DATA / "processed"


def resolve_existing_path(candidates: Iterable[Path]) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    checked = "\n".join(str(c) for c in candidates)
    raise FileNotFoundError(f"Could not resolve path. Checked:\n{checked}")


def resolve_artifact(filename: str, *fallbacks: Path) -> Path:
    candidates = [ARTIFACTS_DIR / filename, *fallbacks]
    return resolve_existing_path(candidates)


def resolve_raw_data(filename: str, *fallbacks: Path) -> Path:
    candidates = [RAW_DATA_DIR / filename, *fallbacks]
    return resolve_existing_path(candidates)


def resolve_config(filename: str, *fallbacks: Path) -> Path:
    candidates = [BACKEND_CONFIG / filename, *fallbacks]
    return resolve_existing_path(candidates)


def resolve_asset(filename: str, *fallbacks: Path) -> Path:
    candidates = [BACKEND_ASSETS / filename, *fallbacks]
    return resolve_existing_path(candidates)
