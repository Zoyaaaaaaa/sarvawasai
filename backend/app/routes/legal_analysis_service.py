import os
import logging
import base64
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Import Google Genai
try:
    from google import genai
    from google.genai.types import HttpOptions, Part
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-genai not available. Please install via: pip install google-genai")


class LegalAnalysisResponse(BaseModel):
    """Response model for legal analysis"""
    status: str = Field(description="Success or failure status")
    analysis: str = Field(description="The legal analysis of the document")
    key_points: list = Field(default_factory=list, description="Key legal points extracted")
    recommendations: list = Field(default_factory=list, description="Recommendations for the user")
    risk_factors: list = Field(default_factory=list, description="Potential legal risks identified")
    model_used: str = Field(default="gemini-2.5-flash", description="Model used for analysis")


class QuotaExceededError(Exception):
    """Raised when the Gemini API quota is exceeded"""
    pass


class LegalAnalysisService:
    """Service for analyzing legal documents using Google Gemini API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the legal analysis service"""
        if not GENAI_AVAILABLE:
            raise ImportError("google-genai package is required. Install with: pip install google-genai")
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set")
        
        self.client = genai.Client(
            api_key=self.api_key,
            http_options=HttpOptions(api_version="v1")
        )
        self.model_id = os.getenv("GEMINI_MODEL_ID", "gemini-2.5-flash-lite")
    
    def get_system_prompt(self, focus_area: str = "general", language: str = "english") -> str:
        """Generate system prompt based on focus area and language"""
        
        base_prompt = """You are a highly skilled legal document analysis specialist with expertise in Indian real estate law and regulations. 
Your task is to analyze legal documents with a focus on Indian legal framework including:
- RERA (Real Estate Regulation and Development Act)
- Property Transfer Act and regulations
- Stamp Duty and Registration laws
- Landlord-Tenant Act (vary by state)
- Housing Finance regulations
- Environmental and Municipal compliance

Provide analysis in a clear, professional manner suitable for non-lawyers."""

        focus_prompts = {
            "property_transfer": """Focus your analysis on property transfer legalities including:
- Title verification requirements
- Chain of ownership
- Encumbrances and liabilities
- Transfer tax implications
- Registration procedures under Indian Registration Act""",
            
            "mortgage": """Focus your analysis on mortgage/loan agreement legalities including:
- Mortgage terms and conditions
- Default clauses and penalties
- Prepayment terms
- Foreclosure procedures under Hindu Succession Act
- Lender's rights and borrower's obligations""",
            
            "tenant_rights": """Focus your analysis on tenant and landlord legalities including:
- Rent control regulations
- Lease terms and conditions
- Eviction procedures
- Security deposits and their usage
- Maintenance and repair obligations""",
            
            "rera_compliance": """Focus your analysis on RERA (Real Estate Regulation and Development Act) compliance including:
- Project registration requirements
- Disclosure obligations
- Timeline and completion clauses
- Buyer protection mechanisms
- Remedies for breach""",
            
            "general": """Provide comprehensive analysis covering all relevant legal aspects of the document."""
        }
        
        focus_text = focus_prompts.get(focus_area, focus_prompts["general"])
        
        language_instruction = {
            "english": "Provide your response entirely in English.",
            "hindi": "Provide your response in Hindi language.",
            "mixed": "Provide response with legal terms in English and explanations in Hindi/English as appropriate."
        }.get(language, "Provide your response entirely in English.")
        
        return f"""{base_prompt}

{focus_text}

{language_instruction}

Provide your analysis in the following structure:
1. **Executive Summary** (2-3 sentences)
2. **Key Legal Points** (bullet points)
3. **Potential Risk Factors** (if any)
4. **Compliance Status** (with Indian laws)
5. **Recommendations** (actionable advice)

Keep the analysis concise (300-500 words) and suitable for a general audience."""
    
    async def analyze_pdf_content(self, pdf_bytes: bytes, focus_area: str = "general", language: str = "english") -> LegalAnalysisResponse:
        """Analyze a PDF document from bytes using Gemini"""
        try:
            if not pdf_bytes:
                raise ValueError("PDF content is empty")
            
            logger.info(f"Analyzing PDF content ({len(pdf_bytes)} bytes)")
            
            # Create PDF part from bytes
            pdf_part = Part.from_bytes(
                data=pdf_bytes,
                mime_type="application/pdf",
            )
            
            # Get system prompt
            system_prompt = self.get_system_prompt(
                focus_area=focus_area,
                language=language
            )
            
            # Generate content using Gemini, with fallback for temporarily unavailable models
            response, used_model = self._generate_content_with_fallback(
                pdf_part=pdf_part,
                system_prompt=system_prompt,
            )
            
            # Parse the response
            analysis_text = response.text
            
            logger.info(f"Analysis completed successfully with model {used_model}")
            
            # Extract key information from analysis
            key_points = self._extract_key_points(analysis_text)
            recommendations = self._extract_recommendations(analysis_text)
            risk_factors = self._extract_risk_factors(analysis_text)
            
            return LegalAnalysisResponse(
                status="success",
                analysis=analysis_text,
                key_points=key_points,
                recommendations=recommendations,
                risk_factors=risk_factors,
                model_used=used_model
            )
        except ValueError as ve:
            logger.error(f"Validation error: {str(ve)}")
            raise
        except Exception as e:
            error_message = str(e)
            if self._is_quota_exceeded_error(error_message):
                logger.error(f"Quota exceeded when analyzing PDF: {error_message}", exc_info=True)
                raise QuotaExceededError(
                    "Gemini quota exceeded. Check your Google Cloud billing and API quota. "
                    "If you are on free tier, switch to a paid project or use a model with an available quota."
                )
            logger.error(f"Error analyzing PDF: {error_message}", exc_info=True)
            raise
    
    def _extract_key_points(self, analysis: str) -> list:
        """Extract key points from analysis"""
        points = []
        try:
            if "**Key Legal Points**" in analysis or "Key Legal Points" in analysis:
                lines = analysis.split("\n")
                in_section = False
                for line in lines:
                    if "Key Legal Points" in line:
                        in_section = True
                        continue
                    if in_section:
                        if line.startswith("**") or line.startswith("###"):
                            break
                        if line.strip().startswith("-") or line.strip().startswith("•"):
                            points.append(line.strip().lstrip("-•").strip())
        except Exception as e:
            logger.warning(f"Could not extract key points: {e}")
        return points[:10]
    
    def _is_quota_exceeded_error(self, error_message: str) -> bool:
        """Detect quota/rate-limit errors from Gemini API response text"""
        lowered = error_message.lower()
        return (
            "resource_exhausted" in lowered
            or "quota exceeded" in lowered
            or "rate limit" in lowered
            or "429" in lowered
        )

    def _is_model_unavailable_error(self, error_message: str) -> bool:
        """Detect temporary model unavailable/high-demand errors"""
        lowered = error_message.lower()
        return (
            "unavailable" in lowered
            or "high demand" in lowered
            or "503" in lowered
            or "service unavailable" in lowered
        )

    def _generate_content_with_fallback(self, pdf_part, system_prompt: str):
        """Try the configured model only."""
        fallback_candidates = [self.model_id]
        tried = set()
        last_exception = None

        for model in fallback_candidates:
            if model in tried:
                continue
            tried.add(model)
            try:
                logger.info(f"Attempting Gemini model: {model}")
                response = self.client.models.generate_content(
                    model=model,
                    contents=[pdf_part, f"\n\n{system_prompt}"],
                )
                return response, model
            except Exception as exc:
                error_message = str(exc)
                if self._is_model_unavailable_error(error_message):
                    logger.warning(
                        f"Gemini model {model} unavailable; trying fallback. error={error_message}"
                    )
                    last_exception = exc
                    continue
                raise

        raise last_exception or RuntimeError("No available Gemini model could be used.")
    
    def _extract_recommendations(self, analysis: str) -> list:
        """Extract recommendations from analysis"""
        recommendations = []
        try:
            if "**Recommendations**" in analysis or "Recommendations" in analysis:
                lines = analysis.split("\n")
                in_section = False
                for line in lines:
                    if "Recommendations" in line:
                        in_section = True
                        continue
                    if in_section:
                        if line.startswith("**") or line.startswith("###"):
                            break
                        if line.strip().startswith("-") or line.strip().startswith("•"):
                            recommendations.append(line.strip().lstrip("-•").strip())
        except Exception as e:
            logger.warning(f"Could not extract recommendations: {e}")
        return recommendations[:10]
    
    def _extract_risk_factors(self, analysis: str) -> list:
        """Extract risk factors from analysis"""
        risk_factors = []
        try:
            if "**Risk" in analysis or "risk" in analysis.lower():
                lines = analysis.split("\n")
                in_section = False
                for line in lines:
                    if "Risk" in line or "risk" in line.lower():
                        in_section = True
                        continue
                    if in_section and (line.startswith("**") or line.startswith("###")):
                        break
                    if in_section and (line.strip().startswith("-") or line.strip().startswith("•")):
                        risk_factors.append(line.strip().lstrip("-•").strip())
        except Exception as e:
            logger.warning(f"Could not extract risk factors: {e}")
        return risk_factors[:10]
