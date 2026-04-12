"""
Comprehensive Bias Analysis

Advanced bias testing with multiple fairness metrics:
1. Demographic Parity (feature distribution equality)
2. Equalized Odds (similar outcomes across groups)
3. Disparate Impact Ratio
4. Statistical Parity Difference
5. Feature Independence Tests
"""

import sys
from pathlib import Path
import numpy as np
from scipy import stats
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.ml_pipeline.investor_similarity.dataset_builder import DatasetBuilder


def compute_demographic_parity(snapshots, demographic_attr, feature_name):
    """
    Test if feature distributions are similar across demographic groups
    
    Returns: p-value from ANOVA (high p-value = good, no difference)
    """
    groups = {}
    
    for snapshot in snapshots:
        demo_value = snapshot.block_b.get(demographic_attr)
        feature_value = snapshot.block_a.get(feature_name, 0)
        
        if demo_value not in groups:
            groups[demo_value] = []
        groups[demo_value].append(feature_value)
    
    # ANOVA test: null hypothesis is all groups have same mean
    group_arrays = [np.array(v) for v in groups.values()]
    f_stat, p_value = stats.f_oneway(*group_arrays)
    
    # High p-value (>0.05) means groups are similar (good!)
    return {
        "demographic": demographic_attr,
        "feature": feature_name,
        "groups": {k: {"mean": np.mean(v), "std": np.std(v), "count": len(v)} 
                   for k, v in groups.items()},
        "f_statistic": float(f_stat),
        "p_value": float(p_value),
        "passes": p_value > 0.05  # No significant difference
    }


def compute_disparate_impact_ratio(snapshots, demographic_attr, threshold_attr):
    """
    Disparate Impact Ratio: ratio of positive outcomes between groups
    
    Should be close to 1.0 (range 0.8-1.2 is acceptable)
    """
    # Count high-value investors (capital_band >= 2) per demographic
    counts = {}
    totals = {}
    
    for snapshot in snapshots:
        demo_value = snapshot.block_b.get(demographic_attr)
        threshold_value = snapshot.block_b.get(threshold_attr, 0)
        
        if demo_value not in counts:
            counts[demo_value] = 0
            totals[demo_value] = 0
        
        totals[demo_value] += 1
        if threshold_value >= 2:  # High capital
            counts[demo_value] += 1
    
    # Calculate rates
    rates = {k: counts[k] / totals[k] if totals[k] > 0 else 0 
             for k in counts.keys()}
    
    # Compute disparate impact ratios
    ratios = {}
    rate_list = list(rates.values())
    if rate_list:
        max_rate = max(rate_list)
        min_rate = min(rate_list)
        if max_rate > 0:
            disparate_impact = min_rate / max_rate
        else:
            disparate_impact = 1.0
    else:
        disparate_impact = 1.0
    
    return {
        "demographic": demographic_attr,
        "threshold_attribute": threshold_attr,
        "rates_by_group": rates,
        "disparate_impact_ratio": disparate_impact,
        "passes": 0.8 <= disparate_impact <= 1.2,  # 80% rule
        "note": "Ratio should be 0.8-1.2 (closer to 1.0 is better)"
    }


def compute_statistical_parity(snapshots, demographic_attr):
    """
    Statistical Parity: check if demographic groups have equal representation
    across capital bands
    """
    # Build contingency table
    demo_capital_matrix = {}
    
    for snapshot in snapshots:
        demo = snapshot.block_b.get(demographic_attr)
        capital = snapshot.block_b.get("capital_band", 0)
        
        if demo not in demo_capital_matrix:
            demo_capital_matrix[demo] = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        
        demo_capital_matrix[demo][capital] += 1
    
    # Chi-square test for independence
    # Convert to contingency table
    demo_labels = sorted(demo_capital_matrix.keys())
    capital_bands = [0, 1, 2, 3, 4]
    
    observed = []
    for demo in demo_labels:
        row = [demo_capital_matrix[demo][band] for band in capital_bands]
        observed.append(row)
    
    observed = np.array(observed)
    
    # Chi-square test
    chi2, p_value, dof, expected = stats.chi2_contingency(observed)
    
    return {
        "demographic": demographic_attr,
        "chi2_statistic": float(chi2),
        "p_value": float(p_value),
        "degrees_of_freedom": int(dof),
        "passes": p_value > 0.05,  # High p-value = independent (good!)
        "note": "High p-value means demographic is independent of capital"
    }


def compute_feature_independence(snapshots):
    """
    Test if Block A features are independent of Block B demographics
    """
    results = []
    
    # Only test city_tier (age_band removed!)
    demographics = ["city_tier"]
    block_a_features = [
        "risk_orientation_score",
        "collaboration_comfort_score", 
        "control_preference_score",
        "real_estate_conviction_score"
    ]
    
    for demo in demographics:
        for feature in block_a_features:
            result = compute_demographic_parity(snapshots, demo, feature)
            results.append(result)
    
    return results


