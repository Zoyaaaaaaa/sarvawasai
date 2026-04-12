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

# Lazy loaded variables
_spatial_model = None
_loc_df = None
_hpi = None

def get_spatial_model():
    global _spatial_model
    if _spatial_model is None:
        with open(
            resolve_artifact(
                "spatial_random_forest2.pkl",
                Path(BASE) / "models" / "spatial_random_forest2.pkl",
            ),
            "rb"
        ) as f:
            _spatial_model = joblib.load(f)
    return _spatial_model

def get_loc_df():
    global _loc_df
    if _loc_df is None:
        _loc_df = pd.read_csv(
            resolve_raw_data(
                "mumbai_location_coordinates.csv",
                Path(BASE) / "data" / "mumbai_location_coordinates.csv",
            )
        )
    return _loc_df

def get_hpi():
    global _hpi
    if _hpi is None:
        _hpi = pd.read_csv(
            resolve_raw_data(
                "mumbai_hpi.csv",
                Path(BASE) / "data" / "mumbai_hpi.csv",
            )
        )
        _hpi["month"] = pd.to_datetime(_hpi["month"])
        _hpi.set_index("month", inplace=True)
        _hpi = _hpi.asfreq("MS")
        _hpi.columns = ["bhk1", "bhk2", "bhk3", "all"]
    return _hpi
