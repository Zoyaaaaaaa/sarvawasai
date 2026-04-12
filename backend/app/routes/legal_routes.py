"""
Legal Document Analysis API Routes
Endpoints for analyzing PDFs with focus on Indian real estate legalities
"""

from fastapi import APIRouter, HTTPException, File, UploadFile, Query
from typing import Optional
import logging
import os

from .legal_analysis_service import (
    LegalAnalysisService,
    LegalAnalysisRequest,
    LegalAnalysisResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/legal", tags=["legal"])

# Global service instance
_legal_service = None


def get_legal_service() -> LegalAnalysisService:
    """Get or initialize the legal analysis service"""
    global _legal_service
    if _legal_service is None:
        try:
            _legal_service = LegalAnalysisService()
        except ImportError as e:
            logger.error(f"Failed to initialize legal service: {e}")
            raise
    return _legal_service


@router.on_event("startup")
async def startup_event():
    """Initialize legal service on startup"""
    try:
        get_legal_service()
        logger.info("Legal Analysis Service initialized successfully")
    except Exception as e:
        logger.warning(f"Legal Analysis Service not initialized: {e}")


@router.get("/", response_model=dict, status_code=200)
async def legal_health_check():
    """Health check for legal analysis service"""
    try:
        service = get_legal_service()
        return {
            "status": "healthy",
            "service": "Legal Document Analysis",
            "model": "gemini-2.5-flash",
            "focus": "Indian Real Estate Legalities"
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Legal service unavailable: {str(e)}"
        )


@router.post("/analyze-pdf", response_model=LegalAnalysisResponse, status_code=200)
async def analyze_legal_document(request: LegalAnalysisRequest):
    """
    Analyze a legal document PDF from Google Cloud Storage.
    
    Args:
        request: LegalAnalysisRequest containing:
            - file_uri: GCS path (gs://bucket/file.pdf)
            - analysis_type: comprehensive, summary, or specific
            - focus_area: general, property_transfer, mortgage, tenant_rights, rera_compliance
            - language: english, hindi, or mixed
    
    Returns:
        LegalAnalysisResponse with comprehensive legal analysis
    
    Example:
        ```
        {
            "file_uri": "gs://cloud-samples-data/generative-ai/pdf/sample.pdf",
            "focus_area": "property_transfer",
            "language": "english"
        }
        ```
    """
    try:
        service = get_legal_service()
        
        # Validate request
        valid_focus_areas = ["general", "property_transfer", "mortgage", "tenant_rights", "rera_compliance"]
        if request.focus_area not in valid_focus_areas:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid focus_area. Must be one of: {', '.join(valid_focus_areas)}"
            )
        
        valid_languages = ["english", "hindi", "mixed"]
        if request.language not in valid_languages:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid language. Must be one of: {', '.join(valid_languages)}"
            )
        
        logger.info(f"Analyzing PDF: {request.file_uri} with focus: {request.focus_area}")
        
        # Perform analysis
        result = await service.analyze_pdf(request)
        
        logger.info(f"Successfully analyzed: {request.file_uri}")
        return result
    
    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except ImportError as ie:
        logger.error(f"Service initialization error: {str(ie)}")
        raise HTTPException(
            status_code=503,
            detail="Legal analysis service not available. Please install google-genai package."
        )
    except Exception as e:
        logger.error(f"Error analyzing document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing document: {str(e)}"
        )


@router.get("/analysis-types", response_model=dict)
async def get_analysis_types():
    """Get available analysis types and focus areas"""
    return {
        "analysis_types": [
            {
                "type": "comprehensive",
                "description": "Full analysis of all legal aspects"
            },
            {
                "type": "summary",
                "description": "Concise summary of key legal points"
            },
            {
                "type": "specific",
                "description": "Analysis focused on specific area"
            }
        ],
        "focus_areas": [
            {
                "code": "general",
                "name": "General",
                "description": "All relevant legal aspects"
            },
            {
                "code": "property_transfer",
                "name": "Property Transfer",
                "description": "Title verification, ownership chain, transfer taxes, registration"
            },
            {
                "code": "mortgage",
                "name": "Mortgage Agreement",
                "description": "Loan terms, default clauses, foreclosure procedures"
            },
            {
                "code": "tenant_rights",
                "name": "Tenant Rights",
                "description": "Rent control, lease terms, eviction procedures, security deposits"
            },
            {
                "code": "rera_compliance",
                "name": "RERA Compliance",
                "description": "Project registration, disclosure, timeline, buyer protection"
            }
        ],
        "languages": ["english", "hindi", "mixed"],
        "model": "gemini-2.5-flash",
        "expertise": "Indian Real Estate Law"
    }


@router.post("/batch-analyze", status_code=200)
async def batch_analyze_documents(requests: list[LegalAnalysisRequest]) -> dict:
    """
    Analyze multiple legal documents in batch.
    
    Args:
        requests: List of LegalAnalysisRequest objects
    
    Returns:
        Dictionary with analysis results and any errors
    """
    if len(requests) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 documents per batch request"
        )
    
    try:
        service = get_legal_service()
        results = []
        errors = []
        
        for idx, request in enumerate(requests):
            try:
                logger.info(f"Batch analysis [{idx+1}/{len(requests)}]: {request.file_uri}")
                result = await service.analyze_pdf(request)
                results.append({
                    "index": idx,
                    "file_uri": request.file_uri,
                    "result": result.dict(),
                    "error": None
                })
            except Exception as e:
                logger.error(f"Error analyzing batch item {idx}: {str(e)}")
                errors.append({
                    "index": idx,
                    "file_uri": request.file_uri,
                    "error": str(e)
                })
        
        return {
            "total_documents": len(requests),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }
    
    except Exception as e:
        logger.error(f"Batch analysis error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch analysis error: {str(e)}")


@router.get("/help", response_model=dict)
async def help_endpoint():
    """Get help and documentation for legal analysis API"""
    return {
        "title": "Legal Document Analysis API",
        "description": "Analyze legal documents with focus on Indian real estate regulations",
        "endpoints": {
            "/legal/analyze-pdf": {
                "method": "POST",
                "description": "Analyze a single PDF document",
                "parameters": {
                    "file_uri": "gs://cloud-samples-data/path/file.pdf",
                    "analysis_type": "comprehensive|summary|specific",
                    "focus_area": "general|property_transfer|mortgage|tenant_rights|rera_compliance",
                    "language": "english|hindi|mixed"
                }
            },
            "/legal/batch-analyze": {
                "method": "POST",
                "description": "Analyze multiple PDFs (max 10)",
                "parameters": "Array of analyze-pdf parameters"
            },
            "/legal/analysis-types": {
                "method": "GET",
                "description": "Get available analysis types and focus areas"
            }
        },
        "setup": {
            "required": "Set GOOGLE_API_KEY environment variable",
            "install": "pip install google-genai"
        },
        "example_response": {
            "status": "success",
            "analysis": "Comprehensive legal analysis text...",
            "key_points": ["Point 1", "Point 2"],
            "recommendations": ["Recommendation 1"],
            "risk_factors": ["Risk 1"],
            "model_used": "gemini-2.5-flash"
        }
    }
