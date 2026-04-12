"""
Test Script for Legal Document Analysis API
Tests the Gemini-powered legal analysis endpoints
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
LEGAL_API_BASE = f"{BASE_URL}/legal"

# Sample GCS URIs for testing (replace with actual files if available)
TEST_SAMPLES = {
    "property_transfer": "gs://cloud-samples-data/generative-ai/pdf/2024-09-sample-form-10.pdf",
    "general": "gs://cloud-samples-data/generative-ai/pdf/1706.03762v7.pdf",
}


def print_section(title: str):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_health_check():
    """Test the health check endpoint"""
    print_section("Test 1: Health Check")
    try:
        response = requests.get(f"{LEGAL_API_BASE}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_analysis_types():
    """Test getting available analysis types"""
    print_section("Test 2: Get Available Analysis Types")
    try:
        response = requests.get(f"{LEGAL_API_BASE}/analysis-types")
        data = response.json()
        print(f"Status Code: {response.status_code}")
        print(f"\nAnalysis Types:")
        for type_info in data.get("analysis_types", []):
            print(f"  - {type_info['type']}: {type_info['description']}")
        
        print(f"\nFocus Areas:")
        for area in data.get("focus_areas", []):
            print(f"  - {area['code']}: {area['name']}")
            print(f"    Description: {area['description']}")
        
        print(f"\nLanguages: {', '.join(data.get('languages', []))}")
        print(f"Model: {data.get('model')}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_help():
    """Test the help endpoint"""
    print_section("Test 3: Get Help & Documentation")
    try:
        response = requests.get(f"{LEGAL_API_BASE}/help")
        data = response.json()
        print(f"Status Code: {response.status_code}")
        print(f"Title: {data.get('title')}")
        print(f"Description: {data.get('description')}")
        print(f"\nEndpoints:")
        for endpoint, info in data.get("endpoints", {}).items():
            print(f"  {endpoint}")
            print(f"    Method: {info['method']}")
            print(f"    Description: {info['description']}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_invalid_focus_area():
    """Test with invalid focus area"""
    print_section("Test 4: Validation - Invalid Focus Area")
    try:
        request_data = {
            "file_uri": "gs://bucket/sample.pdf",
            "focus_area": "invalid_focus_area",
            "language": "english"
        }
        response = requests.post(
            f"{LEGAL_API_BASE}/analyze-pdf",
            json=request_data
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 400
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_invalid_language():
    """Test with invalid language"""
    print_section("Test 5: Validation - Invalid Language")
    try:
        request_data = {
            "file_uri": "gs://bucket/sample.pdf",
            "focus_area": "property_transfer",
            "language": "spanish"
        }
        response = requests.post(
            f"{LEGAL_API_BASE}/analyze-pdf",
            json=request_data
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 400
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_invalid_file_uri():
    """Test with invalid file URI format"""
    print_section("Test 6: Validation - Invalid File URI")
    try:
        request_data = {
            "file_uri": "https://example.com/file.pdf",  # Not gs://
            "focus_area": "property_transfer",
            "language": "english"
        }
        response = requests.post(
            f"{LEGAL_API_BASE}/analyze-pdf",
            json=request_data
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Should either return 400 or 500 depending on error handling
        return response.status_code in [400, 500]
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_single_analysis(file_uri: str, focus_area: str = "general"):
    """Test single document analysis"""
    print_section(f"Test 7: Analyze Single Document ({focus_area})")
    print(f"File URI: {file_uri}")
    print(f"Focus Area: {focus_area}")
    
    try:
        request_data = {
            "file_uri": file_uri,
            "analysis_type": "comprehensive",
            "focus_area": focus_area,
            "language": "english"
        }
        
        print("\nSending request...")
        print(f"Payload: {json.dumps(request_data, indent=2)}")
        
        response = requests.post(
            f"{LEGAL_API_BASE}/analyze-pdf",
            json=request_data,
            timeout=120  # 2 minute timeout for API processing
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data.get('status')}")
            print(f"Model Used: {data.get('model_used')}")
            
            print(f"\nAnalysis (first 500 chars):")
            analysis = data.get('analysis', '')
            print(analysis[:500] + ("..." if len(analysis) > 500 else ""))
            
            print(f"\nKey Points ({len(data.get('key_points', []))} found):")
            for point in data.get('key_points', [])[:5]:
                print(f"  - {point}")
            
            print(f"\nRecommendations ({len(data.get('recommendations', []))} found):")
            for rec in data.get('recommendations', [])[:5]:
                print(f"  - {rec}")
            
            print(f"\nRisk Factors ({len(data.get('risk_factors', []))} found):")
            for risk in data.get('risk_factors', [])[:5]:
                print(f"  - {risk}")
            
            return True
        else:
            print(f"Error Response:")
            print(json.dumps(response.json(), indent=2))
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out. API is taking too long to process.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_batch_analysis():
    """Test batch analysis"""
    print_section("Test 8: Batch Analysis (Multiple Documents)")
    
    try:
        batch_data = [
            {
                "file_uri": TEST_SAMPLES["general"],
                "focus_area": "general",
                "language": "english"
            },
            {
                "file_uri": TEST_SAMPLES["general"],
                "focus_area": "property_transfer",
                "language": "english"
            }
        ]
        
        print(f"Analyzing {len(batch_data)} documents...")
        print(json.dumps(batch_data, indent=2))
        
        response = requests.post(
            f"{LEGAL_API_BASE}/batch-analyze",
            json=batch_data,
            timeout=180
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total Documents: {data.get('total_documents')}")
            print(f"Successful: {data.get('successful')}")
            print(f"Failed: {data.get('failed')}")
            
            if data.get('errors'):
                print(f"\nErrors:")
                for error in data.get('errors', []):
                    print(f"  [{error['index']}] {error['error']}")
            
            return response.status_code == 200
        else:
            print(json.dumps(response.json(), indent=2))
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_batch_too_many():
    """Test batch with too many documents"""
    print_section("Test 9: Validation - Batch Too Many Documents")
    
    try:
        # Create 11 documents
        batch_data = [
            {
                "file_uri": TEST_SAMPLES["general"],
                "focus_area": "general"
            }
        ] * 11
        
        response = requests.post(
            f"{LEGAL_API_BASE}/batch-analyze",
            json=batch_data
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        return response.status_code == 400
    except Exception as e:
        print(f"Error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print_section("LEGAL DOCUMENT ANALYSIS API - TEST SUITE")
    print("Testing the Gemini-powered legal analysis endpoints\n")
    
    results = []
    
    # Non-API tests (always run)
    print("Running validation tests...\n")
    results.append(("Health Check", test_health_check()))
    results.append(("Get Analysis Types", test_analysis_types()))
    results.append(("Get Help", test_help()))
    results.append(("Validation: Invalid Focus Area", test_invalid_focus_area()))
    results.append(("Validation: Invalid Language", test_invalid_language()))
    results.append(("Validation: Invalid File URI", test_invalid_file_uri()))
    results.append(("Validation: Batch Too Many", test_batch_too_many()))
    
    # Actual analysis tests (requires valid GCS file and API key)
    print("\n\nRunning analysis tests...")
    print("(These tests require valid GCS files and GOOGLE_API_KEY)")
    
    try:
        results.append(("Single Analysis - General", 
                       test_single_analysis(TEST_SAMPLES["general"], "general")))
        
        time.sleep(2)  # Small delay between API calls
        
        results.append(("Single Analysis - Property Transfer", 
                       test_single_analysis(TEST_SAMPLES["property_transfer"], "property_transfer")))
        
        time.sleep(2)
        
        results.append(("Batch Analysis", test_batch_analysis()))
    except Exception as e:
        print(f"\n⚠️ Analysis tests skipped: {e}")
    
    # Print summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Total: {passed}/{total} tests passed")
    print(f"{'='*60}\n")
    
    return passed == total


if __name__ == "__main__":
    import sys
    
    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        print(f"✅ Backend API is running at {BASE_URL}")
    except:
        print(f"❌ Backend API is not running at {BASE_URL}")
        print("Please start the backend with: python -m uvicorn app.main:app --reload")
        sys.exit(1)
    
    # Run tests
    success = run_all_tests()
    sys.exit(0 if success else 1)
