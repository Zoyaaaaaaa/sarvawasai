from fastapi import APIRouter, HTTPException
try:
    from ..ml_pipeline.stepup.stepup_service import run_stepup
    from ..ml_pipeline.stepup.loader import spatial_model
except Exception:
    from app.ml_pipeline.stepup.stepup_service import run_stepup  # type: ignore
    from app.ml_pipeline.stepup.loader import spatial_model  # type: ignore

router = APIRouter(prefix="/stepup", tags=["StepUp"])

@router.post("/simulate")
def simulate(payload: dict):
    if spatial_model is None:
        raise HTTPException(
            status_code=503,
            detail="StepUp service unavailable: ML model incompatibility. Please regenerate the model with current scikit-learn version."
        )
    return run_stepup(payload)
