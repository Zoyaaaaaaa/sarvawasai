from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Union
from io import BytesIO
from pathlib import Path
import os
import dotenv
from pydantic import BaseModel
import pandas as pd
import numpy as np
import joblib
import os
import base64
import time
import asyncio
from datetime import datetime, timezone
from fastapi import HTTPException, UploadFile, File, Response
from pydantic import BaseModel
import pandas as pd
import numpy as np
import joblib
import os
import cv2
from PIL import Image
import io
from skimage.metrics import structural_similarity as ssim


# Load environment variables from common locations
try:
    # CWD .env
    dotenv.load_dotenv()
    # backend/app/.env
    dotenv.load_dotenv(Path(__file__).resolve().parent / ".env")
    # backend/.env
    dotenv.load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except Exception:
    pass

# Robust import for utilities: prefer relative import when running as package
try:
    from ..services.pdf_utils import (  # type: ignore
        generate_overlay_pdf,
        compose_pdf_with_base,
        get_base_page_size,
        generate_positioned_overlay,
        append_signature_page,
    )
except Exception:
    try:
        from backend.app.services.pdf_utils import (  # type: ignore
            generate_overlay_pdf,
            compose_pdf_with_base,
            get_base_page_size,
            generate_positioned_overlay,
            append_signature_page,
        )
    except Exception:
        from backend.app.services.pdf_utils import (  # type: ignore
            generate_overlay_pdf,
            compose_pdf_with_base,
            get_base_page_size,
            generate_positioned_overlay,
            append_signature_page,
        )

# DocuSeal client import (prefer relative when packaged)
try:
    from ..services.docuseal_client import DocuSealClient, DocuSealError  # type: ignore
except Exception:
    try:
        from backend.app.services.docuseal_client import DocuSealClient, DocuSealError  # type: ignore
    except Exception:
        from backend.app.services.docuseal_client import DocuSealClient, DocuSealError  # type: ignore

# IPFS client import (prefer relative when packaged)
try:
    from ..services.ipfs_client import IPFSClient  # type: ignore
except Exception:
    try:
        from backend.app.services.ipfs_client import IPFSClient  # type: ignore
    except Exception:
        from backend.app.services.ipfs_client import IPFSClient  # type: ignore

try:
    from ..core.paths import resolve_artifact, resolve_asset, resolve_raw_data  # type: ignore
except Exception:
    try:
        from app.core.paths import resolve_artifact, resolve_asset, resolve_raw_data  # type: ignore
    except Exception:
        from core.paths import resolve_artifact, resolve_asset, resolve_raw_data  # type: ignore

router = APIRouter(prefix="/api")

# In-memory store for finalize/upload results without DB
FINALIZE_RESULTS: Dict[str, Any] = {}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = resolve_artifact(
    "knn_investor_model.pkl",
    Path(BASE_DIR).parent / "models" / "knn_investor_model.pkl",
    Path(BASE_DIR).parent / "knn_investor_model.pkl",
)
SCALER_PATH = resolve_artifact(
    "scaler.pkl",
    Path(BASE_DIR).parent / "models" / "scaler.pkl",
    Path(BASE_DIR).parent / "scaler.pkl",
)

# Lazy loaded models
_model = None
_scaler = None

def get_model():
    global _model
    if _model is None:
        try:
            _model = joblib.load(MODEL_PATH)
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
    return _model

def get_scaler():
    global _scaler
    if _scaler is None:
        try:
            _scaler = joblib.load(SCALER_PATH)
        except Exception as e:
            print(f"Error loading scaler: {e}")
            raise
    return _scaler

class BuyerInput(BaseModel):
    buyerBudgetMax: float
    buyerRisk: int  # 0=Low, 1=Medium, 2=High
    location: str

def recommend_investors(buyer_input, investors_df):
    recommendations = []

    for _, inv in investors_df.iterrows():
        # Location match
        preferred = str(inv['preferredLocations'])
        location_match = 1 if buyer_input['location'] in preferred else 0

        # Prepare features for prediction
        features = pd.DataFrame([{
            'buyerBudgetMax': buyer_input['buyerBudgetMax'],
            'buyerRisk': buyer_input['buyerRisk'],
            'locationMatch': location_match,
            'investorMaxDeal': inv['maxInvestmentPerDeal'],
            'investorRisk': (
                0 if inv['riskAppetite'] == 'Low' else
                1 if inv['riskAppetite'] == 'Medium' else
                2
            )
        }])

        features[['buyerBudgetMax', 'investorMaxDeal']] = scaler.transform(
            features[['buyerBudgetMax', 'investorMaxDeal']]
        )

        score = model.predict(features)[0]

        recommendations.append({
            "investorId": inv['userId'],
            "profession": inv['profession'],
            "riskAppetite": inv['riskAppetite'],
            "budget": inv['maxInvestmentPerDeal'],
            "locationMatch": location_match,
            "score": round(float(score), 3)
        })

    top3 = sorted(recommendations, key=lambda x: x['score'], reverse=True)[:3]
    labels = ["Best Match", "Better Match", "Good Match"]

    for i, rec in enumerate(top3):
        rec["label"] = labels[i]

    return top3

@router.post("/recommend")
async def recommend_endpoint(buyer: BuyerInput):
    try:
        model = get_model()
        scaler = get_scaler()
    except Exception:
        raise HTTPException(status_code=500, detail="Model or scaler not loaded")

    try:
        investors_path = resolve_raw_data(
            "investor_profiles_mumbai.csv",
            Path(BASE_DIR).parent / "investor_profiles_mumbai.csv",
        )

        investors_df = pd.read_csv(investors_path)
        print("Investors loaded:", investors_df.shape)

        buyer_input = buyer.dict()
        top_matches = recommend_investors(buyer_input, investors_df)

        return {"buyer_input": buyer_input, "recommendations": top_matches}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-pan")
async def verify_pan_card(file: UploadFile = File(...), response: Response = None):
    try:
        print("Received PAN verification request")
        print("File details:", file.filename, file.content_type)
        
        # Read the uploaded image
        try:
            contents = await file.read()
            print("File read successfully, size:", len(contents))
        except Exception as e:
            print("Error reading file:", str(e))
            raise HTTPException(status_code=500, detail=f"Error reading uploaded file: {str(e)}")

        # Open and process the uploaded image
        try:
            # Convert to PIL Image
            user_image = Image.open(io.BytesIO(contents))
            print("Image opened successfully, size:", user_image.size, "mode:", user_image.mode)
            
            # Convert to RGB if needed
            if user_image.mode != 'RGB':
                user_image = user_image.convert('RGB')
                print("Converted image to RGB mode")
            
            # Convert to OpenCV format
            user_image_array = np.array(user_image)
            print("Image array shape:", user_image_array.shape)
            user_image_cv = cv2.cvtColor(user_image_array, cv2.COLOR_RGB2BGR)
            print("Converted to BGR format")
        except Exception as e:
            print("Error processing uploaded image:", str(e))
            raise HTTPException(status_code=500, detail=f"Error processing uploaded image: {str(e)}")

        # Load and check reference image
        try:
            real_image_path = resolve_asset(
                "real.png",
                Path(BASE_DIR).parent / "real.png",
            )
            
            real_image = cv2.imread(str(real_image_path))
            if real_image is None:
                print("Failed to load reference image with OpenCV")
                raise HTTPException(status_code=500, detail="Could not load reference PAN card image")
            
            print("Reference image loaded, shape:", real_image.shape)
            
            # Resize user image to match reference dimensions
            user_image_resized = cv2.resize(user_image_cv, (real_image.shape[1], real_image.shape[0]))
            print("Resized user image to match reference:", user_image_resized.shape)
            
            # Convert both to grayscale for comparison
            real_gray = cv2.cvtColor(real_image, cv2.COLOR_BGR2GRAY)
            user_gray = cv2.cvtColor(user_image_resized, cv2.COLOR_BGR2GRAY)
            print("Converted both images to grayscale")
        except Exception as e:
            print("Error processing reference image:", str(e))
            raise HTTPException(status_code=500, detail=f"Error processing reference image: {str(e)}")
        
        # Calculate similarity
        try:
            # Calculate SSIM between the grayscale images
            ssim_value = ssim(real_gray, user_gray)
            print("Calculated SSIM value:", ssim_value)
            
            threshold = 0.9
            is_genuine = ssim_value >= threshold
            
            # Convert numpy bool_ to regular Python bool
            is_genuine_bool = bool(is_genuine)
            
            result = {
                "ssim_value": float(ssim_value),
                "is_genuine": is_genuine_bool,
                "message": "Genuine PAN Card" if is_genuine_bool else "Potentially Fake PAN Card"
            }
            print("Returning result:", result)
            return result
        except Exception as e:
            print("Error calculating similarity:", str(e))
            raise HTTPException(status_code=500, detail=f"Error calculating similarity: {str(e)}")
            
    except HTTPException as he:
        # Re-raise HTTP exceptions as-is to preserve status codes
        raise he
    except Exception as e:
        print("Unexpected error:", str(e))
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

        # Load the reference PAN card image
        real_image_path = resolve_asset(
            "real.png",
            Path(BASE_DIR).parent / "real.png",
        )
        if not os.path.exists(real_image_path):
            raise HTTPException(status_code=404, detail="Reference PAN card image not found")
        
        real_image = cv2.imread(str(real_image_path))
        
        # Resize user image to match reference image dimensions
        user_image_resized = cv2.resize(user_image_cv, (real_image.shape[1], real_image.shape[0]))
        
        # Convert both images to grayscale
        real_gray = cv2.cvtColor(real_image, cv2.COLOR_BGR2GRAY)
        user_gray = cv2.cvtColor(user_image_resized, cv2.COLOR_BGR2GRAY)
        
        # Calculate SSIM
        ssim_value = ssim(real_gray, user_gray)
        
        # Determine if the PAN card is genuine based on SSIM value
        threshold = 0.9
        is_genuine = ssim_value >= threshold
        
        return {
            "ssim_value": float(ssim_value),
            "is_genuine": is_genuine,
            "message": "Genuine PAN Card" if is_genuine else "Potentially Fake PAN Card"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ping")
async def ping():
    """Simple health and CORS check endpoint."""
    return {"status": "ok", "message": "pong"}

@router.get("/docuseal/status")
async def docuseal_status():
    """Lightweight env diagnostics without exposing secrets."""
    try:
      api_key = os.getenv("DOCUSEAL_API_KEY")
      base_url_env = (os.getenv("DOCUSEAL_BASE_URL") or "https://api.docuseal.com").rstrip("/")
      template_raw = os.getenv("DOCUSEAL_TEMPLATE_ID_BUYER") or "1891040"
      try:
          template_id = int(template_raw)
      except Exception:
          template_id = None
      # Also provide normalized base from client (reflects '/api' logic and quote stripping)
      normalized_base = None
      try:
          client = DocuSealClient(api_key=api_key, base_url=base_url_env)
          normalized_base = client.base_url
      except Exception:
          normalized_base = None
      return {
          "hasApiKey": bool(api_key),
          "baseUrlEnv": base_url_env,
          "baseUrlNormalized": normalized_base,
          "templateIdBuyer": template_id,
      }
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))


