import os
import joblib
import pandas as pd
from pathlib import Path

try:
    from ...core.paths import resolve_artifact, resolve_raw_data  # type: ignore
except Exception:
    try:
        from app.core.paths import resolve_artifact, resolve_raw_data  # type: ignore
    except Exception:
        from core.paths import resolve_artifact, resolve_raw_data  # type: ignore

BASE = os.path.dirname(__file__)

# -----------------------------------------------------
# LOAD SPATIAL MODEL
# -----------------------------------------------------
with open(
    resolve_artifact(
        "spatial_random_forest2.pkl",
        Path(BASE) / "models" / "spatial_random_forest2.pkl",
    ),
    "rb"
) as f:
    spatial_model = joblib.load(f)

# -----------------------------------------------------
# LOAD LOCALITY COORDINATES
# -----------------------------------------------------
loc_df = pd.read_csv(
    resolve_raw_data(
        "mumbai_location_coordinates.csv",
        Path(BASE) / "data" / "mumbai_location_coordinates.csv",
    )
)

# -----------------------------------------------------
# LOAD HPI DATA
# -----------------------------------------------------
hpi = pd.read_csv(
    resolve_raw_data(
        "mumbai_hpi.csv",
        Path(BASE) / "data" / "mumbai_hpi.csv",
    )
)

hpi["month"] = pd.to_datetime(hpi["month"])
hpi.set_index("month", inplace=True)
hpi = hpi.asfreq("MS")

hpi.columns = ["bhk1", "bhk2", "bhk3", "all"]
