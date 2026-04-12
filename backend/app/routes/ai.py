# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel, Field, validator
# from typing import Optional, Dict, Any, List
# import pandas as pd
# import numpy as np
# import pickle
# import logging
# from datetime import datetime
# import re
# from pathlib import Path
# import traceback

# # Configure logging
# logger = logging.getLogger(__name__)

# from .models import ProjectInput, PredictionResponse, ModelManager

# router = APIRouter(prefix="/ai")

# # Global model manager instance
# model_manager = ModelManager()

# @router.on_event("startup")
# async def startup_event():
#     """Load models on startup"""
#     try:
#         logger.info("Starting model loading process...")
#         model_manager.load_models()
#         logger.info("Models loaded successfully on startup")
#     except Exception as e:
#         logger.error(f"Failed to load models on startup: {str(e)}")
#         logger.error(f"Full traceback: {traceback.format_exc()}")

# @router.get("/")
# async def get_apicall():
#     return {"message": "Hello from FastAPI! AI SIDE"}

# @router.get("/health")
# async def health_check():
#     """Health check endpoint"""
#     return {
#         "status": "healthy",
#         "model_loaded": model_manager.is_loaded,
#         "timestamp": datetime.now().isoformat()
#     }

# @router.get("/model-info")
# async def model_info():
#     """Get model information"""
#     if not model_manager.is_loaded:
#         try:
#             model_manager.load_models()
#         except Exception as e:
#             logger.error(f"Model loading failed in model-info: {str(e)}")
#             raise HTTPException(status_code=503, detail=f"Models not available: {str(e)}")
    
#     return {
#         "model_loaded": model_manager.is_loaded,
#         "feature_count": len(model_manager.feature_columns) if model_manager.feature_columns else 0,
#         "feature_columns": model_manager.feature_columns[:10] if model_manager.feature_columns else [],
#         "categorical_encoders": list(model_manager.label_encoders.keys()) if model_manager.label_encoders else [],
#         "model_type": str(type(model_manager.model).__name__) if model_manager.model else None
#     }

# @router.post("/predict", response_model=PredictionResponse)
# async def predict_completion(project_data: ProjectInput):
#     """Predict project completion status"""
#     try:
#         # Log the input data for debugging
#         logger.info(f"Received prediction request for project: {project_data.project_name}")
#         logger.info(f"Input features: apartments={project_data.number_of_appartments}, "
#                    f"booked={project_data.number_of_booked_appartments}, "
#                    f"area={project_data.project_area_sqmts}")
        
#         result = model_manager.predict(project_data)
        
#         logger.info(f"Prediction completed. Status: {result.prediction}, "
#                    f"Confidence: {result.confidence}, "
#                    f"Probabilities: {result.probabilities}")
        
#         return result
#     except Exception as e:
#         logger.error(f"Prediction endpoint error: {str(e)}")
#         logger.error(f"Full traceback: {traceback.format_exc()}")
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/predict-batch")
# async def predict_batch(projects: List[ProjectInput]):
#     """Predict completion status for multiple projects"""
#     if len(projects) > 100:
#         raise HTTPException(status_code=400, detail="Maximum 100 projects per batch")
    
#     try:
#         results = []
#         for i, project in enumerate(projects):
#             try:
#                 result = model_manager.predict(project)
#                 results.append({"index": i, "result": result.dict(), "error": None})
#             except Exception as e:
#                 logger.error(f"Error predicting project {i}: {str(e)}")
#                 results.append({"index": i, "result": None, "error": str(e)})
        
#         return {"predictions": results, "total": len(projects)}
    
#     except Exception as e:
#         logger.error(f"Batch prediction error: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/debug-features")
# async def debug_features(project_data: ProjectInput):
#     """Debug endpoint to see feature construction"""
#     try:
#         if not model_manager.is_loaded:
#             model_manager.load_models()
        
#         # Create feature dictionary
#         input_dict = project_data.dict()
        
#         # Convert to DataFrame
#         df = pd.DataFrame([input_dict])
        
#         # Apply feature engineering (same as in training)
#         df = model_manager._apply_feature_engineering(df)
        
#         # Show the constructed features
#         feature_values = {}
#         for col in model_manager.feature_columns:
#             if col in df.columns:
#                 feature_values[col] = float(df[col].iloc[0]) if pd.notna(df[col].iloc[0]) else None
#             else:
#                 feature_values[col] = None
        
#         return {
#             "input_data": input_dict,
#             "engineered_features": feature_values,
#             "feature_count": len(feature_values),
#             "missing_features": [col for col in model_manager.feature_columns if col not in df.columns]
#         }
    
#     except Exception as e:
#         logger.error(f"Debug features error: {str(e)}")
#         logger.error(f"Full traceback: {traceback.format_exc()}")
#         raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
import pickle
import logging
from datetime import datetime
import re
from pathlib import Path
import traceback

