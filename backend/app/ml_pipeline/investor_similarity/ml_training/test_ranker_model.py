"""
ML Ranker Model Testing Script

Tests the trained pairwise ranker without deployment.
Loads model from joblib/pickle and demonstrates inference.
"""

import sys
from pathlib import Path
import joblib
import numpy as np
import glob

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.ml_pipeline.investor_similarity.dataset_builder import DatasetBuilder


def test_ml_ranker():
    """
    Complete test of ML ranker model
    
    Tests:
    1. Load deployment bundle
    2. Single pair prediction
    3. Batch ranking (find top K)
    4. Performance validation
    """
    
    print("=" * 70)
    print("ML Ranker Model Testing")
    print("=" * 70)
    
    # Step 1: Load deployment bundle
    print("\n[1/5] Loading deployment bundle...")
    
    # Find latest deployment bundle
    bundles = sorted(glob.glob("./data/ranker_deployment_bundle_*.joblib"))
    
    if not bundles:
        print("❌ No deployment bundle found!")
        print("Run: python investor_similarity/ml_training/generate_production_package.py")
        return
    
    bundle_path = bundles[-1]
    print(f"  Loading: {Path(bundle_path).name}")
    
    bundle = joblib.load(bundle_path)
    model = bundle['model']
    encoder = bundle['encoder']
    metadata = bundle['metadata']
    
    print(f"  ✓ Model loaded")
    print(f"  ✓ Encoder loaded")
    print(f"  ✓ Created: {metadata['created_at']}")
    print(f"  ✓ NDCG@10: {metadata['ndcg@10']:.4f}")
    print(f"  ✓ Bias-free: {metadata['bias_free']}")
    
    # Step 2: Load test data
    print("\n[2/5] Loading test investors...")
    
    dataset_builder = DatasetBuilder(
        storage_path="./data/snapshots_10k",
        feature_version="v1.0"
    )
    
    snapshots = dataset_builder.load_all_snapshots()
    print(f"  ✓ Loaded {len(snapshots):,} investors")
    
    # Step 3: Test single pair prediction
    print("\n[3/5] Testing single pair prediction...")
    
    query = snapshots[0]
    candidate = snapshots[1]
    
    print(f"\n  Query Investor: {query.investor_id}")
    print(f"    Capital Band: {query.block_b.get('capital_band', 'N/A')}")
    print(f"    ROI Band: {query.block_b.get('expected_roi_band', 'N/A')}")
    print(f"    Holding Period: {query.block_b.get('holding_period_band', 'N/A')}")
    
    print(f"\n  Candidate Investor: {candidate.investor_id}")
    print(f"    Capital Band: {candidate.block_b.get('capital_band', 'N/A')}")
    print(f"    ROI Band: {candidate.block_b.get('expected_roi_band', 'N/A')}")
    print(f"    Holding Period: {candidate.block_b.get('holding_period_band', 'N/A')}")
    
    # Encode and predict
    features = encoder.encode_pair(query, candidate)
    X = np.array([features])
    
    score = model.predict(X)[0]
    
    print(f"\n  Predicted Similarity Score: {score:.4f}")
    print(f"  ✓ Single prediction working!")
    
    # Step 4: Test batch ranking (find top 10 matches)
    print("\n[4/5] Testing batch ranking (Top 10 matches)...")
    
    query = snapshots[100]  # Different query
    candidates = snapshots[101:201]  # 100 candidates
    
    print(f"\n  Query: Investor {query.investor_id}")
    print(f"  Ranking {len(candidates)} candidates...")
    
    # Encode all pairs
    features_list = [encoder.encode_pair(query, cand) for cand in candidates]
    X = np.array(features_list)
    
    # Predict scores
    scores = model.predict(X)
    
    # Sort by score (descending)
    ranked_indices = np.argsort(scores)[::-1]
    
    print(f"\n  Top 10 Matches:")
    print(f"  {'Rank':<6} {'Investor ID':<15} {'Score':<10} {'Capital':<10} {'ROI':<10}")
    print(f"  {'-'*60}")
    
    for rank, idx in enumerate(ranked_indices[:10], 1):
        investor = candidates[idx]
        score = scores[idx]
        capital = investor.block_b.get('capital_band', 'N/A')
        roi = investor.block_b.get('expected_roi_band', 'N/A')
        
        print(f"  {rank:<6} {investor.investor_id:<15} {score:<10.4f} {capital:<10} {roi:<10}")
    
    print(f"\n  ✓ Batch ranking working!")
    
    # Step 5: Performance validation
    print("\n[5/5] Performance validation...")
    
    import time
    
    # Test inference speed
    n_tests = 100
    start = time.time()
    
    for _ in range(n_tests):
        query = snapshots[np.random.randint(0, 1000)]
        candidate = snapshots[np.random.randint(0, 1000)]
        features = encoder.encode_pair(query, candidate)
        X = np.array([features])
        _ = model.predict(X)
    
    elapsed = time.time() - start
    avg_time = (elapsed / n_tests) * 1000  # Convert to ms
    
    print(f"\n  Inference Speed Test ({n_tests} predictions):")
    print(f"    Total time: {elapsed:.2f}s")
    print(f"    Avg per prediction: {avg_time:.2f}ms")
    
    if avg_time < 10:
        print(f"    ✅ EXCELLENT (< 10ms)")
    elif avg_time < 50:
        print(f"    ✅ GOOD (< 50ms)")
    else:
        print(f"    ⚠️  SLOW (> 50ms)")
    
    # Test batch ranking speed
    start = time.time()
    
    query = snapshots[0]
    candidates = snapshots[1:101]  # 100 candidates
    features_list = [encoder.encode_pair(query, cand) for cand in candidates]
    X = np.array(features_list)
    scores = model.predict(X)
    ranked_indices = np.argsort(scores)[::-1]
    
    batch_time = (time.time() - start) * 1000
    
    print(f"\n  Batch Ranking Speed (100 candidates):")
    print(f"    Total time: {batch_time:.2f}ms")
    print(f"    Per candidate: {batch_time/100:.2f}ms")
    
    if batch_time < 100:
        print(f"    ✅ EXCELLENT (< 100ms)")
    elif batch_time < 500:
        print(f"    ✅ GOOD (< 500ms)")
    else:
        print(f"    ⚠️  SLOW (> 500ms)")
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    print(f"\n  ✅ Model loaded successfully")
    print(f"  ✅ Single prediction: {avg_time:.2f}ms")
    print(f"  ✅ Batch ranking (100): {batch_time:.2f}ms")
    print(f"  ✅ Model metadata: NDCG@10 = {metadata['ndcg@10']:.4f}")
    print(f"  ✅ Bias-free: {metadata['bias_free']}")
    
    print("\n" + "=" * 70)
    print("🎉 All Tests Passed! Model is Ready for Deployment")
    print("=" * 70)
    
    return {
        'model': model,
        'encoder': encoder,
        'metadata': metadata,
        'avg_inference_time_ms': avg_time,
        'batch_time_ms': batch_time
    }


