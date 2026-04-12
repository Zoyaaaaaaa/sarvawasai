"""
Example: Using MongoDB Feature Mapper

Demonstrates how to extract features from MongoDB InvestorProfile
and create feature snapshots for similarity matching.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.ml_pipeline.investor_similarity.mongo_feature_mapper import MongoFeatureMapper, InvestorProfileMongo
from backend.app.ml_pipeline.investor_similarity.survey_mapper import SurveyMapper, SurveyResponse
from backend.app.ml_pipeline.investor_similarity.dataset_builder import DatasetBuilder


def example_mongodb_integration():
    """
    Example showing how to create feature snapshots from MongoDB data
    """
    
    print("=" * 70)
    print("MongoDB Feature Extraction Example")
    print("=" * 70)
    
    # Simulate MongoDB investor profile
    print("\n[1/3] Creating sample investor profile from MongoDB...")
    
    investor_profile = InvestorProfileMongo(
        available_capital=10_000_000,  # 1 Crore
        annual_income=2_000_000,        # 20 Lakhs
        min_investment_per_deal=500_000,
        max_investment_per_deal=5_000_000,
        max_holding_period_months=48,   # 4 years
        co_investments=[
            {
                "propertyId": "prop_001",
                "investedAmount": 3_000_000,
                "status": "active",
                "equityShare": 0.3
            },
            {
                "propertyId": "prop_002",
                "investedAmount": 5_000_000,
                "status": "closed",
                "equityShare": 0.5
            },
            {
                "propertyId": "prop_003",
                "investedAmount": 2_500_000,
                "status": "active",
                "equityShare": 0.25
            }
        ],
        risk_appetite="medium",
        expected_roi=12.5,
        preferred_locations=["Mumbai", "Pune"],
        city="Mumbai"
    )
    
    print(f"  Profile: {investor_profile.available_capital:,.0f} INR capital")
    print(f"  {len(investor_profile.co_investments)} past co-investments")
    
    # Extract Block B features
    print("\n[2/3] Extracting behavioral features...")
    
    mapper = MongoFeatureMapper()
    block_b = mapper.extract_block_b(investor_profile)
    
    print("\n  Block B Features (Economic + Behavioral):")
    print(f"    Capital Band: {block_b['capital_band']}")
    print(f"    ROI Band: {block_b['expected_roi_band']}")
    print(f"    Holding Period Band: {block_b['holding_period_band']}")
    print(f"    \n    NEW BEHAVIORAL FEATURES:")
    print(f"    Capital Depth Index: {block_b['capital_depth_index']:.2f}")
    print(f"    Ticket Size Stability: {block_b['ticket_size_stability']:,.0f} INR")
    print(f"    Holding Period Months: {block_b['holding_period_months']}")
    print(f"    Behavioral Consistency: {block_b['behavioral_consistency_score']:.2f}")
    print(f"    Capital Coverage Ratio: {block_b['capital_coverage_ratio']:.2f}")
    print(f"    City Tier: {block_b['city_tier']}")
    
    # Create full snapshot
    print("\n[3/3] Creating feature snapshot...")
    
    # For Block A, you'd get this from survey data
    # Here we use example values
    block_a = {
        "risk_orientation_score": 0.65,
        "collaboration_comfort_score": 0.75,
        "control_preference_score": 0.55,
        "real_estate_conviction_score": 0.85
    }
    
    block_c = {
        "deal_success_ratio": 0.0,  # Not enough data yet
        "avg_holding_duration": 0.0,
        "behavioral_consistency_score": 0.0
    }
    
    dataset_builder = DatasetBuilder(
        storage_path="./data/snapshots_mongodb_example",
        feature_version="v1.0"
    )
    
    snapshot = dataset_builder.create_snapshot(
        investor_id_raw="investor_mongo_001",
        block_a=block_a,
        block_b=block_b,
        block_c=block_c,
        data_source="platform",
        confidence_weight=1.0
    )
    
    print(f"\n  ✓ Created snapshot for investor: {snapshot.investor_id[:16]}...")
    print(f"  Data source: {snapshot.data_source}")
    print(f"  Confidence: {snapshot.confidence_weight}")
    
    # Save snapshot
    snapshot_path = dataset_builder.save_snapshot(snapshot)
    print(f"  ✓ Saved to: {snapshot_path}")
    
    print("\n" + "=" * 70)
    print("✅ MongoDB Integration Complete!")
    print("=" * 70)
    
    print("\nKey Points:")
    print("  • Capital Depth Index replaces age (16.30 = mature investor)")
    print("  • Ticket Size Stability shows consistent 3.5M investments")
    print("  • Behavioral Consistency = 1.0 (all deals active/closed, no defaults)")
    print("  • Capital Coverage Ratio = 2.86 (can cover 2.86x average deal)")
    print("  • City Tier = 1 (Mumbai is metro)")
    print("\n  → All features derived from BEHAVIOR, not demographics!")


if __name__ == "__main__":
    example_mongodb_integration()
