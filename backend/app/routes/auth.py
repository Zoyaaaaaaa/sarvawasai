# auth.py - Twilio OTP integration for phone verification
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from twilio.rest import Client
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
from bson import ObjectId

load_dotenv()

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Initialize Twilio client
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_VERIFY_SERVICE_SID = os.getenv("TWILIO_VERIFY_SERVICE_SID")

if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_VERIFY_SERVICE_SID]):
    raise ValueError(
        "Missing Twilio credentials. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, "
        "and TWILIO_VERIFY_SERVICE_SID in environment variables."
    )

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def normalize_phone(phone: str) -> str:
    """Normalize phone number to E.164 format.

    - If number starts with '+', return as-is
    - If 10 digits, assume India (+91)
    - If 11 digits and starts with '0', strip leading '0' and add +91
    - Otherwise prepend '+' and return
    """
    raw = phone.strip().replace(" ", "").replace("-", "")
    if raw.startswith("+"):
        return raw
    if raw.isdigit():
        if len(raw) == 10:
            return "+91" + raw
        if len(raw) == 11 and raw.startswith("0"):
            return "+91" + raw[1:]
        # Unknown country format; keep with +
        return "+" + raw
    return raw


class SendOtpRequest(BaseModel):
    phone: str


class VerifyOtpRequest(BaseModel):
    phone: str
    otp_code: str


class MarkVerifiedRequest(BaseModel):
    user_id: str
    email: str


@router.post("/send-otp")
async def send_otp(request: SendOtpRequest):
    """
    Send OTP to the provided phone number using Twilio Verify Service
    """
    try:
        # Normalize to E.164 phone number
        phone = normalize_phone(request.phone)

        is_dev = os.getenv("ENV") != "production"

        # DEV MODE BYPASS
        if is_dev:
            print("✅ DEV MODE: Mock OTP sent to:", phone)
            return {
                "status": "success",
                "message": f"OTP sent to {phone} (DEV MODE)",
                "verification_sid": "dev-mode-sid"
            }

        # Send OTP via Twilio Verify Service
        verification = client.verify.v2.services(TWILIO_VERIFY_SERVICE_SID).verifications.create(
            to=phone,
            channel="sms"
        )

        return {
            "status": "success",
            "message": f"OTP sent to {phone}",
            "verification_sid": verification.sid
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send OTP: {str(e)}"
        )


@router.post("/verify-otp")
async def verify_otp(request: VerifyOtpRequest):
    try:
        phone = normalize_phone(request.phone)

        is_dev = os.getenv("ENV") != "production"

        # DEV MODE BYPASS
        if is_dev and request.otp_code == "123456":
            print("✅ DEV OTP used for:", phone)
            return {
                "status": "approved",
                "message": "Dev OTP verified",
                "phone_verified": True
            }

        # Production / real verification
        verification_check = client.verify.v2.services(
            TWILIO_VERIFY_SERVICE_SID
        ).verification_checks.create(
            to=phone,
            code=request.otp_code
        )

        if verification_check.status == "approved":
            return {
                "status": "approved",
                "message": "Phone number verified successfully",
                "phone_verified": True
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid OTP or verification expired"
            )

    except Exception as e:
        if "Invalid" in str(e) or "not found" in str(e):
            raise HTTPException(
                status_code=400,
                detail="Invalid OTP or verification expired"
            )
        raise HTTPException(
            status_code=500,
            detail=f"Verification failed: {str(e)}"
        )


@router.post("/resend-otp")
async def resend_otp(request: SendOtpRequest):
    """
    Resend OTP to the provided phone number
    """
    try:
        # Normalize to E.164 phone number
        phone = normalize_phone(request.phone)

        is_dev = os.getenv("ENV") != "production"

        # DEV MODE BYPASS
        if is_dev:
            print("✅ DEV MODE: Mock OTP resent to:", phone)
            return {
                "status": "success",
                "message": f"OTP resent to {phone} (DEV MODE)",
                "verification_sid": "dev-mode-sid"
            }

        # Send OTP via Twilio Verify Service
        verification = client.verify.v2.services(TWILIO_VERIFY_SERVICE_SID).verifications.create(
            to=phone,
            channel="sms"
        )

        return {
            "status": "success",
            "message": f"OTP resent to {phone}",
            "verification_sid": verification.sid
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resend OTP: {str(e)}"
        )


@router.post("/mark-verified")
async def mark_verified(request: MarkVerifiedRequest):
    """
    Mark user as verified after phone verification succeeds.
    This is called from frontend after successful OTP verification.
    """
    try:
        try:
            from ..services.database import get_database
        except Exception:
            from backend.app.services.database import get_database  # type: ignore
        try:
            db = get_database()
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc))
        
        # Update user document to mark as verified
        result = await db.users.update_one(
            {"_id": ObjectId(request.user_id)},
            {
                "$set": {
                    "isVerified": True,
                    "accountStatus": "active",
                    "updatedAt": datetime.now(timezone.utc)
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        return {
            "status": "success",
            "message": "User marked as verified",
            "isVerified": True
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to mark user as verified: {str(e)}"
        )
