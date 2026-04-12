"""
Scale Real Survey Data to 10k Investors

Processes 54 real survey responses from CSV and generates 9,946 synthetic
investors using copula calibrated on real data distributions.

Usage:
    python investor_similarity/examples/scale_to_10k.py path/to/survey.csv
"""

import sys
from pathlib import Path
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.ml_pipeline.investor_similarity.csv_processor import CSVSurveyProcessor
from backend.app.ml_pipeline.investor_similarity.survey_mapper import SurveyMapper
from backend.app.ml_pipeline.investor_similarity.platform_mapper import PlatformInvestorProfile, PlatformMapper
from backend.app.ml_pipeline.investor_similarity.dataset_builder import DatasetBuilder
from backend.app.ml_pipeline.investor_similarity.synthetic_data_generator import (
    SyntheticDataGenerator,
    SyntheticDataConfig,
    CopulaGenerator
)


def generate_platform_profiles_from_demographics(num_profiles: int) -> list:
    """
    Generate platform profiles with realistic distributions
    
    NOTE: We do NOT use demographic data from CSV for this.
    Instead, we use market priors and distributions.
    """
    np.random.seed(42)
    profiles = []
    
    # Capital distribution (from market research, not demographics!)
    capital_probs = [0.25, 0.30, 0.25, 0.15, 0.05]  # More realistic for India
    capital_bands_inr = [
        (100_000, 500_000),      # 1L - 5L
        (500_000, 2_000_000),    # 5L - 20L
        (2_000_000, 5_000_000),  # 20L - 50L
        (5_000_000, 10_000_000), # 50L - 1Cr
        (10_000_000, 50_000_000) # 1Cr - 5Cr
    ]
    
    for i in range(num_profiles):
        # Sample capital band
        band_idx = np.random.choice(len(capital_probs), p=capital_probs)
        lower, upper = capital_bands_inr[band_idx]
        capital = np.random.uniform(lower, upper)
        
        # ROI expectations correlate with capital (higher capital → lower ROI)
        if band_idx <= 1:
            roi = np.random.uniform(12, 20)  # 12-20% for low capital
        elif band_idx <= 3:
            roi = np.random.uniform(9, 15)   # 9-15% for medium
        else:
            roi = np.random.uniform(7, 12)   # 7-12% for high capital
        
        # Holding period correlates with capital
        if band_idx <= 1:
            holding = np.random.randint(6, 18)  # 6-18 months
        elif band_idx <= 3:
            holding = np.random.randint(12, 36)  # 1-3 years
        else:
            holding = np.random.randint(24, 60)  # 2-5 years
        
        profile = PlatformInvestorProfile(
            available_capital=capital,
            target_roi_annual=roi,
            preferred_holding_months=holding,
            profile_verified=np.random.random() > 0.2,  # 80% verified
            kyc_completed=np.random.random() > 0.1      # 90% KYC
        )
        
        profiles.append((f"investor_{i+1:05d}", profile))
    
    return profiles


