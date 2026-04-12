from fastapi import APIRouter, HTTPException
try:
    from ..ml_pipeline.stepup.stepup_service import run_stepup
    from ..ml_pipeline.stepup.loader import get_spatial_model
except Exception:
    from app.ml_pipeline.stepup.stepup_service import run_stepup  # type: ignore
    from app.ml_pipeline.stepup.loader import get_spatial_model  # type: ignore

router = APIRouter(prefix="/stepup", tags=["StepUp"])

@router.post("/simulate")
def simulate(payload: dict):
    try:
        spatial_model = get_spatial_model()
        if spatial_model is None:
            raise HTTPException(
                status_code=503,
                detail="StepUp service unavailable: ML model incompatibility. Please regenerate the model with current scikit-learn version."
            )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"StepUp service unavailable: {str(e)}"
        )
    return run_stepup(payload)