class BuyerAgreementPayload(BaseModel):
    buyerName: Optional[str] = ""
    buyerAddress: Optional[str] = ""
    buyerMobile: Optional[str] = ""
    buyerEmail: Optional[str] = ""
    investorName: Optional[str] = ""
    investorAddress: Optional[str] = ""
    investorMobile: Optional[str] = ""
    investorEmail: Optional[str] = ""
    propertyName: Optional[str] = ""
    propertyLocationText: Optional[str] = ""
    propertyValue: Optional[str] = ""
    latitude: Optional[str] = ""
    longitude: Optional[str] = ""
    buyerAmount: Optional[str] = ""
    investorAmount: Optional[str] = ""
    downPayment: Optional[str] = ""
    equityPercent: Optional[str] = ""
    positions: Optional[Dict[str, Dict[str, float]]] = None
    drawGrid: Optional[bool] = False
    # Witnesses (optional)
    witness1Name: Optional[str] = ""
    witness1Address: Optional[str] = ""
    witness2Name: Optional[str] = ""
    witness2Address: Optional[str] = ""


@router.post("/buyer-agreement/pdf")
async def generate_buyer_agreement_pdf(payload: BuyerAgreementPayload):
    try:
        data: Dict[str, Any] = payload.model_dump()

        # Try to load base template
        base_pdf_bytes: Optional[bytes] = None
        try:
            repo_root = Path(__file__).resolve().parents[3]
            base_path = repo_root / "frontend" / "public" / "buyer_agreement.pdf"
            if base_path.exists():
                base_pdf_bytes = base_path.read_bytes()
        except Exception:
            base_pdf_bytes = None

        overlay_stream = None
        positions = payload.positions
        draw_grid = bool(payload.drawGrid)

        if positions and base_pdf_bytes:
            # Use exact positioned overlay aligned to base PDF size
            page_size = get_base_page_size(base_pdf_bytes)
            overlay_stream = generate_positioned_overlay(data, positions, page_size, draw_grid)
        else:
            # Fallback: simple textual overlay page
            overlay_stream = generate_overlay_pdf(data)

        final_pdf = compose_pdf_with_base(base_pdf_bytes, overlay_stream)
        stream = BytesIO(final_pdf)
        headers = {"Content-Disposition": "inline; filename=buyer_agreement_generated.pdf"}
        return StreamingResponse(stream, media_type="application/pdf", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/buyer-agreement/pdf-full")
async def generate_buyer_agreement_full(payload: BuyerAgreementPayload):
    """
    Generate the entire PDF from a JSON template with placeholders.
    """
    try:
        data: Dict[str, Any] = payload.model_dump()
        # Locate template
        # Support running from backend/ or backend/app
        here = Path(__file__).resolve()
        root1 = here.parents[1]  # .../backend/app
        root2 = here.parents[2]  # .../backend

        candidates = [
            root1 / "templates" / "buyer_agreement_template.json",
            root2 / "app" / "templates" / "buyer_agreement_template.json",
        ]
        template_path = next((p for p in candidates if p.exists()), None)
        if not template_path:
            raise HTTPException(status_code=500, detail="Template not found")

        # Render using template engine
        try:
            from ..services.pdf_template_renderer import render_pdf_from_template  # type: ignore
        except Exception:
            try:
                from backend.app.services.pdf_template_renderer import render_pdf_from_template  # type: ignore
            except Exception:
                from backend.app.services.pdf_template_renderer import render_pdf_from_template  # type: ignore

        # Include witness placeholders
        data.update({
            "witness1Name": payload.witness1Name or "",
            "witness1Address": payload.witness1Address or "",
            "witness2Name": payload.witness2Name or "",
            "witness2Address": payload.witness2Address or "",
        })
        pdf_bytes = render_pdf_from_template(data, template_path)
        headers = {"Content-Disposition": "inline; filename=buyer_agreement_generated.pdf"}
        return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/buyer-agreement/initiate")
async def initiate_buyer_agreement(payload: BuyerAgreementPayload):
    
    try:
        # Resolve template id from env or default provided by user
        template_str = os.getenv("DOCUSEAL_TEMPLATE_ID_BUYER") or 1891040
        try:
            template_id = int(template_str)
        except ValueError:
            raise HTTPException(status_code=500, detail="Invalid DOCUSEAL_TEMPLATE_ID_BUYER configuration")

        # Build submitters from provided emails
        submitters: List[Dict[str, Any]] = []
        if payload.buyerEmail:
            submitters.append({"email": payload.buyerEmail, "name": payload.buyerName or "Buyer"})
        if payload.investorEmail:
            submitters.append({"email": payload.investorEmail, "name": payload.investorName or "Investor"})
        if not submitters:
            raise HTTPException(status_code=400, detail="At least buyerEmail or investorEmail is required")

        api_key = os.getenv("DOCUSEAL_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Missing DOCUSEAL_API_KEY environment variable")
        client = DocuSealClient(api_key=api_key, base_url=os.getenv("DOCUSEAL_BASE_URL"))
        # Create submission and surface DocuSeal API errors clearly
        try:
            # Optionally include roles for submitters from env; default generic labels
            buyer_role = os.getenv("DOCUSEAL_BUYER_ROLE") or "Buyer"
            investor_role = os.getenv("DOCUSEAL_INVESTOR_ROLE") or "Investor"
            # Attach roles if not already provided
            for s in submitters:
                if "role" not in s:
                    if s.get("email") == (payload.buyerEmail or ""):
                        s["role"] = buyer_role
                    elif s.get("email") == (payload.investorEmail or ""):
                        s["role"] = investor_role

            # Avoid sending emails when embedding by default
            result = client.create_submission(template_id, submitters, send_email=False)
        except Exception as e:
            # Attempt to include HTTP response details when available
            status_detail = str(e)
            resp = getattr(e, "response", None)
            if resp is not None:
                try:
                    status_detail = f"DocuSeal API error {resp.status_code}: {resp.text}"
                except Exception:
                    status_detail = f"DocuSeal API error {resp.status_code}"
            raise HTTPException(status_code=502, detail=status_detail)

        # Build embed links per submitter and provide the first as embed_src for convenience
        embed_src = None
        embed_srcs: List[Dict[str, Any]] = []
        try:
            if isinstance(result, list):
                # Some responses may be a list of submitters
                for s in result:
                    if isinstance(s, dict):
                        embed = s.get("embed_src") or s.get("embed_url")
                        if embed:
                            embed_srcs.append({
                                "email": s.get("email"),
                                "role": s.get("role"),
                                "embed_src": embed,
                            })
                if embed_srcs:
                    embed_src = embed_srcs[0]["embed_src"]
            elif isinstance(result, dict):
                subs = result.get("submitters") or []
                if isinstance(subs, list):
                    for s in subs:
                        if isinstance(s, dict):
                            embed = s.get("embed_src") or s.get("embed_url")
                            if embed:
                                embed_srcs.append({
                                    "email": s.get("email"),
                                    "role": s.get("role"),
                                    "embed_src": embed,
                                })
                if embed_srcs:
                    embed_src = embed_srcs[0]["embed_src"]
                if not embed_src:
                    embed_src = result.get("embed_src") or result.get("embed_url")
        except Exception:
            embed_src = None

        return {"embed_src": embed_src, "embed_srcs": embed_srcs, "submission": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/buyer-agreement/pdf-sign")
async def buyer_pdf_sign(payload: BuyerAgreementPayload):
    try:
        # 1) Render the Buyer Agreement PDF using the JSON template engine
        here = Path(__file__).resolve()
        root1 = here.parents[1]  # .../backend/app
        root2 = here.parents[2]  # .../backend
        candidates = [
            root1 / "templates" / "buyer_agreement_template.json",
            root2 / "app" / "templates" / "buyer_agreement_template.json",
        ]
        template_path = next((p for p in candidates if p.exists()), None)
        if not template_path:
            raise HTTPException(status_code=500, detail="Template not found")

        # Import renderer
        try:
            from ..services.pdf_template_renderer import render_pdf_from_template  # type: ignore
        except Exception:
            try:
                from backend.app.services.pdf_template_renderer import render_pdf_from_template  # type: ignore
            except Exception:
                from backend.app.services.pdf_template_renderer import render_pdf_from_template  # type: ignore

        data: Dict[str, Any] = payload.model_dump()
        # Ensure witness placeholders present
        data.update({
            "witness1Name": payload.witness1Name or "",
            "witness1Address": payload.witness1Address or "",
            "witness2Name": payload.witness2Name or "",
            "witness2Address": payload.witness2Address or "",
        })
        pdf_bytes = render_pdf_from_template(data, template_path)

        # 2) Append a signature page and build DocuSeal fields mapped to that page
        combined_pdf_bytes, signature_page_number = append_signature_page(pdf_bytes)

        # Build normalized field coordinates (0..1) based on A4 210x297mm and our drawn line positions
        page_w_mm = 210.0
        page_h_mm = 297.0

        def mm_x(x_mm: float) -> float:
            return max(0.0, min(1.0, x_mm / page_w_mm))

        def mm_w(w_mm: float) -> float:
            return max(0.0, min(1.0, w_mm / page_w_mm))

        def mm_y_from_top(y_mm_from_top: float) -> float:
            return max(0.0, min(1.0, y_mm_from_top / page_h_mm))

        # Horizontal placements
        sig_x = mm_x(25.0)
        sig_w = mm_w(160.0)
        name_x = mm_x(40.0)
        name_w = mm_w(55.0)
        date_x = mm_x(125.0)
        date_w = mm_w(60.0)

        # Vertical positions (slightly above the line to sit on it)
        buyer_sig_y = mm_y_from_top(61.0)
        buyer_meta_y = mm_y_from_top(68.0)
        investor_sig_y = mm_y_from_top(101.0)
        investor_meta_y = mm_y_from_top(108.0)

        field_h_sig = mm_y_from_top(6.0)
        field_h_txt = mm_y_from_top(6.0)

        buyer_role = os.getenv("DOCUSEAL_BUYER_ROLE") or "Buyer"
        investor_role = os.getenv("DOCUSEAL_INVESTOR_ROLE") or "Investor"

        fields: List[Dict[str, Any]] = [
            {
                "name": "Buyer Signature",
                "type": "signature",
                "role": buyer_role,
                "areas": [
                    {"x": sig_x, "y": buyer_sig_y, "w": sig_w, "h": field_h_sig, "page": signature_page_number}
                ],
            },
            {
                "name": "Buyer Name",
                "type": "text",
                "role": buyer_role,
                "areas": [
                    {"x": name_x, "y": buyer_meta_y, "w": name_w, "h": field_h_txt, "page": signature_page_number}
                ],
                "default_value": payload.buyerName or "",
                "readonly": False,
            },
            {
                "name": "Buyer Date",
                "type": "date",
                "role": buyer_role,
                "areas": [
                    {"x": date_x, "y": buyer_meta_y, "w": date_w, "h": field_h_txt, "page": signature_page_number}
                ],
            },
        ]
        if payload.investorEmail:
            fields.extend([
                {
                    "name": "Investor Signature",
                    "type": "signature",
                    "role": investor_role,
                    "areas": [
                        {"x": sig_x, "y": investor_sig_y, "w": sig_w, "h": field_h_sig, "page": signature_page_number}
                    ],
                },
                {
                    "name": "Investor Name",
                    "type": "text",
                    "role": investor_role,
                    "areas": [
                        {"x": name_x, "y": investor_meta_y, "w": name_w, "h": field_h_txt, "page": signature_page_number}
                    ],
                    "default_value": payload.investorName or "",
                    "readonly": False,
                },
                {
                    "name": "Investor Date",
                    "type": "date",
                    "role": investor_role,
                    "areas": [
                        {"x": date_x, "y": investor_meta_y, "w": date_w, "h": field_h_txt, "page": signature_page_number}
                    ],
                },
            ])

        # 3) build submitters (buyer required, investor optional)
        submitters = []
        if getattr(payload, "buyerEmail", None):
            submitters.append({"email": payload.buyerEmail, "name": getattr(payload, "buyerName", "Buyer"), "role": buyer_role})
        if getattr(payload, "investorEmail", None):
            submitters.append({"email": payload.investorEmail, "name": getattr(payload, "investorName", "Investor"), "role": investor_role})
        if not submitters:
            raise HTTPException(status_code=400, detail="At least buyerEmail or investorEmail is required")

        # 4) send to DocuSeal
        client = DocuSealClient(api_key=os.getenv("DOCUSEAL_API_KEY"), base_url=os.getenv("DOCUSEAL_BASE_URL"))
        resp = client.create_submission_from_pdf(
            combined_pdf_bytes,
            submitters=submitters,
            fields=fields,
            send_email=False,
            filename="buyer_agreement.pdf",
        )

        # 5) normalize response
        submission_id = resp.get("id") or resp.get("submission_id")
        submitters_resp = resp.get("submitters") or resp
        embed_src = None
        embed_srcs = []
        if isinstance(submitters_resp, list):
            for s in submitters_resp:
                link = s.get("embed_src") or s.get("embed_url")
                if link:
                    if not embed_src:
                        embed_src = link
                    embed_srcs.append({"email": s.get("email"), "role": s.get("role"), "embed_src": link})
        else:
            embed_src = resp.get("embed_src")
        return {"submission_id": submission_id, "embed_src": embed_src, "embed_srcs": embed_srcs, "raw": resp}
    except DocuSealError as e:
        # bubble up DocuSeal’s error with 502 so you can see the body
        return JSONResponse(status_code=502, content={"error": str(e)})
    except Exception as e:
        # unexpected errors become 500 with message
        raise HTTPException(status_code=500, detail=f"/pdf-sign failed: {e}")


@router.post("/buyer-agreement/pdf-full")
async def generate_buyer_agreement_full(payload: BuyerAgreementPayload):
    """
    Generate the entire PDF from a JSON template with placeholders.
    """
    try:
        data: Dict[str, Any] = payload.model_dump()
        # Locate template
        # Support running from backend/ or backend/app
        here = Path(__file__).resolve()
        root1 = here.parents[1]  # .../backend/app
        root2 = here.parents[2]  # .../backend

        candidates = [
            root1 / "templates" / "buyer_agreement_template.json",
            root2 / "app" / "templates" / "buyer_agreement_template.json",
        ]
        template_path = next((p for p in candidates if p.exists()), None)
        if not template_path:
            raise HTTPException(status_code=500, detail="Template not found")

        # Render using template engine
        try:
            from ..services.pdf_template_renderer import render_pdf_from_template  # type: ignore
        except Exception:
            try:
                from backend.app.services.pdf_template_renderer import render_pdf_from_template  # type: ignore
            except Exception:
                from backend.app.services.pdf_template_renderer import render_pdf_from_template  # type: ignore

        # Include witness placeholders
        data.update({
            "witness1Name": payload.witness1Name or "",
            "witness1Address": payload.witness1Address or "",
            "witness2Name": payload.witness2Name or "",
            "witness2Address": payload.witness2Address or "",
        })
        pdf_bytes = render_pdf_from_template(data, template_path)
        headers = {"Content-Disposition": "inline; filename=buyer_agreement_generated.pdf"}
        return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/buyer-agreement/initiate")
async def initiate_buyer_agreement(payload: BuyerAgreementPayload):
    
    try:
        # Resolve template id from env or default provided by user
        template_str = os.getenv("DOCUSEAL_TEMPLATE_ID_BUYER") or 1891040
        try:
            template_id = int(template_str)
        except ValueError:
            raise HTTPException(status_code=500, detail="Invalid DOCUSEAL_TEMPLATE_ID_BUYER configuration")

        # Build submitters from provided emails
        submitters: List[Dict[str, Any]] = []
        if payload.buyerEmail:
            submitters.append({"email": payload.buyerEmail, "name": payload.buyerName or "Buyer"})
        if payload.investorEmail:
            submitters.append({"email": payload.investorEmail, "name": payload.investorName or "Investor"})
        if not submitters:
            raise HTTPException(status_code=400, detail="At least buyerEmail or investorEmail is required")

        api_key = os.getenv("DOCUSEAL_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Missing DOCUSEAL_API_KEY environment variable")
        client = DocuSealClient(api_key=api_key, base_url=os.getenv("DOCUSEAL_BASE_URL"))
        # Create submission and surface DocuSeal API errors clearly
        try:
            # Optionally include roles for submitters from env; default generic labels
            buyer_role = os.getenv("DOCUSEAL_BUYER_ROLE") or "Buyer"
            investor_role = os.getenv("DOCUSEAL_INVESTOR_ROLE") or "Investor"
            # Attach roles if not already provided
            for s in submitters:
                if "role" not in s:
                    if s.get("email") == (payload.buyerEmail or ""):
                        s["role"] = buyer_role
                    elif s.get("email") == (payload.investorEmail or ""):
                        s["role"] = investor_role

            # Avoid sending emails when embedding by default
            result = client.create_submission(template_id, submitters, send_email=False)
        except Exception as e:
            # Attempt to include HTTP response details when available
            status_detail = str(e)
            resp = getattr(e, "response", None)
            if resp is not None:
                try:
                    status_detail = f"DocuSeal API error {resp.status_code}: {resp.text}"
                except Exception:
                    status_detail = f"DocuSeal API error {resp.status_code}"
            raise HTTPException(status_code=502, detail=status_detail)

        # Build embed links per submitter and provide the first as embed_src for convenience
        embed_src = None
        embed_srcs: List[Dict[str, Any]] = []
        try:
            if isinstance(result, list):
                # Some responses may be a list of submitters
                for s in result:
                    if isinstance(s, dict):
                        embed = s.get("embed_src") or s.get("embed_url")
                        if embed:
                            embed_srcs.append({
                                "email": s.get("email"),
                                "role": s.get("role"),
                                "embed_src": embed,
                            })
                if embed_srcs:
                    embed_src = embed_srcs[0]["embed_src"]
            elif isinstance(result, dict):
                subs = result.get("submitters") or []
                if isinstance(subs, list):
                    for s in subs:
                        if isinstance(s, dict):
                            embed = s.get("embed_src") or s.get("embed_url")
                            if embed:
                                embed_srcs.append({
                                    "email": s.get("email"),
                                    "role": s.get("role"),
                                    "embed_src": embed,
                                })
                if embed_srcs:
                    embed_src = embed_srcs[0]["embed_src"]
                if not embed_src:
                    embed_src = result.get("embed_src") or result.get("embed_url")
        except Exception:
            embed_src = None

        return {"embed_src": embed_src, "embed_srcs": embed_srcs, "submission": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/buyer-agreement/pdf-sign")
async def buyer_pdf_sign(payload: BuyerAgreementPayload):
    try:
        # 1) Render the Buyer Agreement PDF using the JSON template engine
        here = Path(__file__).resolve()
        root1 = here.parents[1]  # .../backend/app
        root2 = here.parents[2]  # .../backend
        candidates = [
            root1 / "templates" / "buyer_agreement_template.json",
            root2 / "app" / "templates" / "buyer_agreement_template.json",
        ]
        template_path = next((p for p in candidates if p.exists()), None)
        if not template_path:
            raise HTTPException(status_code=500, detail="Template not found")

        # Import renderer
        try:
            from ..services.pdf_template_renderer import render_pdf_from_template  # type: ignore
        except Exception:
            try:
                from backend.app.services.pdf_template_renderer import render_pdf_from_template  # type: ignore
            except Exception:
                from backend.app.services.pdf_template_renderer import render_pdf_from_template  # type: ignore

        data: Dict[str, Any] = payload.model_dump()
        # Ensure witness placeholders present
        data.update({
            "witness1Name": payload.witness1Name or "",
            "witness1Address": payload.witness1Address or "",
            "witness2Name": payload.witness2Name or "",
            "witness2Address": payload.witness2Address or "",
        })
        pdf_bytes = render_pdf_from_template(data, template_path)

        # 2) Append a signature page and build DocuSeal fields mapped to that page
        combined_pdf_bytes, signature_page_number = append_signature_page(pdf_bytes)

        # Build normalized field coordinates (0..1) based on A4 210x297mm and our drawn line positions
        page_w_mm = 210.0
        page_h_mm = 297.0

        def mm_x(x_mm: float) -> float:
            return max(0.0, min(1.0, x_mm / page_w_mm))

        def mm_w(w_mm: float) -> float:
            return max(0.0, min(1.0, w_mm / page_w_mm))

        def mm_y_from_top(y_mm_from_top: float) -> float:
            return max(0.0, min(1.0, y_mm_from_top / page_h_mm))

        # Horizontal placements
        sig_x = mm_x(25.0)
        sig_w = mm_w(160.0)
        name_x = mm_x(40.0)
        name_w = mm_w(55.0)
        date_x = mm_x(125.0)
        date_w = mm_w(60.0)

        # Vertical positions (slightly above the line to sit on it)
        buyer_sig_y = mm_y_from_top(61.0)
        buyer_meta_y = mm_y_from_top(68.0)
        investor_sig_y = mm_y_from_top(101.0)
        investor_meta_y = mm_y_from_top(108.0)

        field_h_sig = mm_y_from_top(6.0)
        field_h_txt = mm_y_from_top(6.0)

        buyer_role = os.getenv("DOCUSEAL_BUYER_ROLE") or "Buyer"
        investor_role = os.getenv("DOCUSEAL_INVESTOR_ROLE") or "Investor"

        fields: List[Dict[str, Any]] = [
            {
                "name": "Buyer Signature",
                "type": "signature",
                "role": buyer_role,
                "areas": [
                    {"x": sig_x, "y": buyer_sig_y, "w": sig_w, "h": field_h_sig, "page": signature_page_number}
                ],
            },
            {
                "name": "Buyer Name",
                "type": "text",
                "role": buyer_role,
                "areas": [
                    {"x": name_x, "y": buyer_meta_y, "w": name_w, "h": field_h_txt, "page": signature_page_number}
                ],
                "default_value": payload.buyerName or "",
                "readonly": False,
            },
            {
                "name": "Buyer Date",
                "type": "date",
                "role": buyer_role,
                "areas": [
                    {"x": date_x, "y": buyer_meta_y, "w": date_w, "h": field_h_txt, "page": signature_page_number}
                ],
            },
        ]
        if payload.investorEmail:
            fields.extend([
                {
                    "name": "Investor Signature",
                    "type": "signature",
                    "role": investor_role,
                    "areas": [
                        {"x": sig_x, "y": investor_sig_y, "w": sig_w, "h": field_h_sig, "page": signature_page_number}
                    ],
                },
                {
                    "name": "Investor Name",
                    "type": "text",
                    "role": investor_role,
                    "areas": [
                        {"x": name_x, "y": investor_meta_y, "w": name_w, "h": field_h_txt, "page": signature_page_number}
                    ],
                    "default_value": payload.investorName or "",
                    "readonly": False,
                },
                {
                    "name": "Investor Date",
                    "type": "date",
                    "role": investor_role,
                    "areas": [
                        {"x": date_x, "y": investor_meta_y, "w": date_w, "h": field_h_txt, "page": signature_page_number}
                    ],
                },
            ])

        # 3) build submitters (buyer required, investor optional)
        submitters = []
        if getattr(payload, "buyerEmail", None):
            submitters.append({"email": payload.buyerEmail, "name": getattr(payload, "buyerName", "Buyer"), "role": buyer_role})
        if getattr(payload, "investorEmail", None):
            submitters.append({"email": payload.investorEmail, "name": getattr(payload, "investorName", "Investor"), "role": investor_role})
        if not submitters:
            raise HTTPException(status_code=400, detail="At least buyerEmail or investorEmail is required")

        # 4) send to DocuSeal
        client = DocuSealClient(api_key=os.getenv("DOCUSEAL_API_KEY"), base_url=os.getenv("DOCUSEAL_BASE_URL"))
        resp = client.create_submission_from_pdf(
            combined_pdf_bytes,
            submitters=submitters,
            fields=fields,
            send_email=False,
            filename="buyer_agreement.pdf",
        )

        # 5) normalize response
        submission_id = resp.get("id") or resp.get("submission_id")
        submitters_resp = resp.get("submitters") or resp
        embed_src = None
        embed_srcs = []
        if isinstance(submitters_resp, list):
            for s in submitters_resp:
                link = s.get("embed_src") or s.get("embed_url")
                if link:
                    if not embed_src:
                        embed_src = link
                    embed_srcs.append({"email": s.get("email"), "role": s.get("role"), "embed_src": link})
        else:
            embed_src = resp.get("embed_src")
        return {"submission_id": submission_id, "embed_src": embed_src, "embed_srcs": embed_srcs, "raw": resp}
    except DocuSealError as e:
        # bubble up DocuSeal’s error with 502 so you can see the body
        return JSONResponse(status_code=502, content={"error": str(e)})
    except Exception as e:
        # unexpected errors become 500 with message
        raise HTTPException(status_code=500, detail=f"/pdf-sign failed: {e}")


@router.post("/buyer-agreement/pdf-full")
async def generate_buyer_agreement_full(payload: BuyerAgreementPayload):
    """
    Generate the entire PDF from a JSON template with placeholders.
    """
    try:
        data: Dict[str, Any] = payload.model_dump()
        # Locate template
        # Support running from backend/ or backend/app
        here = Path(__file__).resolve()
        root1 = here.parents[1]  # .../backend/app
        root2 = here.parents[2]  # .../backend

        candidates = [
            root1 / "templates" / "buyer_agreement_template.json",
            root2 / "app" / "templates" / "buyer_agreement_template.json",
        ]
        template_path = next((p for p in candidates if p.exists()), None)
        if not template_path:
            raise HTTPException(status_code=500, detail="Template not found")

        # Render using template engine
        try:
            from ..services.pdf_template_renderer import render_pdf_from_template  # type: ignore
        except Exception:
            try:
                from backend.app.services.pdf_template_renderer import render_pdf_from_template  # type: ignore
            except Exception:
                from backend.app.services.pdf_template_renderer import render_pdf_from_template  # type: ignore

        # Include witness placeholders
        data.update({
            "witness1Name": payload.witness1Name or "",
            "witness1Address": payload.witness1Address or "",
            "witness2Name": payload.witness2Name or "",
            "witness2Address": payload.witness2Address or "",
        })
        pdf_bytes = render_pdf_from_template(data, template_path)
        headers = {"Content-Disposition": "inline; filename=buyer_agreement_generated.pdf"}
        return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/buyer-agreement/initiate")
async def initiate_buyer_agreement(payload: BuyerAgreementPayload):
    
    try:
        # Resolve template id from env or default provided by user
        template_str = os.getenv("DOCUSEAL_TEMPLATE_ID_BUYER") or 1891040
        try:
            template_id = int(template_str)
        except ValueError:
            raise HTTPException(status_code=500, detail="Invalid DOCUSEAL_TEMPLATE_ID_BUYER configuration")

        # Build submitters from provided emails
        submitters: List[Dict[str, Any]] = []
        if payload.buyerEmail:
            submitters.append({"email": payload.buyerEmail, "name": payload.buyerName or "Buyer"})
        if payload.investorEmail:
            submitters.append({"email": payload.investorEmail, "name": payload.investorName or "Investor"})
        if not submitters:
            raise HTTPException(status_code=400, detail="At least buyerEmail or investorEmail is required")

        api_key = os.getenv("DOCUSEAL_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Missing DOCUSEAL_API_KEY environment variable")
        client = DocuSealClient(api_key=api_key, base_url=os.getenv("DOCUSEAL_BASE_URL"))
        # Create submission and surface DocuSeal API errors clearly
        try:
            # Optionally include roles for submitters from env; default generic labels
            buyer_role = os.getenv("DOCUSEAL_BUYER_ROLE") or "Buyer"
            investor_role = os.getenv("DOCUSEAL_INVESTOR_ROLE") or "Investor"
            # Attach roles if not already provided
            for s in submitters:
                if "role" not in s:
                    if s.get("email") == (payload.buyerEmail or ""):
                        s["role"] = buyer_role
                    elif s.get("email") == (payload.investorEmail or ""):
                        s["role"] = investor_role

            # Avoid sending emails when embedding by default
            result = client.create_submission(template_id, submitters, send_email=False)
        except Exception as e:
            # Attempt to include HTTP response details when available
            status_detail = str(e)
            resp = getattr(e, "response", None)
            if resp is not None:
                try:
                    status_detail = f"DocuSeal API error {resp.status_code}: {resp.text}"
                except Exception:
                    status_detail = f"DocuSeal API error {resp.status_code}"
            raise HTTPException(status_code=502, detail=status_detail)

        # Build embed links per submitter and provide the first as embed_src for convenience
        embed_src = None
        embed_srcs: List[Dict[str, Any]] = []
        try:
            if isinstance(result, list):
                # Some responses may be a list of submitters
                for s in result:
                    if isinstance(s, dict):
                        embed = s.get("embed_src") or s.get("embed_url")
                        if embed:
                            embed_srcs.append({
                                "email": s.get("email"),
                                "role": s.get("role"),
                                "embed_src": embed,
                            })
                if embed_srcs:
                    embed_src = embed_srcs[0]["embed_src"]
            elif isinstance(result, dict):
                subs = result.get("submitters") or []
                if isinstance(subs, list):
                    for s in subs:
                        if isinstance(s, dict):
                            embed = s.get("embed_src") or s.get("embed_url")
                            if embed:
                                embed_srcs.append({
                                    "email": s.get("email"),
                                    "role": s.get("role"),
                                    "embed_src": embed,
                                })
                if embed_srcs:
                    embed_src = embed_srcs[0]["embed_src"]
                if not embed_src:
                    embed_src = result.get("embed_src") or result.get("embed_url")
        except Exception:
            embed_src = None

        return {"embed_src": embed_src, "embed_srcs": embed_srcs, "submission": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


 


@router.post("/buyer-agreement/pdf-full")
async def generate_buyer_agreement_full(payload: BuyerAgreementPayload):
    """
    Generate the entire PDF from a JSON template with placeholders.
    """
    try:
        data: Dict[str, Any] = payload.model_dump()
        # Locate template
        # Support running from backend/ or backend/app
        here = Path(__file__).resolve()
        root1 = here.parents[1]  # .../backend/app
        root2 = here.parents[2]  # .../backend

        candidates = [
            root1 / "templates" / "buyer_agreement_template.json",
            root2 / "app" / "templates" / "buyer_agreement_template.json",
        ]
        template_path = next((p for p in candidates if p.exists()), None)
        if not template_path:
            raise HTTPException(status_code=500, detail="Template not found")

        # Render using template engine
        try:
            from ..services.pdf_template_renderer import render_pdf_from_template  # type: ignore
        except Exception:
            try:
                from backend.app.services.pdf_template_renderer import render_pdf_from_template  # type: ignore
            except Exception:
                from backend.app.services.pdf_template_renderer import render_pdf_from_template  # type: ignore

        # Include witness placeholders
        data.update({
            "witness1Name": payload.witness1Name or "",
            "witness1Address": payload.witness1Address or "",
            "witness2Name": payload.witness2Name or "",
            "witness2Address": payload.witness2Address or "",
        })
        pdf_bytes = render_pdf_from_template(data, template_path)
        headers = {"Content-Disposition": "inline; filename=buyer_agreement_generated.pdf"}
        return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/buyer-agreement/initiate")
async def initiate_buyer_agreement(payload: BuyerAgreementPayload):
    
    try:
        # Resolve template id from env or default provided by user
        template_str = os.getenv("DOCUSEAL_TEMPLATE_ID_BUYER") or 1891040
        try:
            template_id = int(template_str)
        except ValueError:
            raise HTTPException(status_code=500, detail="Invalid DOCUSEAL_TEMPLATE_ID_BUYER configuration")

        # Build submitters from provided emails
        submitters: List[Dict[str, Any]] = []
        if payload.buyerEmail:
            submitters.append({"email": payload.buyerEmail, "name": payload.buyerName or "Buyer"})
        if payload.investorEmail:
            submitters.append({"email": payload.investorEmail, "name": payload.investorName or "Investor"})
        if not submitters:
            raise HTTPException(status_code=400, detail="At least buyerEmail or investorEmail is required")

        api_key = os.getenv("DOCUSEAL_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Missing DOCUSEAL_API_KEY environment variable")
        client = DocuSealClient(api_key=api_key, base_url=os.getenv("DOCUSEAL_BASE_URL"))
        # Create submission and surface DocuSeal API errors clearly
        try:
            # Optionally include roles for submitters from env; default generic labels
            buyer_role = os.getenv("DOCUSEAL_BUYER_ROLE") or "Buyer"
            investor_role = os.getenv("DOCUSEAL_INVESTOR_ROLE") or "Investor"
            # Attach roles if not already provided
            for s in submitters:
                if "role" not in s:
                    if s.get("email") == (payload.buyerEmail or ""):
                        s["role"] = buyer_role
                    elif s.get("email") == (payload.investorEmail or ""):
                        s["role"] = investor_role

            # Avoid sending emails when embedding by default
            result = client.create_submission(template_id, submitters, send_email=False)
        except Exception as e:
            # Attempt to include HTTP response details when available
            status_detail = str(e)
            resp = getattr(e, "response", None)
            if resp is not None:
                try:
                    status_detail = f"DocuSeal API error {resp.status_code}: {resp.text}"
                except Exception:
                    status_detail = f"DocuSeal API error {resp.status_code}"
            raise HTTPException(status_code=502, detail=status_detail)

        # Build embed links per submitter and provide the first as embed_src for convenience
        embed_src = None
        embed_srcs: List[Dict[str, Any]] = []
        try:
            if isinstance(result, list):
                # Some responses may be a list of submitters
                for s in result:
                    if isinstance(s, dict):
                        embed = s.get("embed_src") or s.get("embed_url")
                        if embed:
                            embed_srcs.append({
                                "email": s.get("email"),
                                "role": s.get("role"),
                                "embed_src": embed,
                            })
                if embed_srcs:
                    embed_src = embed_srcs[0]["embed_src"]
            elif isinstance(result, dict):
                subs = result.get("submitters") or []
                if isinstance(subs, list):
                    for s in subs:
                        if isinstance(s, dict):
                            embed = s.get("embed_src") or s.get("embed_url")
                            if embed:
                                embed_srcs.append({
                                    "email": s.get("email"),
                                    "role": s.get("role"),
                                    "embed_src": embed,
                                })
                if embed_srcs:
                    embed_src = embed_srcs[0]["embed_src"]
                if not embed_src:
                    embed_src = result.get("embed_src") or result.get("embed_url")
        except Exception:
            embed_src = None

        return {"embed_src": embed_src, "embed_srcs": embed_srcs, "submission": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


 


@router.post("/buyer-agreement/pdf-full")
async def generate_buyer_agreement_full(payload: BuyerAgreementPayload):
    """
    Generate the entire PDF from a JSON template with placeholders.
    """
    try:
        data: Dict[str, Any] = payload.model_dump()
        # Locate template
        # Support running from backend/ or backend/app
        here = Path(__file__).resolve()
        root1 = here.parents[1]  # .../backend/app
        root2 = here.parents[2]  # .../backend

        candidates = [
            root1 / "templates" / "buyer_agreement_template.json",
            root2 / "app" / "templates" / "buyer_agreement_template.json",
        ]
        template_path = next((p for p in candidates if p.exists()), None)
        if not template_path:
            raise HTTPException(status_code=500, detail="Template not found")

        # Render using template engine
        try:
            from ..services.pdf_template_renderer import render_pdf_from_template  # type: ignore
        except Exception:
            try:
                from backend.app.services.pdf_template_renderer import render_pdf_from_template  # type: ignore
            except Exception:
                from backend.app.services.pdf_template_renderer import render_pdf_from_template  # type: ignore

        # Include witness placeholders
        data.update({
            "witness1Name": payload.witness1Name or "",
            "witness1Address": payload.witness1Address or "",
            "witness2Name": payload.witness2Name or "",
            "witness2Address": payload.witness2Address or "",
        })
        pdf_bytes = render_pdf_from_template(data, template_path)
        headers = {"Content-Disposition": "inline; filename=buyer_agreement_generated.pdf"}
        return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/buyer-agreement/initiate")
async def initiate_buyer_agreement(payload: BuyerAgreementPayload):
    
    try:
        # Resolve template id from env or default provided by user
        template_str = os.getenv("DOCUSEAL_TEMPLATE_ID_BUYER") or 1891040
        try:
            template_id = int(template_str)
        except ValueError:
            raise HTTPException(status_code=500, detail="Invalid DOCUSEAL_TEMPLATE_ID_BUYER configuration")

        # Build submitters from provided emails
        submitters: List[Dict[str, Any]] = []
        if payload.buyerEmail:
            submitters.append({"email": payload.buyerEmail, "name": payload.buyerName or "Buyer"})
        if payload.investorEmail:
            submitters.append({"email": payload.investorEmail, "name": payload.investorName or "Investor"})
        if not submitters:
            raise HTTPException(status_code=400, detail="At least buyerEmail or investorEmail is required")

        api_key = os.getenv("DOCUSEAL_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Missing DOCUSEAL_API_KEY environment variable")
        client = DocuSealClient(api_key=api_key, base_url=os.getenv("DOCUSEAL_BASE_URL"))
        # Create submission and surface DocuSeal API errors clearly
        try:
            # Optionally include roles for submitters from env; default generic labels
            buyer_role = os.getenv("DOCUSEAL_BUYER_ROLE") or "Buyer"
            investor_role = os.getenv("DOCUSEAL_INVESTOR_ROLE") or "Investor"
            # Attach roles if not already provided
            for s in submitters:
                if "role" not in s:
                    if s.get("email") == (payload.buyerEmail or ""):
                        s["role"] = buyer_role
                    elif s.get("email") == (payload.investorEmail or ""):
                        s["role"] = investor_role

            # Avoid sending emails when embedding by default
            result = client.create_submission(template_id, submitters, send_email=False)
        except Exception as e:
            # Attempt to include HTTP response details when available
            status_detail = str(e)
            resp = getattr(e, "response", None)
            if resp is not None:
                try:
                    status_detail = f"DocuSeal API error {resp.status_code}: {resp.text}"
                except Exception:
                    status_detail = f"DocuSeal API error {resp.status_code}"
            raise HTTPException(status_code=502, detail=status_detail)

        # Build embed links per submitter and provide the first as embed_src for convenience
        embed_src = None
        embed_srcs: List[Dict[str, Any]] = []
        try:
            if isinstance(result, list):
                # Some responses may be a list of submitters
                for s in result:
                    if isinstance(s, dict):
                        embed = s.get("embed_src") or s.get("embed_url")
                        if embed:
                            embed_srcs.append({
                                "email": s.get("email"),
                                "role": s.get("role"),
                                "embed_src": embed,
                            })
                if embed_srcs:
                    embed_src = embed_srcs[0]["embed_src"]
            elif isinstance(result, dict):
                subs = result.get("submitters") or []
                if isinstance(subs, list):
                    for s in subs:
                        if isinstance(s, dict):
                            embed = s.get("embed_src") or s.get("embed_url")
                            if embed:
                                embed_srcs.append({
                                    "email": s.get("email"),
                                    "role": s.get("role"),
                                    "embed_src": embed,
                                })
                if embed_srcs:
                    embed_src = embed_srcs[0]["embed_src"]
                if not embed_src:
                    embed_src = result.get("embed_src") or result.get("embed_url")
        except Exception:
            embed_src = None

        return {"embed_src": embed_src, "embed_srcs": embed_srcs, "submission": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


 


@router.post("/buyer-agreement/pdf-full")
async def generate_buyer_agreement_full(payload: BuyerAgreementPayload):
    """
    Generate the entire PDF from a JSON template with placeholders.
    """
    try:
        data: Dict[str, Any] = payload.model_dump()
        # Locate template
        # Support running from backend/ or backend/app
        here = Path(__file__).resolve()
        root1 = here.parents[1]  # .../backend/app
        root2 = here.parents[2]  # .../backend

        candidates = [
            root1 / "templates" / "buyer_agreement_template.json",
            root2 / "app" / "templates" / "buyer_agreement_template.json",
        ]
        template_path = next((p for p in candidates if p.exists()), None)
        if not template_path:
            raise HTTPException(status_code=500, detail="Template not found")

        # Render using template engine
        try:
            from ..services.pdf_template_renderer import render_pdf_from_template  # type: ignore
        except Exception:
            try:
                from backend.app.services.pdf_template_renderer import render_pdf_from_template  # type: ignore
            except Exception:
                from backend.app.services.pdf_template_renderer import render_pdf_from_template  # type: ignore

        # Include witness placeholders
        data.update({
            "witness1Name": payload.witness1Name or "",
            "witness1Address": payload.witness1Address or "",
            "witness2Name": payload.witness2Name or "",
            "witness2Address": payload.witness2Address or "",
        })
        pdf_bytes = render_pdf_from_template(data, template_path)
        headers = {"Content-Disposition": "inline; filename=buyer_agreement_generated.pdf"}
        return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/buyer-agreement/initiate")
async def initiate_buyer_agreement(payload: BuyerAgreementPayload):
    
    try:
        # Resolve template id from env or default provided by user
        template_str = os.getenv("DOCUSEAL_TEMPLATE_ID_BUYER") or 1891040
        try:
            template_id = int(template_str)
        except ValueError:
            raise HTTPException(status_code=500, detail="Invalid DOCUSEAL_TEMPLATE_ID_BUYER configuration")

        # Build submitters from provided emails
        submitters: List[Dict[str, Any]] = []
        if payload.buyerEmail:
            submitters.append({"email": payload.buyerEmail, "name": payload.buyerName or "Buyer"})
        if payload.investorEmail:
            submitters.append({"email": payload.investorEmail, "name": payload.investorName or "Investor"})
        if not submitters:
            raise HTTPException(status_code=400, detail="At least buyerEmail or investorEmail is required")

        api_key = os.getenv("DOCUSEAL_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Missing DOCUSEAL_API_KEY environment variable")
        client = DocuSealClient(api_key=api_key, base_url=os.getenv("DOCUSEAL_BASE_URL"))
        # Create submission and surface DocuSeal API errors clearly
        try:
            # Optionally include roles for submitters from env; default generic labels
            buyer_role = os.getenv("DOCUSEAL_BUYER_ROLE") or "Buyer"
            investor_role = os.getenv("DOCUSEAL_INVESTOR_ROLE") or "Investor"
            # Attach roles if not already provided
            for s in submitters:
                if "role" not in s:
                    if s.get("email") == (payload.buyerEmail or ""):
                        s["role"] = buyer_role
                    elif s.get("email") == (payload.investorEmail or ""):
                        s["role"] = investor_role

            # Avoid sending emails when embedding by default
            result = client.create_submission(template_id, submitters, send_email=False)
        except Exception as e:
            # Attempt to include HTTP response details when available
            status_detail = str(e)
            resp = getattr(e, "response", None)
            if resp is not None:
                try:
                    status_detail = f"DocuSeal API error {resp.status_code}: {resp.text}"
                except Exception:
                    status_detail = f"DocuSeal API error {resp.status_code}"
            raise HTTPException(status_code=502, detail=status_detail)

        # Build embed links per submitter and provide the first as embed_src for convenience
        embed_src = None
        embed_srcs: List[Dict[str, Any]] = []
        try:
            if isinstance(result, list):
                # Some responses may be a list of submitters
                for s in result:
                    if isinstance(s, dict):
                        embed = s.get("embed_src") or s.get("embed_url")
                        if embed:
                            embed_srcs.append({
                                "email": s.get("email"),
                                "role": s.get("role"),
                                "embed_src": embed,
                            })
                if embed_srcs:
                    embed_src = embed_srcs[0]["embed_src"]
            elif isinstance(result, dict):
                subs = result.get("submitters") or []
                if isinstance(subs, list):
                    for s in subs:
                        if isinstance(s, dict):
                            embed = s.get("embed_src") or s.get("embed_url")
                            if embed:
                                embed_srcs.append({
                                    "email": s.get("email"),
                                    "role": s.get("role"),
                                    "embed_src": embed,
                                })
                if embed_srcs:
                    embed_src = embed_srcs[0]["embed_src"]
                if not embed_src:
                    embed_src = result.get("embed_src") or result.get("embed_url")
        except Exception:
            embed_src = None

        return {"embed_src": embed_src, "embed_srcs": embed_srcs, "submission": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class Investor(BaseModel):
    name: Optional[str] = ""
    email: Optional[str] = ""
    address: Optional[str] = ""
    mobile: Optional[str] = ""
    amount: Optional[str] = ""
    downPayment: Optional[str] = ""
    equityPercent: Optional[str] = ""


class InvestorAgreementPayload(BaseModel):
    homebuyer: Dict[str, Any]
    property: Dict[str, Any]
    investors: List[Investor]
    place_of_execution: Optional[str] = ""
    arbitrationCity: Optional[str] = ""
    arbitrationState: Optional[str] = ""
    agreementId: Optional[str] = ""
    agreementDate: Optional[str] = ""
    managingOwnerName: Optional[str] = ""
   
    witness1Name: Optional[str] = ""
    witness1Address: Optional[str] = ""
    witness2Name: Optional[str] = ""
    witness2Address: Optional[str] = ""


@router.post("/investor-agreement/pdf-full")
async def generate_investor_agreement_full(payload: InvestorAgreementPayload):
    try:
        # Flatten and prepare data for template
        hb = payload.homebuyer or {}
        prop = payload.property or {}
        investors = payload.investors or []
        number_of_investors = len(investors)

        # Build investors short and block strings
        shorts = []
        lines = []
        for i, inv in enumerate(investors, start=1):
            n = (inv.name or "").strip()
            amt = (inv.amount or inv.downPayment or "").strip()
            eq = (inv.equityPercent or "").strip()
            mob = (inv.mobile or "").strip()
            addr = (inv.address or "").strip()
            short = f"{n} (₹{amt}, {eq}% eq.)" if n else f"Investor {i} (₹{amt}, {eq}% eq.)"
            shorts.append(short)
            line = (
                f"Investor #{i}: Name {n}; Mobile {mob}; Address {addr}; Contribution ₹{amt}; Equity % {eq}."
            )
            lines.append(line)
        investors_short = "; ".join(shorts)
        investors_block = "\n".join(lines) if lines else "(No investors provided)"

        # Locate template
        here = Path(__file__).resolve()
        root1 = here.parents[1]  # .../backend/app
        root2 = here.parents[2]  # .../backend
        candidates = [
            root1 / "templates" / "investor_agreement_template.json",
            root2 / "app" / "templates" / "investor_agreement_template.json",
        ]
        template_path = next((p for p in candidates if p.exists()), None)
        if not template_path:
            raise HTTPException(status_code=500, detail="Investor template not found")

        # Render
        try:
            from ..services.pdf_template_renderer import render_pdf_from_template  # type: ignore
        except Exception:
            try:
                from backend.app.services.pdf_template_renderer import render_pdf_from_template  # type: ignore
            except Exception:
                from backend.app.services.pdf_template_renderer import render_pdf_from_template  # type: ignore

        data: Dict[str, Any] = {
            # Homebuyer
            "buyerName": hb.get("name", ""),
            "buyerAddress": hb.get("address", ""),
            "buyerMobile": hb.get("mobile", ""),
            # Property
            "propertyName": prop.get("propertyName", ""),
            "propertyLocationText": prop.get("propertyLocationText", ""),
            "propertyValue": prop.get("propertyValue", ""),
            "latitude": prop.get("latitude", ""),
            "longitude": prop.get("longitude", ""),
            "propertyFullDescription": prop.get("propertyFullDescription", ""),
            # Investors derived
            "numberOfInvestors": number_of_investors,
            "investorsShort": investors_short,
            "investorsBlock": investors_block,
            # Meta
            "place_of_execution": payload.place_of_execution or "",
            "arbitrationCity": payload.arbitrationCity or "",
            "arbitrationState": payload.arbitrationState or "",
            "agreementId": payload.agreementId or "",
            "agreementDate": payload.agreementDate or "",
            "managingOwnerName": payload.managingOwnerName or hb.get("name", ""),
            # Witnesses
            "witness1Name": payload.witness1Name or "",
            "witness1Address": payload.witness1Address or "",
            "witness2Name": payload.witness2Name or "",
            "witness2Address": payload.witness2Address or "",
        }

        pdf_bytes = render_pdf_from_template(data, template_path)
        headers = {"Content-Disposition": "inline; filename=investor_agreement_generated.pdf"}
        return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/investor-agreement/pdf-sign")
async def investor_pdf_sign(payload: InvestorAgreementPayload):
    try:
        max_signers = 6
        # 1) Render customized investor agreement PDF from payload JSON
        hb = payload.homebuyer or {}
        prop = payload.property or {}
        investors = payload.investors or []
        number_of_investors = len(investors)

        shorts = []
        lines = []
        for i, inv in enumerate(investors, start=1):
            n = (inv.name or "").strip()
            amt = (inv.amount or inv.downPayment or "").strip()
            eq = (inv.equityPercent or "").strip()
            mob = (inv.mobile or "").strip()
            addr = (inv.address or "").strip()
            short = f"{n} (₹{amt}, {eq}% eq.)" if n else f"Investor {i} (₹{amt}, {eq}% eq.)"
            shorts.append(short)
            line = (
                f"Investor #{i}: Name {n}; Mobile {mob}; Address {addr}; Contribution ₹{amt}; Equity % {eq}."
            )
            lines.append(line)
        investors_short = "; ".join(shorts)
        investors_block = "\n".join(lines) if lines else "(No investors provided)"

        here = Path(__file__).resolve()
        root1 = here.parents[1]  # .../backend/app
        root2 = here.parents[2]  # .../backend
        candidates = [
            root1 / "templates" / "investor_agreement_template.json",
            root2 / "app" / "templates" / "investor_agreement_template.json",
        ]
        template_path = next((p for p in candidates if p.exists()), None)
        if not template_path:
            raise HTTPException(status_code=500, detail="Investor template not found")

        try:
            from ..services.pdf_template_renderer import render_pdf_from_template  # type: ignore
        except Exception:
            try:
                from backend.app.services.pdf_template_renderer import render_pdf_from_template  # type: ignore
            except Exception:
                from backend.app.services.pdf_template_renderer import render_pdf_from_template  # type: ignore

        data: Dict[str, Any] = {
            "buyerName": hb.get("name", ""),
            "buyerAddress": hb.get("address", ""),
            "buyerMobile": hb.get("mobile", ""),
            "propertyName": prop.get("propertyName", ""),
            "propertyLocationText": prop.get("propertyLocationText", ""),
            "propertyValue": prop.get("propertyValue", ""),
            "latitude": prop.get("latitude", ""),
            "longitude": prop.get("longitude", ""),
            "propertyFullDescription": prop.get("propertyFullDescription", ""),
            "numberOfInvestors": number_of_investors,
            "investorsShort": investors_short,
            "investorsBlock": investors_block,
            "place_of_execution": payload.place_of_execution or "",
            "arbitrationCity": payload.arbitrationCity or "",
            "arbitrationState": payload.arbitrationState or "",
            "agreementId": payload.agreementId or "",
            "agreementDate": payload.agreementDate or "",
            "managingOwnerName": payload.managingOwnerName or hb.get("name", ""),
            "witness1Name": payload.witness1Name or "",
            "witness1Address": payload.witness1Address or "",
            "witness2Name": payload.witness2Name or "",
            "witness2Address": payload.witness2Address or "",
        }
        pdf_bytes = render_pdf_from_template(data, template_path)

        # 2) Add signature page and map one signer row per investor
        combined_pdf_bytes, signature_page_number = append_signature_page(pdf_bytes)

        page_w_mm = 210.0
        page_h_mm = 297.0

        def mm_x(x_mm: float) -> float:
            return max(0.0, min(1.0, x_mm / page_w_mm))

        def mm_w(w_mm: float) -> float:
            return max(0.0, min(1.0, w_mm / page_w_mm))

        def mm_y_from_top(y_mm_from_top: float) -> float:
            return max(0.0, min(1.0, y_mm_from_top / page_h_mm))

        sig_x = mm_x(25.0)
        sig_w = mm_w(160.0)
        name_x = mm_x(40.0)
        name_w = mm_w(55.0)
        date_x = mm_x(125.0)
        date_w = mm_w(60.0)

        field_h_sig = mm_y_from_top(6.0)
        field_h_txt = mm_y_from_top(6.0)

        fields: List[Dict[str, Any]] = []
        submitters: List[Dict[str, Any]] = []

        row_start_sig_mm = 58.0
        row_start_meta_mm = 65.0
        row_step_mm = 40.0

        for i, inv in enumerate(investors, start=1):
            email = (inv.email or "").strip()
            name = (inv.name or "").strip() or f"Investor {i}"
            if not email:
                continue

            role = f"Investor {i}"
            submitters.append({"email": email, "name": name, "role": role})

            sig_y = mm_y_from_top(row_start_sig_mm + ((i - 1) * row_step_mm))
            meta_y = mm_y_from_top(row_start_meta_mm + ((i - 1) * row_step_mm))

            fields.extend([
                {
                    "name": f"{role} Signature",
                    "type": "signature",
                    "role": role,
                    "areas": [{"x": sig_x, "y": sig_y, "w": sig_w, "h": field_h_sig, "page": signature_page_number}],
                },
                {
                    "name": f"{role} Name",
                    "type": "text",
                    "role": role,
                    "areas": [{"x": name_x, "y": meta_y, "w": name_w, "h": field_h_txt, "page": signature_page_number}],
                    "default_value": name,
                    "readonly": False,
                },
                {
                    "name": f"{role} Date",
                    "type": "date",
                    "role": role,
                    "areas": [{"x": date_x, "y": meta_y, "w": date_w, "h": field_h_txt, "page": signature_page_number}],
                },
            ])

        if not submitters:
            raise HTTPException(status_code=400, detail="At least one investor with email is required")
        if len(submitters) > max_signers:
            raise HTTPException(status_code=400, detail=f"Investor Agreement supports up to {max_signers} signers")

        # 3) Send customized PDF to DocuSeal
        client = DocuSealClient(api_key=os.getenv("DOCUSEAL_API_KEY"), base_url=os.getenv("DOCUSEAL_BASE_URL"))
        resp = client.create_submission_from_pdf(
            combined_pdf_bytes,
            submitters=submitters,
            fields=fields,
            send_email=False,
            filename="investor_agreement.pdf",
        )

        # 4) Normalize response for frontend
        submission_id = resp.get("id") or resp.get("submission_id")
        embed_src = None
        embed_srcs: List[Dict[str, Any]] = []

        def _pick_link(obj: Any) -> Optional[str]:
            if not isinstance(obj, dict):
                return None
            return (
                obj.get("embed_src")
                or obj.get("embed_url")
                or obj.get("signing_url")
                or obj.get("sign_url")
                or obj.get("url")
                or obj.get("link")
            )

        possible_submitters = []
        if isinstance(resp, dict):
            if isinstance(resp.get("submitters"), list):
                possible_submitters.extend(resp.get("submitters") or [])
            submission_obj = resp.get("submission")
            if isinstance(submission_obj, dict) and isinstance(submission_obj.get("submitters"), list):
                possible_submitters.extend(submission_obj.get("submitters") or [])
            data_obj = resp.get("data")
            if isinstance(data_obj, dict) and isinstance(data_obj.get("submitters"), list):
                possible_submitters.extend(data_obj.get("submitters") or [])
            if isinstance(resp.get("embed_srcs"), list):
                possible_submitters.extend(resp.get("embed_srcs") or [])
        elif isinstance(resp, list):
            possible_submitters.extend(resp)

        if not possible_submitters and isinstance(resp, dict):
            maybe_link = _pick_link(resp)
            if maybe_link:
                possible_submitters.append(resp)

        seen_links = set()
        for i, s in enumerate(possible_submitters):
            link = _pick_link(s)
            if not link or link in seen_links:
                continue
            seen_links.add(link)

            mapped_email = ""
            mapped_role = ""
            if isinstance(s, dict):
                mapped_email = (s.get("email") or "").strip()
                mapped_role = (s.get("role") or "").strip()

            # Fallback to the original submitter payload order when DocuSeal omits fields
            if not mapped_email and i < len(submitters):
                mapped_email = str(submitters[i].get("email") or "")
            if not mapped_role and i < len(submitters):
                mapped_role = str(submitters[i].get("role") or "")

            if not embed_src:
                embed_src = link
            embed_srcs.append({"email": mapped_email, "role": mapped_role, "embed_src": link})

        if not embed_src and isinstance(resp, dict):
            embed_src = _pick_link(resp)

        return {"submission_id": submission_id, "embed_src": embed_src, "embed_srcs": embed_srcs, "raw": resp}
    except DocuSealError as e:
        return JSONResponse(status_code=502, content={"error": str(e)})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"/investor-agreement/pdf-sign failed: {e}")


class DocuSealSubmitter(BaseModel):
    email: str
    name: str


class DocuSealSubmissionPayload(BaseModel):
    template_id: int
    submitters: List[DocuSealSubmitter]


@router.post("/buyer-agreement/docuseal/submission")
async def buyer_docuseal_submission(payload: DocuSealSubmissionPayload):
    try:
        client = DocuSealClient(api_key=os.getenv("DOCUSEAL_API_KEY"), base_url=os.getenv("DOCUSEAL_BASE_URL"))
        result = client.create_submission(payload.template_id, [s.model_dump() for s in payload.submitters])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/investor-agreement/docuseal/submission")
async def investor_docuseal_submission(payload: DocuSealSubmissionPayload):
    try:
        client = DocuSealClient(api_key=os.getenv("DOCUSEAL_API_KEY"), base_url=os.getenv("DOCUSEAL_BASE_URL"))
        result = client.create_submission(payload.template_id, [s.model_dump() for s in payload.submitters])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class DocuSealAutoSignPayload(BaseModel):
    submitter_id: int
    fields: Optional[List[Dict[str, Any]]] = None


@router.put("/docuseal/submitters/auto-sign")
async def docuseal_auto_sign(payload: DocuSealAutoSignPayload):
    try:
        client = DocuSealClient(api_key=os.getenv("DOCUSEAL_API_KEY"), base_url=os.getenv("DOCUSEAL_BASE_URL"))
        data = {"completed": True}
        if payload.fields:
            data["fields"] = payload.fields
        result = client.update_submitter(payload.submitter_id, data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/docuseal/finalize-status/{submission_id}")
async def get_finalize_status(submission_id: str):
    # Return current status/result from in-memory store; useful for frontend polling
    res = FINALIZE_RESULTS.get(submission_id)
    if not res:
        return {"status": "unknown"}
    return res


class IPFSUploadPayload(BaseModel):
    pdf_base64: str
    filename: Optional[str] = "document.pdf"


@router.post("/ipfs/upload")
async def ipfs_upload(payload: IPFSUploadPayload):
    try:
        if not payload.pdf_base64:
            raise HTTPException(status_code=400, detail="pdf_base64 is required")
        try:
            data = base64.b64decode(payload.pdf_base64)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 data")

        client = IPFSClient()
        res = client.upload_bytes(data, filename=payload.filename or "document.pdf")
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class DocuSealFinalizePayload(BaseModel):
    submission_id: Union[str, int]
    filename: Optional[str] = "signed_document.pdf"
    max_wait_seconds: Optional[int] = 120
    poll_interval_seconds: Optional[float] = 2.0


def _is_submitter_completed(sub: Dict[str, Any]) -> bool:
    try:
        if isinstance(sub, dict):
            if bool(sub.get("completed")):
                return True
            if sub.get("completed_at"):
                return True
            status = str(sub.get("status") or "").lower()
            if status in ("completed", "done", "finished"):
                return True
    except Exception:
        pass
    return False


@router.post("/docuseal/finalize-and-ipfs")
async def docuseal_finalize_and_ipfs(payload: DocuSealFinalizePayload):
    """
    Poll a DocuSeal submission until all submitters are completed (bounded wait),
    download the finalized PDF(s), and upload to IPFS (Pinata). Returns CID and SHA-256.
    No webhooks used.
    """
    try:
        api_key = os.getenv("DOCUSEAL_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Missing DOCUSEAL_API_KEY environment variable")
        client = DocuSealClient(api_key=api_key, base_url=os.getenv("DOCUSEAL_BASE_URL"))

        max_wait = int(payload.max_wait_seconds or 120)
        interval = float(payload.poll_interval_seconds or 2.0)
        waited = 0.0

        # Poll submission status
        submission = None
        while waited <= max_wait:
            try:
                submission = client.get_submission(str(payload.submission_id))
            except Exception as e:
                raise HTTPException(status_code=502, detail=f"DocuSeal fetch error: {e}")

            # Check if all submitters completed
            submitters = submission.get("submitters") or []
            if submitters and all(_is_submitter_completed(s) for s in submitters if isinstance(s, dict)):
                break
            await asyncio.sleep(interval)
            waited += interval

        if not submission:
            raise HTTPException(status_code=500, detail="No submission data returned from DocuSeal")

        # If still not completed after wait, return 202 with partial info
        submitters = submission.get("submitters") or []
        if not (submitters and all(_is_submitter_completed(s) for s in submitters if isinstance(s, dict))):
            return {"status": "pending", "submission": submission}

        # Try to locate finalized document(s)
        # DocuSeal responses often include 'documents' with 'download_url' or similar
        documents = submission.get("documents") or []
        pdf_bytes_combined: bytes | None = None
        try:
            if documents and isinstance(documents, list):
                # Download all PDFs and concatenate if multiple
                pdf_parts: List[bytes] = []
                for doc in documents:
                    if isinstance(doc, dict):
                        url = doc.get("download_url") or doc.get("url") or doc.get("file_url")
                        if url:
                            content, _ctype = client.download_file(url)
                            if content:
                                pdf_parts.append(content)
                if pdf_parts:
                    if len(pdf_parts) == 1:
                        pdf_bytes_combined = pdf_parts[0]
                    else:
                        # Simple concat fallback: for PDFs this is not guaranteed to produce a valid merged doc.
                        # If needed, integrate PyPDF2 to merge, but try direct return of first for now.
                        pdf_bytes_combined = pdf_parts[0]
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"DocuSeal download error: {e}")

        if not pdf_bytes_combined:
            # As a fallback, try 'final_pdf_url' at top-level if present
            url = submission.get("final_pdf_url") or submission.get("download_url")
            if url:
                try:
                    pdf_bytes_combined, _ctype = client.download_file(url)
                except Exception as e:
                    raise HTTPException(status_code=502, detail=f"DocuSeal download error: {e}")

        if not pdf_bytes_combined:
            raise HTTPException(status_code=500, detail="Unable to locate finalized PDF to download")

        # Upload to IPFS (Pinata)
        try:
            ipfs = IPFSClient()
            res = ipfs.upload_bytes(pdf_bytes_combined, filename=payload.filename or "signed_document.pdf")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"IPFS upload error: {e}")

        return {"status": "completed", **res}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class DocuSealFinalizeStartPayload(BaseModel):
    submission_id: Union[str, int]
    filename: Optional[str] = "signed_document.pdf"


@router.post("/docuseal/finalize-start")
async def docuseal_finalize_start(payload: DocuSealFinalizeStartPayload):
    """
    Manually start the background finalize-and-IPFS job for a given submission_id.
    Useful if the server restarted (in-memory state lost) or if you created the
    submission via another endpoint without auto-kickoff.
    """
    try:
        sub_id = str(payload.submission_id)
        if not sub_id:
            raise HTTPException(status_code=400, detail="submission_id is required")

        # Mark pending and kick off background task (same logic as auto-start)
        FINALIZE_RESULTS[sub_id] = {"status": "pending", "note": "manual start"}

        async def _bg_finalize_manual(sub_id: str, file_name: str):
            try:
                api_key = os.getenv("DOCUSEAL_API_KEY")
                client = DocuSealClient(api_key=api_key, base_url=os.getenv("DOCUSEAL_BASE_URL"))
                max_wait = 3600
                interval = 5.0
                waited = 0.0
                while waited <= max_wait:
                    sub = client.get_submission(sub_id)
                    subs = sub.get("submitters") or []
                    try:
                        total = len(subs) if isinstance(subs, list) else 0
                        completed = sum(1 for s in subs if isinstance(s, dict) and bool(s.get("completed")))
                        FINALIZE_RESULTS[sub_id] = {
                            "status": "pending",
                            "submitters_total": total,
                            "submitters_completed": completed,
                            "last_checked": datetime.now(timezone.utc).isoformat(),
                        }
                    except Exception:
                        pass
                    if subs and all(bool(s.get("completed")) for s in subs if isinstance(s, dict)):
                        documents = sub.get("documents") or []
                        pdf_bytes: bytes | None = None
                        if documents and isinstance(documents, list):
                            for d in documents:
                                if isinstance(d, dict):
                                    url = d.get("download_url") or d.get("url") or d.get("file_url")
                                    if url:
                                        pdf_bytes, _ctype = client.download_file(url)
                                        if pdf_bytes:
                                            break
                        if not pdf_bytes:
                            url = sub.get("final_pdf_url") or sub.get("download_url")
                            if url:
                                pdf_bytes, _ctype = client.download_file(url)
                        if pdf_bytes:
                            ipfs = IPFSClient()
                            res = ipfs.upload_bytes(pdf_bytes, filename=file_name or "signed_document.pdf")
                            FINALIZE_RESULTS[sub_id] = {"status": "completed", **res}
                        else:
                            FINALIZE_RESULTS[sub_id] = {"status": "error", "error": "No finalized PDF found"}
                        return
                    await asyncio.sleep(interval)
                    waited += interval
                FINALIZE_RESULTS[sub_id] = {"status": "pending", "message": "Not completed within wait window"}
            except Exception as e:
                FINALIZE_RESULTS[sub_id] = {"status": "error", "error": str(e)}

        asyncio.create_task(_bg_finalize_manual(sub_id, payload.filename or "signed_document.pdf"))
        return {"status": "started", "submission_id": sub_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class DocuSealFinalizeNowPayload(BaseModel):
    submission_id: Union[str, int]
    filename: Optional[str] = "signed_document.pdf"


@router.post("/docuseal/finalize-now")
async def docuseal_finalize_now(payload: DocuSealFinalizeNowPayload):
    """
    Single-attempt finalize: no polling, no webhooks.
    If submission isn't fully completed yet, returns 409 with submitter counts.
    If completed, downloads the final PDF and uploads to IPFS (Pinata) immediately.
    """
    try:
        api_key = os.getenv("DOCUSEAL_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Missing DOCUSEAL_API_KEY environment variable")
        client = DocuSealClient(api_key=api_key, base_url=os.getenv("DOCUSEAL_BASE_URL"))

        sub_id = str(payload.submission_id)
        sub = client.get_submission(sub_id)
        subs = sub.get("submitters") or []
        total = len(subs) if isinstance(subs, list) else 0
        completed = sum(1 for s in subs if isinstance(s, dict) and bool(s.get("completed")))
        if not (subs and all(_is_submitter_completed(s) for s in subs if isinstance(s, dict))):
            raise HTTPException(status_code=409, detail={
                "status": "not-completed",
                "submitters_total": total,
                "submitters_completed": completed,
            })

        # Attempt to locate and download the finalized PDF
        documents = sub.get("documents") or []
        pdf_bytes: bytes | None = None
        if documents and isinstance(documents, list):
            for d in documents:
                if isinstance(d, dict):
                    url = d.get("download_url") or d.get("url") or d.get("file_url")
                    if url:
                        pdf_bytes, _ctype = client.download_file(url)
                        if pdf_bytes:
                            break
        if not pdf_bytes:
            url = sub.get("final_pdf_url") or sub.get("download_url")
            if url:
                pdf_bytes, _ctype = client.download_file(url)
        if not pdf_bytes:
            raise HTTPException(status_code=502, detail="No finalized PDF found to download")

        ipfs = IPFSClient()
        res = ipfs.upload_bytes(pdf_bytes, filename=payload.filename or "signed_document.pdf")
        return {"status": "completed", **res}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/docuseal/finalized-pdf/{submission_id}")
async def docuseal_finalized_pdf(submission_id: str):
    """
    Return the finalized signed PDF as a streaming response.
    If the submission isn't completed yet, return 409.
    """
    try:
        api_key = os.getenv("DOCUSEAL_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Missing DOCUSEAL_API_KEY environment variable")
        client = DocuSealClient(api_key=api_key, base_url=os.getenv("DOCUSEAL_BASE_URL"))

        sub = client.get_submission(submission_id)
        subs = sub.get("submitters") or []
        if not (subs and all(_is_submitter_completed(s) for s in subs if isinstance(s, dict))):
            raise HTTPException(status_code=409, detail={"status": "not-completed"})

        documents = sub.get("documents") or []
        pdf_bytes: bytes | None = None
        if documents and isinstance(documents, list):
            for d in documents:
                if isinstance(d, dict):
                    url = d.get("download_url") or d.get("url") or d.get("file_url")
                    if url:
                        pdf_bytes, _ctype = client.download_file(url)
                        if pdf_bytes:
                            break
        if not pdf_bytes:
            url = sub.get("final_pdf_url") or sub.get("download_url")
            if url:
                pdf_bytes, _ctype = client.download_file(url)
        if not pdf_bytes:
            raise HTTPException(status_code=502, detail="No finalized PDF found to download")

        headers = {"Content-Disposition": "attachment; filename=finalized_signed.pdf"}
        return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers=headers)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