def main():
    if len(sys.argv) < 2:
        print("Usage: python scale_to_10k.py <path_to_survey_csv>")
        print("\nExample:")
        print("  python investor_similarity/examples/scale_to_10k.py data/raw/legacy/survey_responses.csv")
        sys.exit(1)
    
    csv_filepath = sys.argv[1]
    
    print("=" * 70)
    print("Scaling Real Survey Data to 10,000 Investors")
    print("=" * 70)
    
    # Phase 1: Process real survey data
    print("\n[1/6] Processing real survey CSV data...")
    print(f"  Reading from: {csv_filepath}")
    
    csv_processor = CSVSurveyProcessor()
    survey_mapper = SurveyMapper()
    platform_mapper = PlatformMapper()
    
    real_surveys = csv_processor.process_csv(csv_filepath)
    print(f"  ✓ Processed {len(real_surveys)} real survey responses")
    
    # Phase 2: Extract feature distributions from real data
    print("\n[2/6] Extracting feature distributions from real data...")
    
    distributions = csv_processor.extract_feature_distributions(
        real_surveys,
        survey_mapper
    )
    
    print(f"  ✓ Extracted distributions from {distributions['num_samples']} responses")
    print(f"  Block A means: {[f'{m:.3f}' for m in distributions['means']]}")
    print(f"  Block A stds:  {[f'{s:.3f}' for s in distributions['stds']]}")
    
    # Phase 3: Create real investor snapshots
    print("\n[3/6] Creating feature snapshots from real data...")
    
    dataset_builder = DatasetBuilder(
        storage_path="./data/snapshots_10k",
        feature_version="v1.0"
    )
    
    real_snapshots = []
    
    # Generate platform profiles for real investors
    real_platform_profiles = generate_platform_profiles_from_demographics(len(real_surveys))
    
    for (investor_id, survey, economic_context), (_, profile) in zip(real_surveys, real_platform_profiles):
        # Extract Block A from survey
        block_a = survey_mapper.map_to_block_a(survey)
        
        # Extract Block B from platform + economic context (city_tier only, NO AGE!)
        block_b = platform_mapper.map_to_block_b(
            profile,
            city_tier=economic_context["city_tier"]
        )
        confidence = platform_mapper.adjust_for_verification(block_b, profile)
        
        # Block C empty (no behavioral data yet)
        block_c = {
            "deal_success_ratio": 0.0,
            "avg_holding_duration": 0.0,
            "behavioral_consistency_score": 0.0
        }
        
        snapshot = dataset_builder.create_snapshot(
            investor_id_raw=investor_id,
            block_a=block_a,
            block_b=block_b,
            block_c=block_c,
            data_source="platform",
            confidence_weight=confidence
        )
        
        real_snapshots.append(snapshot)
    
    print(f"  ✓ Created {len(real_snapshots)} real investor snapshots")
    
    # Phase 4: Generate synthetic data calibrated on real data
    print("\n[4/6] Generating synthetic data calibrated on real distributions...")
    
    num_synthetic = 10_000 - len(real_snapshots)
    print(f"  Target: {num_synthetic} synthetic investors")
    
    # Create calibrated copula generator
    correlation_matrix = np.array(distributions['correlation_matrix'])
    
    copula_gen = CopulaGenerator(random_seed=42)
    synthetic_block_a = copula_gen.generate_block_a(
        num_samples=num_synthetic,
        correlation_matrix=correlation_matrix
    )
    
    print(f"  ✓ Generated {num_synthetic} synthetic Block A features")
    
    # Generate Block B for synthetic investors
    print("  Generating synthetic Block B features...")
    from backend.app.ml_pipeline.investor_similarity.synthetic_data_generator import BayesianNetworkGenerator
    
    bayesian_gen = BayesianNetworkGenerator(random_seed=42)
    synthetic_block_b = bayesian_gen.generate_block_b(num_synthetic)
    
    # Create synthetic snapshots
    synthetic_snapshots = []
    block_c_empty = {
        "deal_success_ratio": 0.0,
        "avg_holding_duration": 0.0,
        "behavioral_consistency_score": 0.0
    }
    
    for i in range(num_synthetic):
        snapshot = dataset_builder.create_snapshot(
            investor_id_raw=f"synthetic_{i+1:06d}",
            block_a=synthetic_block_a[i],
            block_b=synthetic_block_b[i],
            block_c=block_c_empty,
            data_source="synthetic",
            confidence_weight=0.3
        )
        synthetic_snapshots.append(snapshot)
    
    print(f"  ✓ Created {len(synthetic_snapshots)} synthetic snapshots")
    
    # Phase 5: Combine and save
    print("\n[5/6] Combining real + synthetic data...")
    
    all_snapshots = real_snapshots + synthetic_snapshots
    print(f"  Total investors: {len(all_snapshots)}")
    print(f"    - Real: {len(real_snapshots)} ({len(real_snapshots)/len(all_snapshots)*100:.1f}%)")
    print(f"    - Synthetic: {len(synthetic_snapshots)} ({len(synthetic_snapshots)/len(all_snapshots)*100:.1f}%)")
    
    # Save snapshots
    print("\n  Saving snapshots to disk...")
    saved_paths = dataset_builder.save_batch(all_snapshots)
    print(f"  ✓ Saved {len(saved_paths)} snapshots")
    
    # Export consolidated dataset
    dataset_builder.export_dataset("./data/investor_dataset_10k_v1.0.jsonl")
    
    # Phase 6: Statistics and validation
    print("\n[6/6] Dataset Statistics")
    print("=" * 70)
    
    stats = dataset_builder.get_statistics()
    print(f"Total snapshots: {stats['total_snapshots']}")
    print(f"Unique investors: {stats['unique_investors']}")
    print(f"Source distribution: {stats['source_distribution']}")
    print(f"Avg confidence weight: {stats['avg_confidence_weight']:.3f}")
    print(f"Feature version: {stats['feature_version']}")
    
    # Verify distributions preserved
    print("\n📊 Feature Distribution Comparison:")
    print("(Real vs Synthetic - should be similar)")
    
    real_features = []
    synthetic_features = []
    
    for snapshot in all_snapshots:
        features = [
            snapshot.block_a["risk_orientation_score"],
            snapshot.block_a["collaboration_comfort_score"],
            snapshot.block_a["control_preference_score"],
            snapshot.block_a["real_estate_conviction_score"]
        ]
        
        if snapshot.data_source == "platform":
            real_features.append(features)
        else:
            synthetic_features.append(features)
    
    real_features = np.array(real_features)
    synthetic_features = np.array(synthetic_features)
    
    feature_names = ["Risk", "Collab", "Control", "RE Conv"]
    
    print("\nFeature Means:")
    print(f"{'Feature':<10} {'Real':<10} {'Synthetic':<10} {'Diff':<10}")
    print("-" * 45)
    for i, name in enumerate(feature_names):
        real_mean = real_features[:, i].mean()
        synth_mean = synthetic_features[:, i].mean()
        diff = abs(real_mean - synth_mean)
        print(f"{name:<10} {real_mean:.3f}      {synth_mean:.3f}       {diff:.3f}")
    
    print("\n✅ Dataset scaling complete!")
    print(f"📁 Dataset location: ./data/investor_dataset_10k_v1.0.jsonl")
    print(f"📁 Snapshots location: ./data/snapshots_10k/")
    
    print("\n💡 Next steps:")
    print("  1. Run bias audit: python investor_similarity/examples/run_bias_audit.py")
    print("  2. Compute similarity: python investor_similarity/examples/compute_similarity.py")
    print("  3. Deploy to production!")


if __name__ == "__main__":
    main()
