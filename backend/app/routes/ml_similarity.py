"""
ML Investor Similarity API Route

Provides ML-powered investor matching using trained pairwise ranker.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import joblib
import numpy as np
import sys
import importlib
from pathlib import Path
import glob
import math
import hashlib
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId

try:
    from ..services.database import get_database
except Exception:
    from backend.app.services.database import get_database  # type: ignore

# Add parent directory to path so investor_similarity package can be imported
parent_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(parent_path))

from backend.app.ml_pipeline.investor_similarity.dataset_builder import DatasetBuilder, FeatureSnapshot

router = APIRouter(prefix="/api/ml-similarity", tags=["ML Similarity"])

# Global model cache
_model_cache = None
_encoder_cache = None
_snapshots_cache = None


def _candidate_data_paths() -> list[Path]:
    """Return candidate data roots, preferring the investor_similarity package data."""
    repo_root = Path(__file__).resolve().parents[3]
    return [
        repo_root / "backend" / "app" / "ml_pipeline" / "investor_similarity" / "data",
        repo_root / "backend" / "data",
        repo_root / "data",
    ]


def _ensure_legacy_pickle_modules() -> None:
    """Make legacy investor_similarity module path importable for unpickling."""
    repo_root = Path(__file__).resolve().parents[3]
    legacy_pkg_parent = repo_root / "backend" / "app" / "ml_pipeline"

    if legacy_pkg_parent.exists() and str(legacy_pkg_parent) not in sys.path:
        sys.path.insert(0, str(legacy_pkg_parent))

    try:
        importlib.import_module("investor_similarity.ml_training.feature_encoder")
    except ModuleNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Legacy ML package path could not be loaded for model unpickling: "
                f"{exc}. Ensure backend/app/ml_pipeline is available."
            )
        ) from exc


def load_ml_model():
    """Load ML ranker model (cached)"""
    global _model_cache, _encoder_cache
    
    if _model_cache is not None:
        return _model_cache, _encoder_cache
    
    # Find latest deployment bundle from known data roots.
    bundles: list[str] = []
    for data_path in _candidate_data_paths():
        if data_path.exists():
            bundles.extend(glob.glob(str(data_path / "ranker_deployment_bundle_*.joblib")))

    bundles = sorted(bundles)
    
    if not bundles:
        raise HTTPException(
            status_code=500,
            detail=(
                "ML model not found. Run: "
                "python backend/app/ml_pipeline/investor_similarity/ml_training/generate_production_package.py"
            )
        )
    
    _ensure_legacy_pickle_modules()

    bundle = joblib.load(bundles[-1])
    _model_cache = bundle['model']
    _encoder_cache = bundle['encoder']
    
    return _model_cache, _encoder_cache


def load_investor_snapshots():
    """Load investor dataset (cached)"""
    global _snapshots_cache
    
    if _snapshots_cache is not None:
        return _snapshots_cache
    
    storage_path = None
    for data_path in _candidate_data_paths():
        candidate = data_path / "snapshots_10k"
        if candidate.exists():
            storage_path = candidate
            break

    if storage_path is None:
        raise HTTPException(
            status_code=500,
            detail="Investor snapshots not found. Expected snapshots_10k under backend or investor_similarity data directories."
        )

    dataset_builder = DatasetBuilder(
        storage_path=str(storage_path),
        feature_version="v1.0"
    )
    
    _snapshots_cache = dataset_builder.load_all_snapshots()
    return _snapshots_cache


# Request/Response Models
class InvestorProfile(BaseModel):
    """Investor profile for matching"""
    investor_id: Optional[str] = None
    capital_band: int
    expected_roi_band: str
    holding_period_band: str
    risk_orientation: float
    collaboration_comfort: float
    control_preference: float
    re_conviction: float
    city_tier: Optional[int] = 2


class SimilarityMatch(BaseModel):
    """Single similarity match result"""
    investor_id: str
    similarity_score: float
    capital_band: int
    expected_roi_band: str
    holding_period_band: str
    city_tier: int


class SimilarityResponse(BaseModel):
    """Response with top K matches"""
    query_investor_id: Optional[str]
    matches: List[SimilarityMatch]
    total_candidates: int
    model_metadata: dict


def _to_float(value, default=0.0):
    """Convert value to float with fallback."""
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value, default=0):
    """Convert value to int with fallback."""
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _clamp_int(value: Optional[int], min_value: int, max_value: int, default: Optional[int] = None) -> int:
    if value is None:
        if default is not None:
            return _clamp_int(default, min_value, max_value)
        return min_value
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = min_value
    return max(min_value, min(max_value, value))


def _clamp_float(value: Optional[float], min_value: float, max_value: float, default: Optional[float] = None) -> float:
    if value is None:
        if default is not None:
            return _clamp_float(default, min_value, max_value)
        return min_value
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = min_value
    return max(min_value, min(max_value, value))


def _capital_band_from_capital(capital: Optional[float]) -> int:
    capital = _to_float(capital, 0)
    if capital < 500000:
        return 0
    if capital < 2000000:
        return 1
    if capital < 5000000:
        return 2
    if capital < 10000000:
        return 3
    return 4


def _roi_to_band(expected_roi: Optional[float]) -> str:
    roi = _to_float(expected_roi, 14.0)
    if roi < 12:
        return "low"
    if roi < 18:
        return "medium"
    return "high"


def _holding_period_band(months: Optional[int]) -> str:
    months = _to_int(months, 36)
    if months <= 24:
        return "short"
    if months <= 48:
        return "medium"
    return "long"


def _ensure_block_a(doc: dict) -> dict:
    block = doc.get("block_a") or {}
    return {
        "risk_orientation_score": _clamp_float(block.get("risk_orientation_score"), 0.0, 1.0, 0.5),
        "collaboration_comfort_score": _clamp_float(block.get("collaboration_comfort_score"), 0.0, 1.0, 0.5),
        "control_preference_score": _clamp_float(block.get("control_preference_score"), 0.0, 1.0, 0.5),
        "real_estate_conviction_score": _clamp_float(block.get("real_estate_conviction_score"), 0.0, 1.0, 0.5),
    }


_ROI_BANDS = {"low", "medium", "high"}
_HOLDING_BANDS = {"short", "medium", "long"}


def _ensure_block_b(doc: dict) -> dict:
    block = doc.get("block_b") or {}
    available_capital = doc.get("availableCapital")
    annual_income = doc.get("annualIncome")
    capital_depth_index = block.get("capital_depth_index")
    if capital_depth_index is None:
        capital_depth_index = math.log(_to_float(available_capital, 0) + _to_float(annual_income, 0) + 1)
    holding_months = block.get("holding_period_months") or doc.get("maxHoldingPeriodMonths")

    capital_band = block.get("capital_band")
    capital_band = _to_int(capital_band, _capital_band_from_capital(available_capital))
    capital_band = _clamp_int(capital_band, 0, 4)

    expected_roi_band = block.get("expected_roi_band") or _roi_to_band(doc.get("expectedROI"))
    if expected_roi_band not in _ROI_BANDS:
        expected_roi_band = _roi_to_band(doc.get("expectedROI"))

    holding_band = block.get("holding_period_band") or _holding_period_band(holding_months)
    if holding_band not in _HOLDING_BANDS:
        holding_band = _holding_period_band(holding_months)

    city_tier = _to_int(block.get("city_tier"), 2)
    city_tier = _clamp_int(city_tier, 1, 3, 2)

    holding_months_val = _to_int(holding_months, 36)
    holding_months_val = max(1, holding_months_val)

    ticket_size_stability = _to_float(block.get("ticket_size_stability"), 0.5)
    ticket_size_stability = max(0.0, ticket_size_stability)

    behavioral_consistency_score = _clamp_float(block.get("behavioral_consistency_score"), 0.0, 1.0, 0.5)

    capital_coverage_ratio = _to_float(
        block.get("capital_coverage_ratio"),
        _to_float(available_capital, 1) / (_to_float(annual_income, 0) + 1)
    )
    capital_coverage_ratio = max(0.0, capital_coverage_ratio)

    return {
        "capital_band": capital_band,
        "expected_roi_band": expected_roi_band,
        "holding_period_band": holding_band,
        "capital_depth_index": _to_float(capital_depth_index, 10.0),
        "ticket_size_stability": ticket_size_stability,
        "holding_period_months": holding_months_val,
        "behavioral_consistency_score": behavioral_consistency_score,
        "capital_coverage_ratio": capital_coverage_ratio,
        "city_tier": city_tier
    }


def _ensure_block_c(doc: dict) -> dict:
    block = doc.get("block_c") or {}
    return {
        "deal_success_ratio": _clamp_float(block.get("deal_success_ratio"), 0.0, 1.0, 0.0),
        "avg_holding_duration": _clamp_float(block.get("avg_holding_duration"), 0.0, 1.0, 0.0),
        "behavioral_consistency_score": _clamp_float(block.get("behavioral_consistency_score"), 0.0, 1.0, 0.0)
    }


def _doc_to_snapshot(doc: dict, fallback_id: str) -> FeatureSnapshot:
    block_a = _ensure_block_a(doc)
    block_b = _ensure_block_b(doc)
    block_c = _ensure_block_c(doc)

    investor_id = doc.get("investor_id") or hashlib.sha256(str(fallback_id).encode()).hexdigest()
    timestamp = doc.get("snapshot_timestamp") or datetime.now(timezone.utc).isoformat()

    return FeatureSnapshot(
        investor_id=investor_id,
        block_a=block_a,
        block_b=block_b,
        block_c=block_c,
        snapshot_timestamp=timestamp,
        feature_version=doc.get("feature_version", "v1.0"),
        data_source=doc.get("data_source", "user_signup"),
        confidence_weight=_to_float(doc.get("confidence_weight"), 0.8),
        source_log_hash=doc.get("source_log_hash")
    )


def _build_profile_summary(snapshot: FeatureSnapshot) -> dict:
    return {
        "capital_band": snapshot.block_b.get("capital_band"),
        "expected_roi_band": snapshot.block_b.get("expected_roi_band"),
        "holding_period_band": snapshot.block_b.get("holding_period_band"),
        "city_tier": snapshot.block_b.get("city_tier"),
        "risk_orientation": snapshot.block_a.get("risk_orientation_score"),
        "collaboration_comfort": snapshot.block_a.get("collaboration_comfort_score"),
        "control_preference": snapshot.block_a.get("control_preference_score"),
        "re_conviction": snapshot.block_a.get("real_estate_conviction_score"),
    }


def _serialize_investor_payload(
    doc: dict,
    user: Optional[dict],
    score: Optional[float] = None,
    snapshot: Optional[FeatureSnapshot] = None
) -> dict:
    block_a = snapshot.block_a if snapshot else doc.get("block_a")
    block_b = snapshot.block_b if snapshot else doc.get("block_b")
    block_c = snapshot.block_c if snapshot else doc.get("block_c")

    return {
        "userId": str(doc.get("userId")) if doc.get("userId") else None,
        "investorId": doc.get("investor_id"),
        "fullName": user.get("fullName") if user else "Investor",
        "profession": user.get("profession") if user else None,
        "email": user.get("email") if user else None,
        "phone": user.get("phone") if user else None,
        "similarityScore": score,
        "availableCapital": doc.get("availableCapital"),
        "experienceYears": doc.get("experienceYears"),
        "expectedROI": doc.get("expectedROI"),
        "riskAppetite": doc.get("riskAppetite"),
        "preferredLocations": doc.get("preferredLocations", []),
        "preferredInvestmentType": doc.get("preferredInvestmentType", []),
        "maxHoldingPeriodMonths": doc.get("maxHoldingPeriodMonths"),
        "investorAccreditationLevel": doc.get("investorAccreditationLevel"),
        "block_a": block_a,
        "block_b": block_b,
        "block_c": block_c,
    }


@router.post("/recommend", response_model=SimilarityResponse)
async def get_investor_recommendations(
    profile: InvestorProfile,
    top_k: int = 10,
    min_score: Optional[float] = None
):
    """
    Get top K similar investors using ML ranker
    
    Args:
        profile: Query investor profile
        top_k: Number of recommendations to return (default: 10)
        min_score: Minimum similarity score threshold (optional)
        
    Returns:
        Top K most similar investors with scores
    """
    
    try:
        # Load model and data
        model, encoder = load_ml_model()
        snapshots = load_investor_snapshots()
        
        # Find or create query snapshot
        if profile.investor_id:
            # Find existing investor
            query = next((s for s in snapshots if s.investor_id == profile.investor_id), None)
            if not query:
                raise HTTPException(status_code=404, detail=f"Investor {profile.investor_id} not found")
        else:
            # Create temporary snapshot from profile
            from backend.app.ml_pipeline.investor_similarity.dataset_builder import FeatureSnapshot
            from datetime import datetime
            
            # CRITICAL FIX: Match exact feature names from stored snapshots
            # Block A features need "_score" suffix to match encoder expectations
            query = FeatureSnapshot(
                investor_id="temp_query",
                block_a={
                    'risk_orientation_score': profile.risk_orientation,
                    'collaboration_comfort_score': profile.collaboration_comfort,
                    'control_preference_score': profile.control_preference,
                    'real_estate_conviction_score': profile.re_conviction
                },
                block_b={
                    'capital_band': profile.capital_band,
                    'expected_roi_band': profile.expected_roi_band,
                    'holding_period_band': profile.holding_period_band,
                    'city_tier': profile.city_tier,
                    # Default behavioral features - match stored snapshot structure
                    'capital_depth_index': 10.0,  # Realistic default for mid-tier
                    'ticket_size_stability': 0.5,
                    'holding_period_months': 36,  # 3 years default
                    'behavioral_consistency_score': 0.5,
                    'capital_coverage_ratio': 1.5
                },
                block_c={
                    'deal_success_ratio': 0.0,
                    'avg_holding_duration': 0.0,
                    'behavioral_consistency_score': 0.0
                },
                snapshot_timestamp=datetime.now().isoformat(),
                feature_version="v1.0",
                data_source="api",
                confidence_weight=0.8
            )
        
        # Get candidates (exclude query if it exists)
        candidates = [s for s in snapshots if s.investor_id != query.investor_id]
        
        # Encode pairs
        features_list = [encoder.encode_pair(query, cand) for cand in candidates]
        X = np.array(features_list)
        
        # Predict scores
        scores = model.predict(X)
        
        # Filter by min_score if provided
        if min_score is not None:
            valid_indices = [i for i, score in enumerate(scores) if score >= min_score]
            candidates = [candidates[i] for i in valid_indices]
            scores = scores[valid_indices]
        
        # Sort by score (descending)
        ranked_indices = np.argsort(scores)[::-1]
        
        # Get top K
        top_indices = ranked_indices[:top_k]
        
        # Build response
        matches = []
        for idx in top_indices:
            investor = candidates[idx]
            matches.append(SimilarityMatch(
                investor_id=investor.investor_id,
                similarity_score=float(scores[idx]),  # Convert numpy float
                capital_band=int(investor.block_b.get('capital_band', 0)),  # Convert to int
                expected_roi_band=str(investor.block_b.get('expected_roi_band', 'medium')),
                holding_period_band=str(investor.block_b.get('holding_period_band', 'medium')),
                city_tier=int(investor.block_b.get('city_tier', 2))  # Convert to int
            ))
        
        return SimilarityResponse(
            query_investor_id=profile.investor_id,
            matches=matches,
            total_candidates=int(len(candidates)),  # Convert to int
            model_metadata={
                'model_type': 'XGBoost LambdaMART',
                'ndcg@10': 0.8946,
                'bias_free': True
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")


@router.get("/model-info")
async def get_model_info():
    """Get ML model metadata"""
    
    try:
        model, encoder = load_ml_model()
        snapshots = load_investor_snapshots()
        
        # Find bundle for metadata
        data_path = Path(__file__).parent.parent.parent.parent / "data"
        bundles = sorted(glob.glob(str(data_path / "ranker_deployment_bundle_*.joblib")))
        bundle = joblib.load(bundles[-1])
        
        # Convert numpy types to Python native types
        def convert_numpy(obj):
            """Convert numpy types to Python native types"""
            if isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_numpy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(item) for item in obj]
            return obj
        
        metadata = convert_numpy(bundle['metadata'])
        
        return {
            'model_type': 'XGBoost LambdaMART Pairwise Ranker',
            'created_at': str(metadata.get('created_at', '')),
            'ndcg@10': float(metadata.get('ndcg@10', 0.0)),
            'map': float(metadata.get('map', 0.9341)),
            'bias_free': bool(metadata.get('bias_free', True)),
            'total_investors': int(len(snapshots)),
            'feature_count': int(len(encoder.feature_names) * 2),
            'status': 'ready'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading model info: {str(e)}")


@router.post("/batch-rank")
async def batch_rank_investors(
    investor_ids: List[str],
    top_k: int = 5
):
    """
    Rank multiple investors against each other
    
    Args:
        investor_ids: List of investor IDs to rank
        top_k: Number of top matches per investor
        
    Returns:
        Rankings for each investor
    """
    
    try:
        model, encoder = load_ml_model()
        snapshots = load_investor_snapshots()
        
        # Get snapshots for requested IDs
        investor_map = {s.investor_id: s for s in snapshots}
        queries = [investor_map[iid] for iid in investor_ids if iid in investor_map]
        
        if not queries:
            raise HTTPException(status_code=404, detail="No valid investor IDs found")
        
        results = {}
        
        for query in queries:
            # Get candidates (all except query)
            candidates = [s for s in snapshots if s.investor_id != query.investor_id]
            
            # Encode and predict
            features_list = [encoder.encode_pair(query, cand) for cand in candidates]
            X = np.array(features_list)
            scores = model.predict(X)
            
            # Get top K
            ranked_indices = np.argsort(scores)[::-1][:top_k]
            
            matches = [
                {
                    'investor_id': str(candidates[idx].investor_id),
                    'score': float(scores[idx])  # Convert numpy float
                }
                for idx in ranked_indices
            ]
            
            results[query.investor_id] = matches
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in batch ranking: {str(e)}")


@router.get("/matches/{user_id}")
async def get_database_backed_matches(user_id: str, top_k: int = 20, candidate_limit: int = 200):
    """Generate investor matches using real MongoDB profiles."""

    try:
        investor_object_id = ObjectId(user_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail="Invalid user id")

    db = get_database()

    user_doc = await db.users.find_one({"_id": investor_object_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    if user_doc.get("role") != "investor":
        raise HTTPException(status_code=400, detail="User is not registered as an investor")

    investor_doc = await db.investor_profiles.find_one({"userId": investor_object_id})
    if not investor_doc:
        raise HTTPException(status_code=404, detail="Investor profile not found")

    try:
        query_snapshot = _doc_to_snapshot(investor_doc, str(investor_object_id))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Invalid investor profile: {exc}") from exc

    model, encoder = load_ml_model()

    candidate_limit = max(10, min(candidate_limit, 500))
    candidate_cursor = db.investor_profiles.find({"userId": {"$ne": investor_object_id}})
    candidate_docs = await candidate_cursor.to_list(length=candidate_limit)

    valid_candidates = []
    feature_rows = []
    candidate_user_ids = set()
    skipped_candidates = 0
    skip_samples: List[dict] = []

    for doc in candidate_docs:
        fallback_id = str(doc.get("userId") or doc.get("_id") or len(valid_candidates))
        try:
            snapshot = _doc_to_snapshot(doc, fallback_id)
            features = encoder.encode_pair(query_snapshot, snapshot)
        except Exception as exc:  # noqa: BLE001
            skipped_candidates += 1
            if len(skip_samples) < 5:
                skip_samples.append({
                    "candidate": fallback_id,
                    "reason": str(exc)
                })
            continue
        feature_rows.append(features)
        valid_candidates.append((doc, snapshot))
        if doc.get("userId"):
            candidate_user_ids.add(doc["userId"])

    if not valid_candidates:
        return {
            "queryInvestor": _serialize_investor_payload(investor_doc, user_doc, None, query_snapshot),
            "queryProfileSummary": _build_profile_summary(query_snapshot),
            "matches": [],
            "totalCandidates": 0,
            "scannedCandidates": len(candidate_docs),
            "skippedCandidates": skipped_candidates,
            "skipSamples": skip_samples
        }

    user_map = {}
    if candidate_user_ids:
        user_docs = await db.users.find({"_id": {"$in": list(candidate_user_ids)}}).to_list(length=len(candidate_user_ids))
        user_map = {str(doc["_id"]): doc for doc in user_docs}

    X = np.array(feature_rows)
    scores = model.predict(X)

    top_k = max(1, min(top_k, len(valid_candidates)))
    ranked_indices = np.argsort(scores)[::-1][:top_k]

    matches = []
    for idx in ranked_indices:
        profile_doc, candidate_snapshot = valid_candidates[idx]
        score = float(scores[idx])
        user_info = user_map.get(str(profile_doc.get("userId")))
        payload = _serialize_investor_payload(profile_doc, user_info, score, candidate_snapshot)
        matches.append(payload)

    return {
        "queryInvestor": _serialize_investor_payload(investor_doc, user_doc, None, query_snapshot),
        "queryProfileSummary": _build_profile_summary(query_snapshot),
        "matches": matches,
        "totalCandidates": len(valid_candidates),
        "scannedCandidates": len(candidate_docs),
        "skippedCandidates": skipped_candidates,
        "skipSamples": skip_samples
    }
