# users.py
from fastapi import APIRouter, HTTPException
try:
    from ..services.database import get_database
except Exception:
    from backend.app.services.database import get_database  # type: ignore
from datetime import datetime, timezone
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from passlib.context import CryptContext
import math
import hashlib

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(prefix="/users", tags=["users"])

@router.post("/signup")
async def signup_user(payload: dict):
    """
    Signup Endpoint:
    - Validates required fields
    - Checks for duplicate email
    - Creates User document and role-specific profile
    
    For Investors, accepts additional ML feature fields:
    - annualIncome: Annual income of investor
    - investmentCapital: Available capital for investment
    - riskAppetite: conservative/moderate/aggressive
    - expectedROI: Expected return on investment (%)
    - maxHoldingPeriodMonths: Maximum holding period in months
    - diversificationPreference: low/medium/high
    - investorAccreditationLevel: basic/accredited/institutional
    
    Block A (Behavioral Scores):
    - risk_orientation_score: 0.0 to 1.0
    - collaboration_comfort_score: 0.0 to 1.0
    - control_preference_score: 0.0 to 1.0
    - real_estate_conviction_score: 0.0 to 1.0
    
    Block B (Capital & Market Context):
    - capital_band: 1-5 (auto-calculated if not provided)
    - expected_roi_band: low/medium/high (auto-calculated)
    - holding_period_band: short/medium/long (auto-calculated)
    - ticket_size_stability: 0.0 to 1.0
    - behavioral_consistency_score: 0.0 to 1.0
    - capital_coverage_ratio: Calculated ratio
    - city_tier: 1, 2, or 3
    
    Block C (Historical Performance):
    - deal_success_ratio: 0.0 to 1.0
    - avg_holding_duration: Average months held
    """

    db = get_database()

    # -------------------- Validate required fields --------------------
    required_fields = ["fullName", "email", "phone", "userType", "password"]
    for field in required_fields:
        if not payload.get(field):
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    password = payload.get("password")
    if password:
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password = password_bytes[:72].decode('utf-8', errors='replace')

    role = payload.get("userType")
    if role not in ["buyer", "investor"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'buyer' or 'investor'.")

    # -------------------- Check for duplicate email --------------------
    existing_user = await db.users.find_one({"email": payload["email"]})
    if existing_user:
        raise HTTPException(status_code=400, detail="A user with this email already exists.")

    # -------------------- Build User document --------------------
    # Generate unique blockchain wallet address
    wallet_string = f"{payload['email']}{payload['phone']}{datetime.now(timezone.utc).isoformat()}"
    blockchain_wallet = hashlib.sha256(wallet_string.encode()).hexdigest()
    
    user_doc = {
        "fullName": payload.get("fullName"),
        "email": payload.get("email"),
        "phone": payload.get("phone"),
        "passwordHash": pwd_ctx.hash(password),
        "role": role,
        "casteCategory": payload.get("casteCategory", "Prefer not to say"),
        "age": payload.get("age"),
        "profession": payload.get("profession"),
        "additionalInfo": payload.get("additionalInfo"),
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc),
        "lastLogin": None,
        "loginProvider": "email",
        "mfaEnabled": False,
        "accountStatus": "pendingKYC",
        "kycStatus": "not_verified",
        "isVerified": False,
        "blockchainWallet": blockchain_wallet,
        "trustBadgeNFT": None,
        "blockchainTxRefs": []    
    }

    # -------------------- Insert into users collection --------------------
    try:
        user_res = await db.users.insert_one(user_doc)
        user_id = user_res.inserted_id
    except DuplicateKeyError as e:
        raise HTTPException(status_code=400, detail=f"Duplicate key error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

    # -------------------- Create role-specific profile --------------------
    if role == "investor":
        available_capital = payload.get("investmentCapital", 0)
        annual_income = payload.get("annualIncome", 0)
        
        # Calculate Capital Depth Index: CDI = log(availableCapital + annualIncome)
        capital_depth_index = math.log(available_capital + annual_income + 1) if (available_capital + annual_income) > 0 else 0
        
        investor_doc = {
            "userId": user_id,
            "availableCapital": available_capital,
            "annualIncome": annual_income,
            "preferredLocations": payload.get("preferredLocations", []),
            "experienceYears": payload.get("experienceYears"),
            "matchScore": 0,
            "coInvestments": [],
            "riskAppetite": payload.get("riskAppetite"),
            "preferredInvestmentType": payload.get("preferredInvestmentType", []),
            "expectedROI": payload.get("expectedROI"),
            "maxHoldingPeriodMonths": payload.get("maxHoldingPeriodMonths"),
            "diversificationPreference": payload.get("diversificationPreference"),
            "investorAccreditationLevel": payload.get("investorAccreditationLevel"),
            "auditFlag": False,
            
            # Block A: Behavioral Scores
            "block_a": {
                "risk_orientation_score": payload.get("risk_orientation_score"),
                "collaboration_comfort_score": payload.get("collaboration_comfort_score"),
                "control_preference_score": payload.get("control_preference_score"),
                "real_estate_conviction_score": payload.get("real_estate_conviction_score")
            },
            
            # Block B: Capital & Market Context
            "block_b": {
                "capital_band": payload.get("capital_band"),
                "expected_roi_band": payload.get("expected_roi_band"),
                "holding_period_band": payload.get("holding_period_band"),
                "capital_depth_index": capital_depth_index,
                "ticket_size_stability": payload.get("ticket_size_stability", 0.0),
                "holding_period_months": payload.get("maxHoldingPeriodMonths"),
                "behavioral_consistency_score": payload.get("behavioral_consistency_score", 0.0),
                "capital_coverage_ratio": payload.get("capital_coverage_ratio"),
                "city_tier": payload.get("city_tier")
            },
            
            # Block C: Historical Performance
            "block_c": {
                "deal_success_ratio": payload.get("deal_success_ratio", 0.0),
                "avg_holding_duration": payload.get("avg_holding_duration", 0.0),
                "behavioral_consistency_score": payload.get("behavioral_consistency_score", 0.0)
            },
            
            # ML Feature Metadata
            "snapshot_timestamp": datetime.utcnow(),
            "feature_version": "v1.0",
            "data_source": payload.get("data_source", "user_signup"),
            "confidence_weight": payload.get("confidence_weight", 1.0),
            "source_log_hash": payload.get("source_log_hash")
        }
        await db.investor_profiles.insert_one(investor_doc)

    elif role == "buyer":
        homebuyer_doc = {
            "userId": user_id,
            "monthlyIncome": payload.get("monthlyIncome"),
            "propertyType": payload.get("propertyType"),
            "preferredCities": payload.get("preferredLocations", []),
            "budgetRange": {
                "min": payload.get("budgetMin", 0),
                "max": payload.get("budgetMax", 0)
            },
            "riskToleranceLevel": payload.get("riskToleranceLevel"),
            "investmentExperienceYears": payload.get("experienceYears"),
            "financialBehaviorScore": None,
            "spendingPattern": "balanced",
            "emergencyFundAvailable": None,
            "latePaymentHistory": "never",
            "financialStabilityRating": None,
            "financialHistory": {
                "loanHistory": [],
                "investmentHistory": [],
                "defaultHistory": {
                    "hasDefaulted": False,
                    "defaultCount": 0,
                    "lastDefaultDate": None,
                    "totalAmountDefaulted": 0
                }
            },
            "profileCompletionPercent": 0,
            "lastPropertyViewed": None,
            "averageResponseTime": None,
            "trustScore": 0,
            "savingGoal": None,
            "savingDurationMonths": None,
            "autoDebitConsent": False,
            "preferredBank": None,
            "razorpayCustomerId": None,
            "homeLoanEligibility": None,
            "preferredDownPaymentSupport": None,
            "stepUpReadinessScore": None
        }
        await db.homebuyer_profiles.insert_one(homebuyer_doc)

    # -------------------- Return success --------------------
    return {
        "userId": str(user_id),
        "role": role,
        "casteCategory": user_doc["casteCategory"],
        "status": "created"
    }


@router.post("/login")
async def login_user(payload: dict):
    db = get_database()

    email = payload.get("email")
    password = payload.get("password")

    try:
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")

        user = await db.users.find_one(
            {"$or": [{"email": email}, {"phone": email}]}
        )

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        pw_hash = user.get("passwordHash")

        if not pw_hash or not pwd_ctx.verify(password, pw_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"lastLogin": datetime.now(timezone.utc)}}
        )

        return {
            "success": True,
            "userId": str(user["_id"]),
            "role": user["role"],
            "fullName": user["fullName"],
            "email": user["email"],
            "phone": user.get("phone", "")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.get("/profile/{user_id}")
async def get_user_profile(user_id: str):
    """
    Get user profile with role-specific data
    """
    db = get_database()
    
    try:
        # Get user document
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Convert ObjectId to string
        user["_id"] = str(user["_id"])
        
        # Get role-specific profile
        if user["role"] == "investor":
            profile = await db.investor_profiles.find_one({"userId": ObjectId(user_id)})
            if profile:
                profile["_id"] = str(profile["_id"])
                profile["userId"] = str(profile["userId"])
        elif user["role"] == "buyer":
            profile = await db.homebuyer_profiles.find_one({"userId": ObjectId(user_id)})
            if profile:
                profile["_id"] = str(profile["_id"])
                profile["userId"] = str(profile["userId"])
        else:
            profile = None
        
        return {
            "user": user,
            "profile": profile
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching profile: {str(e)}")


@router.get("/notifications/{user_id}")
async def get_user_notifications(user_id: str):
    """
    Get user notifications
    """
    db = get_database()
    
    try:
        # Mock notifications for now - replace with actual notification logic later
        notifications = [
            {
                "id": "1",
                "type": "info",
                "title": "Complete Your Profile",
                "message": "Add preferred localities and other details to get better matches",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "read": False,
                "action": "complete-profile"
            },
            {
                "id": "2",
                "type": "success",
                "title": "Set Up Your Profile",
                "message": "Complete your buyer/investor profile for personalized recommendations",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "read": False,
                "action": "setup-profile"
            }
        ]
        
        return {"notifications": notifications}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching notifications: {str(e)}")


@router.post("/notifications/{user_id}/dismiss/{notification_id}")
async def dismiss_notification(user_id: str, notification_id: str):
    """
    Mark a notification as dismissed/read
    """
    try:
        # For now, just return success - in a real app, you'd update the database
        return {"success": True, "message": "Notification dismissed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error dismissing notification: {str(e)}")


@router.put("/profile/{user_id}")
async def update_user_profile(user_id: str, payload: dict):
    """
    Update user profile with additional details
    """
    db = get_database()
    
    try:
        # Get current user data
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prepare update data
        update_data = {}
        
        # Handle password change
        if "currentPassword" in payload and "newPassword" in payload:
            if not pwd_ctx.verify(payload["currentPassword"], user.get("password", "")):
                raise HTTPException(status_code=400, detail="Current password is incorrect")
            update_data["password"] = pwd_ctx.hash(payload["newPassword"])
        
        # Update user fields
        user_fields = ["fullName", "phone", "email", "profession"]
        for field in user_fields:
            if field in payload:
                update_data[field] = payload[field]
        
        # Update user document
        if update_data:
            await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
        
        # Update profile fields
        profile_update = {}
        profile_fields = [
            "preferredLocalities", "monthlyIncome", "budgetRange", "propertyType",
            "annualIncome", "investmentCapital", "riskAppetite", "expectedROI", 
            "maxHoldingPeriodMonths", "diversificationPreference", "investorAccreditationLevel",
            "risk_orientation_score", "collaboration_comfort_score", "control_preference_score",
            "real_estate_conviction_score", "capital_band", "expected_roi_band", 
            "holding_period_band", "ticket_size_stability", "behavioral_consistency_score",
            "capital_coverage_ratio", "city_tier", "deal_success_ratio", "avg_holding_duration",
            "employmentType", "creditScore", "downPaymentCapability", "loanRequired", 
            "preferredTenure", "coApplicant"
        ]
        
        for field in profile_fields:
            if field in payload:
                profile_update[field] = payload[field]
        
        # Update profile document (use correct collection name, not pluralized role)
        if profile_update:
            profile_collection = "investor_profiles" if user["role"] == "investor" else "homebuyer_profiles"
            await db[profile_collection].update_one(
                {"userId": ObjectId(user_id)},
                {"$set": profile_update}
            )

        return {"success": True, "message": "Profile updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating profile: {str(e)}")


@router.post("/request-delete-otp/{user_id}")
async def request_delete_otp(user_id: str):
    """
    Send OTP for account deletion
    """
    try:
        # For now, just return success - in a real app, you'd send an actual OTP
        return {"success": True, "message": "OTP sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending OTP: {str(e)}")


@router.delete("/delete/{user_id}")
async def delete_user_account(user_id: str, payload: dict):
    """
    Delete user account after OTP verification
    """
    db = get_database()
    
    try:
        # For now, accept any OTP - in a real app, you'd verify the actual OTP
        otp = payload.get("otp")
        if not otp:
            raise HTTPException(status_code=400, detail="OTP is required")
        
        # Delete user profile first
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if user:
            await db[f"{user['role']}s"].delete_one({"userId": ObjectId(user_id)})
        
        # Delete user account
        await db.users.delete_one({"_id": ObjectId(user_id)})
        
        return {"success": True, "message": "Account deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting account: {str(e)}")