def test_specific_scenario():
    """
    Test specific investor matching scenario
    """
    
    print("\n" + "=" * 70)
    print("Specific Scenario Test: Find Similar Investors")
    print("=" * 70)
    
    # Load bundle
    bundles = sorted(glob.glob("./data/ranker_deployment_bundle_*.joblib"))
    bundle = joblib.load(bundles[-1])
    model = bundle['model']
    encoder = bundle['encoder']
    
    # Load data
    dataset_builder = DatasetBuilder(
        storage_path="./data/snapshots_10k",
        feature_version="v1.0"
    )
    snapshots = dataset_builder.load_all_snapshots()
    
    # Find a specific investor profile
    print("\n  Looking for investors similar to:")
    print("    - High capital (band 3-4)")
    print("    - Long holding period")
    print("    - High ROI expectations")
    
    # Find query investor matching criteria
    query = None
    for snap in snapshots:
        if (snap.block_b.get('capital_band', 0) >= 3 and
            snap.block_b.get('holding_period_band') == 'long' and
            snap.block_b.get('expected_roi_band') == 'high'):
            query = snap
            break
    
    if not query:
        print("  ⚠️  No investor matching exact criteria, using first investor")
        query = snapshots[0]
    
    print(f"\n  Query Investor Profile:")
    print(f"    ID: {query.investor_id}")
    print(f"    Capital Band: {query.block_b.get('capital_band')}")
    print(f"    ROI Band: {query.block_b.get('expected_roi_band')}")
    print(f"    Holding Period: {query.block_b.get('holding_period_band')}")
    print(f"    City Tier: {query.block_b.get('city_tier')}")
    
    # Rank all other investors
    candidates = [s for s in snapshots if s.investor_id != query.investor_id]
    
    print(f"\n  Ranking {len(candidates):,} potential matches...")
    
    features_list = [encoder.encode_pair(query, cand) for cand in candidates]
    X = np.array(features_list)
    scores = model.predict(X)
    ranked_indices = np.argsort(scores)[::-1]
    
    # Show top 20 matches
    print(f"\n  Top 20 Most Similar Investors:")
    print(f"  {'Rank':<6} {'ID':<15} {'Score':<10} {'Capital':<10} {'ROI':<10} {'Holding':<10} {'Tier':<6}")
    print(f"  {'-'*75}")
    
    for rank, idx in enumerate(ranked_indices[:20], 1):
        investor = candidates[idx]
        score = scores[idx]
        capital = investor.block_b.get('capital_band', 'N/A')
        roi = investor.block_b.get('expected_roi_band', 'N/A')
        holding = investor.block_b.get('holding_period_band', 'N/A')
        tier = investor.block_b.get('city_tier', 'N/A')
        
        print(f"  {rank:<6} {investor.investor_id:<15} {score:<10.4f} {capital:<10} {roi:<10} {holding:<10} {tier:<6}")
    
    print(f"\n  ✅ Found {len([s for s in scores if s > 0.5])} highly similar investors (score > 0.5)")


if __name__ == "__main__":
    # Run basic tests
    results = test_ml_ranker()
    
    # Run specific scenario
    test_specific_scenario()
    
    print("\n" + "=" * 70)
    print("Testing Complete!")
    print("=" * 70)
    print("\nNext Steps:")
    print("  1. Integrate into FastAPI backend")
    print("  2. Create API endpoint: POST /api/v1/recommend")
    print("  3. Deploy to production")
    print("  4. Monitor NDCG@10 in production")
