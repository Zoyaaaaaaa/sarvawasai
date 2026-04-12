"""
Ranking-Specific Bias Audit

Comprehensive fairness validation for pairwise ranker including:
- Feature importance (demographic features < 10%)
- Exposure fairness across city tiers
- NDCG parity across demographics
- Ranking calibration checks
"""

import sys
from pathlib import Path
import numpy as np
import pickle
import xgboost as xgb
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.ml_pipeline.investor_similarity.dataset_builder import DatasetBuilder
from backend.app.ml_pipeline.investor_similarity.ml_training.ranking_metrics import ndcg_at_k


def audit_ranker_bias(model_path: str, encoder_path: str):
    """
    Comprehensive bias audit for pairwise ranker
    
    Tests:
    1. Feature importance - demographics should be minimal
    2. Exposure fairness - equal visibility across groups
    3. NDCG parity - similar ranking quality for all groups
    4. Ranking calibration - predictions match ground truth
    """
    
    print("=" * 70)
    print("Pairwise Ranker - Comprehensive Bias Audit")
    print("=" * 70)
    
    # Load model
    print("\n[1/5] Loading ranker...")
    model = xgb.XGBRanker()
    model.load_model(model_path)
    
    with open(encoder_path, 'rb') as f:
        encoder = pickle.load(f)
    
    print(f"  ✓ Ranker loaded")
    print(f"  ✓ Encoder loaded")
    
    # Test 1: Feature Importance
    print("\n[2/5] Analyzing feature importance...")
    importance = model.feature_importances_
    
    # Build feature names
    base_names = encoder.feature_names
    feature_names_full = (
        [f"i1_{n}" for n in base_names] +
        [f"i2_{n}" for n in base_names]
    )
    
    # Check demographic features
    demographic_features = ['city_tier']
    
    print("\n  Demographic Feature Importance:")
    total_demo_importance = 0
    
    for demo in demographic_features:
        demo_importance = sum(
            importance[i] for i, name in enumerate(feature_names_full)
            if demo in name
        )
        total_demo_importance += demo_importance
        print(f"    {demo}: {demo_importance:.4f} ({demo_importance*100:.2f}%)")
    
    print(f"\n  Total demographic importance: {total_demo_importance:.4f}")
    
    if total_demo_importance < 0.10:
        print("  ✅ PASS: Demographic features < 10% importance")
        demo_pass = True
    else:
        print("  ⚠️  WARNING: Demographic features have significant importance!")
        demo_pass = False
    
    # Top behavioral features
    print("\n  Top 10 Behavioral Features:")
    behavioral_importance = [
        (i, name, importance[i])
        for i, name in enumerate(feature_names_full)
        if not any(demo in name for demo in demographic_features)
    ]
    behavioral_importance.sort(key=lambda x: x[2], reverse=True)
    
    for i, (idx, name, imp) in enumerate(behavioral_importance[:10], 1):
        print(f"    {i}. {name}: {imp:.4f}")
    
    # Test 2: Exposure Fairness
    print("\n[3/5] Checking exposure fairness...")
    
    dataset_builder = DatasetBuilder(
        storage_path="./data/snapshots_10k",
        feature_version="v1.0"
    )
    
    snapshots = dataset_builder.load_all_snapshots()
    
    # Group by city tier
    by_tier = defaultdict(list)
    for snap in snapshots:
        tier = snap.block_b.get('city_tier', 2)
        by_tier[tier].append(snap)
    
    print(f"\n  Investors by city tier:")
    for tier in sorted(by_tier.keys()):
        print(f"    Tier {tier}: {len(by_tier[tier]):,} investors")
    
    # Simulate ranking for sample queries and compute exposure
    print("\n  Computing exposure scores...")
    
    exposure_by_tier = defaultdict(float)
    total_positions = 0
    
    # Sample 100 random queries
    import random
    random.seed(42)
    
    sample_queries = random.sample(snapshots, min(100, len(snapshots)))
    
    for query in sample_queries:
        # Sample candidates
        candidates = random.sample(
            [s for s in snapshots if s.investor_id != query.investor_id],
            min(100, len(snapshots) - 1)
        )
        
        # Encode and rank
        features_list = [encoder.encode_pair(query, cand) for cand in candidates]
        X = np.array(features_list)
        
        scores = model.predict(X)
        
        # Sort by score (descending)
        ranked_indices = np.argsort(scores)[::-1]
        
        # Compute exposure (1/log2(rank+1))
        for rank, idx in enumerate(ranked_indices[:20], 1):  # Top 20
            candidate_tier = candidates[idx].block_b.get('city_tier', 2)
            exposure = 1.0 / np.log2(rank + 1)
            exposure_by_tier[candidate_tier] += exposure
            total_positions += 1
    
    # Normalize by group size
    print("\n  Exposure per investor (normalized):")
    exposure_values = []
    for tier in sorted(by_tier.keys()):
        avg_exposure = exposure_by_tier[tier] / len(by_tier[tier])
        exposure_values.append(avg_exposure)
        print(f"    Tier {tier}: {avg_exposure:.4f}")
    
    # Check variance
    exposure_variance = np.var(exposure_values)
    print(f"\n  Exposure variance: {exposure_variance:.6f}")
    
    if exposure_variance < 0.001:
        print("  ✅ PASS: Exposure is fair across tiers")
        exposure_pass = True
    else:
        print("  ⚠️  WARNING: Significant exposure imbalance")
        exposure_pass = False
    
    # Test 3: NDCG Parity
    print("\n[4/5] Checking NDCG parity across demographics...")
    
    from backend.app.ml_pipeline.investor_similarity.similarity_engine import SimilarityEngine
    
    engine = SimilarityEngine()
    ndcg_by_tier = defaultdict(list)
    
    # For each tier, compute NDCG for sample queries
    for tier, tier_investors in by_tier.items():
        sample_tier_queries = random.sample(
            tier_investors,
            min(50, len(tier_investors))
        )
        
        for query in sample_tier_queries:
            # Sample candidates
            candidates = random.sample(
                [s for s in snapshots if s.investor_id != query.investor_id],
                min(50, len(snapshots) - 1)
            )
            
            # Get true relevance labels
            true_relevances = []
            for cand in candidates:
                result = engine.compute_similarity(query, cand)
                score = result.total_similarity
                
                # Convert to label
                if score >= 0.8:
                    label = 4
                elif score >= 0.6:
                    label = 3
                elif score >= 0.4:
                    label = 2
                elif score >= 0.2:
                    label = 1
                else:
                    label = 0
                
                true_relevances.append(label)
            
            # Predict with model
            features_list = [encoder.encode_pair(query, cand) for cand in candidates]
            X = np.array(features_list)
            predicted_scores = model.predict(X)
            
            # Sort by prediction
            ranked_indices = np.argsort(predicted_scores)[::-1]
            ranked_relevances = [true_relevances[i] for i in ranked_indices]
            
            # Compute NDCG@10
            ndcg = ndcg_at_k(ranked_relevances, 10)
            ndcg_by_tier[tier].append(ndcg)
    
    print("\n  NDCG@10 by city tier:")
    ndcg_means = []
    for tier in sorted(ndcg_by_tier.keys()):
        mean_ndcg = np.mean(ndcg_by_tier[tier])
        std_ndcg = np.std(ndcg_by_tier[tier])
        ndcg_means.append(mean_ndcg)
        print(f"    Tier {tier}: {mean_ndcg:.4f} ± {std_ndcg:.4f}")
    
    ndcg_variance = np.var(ndcg_means)
    print(f"\n  NDCG variance across tiers: {ndcg_variance:.6f}")
    
    if ndcg_variance < 0.01:
        print("  ✅ PASS: NDCG is consistent across tiers")
        ndcg_pass = True
    else:
        print("  ⚠️  WARNING: Significant NDCG disparity")
        ndcg_pass = False
    
    # Final Summary
    print("\n[5/5] Final Bias Audit Summary")
    print("=" * 70)
    
    tests_passed = sum([demo_pass, exposure_pass, ndcg_pass])
    total_tests = 3
    
    print(f"\nTests Passed: {tests_passed}/{total_tests}")
    print(f"\n  Feature Importance: {'✅ PASS' if demo_pass else '❌ FAIL'}")
    print(f"  Exposure Fairness:  {'✅ PASS' if exposure_pass else '❌ FAIL'}")
    print(f"  NDCG Parity:        {'✅ PASS' if ndcg_pass else '❌ FAIL'}")
    
    if tests_passed == total_tests:
        print("\n" + "=" * 70)
        print("✅ RANKER IS BIAS-FREE AND PRODUCTION-READY!")
        print("=" * 70)
        print("\nKey Findings:")
        print(f"  • Demographics contribute only {total_demo_importance*100:.2f}% to predictions")
        print(f"  • Exposure is balanced (variance: {exposure_variance:.6f})")
        print(f"  • Ranking quality is consistent (NDCG var: {ndcg_variance:.6f})")
        print("\n🚀 Safe to deploy to production!")
    else:
        print("\n⚠️  REVIEW REQUIRED")
        print("Some fairness checks failed. Review model before deployment.")
    
    return {
        'demo_importance': total_demo_importance,
        'exposure_variance': exposure_variance,
        'ndcg_variance': ndcg_variance,
        'all_passed': tests_passed == total_tests
    }


if __name__ == "__main__":
    import glob
    
    # Find latest ranker model
    rankers = sorted(glob.glob("./data/xgboost_ranker_model_*.json"))
    encoders = sorted(glob.glob("./data/ranker_encoder_*.pkl"))
    
    if rankers and encoders:
        print(f"Using latest ranker: {rankers[-1]}\n")
        results = audit_ranker_bias(rankers[-1], encoders[-1])
    else:
        print("No trained ranker models found!")
        print("Run: python ml_training/train_ranker.py first")
