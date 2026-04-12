"""
Test ML Similarity Differentiation

Verifies that different input profiles produce different results
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_capital_band_differentiation():
    """Test that different capital bands produce different results"""
    print("\n" + "=" * 60)
    print("TEST 1: Capital Band Differentiation")
    print("=" * 60)
    
    # Profile with capital_band = 0 (low capital)
    profile_low = {
        "capital_band": 0,
        "expected_roi_band": "medium",
        "holding_period_band": "medium",
        "risk_orientation": 0.5,
        "collaboration_comfort": 0.5,
        "control_preference": 0.5,
        "re_conviction": 0.5,
        "city_tier": 2
    }
    
    # Profile with capital_band = 4 (high capital)
    profile_high = {
        "capital_band": 4,
        "expected_roi_band": "medium",
        "holding_period_band": "medium",
        "risk_orientation": 0.5,
        "collaboration_comfort": 0.5,
        "control_preference": 0.5,
        "re_conviction": 0.5,
        "city_tier": 2
    }
    
    response_low = requests.post(
        f"{BASE_URL}/api/ml-similarity/recommend",
        json=profile_low,
        params={"top_k": 3}
    )
    
    response_high = requests.post(
        f"{BASE_URL}/api/ml-similarity/recommend",
        json=profile_high,
        params={"top_k": 3}
    )
    
    matches_low = response_low.json()['matches']
    matches_high = response_high.json()['matches']
    
    print("\n🔍 Capital Band = 0 (Low)")
    print("-" * 60)
    for i, match in enumerate(matches_low, 1):
        print(f"  {i}. Band {match['capital_band']} | {match['expected_roi_band']:6s} ROI | Score: {match['similarity_score']:.4f}")
    
    print("\n🔍 Capital Band = 4 (High)")
    print("-" * 60)
    for i, match in enumerate(matches_high, 1):
        print(f"  {i}. Band {match['capital_band']} | {match['expected_roi_band']:6s} ROI | Score: {match['similarity_score']:.4f}")
    
    # Check if results are different
    top_ids_low = [m['investor_id'] for m in matches_low]
    top_ids_high = [m['investor_id'] for m in matches_high]
    
    if top_ids_low != top_ids_high:
        print("\n✅ PASS: Different capital bands produce different results")
        return True
    else:
        print("\n❌ FAIL: Same results for different capital bands")
        return False


def test_roi_differentiation():
    """Test that different ROI expectations produce different results"""
    print("\n" + "=" * 60)
    print("TEST 2: ROI Band Differentiation")
    print("=" * 60)
    
    # Profile with low ROI expectation
    profile_low = {
        "capital_band": 2,
        "expected_roi_band": "low",
        "holding_period_band": "medium",
        "risk_orientation": 0.5,
        "collaboration_comfort": 0.5,
        "control_preference": 0.5,
        "re_conviction": 0.5,
        "city_tier": 2
    }
    
    # Profile with high ROI expectation
    profile_high = {
        "capital_band": 2,
        "expected_roi_band": "high",
        "holding_period_band": "medium",
        "risk_orientation": 0.5,
        "collaboration_comfort": 0.5,
        "control_preference": 0.5,
        "re_conviction": 0.5,
        "city_tier": 2
    }
    
    response_low = requests.post(
        f"{BASE_URL}/api/ml-similarity/recommend",
        json=profile_low,
        params={"top_k": 3}
    )
    
    response_high = requests.post(
        f"{BASE_URL}/api/ml-similarity/recommend",
        json=profile_high,
        params={"top_k": 3}
    )
    
    matches_low = response_low.json()['matches']
    matches_high = response_high.json()['matches']
    
    print("\n🔍 Expected ROI = Low")
    print("-" * 60)
    for i, match in enumerate(matches_low, 1):
        print(f"  {i}. Band {match['capital_band']} | {match['expected_roi_band']:6s} ROI | Score: {match['similarity_score']:.4f}")
    
    print("\n🔍 Expected ROI = High")
    print("-" * 60)
    for i, match in enumerate(matches_high, 1):
        print(f"  {i}. Band {match['capital_band']} | {match['expected_roi_band']:6s} ROI | Score: {match['similarity_score']:.4f}")
    
    # Check if results are different
    top_ids_low = [m['investor_id'] for m in matches_low]
    top_ids_high = [m['investor_id'] for m in matches_high]
    
    if top_ids_low != top_ids_high:
        print("\n✅ PASS: Different ROI bands produce different results")
        return True
    else:
        print("\n❌ FAIL: Same results for different ROI bands")
        return False


def test_risk_orientation_differentiation():
    """Test that different risk orientations produce different results"""
    print("\n" + "=" * 60)
    print("TEST 3: Risk Orientation Differentiation")
    print("=" * 60)
    
    # Conservative profile
    profile_conservative = {
        "capital_band": 2,
        "expected_roi_band": "medium",
        "holding_period_band": "medium",
        "risk_orientation": 0.1,  # Very conservative
        "collaboration_comfort": 0.5,
        "control_preference": 0.5,
        "re_conviction": 0.5,
        "city_tier": 2
    }
    
    # Aggressive profile
    profile_aggressive = {
        "capital_band": 2,
        "expected_roi_band": "medium",
        "holding_period_band": "medium",
        "risk_orientation": 0.9,  # Very aggressive
        "collaboration_comfort": 0.5,
        "control_preference": 0.5,
        "re_conviction": 0.5,
        "city_tier": 2
    }
    
    response_conservative = requests.post(
        f"{BASE_URL}/api/ml-similarity/recommend",
        json=profile_conservative,
        params={"top_k": 3}
    )
    
    response_aggressive = requests.post(
        f"{BASE_URL}/api/ml-similarity/recommend",
        json=profile_aggressive,
        params={"top_k": 3}
    )
    
    matches_conservative = response_conservative.json()['matches']
    matches_aggressive = response_aggressive.json()['matches']
    
    print("\n🔍 Risk Orientation = 0.1 (Conservative)")
    print("-" * 60)
    for i, match in enumerate(matches_conservative, 1):
        print(f"  {i}. Band {match['capital_band']} | {match['expected_roi_band']:6s} ROI | Score: {match['similarity_score']:.4f}")
    
    print("\n🔍 Risk Orientation = 0.9 (Aggressive)")
    print("-" * 60)
    for i, match in enumerate(matches_aggressive, 1):
        print(f"  {i}. Band {match['capital_band']} | {match['expected_roi_band']:6s} ROI | Score: {match['similarity_score']:.4f}")
    
    # Check if results are different
    top_ids_conservative = [m['investor_id'] for m in matches_conservative]
    top_ids_aggressive = [m['investor_id'] for m in matches_aggressive]
    
    if top_ids_conservative != top_ids_aggressive:
        print("\n✅ PASS: Different risk orientations produce different results")
        return True
    else:
        print("\n❌ FAIL: Same results for different risk orientations")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("ML SIMILARITY DIFFERENTIATION TEST SUITE")
    print("=" * 60)
    print("\nVerifying that different inputs produce different outputs...")
    
    results = []
    
    try:
        results.append(("Capital Band", test_capital_band_differentiation()))
        results.append(("ROI Band", test_roi_differentiation()))
        results.append(("Risk Orientation", test_risk_orientation_differentiation()))
        
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        for test_name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}: {test_name}")
        
        all_passed = all(result[1] for result in results)
        
        if all_passed:
            print("\n🎉 ALL TESTS PASSED - ML model is differentiating correctly!")
        else:
            print("\n⚠️  SOME TESTS FAILED - Check feature encoding")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