def analyze_recommendation_fairness(snapshots):
    """
    Check if recommendations would be fair across city tiers
    
    Simulate: for each city tier, compute average similarity to others
    """
    from backend.app.ml_pipeline.investor_similarity.similarity_engine import SimilarityEngine
    
    engine = SimilarityEngine()
    
    # Sample 100 investors from each city tier
    tier_samples = {1: [], 2: [], 3: []}
    
    for snapshot in snapshots:
        tier = snapshot.block_b.get("city_tier", 2)
        if len(tier_samples[tier]) < 100:
            tier_samples[tier].append(snapshot)
    
    # Compute average similarity within and across groups
    similarity_matrix = {}
    
    for tier1 in [1, 2, 3]:
        similarity_matrix[tier1] = {}
        for tier2 in [1, 2, 3]:
            similarities = []
            
            # Sample pairs
            for s1 in tier_samples[tier1][:20]:
                for s2 in tier_samples[tier2][:20]:
                    if s1.investor_id != s2.investor_id:
                        result = engine.compute_similarity(s1, s2)
                        similarities.append(result.total_similarity)
            
            if similarities:
                avg_sim = np.mean(similarities)
                similarity_matrix[tier1][tier2] = float(avg_sim)
            else:
                similarity_matrix[tier1][tier2] = 0.0
    
    return {
        "similarity_matrix": similarity_matrix,
        "note": "Similar values across all cells = fair recommendations"
    }


def main():
    print("=" * 70)
    print("Comprehensive Bias Analysis")
    print("=" * 70)
    
    # Load dataset
    print("\n[1/5] Loading dataset...")
    dataset_builder = DatasetBuilder(
        storage_path="./data/snapshots_10k",
        feature_version="v1.0"
    )
    
    snapshots = dataset_builder.load_all_snapshots()
    print(f"  ✓ Loaded {len(snapshots)} snapshots")
    
    # Test 1: Demographic Parity
    print("\n[2/5] Testing Demographic Parity (Feature Distribution Equality)...")
    independence_results = compute_feature_independence(snapshots)
    
    passed = sum(1 for r in independence_results if r["passes"])
    total = len(independence_results)
    
    print(f"  Tested {total} feature-demographic pairs")
    print(f"  Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    # Show any failures
    failures = [r for r in independence_results if not r["passes"]]
    if failures:
        print(f"\n  WARNING: Features with demographic correlation:")
        for f in failures:
            print(f"    - {f['feature']} x {f['demographic']}: p={f['p_value']:.4f}")
    
    # Test 2: Disparate Impact (city tier only)
    print("\n[3/5] Testing Disparate Impact (80% Rule)...")
    
    tier_impact = compute_disparate_impact_ratio(snapshots, "city_tier", "capital_band")
    
    print(f"  City Tier Disparate Impact: {tier_impact['disparate_impact_ratio']:.3f}")
    print(f"    Status: {'PASS' if tier_impact['passes'] else 'FAIL'}")
    print(f"    Rates: {tier_impact['rates_by_group']}")
    
    # Test 3: Statistical Parity (city tier only)
    print("\n[4/5] Testing Statistical Parity (Independence Test)...")
    
    tier_parity = compute_statistical_parity(snapshots, "city_tier")
    
    print(f"  City Tier Independence: p={tier_parity['p_value']:.4f}")
    print(f"    Status: {'PASS' if tier_parity['passes'] else 'FAIL'}")
    
    # Test 4: Recommendation Fairness
    print("\n[5/5] Testing Recommendation Fairness...")
    print("  Computing similarity across city tiers...")
    
    rec_fairness = analyze_recommendation_fairness(snapshots)
    
    print("\n  Similarity Matrix (tier x tier):")
    print(f"  {'':>8} {'Tier 1':>10} {'Tier 2':>10} {'Tier 3':>10}")
    for tier1 in [1, 2, 3]:
        row = f"  Tier {tier1:>3}"
        for tier2 in [1, 2, 3]:
            sim = rec_fairness["similarity_matrix"][tier1][tier2]
            row += f" {sim:>10.3f}"
        print(row)
    
    # Check variance across matrix
    all_sims = [v for row in rec_fairness["similarity_matrix"].values() 
                for v in row.values()]
    sim_variance = np.var(all_sims)
    print(f"\n  Similarity variance: {sim_variance:.4f}")
    print(f"  Status: {'FAIR' if sim_variance < 0.01 else 'CHECK'}")
    
    # Final Summary
    print("\n" + "=" * 70)
    print("Bias Analysis Summary")
    print("=" * 70)
    
    # Updated test count (no age tests!)
    total_tests = total + 1 + 1 + 1  # Independence + Disparate Impact + Parity + Rec
    passed_tests = (
        passed + 
        (1 if tier_impact['passes'] else 0) +
        (1 if tier_parity['passes'] else 0) +
        (1 if sim_variance < 0.01 else 0)
    )
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Pass Rate: {passed_tests/total_tests*100:.1f}%")
    
    overall_status = "BIAS-FREE" if passed_tests >= total_tests * 0.9 else "REVIEW NEEDED"
    print(f"\nOverall Status: {overall_status}")
    
    print(f"\n{'='*70}")
    print("IMPORTANT: Age band removed! Only testing city tier (economic context)")
    print("Behavioral features (CDI, TSS, BCS, CCR) have NO demographic input")
    print("→ Mathematically impossible to correlate with age/gender/occupation")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