# Configure logging
logger = logging.getLogger(__name__)

from .models import ProjectInput, PredictionResponse, ModelManager

router = APIRouter(prefix="/ai")

# Global model manager instance
model_manager = ModelManager()

@router.on_event("startup")
async def startup_event():
    """Load models on startup"""
    try:
        logger.info("Starting model loading process...")
        model_manager.load_models()
        logger.info("Models loaded successfully on startup")
    except Exception as e:
        logger.error(f"Failed to load models on startup: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")

@router.get("/")
async def get_apicall():
    return {"message": "Hello from FastAPI! AI SIDE"}

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model_manager.is_loaded,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/model-info")
async def model_info():
    """Get model information"""
    if not model_manager.is_loaded:
        try:
            model_manager.load_models()
        except Exception as e:
            logger.error(f"Model loading failed in model-info: {str(e)}")
            raise HTTPException(status_code=503, detail=f"Models not available: {str(e)}")
    
    return {
        "model_loaded": model_manager.is_loaded,
        "feature_count": len(model_manager.feature_columns) if model_manager.feature_columns else 0,
        "feature_columns": model_manager.feature_columns[:10] if model_manager.feature_columns else [],
        "categorical_encoders": list(model_manager.label_encoders.keys()) if model_manager.label_encoders else [],
        "model_type": str(type(model_manager.model).__name__) if model_manager.model else None
    }

@router.post("/predict", response_model=PredictionResponse)
async def predict_completion(project_data: ProjectInput):
    """Predict project completion status"""
    try:
        # Log the input data for debugging
        logger.info(f"Received prediction request for project: {project_data.project_name}")
        logger.info(f"Input features: apartments={project_data.number_of_appartments}, "
                   f"booked={project_data.number_of_booked_appartments}, "
                   f"area={project_data.project_area_sqmts}")
        
        result = model_manager.predict(project_data)
        
        logger.info(f"Prediction completed. Status: {result.prediction}, "
                   f"Confidence: {result.confidence}, "
                   f"Probabilities: {result.probabilities}")
        
        return result
    except Exception as e:
        logger.error(f"Prediction endpoint error: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict-batch")
async def predict_batch(projects: List[ProjectInput]):
    """Predict completion status for multiple projects"""
    if len(projects) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 projects per batch")
    
    try:
        results = []
        for i, project in enumerate(projects):
            try:
                result = model_manager.predict(project)
                results.append({"index": i, "result": result.dict(), "error": None})
            except Exception as e:
                logger.error(f"Error predicting project {i}: {str(e)}")
                results.append({"index": i, "result": None, "error": str(e)})
        
        return {"predictions": results, "total": len(projects)}
    
    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/debug-features")
async def debug_features(project_data: ProjectInput):
    """Debug endpoint to see feature construction"""
    try:
        if not model_manager.is_loaded:
            model_manager.load_models()
        
        # Create feature dictionary
        input_dict = project_data.dict()
        
        # Convert to DataFrame
        df = pd.DataFrame([input_dict])
        
        # Apply feature engineering (same as in training)
        df = model_manager._apply_feature_engineering(df)
        
        # Show the constructed features
        feature_values = {}
        for col in model_manager.feature_columns:
            if col in df.columns:
                feature_values[col] = float(df[col].iloc[0]) if pd.notna(df[col].iloc[0]) else None
            else:
                feature_values[col] = None
        
        return {
            "input_data": input_dict,
            "engineered_features": feature_values,
            "feature_count": len(feature_values),
            "missing_features": [col for col in model_manager.feature_columns if col not in df.columns]
        }
    
    except Exception as e:
        logger.error(f"Debug features error: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model-diagnostics")
async def model_diagnostics():
    """Get detailed model diagnostics"""
    try:
        if not model_manager.is_loaded:
            model_manager.load_models()
        
        # Get model info
        model = model_manager.model
        classifier = model.named_steps['classifier']
        
        diagnostics = {
            "model_loaded": model_manager.is_loaded,
            "model_type": str(type(classifier).__name__),
            "n_classes": len(classifier.classes_) if hasattr(classifier, 'classes_') else None,
            "classes": classifier.classes_.tolist() if hasattr(classifier, 'classes_') else None,
            "n_estimators": classifier.n_estimators if hasattr(classifier, 'n_estimators') else None,
            "feature_count": len(model_manager.feature_columns),
            "sample_features": model_manager.feature_columns[:20],
            "categorical_features": list(model_manager.label_encoders.keys())[:10],
            "feature_medians_sample": dict(list(model_manager.feature_medians.items())[:10])
        }
        
        return diagnostics
    
    except Exception as e:
        logger.error(f"Diagnostics error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))