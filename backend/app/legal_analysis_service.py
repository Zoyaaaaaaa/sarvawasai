"""
Legal Document Analysis Service using Google Gemini API
Specializes in Indian real estate legalities and document analysis
"""

import os
import logging
from typing import Optional, Dict, Any
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


class LegalAnalysisRequest(BaseModel):
    """Request model for legal document analysis"""
    file_uri: str = Field(..., description="GCS URI of the PDF file (e.g., gs://bucket/file.pdf)")
    analysis_type: str = Field(default="comprehensive", description="Type of analysis: comprehensive, summary, or specific")
    focus_area: Optional[str] = Field(default="general", description="Focus area: general, property_transfer, mortgage, tenant_rights, etc.")
    language: str = Field(default="english", description="Language for response: english, hindi, mixed")


class LegalAnalysisResponse(BaseModel):
    """Response model for legal analysis"""
    status: str = Field(description="Success or failure status")
    analysis: str = Field(description="The legal analysis of the document")
    key_points: list = Field(default_factory=list, description="Key legal points extracted")
    recommendations: list = Field(default_factory=list, description="Recommendations for the user")
    risk_factors: list = Field(default_factory=list, description="Potential legal risks identified")
    model_used: str = Field(default="gemini-2.5-flash", description="Model used for analysis")


class LegalAnalysisService:
    """Service for analyzing legal documents using Google Gemini API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the legal analysis service"""
        if not GENAI_AVAILABLE:
            raise ImportError("google-genai package is required. Install with: pip install google-genai")
        
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        self.client = genai.Client(
            api_key=self.api_key,
            http_options=HttpOptions(api_version="v1")
        )
        self.model_id = "gemini-2.5-flash"
    
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
    
    async def analyze_pdf(self, request: LegalAnalysisRequest) -> LegalAnalysisResponse:
        """Analyze a PDF document from GCS using Gemini"""
        try:
            # Validate file URI
            if not request.file_uri.startswith("gs://"):
                raise ValueError("File URI must be a Google Cloud Storage path (gs://...)")
            
            logger.info(f"Analyzing PDF from: {request.file_uri}")
            
            # Create PDF part from URI
            pdf_file = Part.from_uri(
                file_uri=request.file_uri,
                mime_type="application/pdf",
            )
            
            # Get system prompt
            system_prompt = self.get_system_prompt(
                focus_area=request.focus_area,
                language=request.language
            )
            
            # Generate content using Gemini
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=[pdf_file, system_prompt],
            )
            
            # Parse the response
            analysis_text = response.text
            
            logger.info(f"Analysis completed successfully for: {request.file_uri}")
            
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
                model_used=self.model_id
            )
        
        except ValueError as ve:
            logger.error(f"Validation error: {str(ve)}")
            raise
        except Exception as e:
            logger.error(f"Error analyzing PDF: {str(e)}", exc_info=True)
            raise
    
    def _extract_key_points(self, analysis: str) -> list:
        """Extract key points from analysis"""
        points = []
        try:
            if "**Key Legal Points**" in analysis or "Key Legal Points" in analysis:
                # Simple extraction - in production, use more sophisticated parsing
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
        
        return points[:10]  # Return top 10 points
    
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
        
        return recommendations[:10]  # Return top 10 recommendations
    
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
        
        return risk_factors[:10]  # Return top 10 risk factors
