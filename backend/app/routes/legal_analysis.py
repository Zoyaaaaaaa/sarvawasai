"""Legal Document Analysis API Routes
Endpoints for analyzing PDFs with focus on Indian real estate legalities
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
import logging

from .legal_analysis_service import (
    LegalAnalysisService,
    LegalAnalysisResponse,
    QuotaExceededError,
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
            "model": service.model_id,
            "focus": "Indian Real Estate Legalities"
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Legal service unavailable: {str(e)}"
        )


@router.post("/analyze-pdf", response_model=LegalAnalysisResponse, status_code=200)
async def analyze_legal_document(
    file: UploadFile = File(...),
    focus_area: str = Form(default="general"),
    language: str = Form(default="english")
):
    """Analyze a legal document PDF file upload."""
    try:
        service = get_legal_service()
        
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Validate focus area
        valid_focus_areas = ["general", "property_transfer", "mortgage", "tenant_rights", "rera_compliance"]
        if focus_area not in valid_focus_areas:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid focus_area. Must be one of: {', '.join(valid_focus_areas)}"
            )
        
        # Validate language
        valid_languages = ["english", "hindi", "mixed"]
        if language not in valid_languages:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid language. Must be one of: {', '.join(valid_languages)}"
            )

        logger.info(f"Analyzing uploaded PDF: {file.filename} with focus: {focus_area}")
        
        # Read file content
        pdf_content = await file.read()
        
        if not pdf_content:
            raise HTTPException(
                status_code=400,
                detail="File is empty"
            )
        
        # Perform analysis
        result = await service.analyze_pdf_content(
            pdf_bytes=pdf_content,
            focus_area=focus_area,
            language=language
        )
        
        logger.info(f"Successfully analyzed: {file.filename}")
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
    except QuotaExceededError as qe:
        logger.error(f"Quota error analyzing document: {str(qe)}")
        raise HTTPException(
            status_code=429,
            detail=str(qe)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing document: {str(e)}"
        )


@router.get("/analysis-types", response_model=dict)
async def get_analysis_types():
    """Get available analysis types and focus areas"""
    service = get_legal_service()
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
        "model": service.model_id,
        "expertise": "Indian Real Estate Law"
    }


@router.get("/help", response_model=dict)
async def help_endpoint():
    """Get help and documentation for legal analysis API"""
    return {
        "title": "Legal Document Analysis API",
        "description": "Analyze legal documents with focus on Indian real estate regulations",
        "endpoints": {
            "/legal/analyze-pdf": {
                "method": "POST",
                "description": "Analyze a PDF document",
                "parameters": {
                    "file": "PDF file to upload",
                    "focus_area": "general|property_transfer|mortgage|tenant_rights|rera_compliance",
                    "language": "english|hindi|mixed"
                }
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
