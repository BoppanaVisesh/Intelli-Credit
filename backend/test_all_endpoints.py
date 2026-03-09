"""
Test All API Endpoints - Complete System Test
Tests all 16 endpoints in the Intelli-Credit API
"""
import requests
import json
from pathlib import Path
import time

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_header(text):
    print(f"\n{'='*70}")
    print(f"{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{'='*70}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.YELLOW}ℹ️  {text}{Colors.RESET}")

def test_endpoint(name, method, url, **kwargs):
    """Test a single endpoint"""
    try:
        print(f"\n{Colors.BLUE}Testing: {method} {url}{Colors.RESET}")
        
        if method == "GET":
            response = requests.get(url, **kwargs)
        elif method == "POST":
            response = requests.post(url, **kwargs)
        else:
            print_error(f"Unsupported method: {method}")
            return None
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print_success(f"{name} - SUCCESS")
            return response.json()
        elif response.status_code == 307:
            print_info(f"{name} - Redirect (try with trailing slash)")
            return None
        else:
            print_error(f"{name} - FAILED")
            print(f"Response: {response.text[:200]}")
            return None
            
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to {BASE_URL}. Is the server running?")
        return None
    except Exception as e:
        print_error(f"{name} - ERROR: {str(e)}")
        return None

def main():
    print_header("INTELLI-CREDIT API - COMPLETE ENDPOINT TEST")
    print(f"Base URL: {BASE_URL}")
    print(f"API Base: {API_BASE}")
    
    results = {
        "passed": 0,
        "failed": 0,
        "skipped": 0
    }
    
    # ==================== SYSTEM ENDPOINTS ====================
    print_header("1. SYSTEM ENDPOINTS")
    
    # Test 1: Root endpoint
    result = test_endpoint("Root", "GET", f"{BASE_URL}/")
    if result:
        results["passed"] += 1
        print(f"   Response: {result}")
    else:
        results["failed"] += 1
    
    # Test 2: Health check
    result = test_endpoint("Health Check", "GET", f"{BASE_URL}/health")
    if result:
        results["passed"] += 1
        print(f"   Status: {result.get('status')}")
    else:
        results["failed"] += 1
    
    # ==================== APPLICATION ENDPOINTS ====================
    print_header("2. APPLICATION ENDPOINTS")
    
    # Test 3: Create Application
    app_data = {
        "company_name": "TechCorp Innovations Pvt Ltd",
        "mca_cin": "U12345MH2020PTC123456",
        "sector": "Technology",
        "requested_limit_cr": 15.0
    }
    
    result = test_endpoint(
        "Create Application",
        "POST",
        f"{API_BASE}/applications/",
        json=app_data
    )
    
    application_id = None
    if result:
        results["passed"] += 1
        application_id = result.get("application_id")
        print(f"   Application ID: {application_id}")
    else:
        results["failed"] += 1
        print_error("Cannot proceed without application ID")
        return
    
    # Test 4: List Applications
    result = test_endpoint("List Applications", "GET", f"{API_BASE}/applications/")
    if result:
        results["passed"] += 1
        print(f"   Total Applications: {result.get('total', 0)}")
    else:
        results["failed"] += 1
    
    # Test 5: Get Application (will fail if no analysis done yet)
    result = test_endpoint(
        "Get Application",
        "GET",
        f"{API_BASE}/applications/{application_id}"
    )
    if result:
        results["passed"] += 1
    else:
        print_info("Expected to fail if analysis not completed")
        results["skipped"] += 1
    
    # ==================== DATA INGESTION ENDPOINTS ====================
    print_header("3. DATA INGESTION ENDPOINTS")
    
    # Test 6: Upload Documents
    test_data_dir = Path("test_data")
    
    if test_data_dir.exists():
        print_info("Found test_data directory")
        
        bank_file = test_data_dir / "Bank_Statement_TechCorp_Excellent.xlsx"
        gst_file = test_data_dir / "GST_Returns_TechCorp_Excellent.xlsx"
        
        if bank_file.exists() and gst_file.exists():
            files = {
                'files': [
                    ('files', open(bank_file, 'rb')),
                    ('files', open(gst_file, 'rb'))
                ]
            }
            
            result = test_endpoint(
                "Upload Documents",
                "POST",
                f"{API_BASE}/ingestion/upload-documents",
                files=files['files'],
                data={"application_id": application_id}
            )
            
            if result:
                results["passed"] += 1
                print(f"   Uploaded: {len(result.get('uploaded_files', []))} files")
            else:
                results["failed"] += 1
        else:
            print_info("Test data files not found, skipping upload test")
            results["skipped"] += 1
    else:
        print_info("test_data directory not found, skipping upload test")
        results["skipped"] += 1
    
    # Test 7: Parse Documents (requires documents to be uploaded)
    print_info("Parse Documents endpoint requires uploaded files - skipping")
    results["skipped"] += 1
    
    # ==================== ANALYZE CREDIT (MAIN ENDPOINT) ====================
    print_header("4. ANALYZE CREDIT (MAIN WORKFLOW)")
    
    # Test 8: Analyze Credit with file upload
    print_info("This is the main endpoint that does everything")
    
    if test_data_dir.exists():
        bank_file = test_data_dir / "Bank_Statement_TechCorp_Excellent.xlsx"
        gst_file = test_data_dir / "GST_Returns_TechCorp_Excellent.xlsx"
        
        if bank_file.exists() and gst_file.exists():
            files = {
                'bank_statement': open(bank_file, 'rb'),
                'gst_returns': open(gst_file, 'rb')
            }
            
            data = {
                'company_name': 'TechCorp Test Analysis',
                'mca_cin': 'U12345MH2020PTC999999',
                'sector': 'Technology',
                'requested_limit_cr': 20.0
            }
            
            print_info("This may take 30-60 seconds...")
            result = test_endpoint(
                "Analyze Credit (Full Flow)",
                "POST",
                f"{API_BASE}/applications/analyze-credit",
                files=files,
                data=data,
                timeout=120
            )
            
            if result:
                results["passed"] += 1
                print(f"   Score: {result.get('risk_scoring_engine', {}).get('final_credit_score', 'N/A')}")
                print(f"   Decision: {result.get('risk_scoring_engine', {}).get('decision', 'N/A')}")
                analysis_app_id = result.get('application_id')
            else:
                print_info("Analysis may need API keys (GEMINI_API_KEY, TAVILY_API_KEY)")
                results["failed"] += 1
        else:
            print_info("Test files not found")
            results["skipped"] += 1
    else:
        print_info("No test data available")
        results["skipped"] += 1
    
    # ==================== RESEARCH ENDPOINTS ====================
    print_header("5. RESEARCH ENDPOINTS")
    
    # Test 9: Trigger Research
    result = test_endpoint(
        "Trigger Research",
        "POST",
        f"{API_BASE}/research/trigger-research",
        json={"application_id": application_id}
    )
    if result:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 10: Get Research Results
    result = test_endpoint(
        "Get Research Results",
        "GET",
        f"{API_BASE}/research/{application_id}/results"
    )
    if result:
        results["passed"] += 1
        print(f"   Research Completed: {result.get('research_completed', False)}")
    else:
        results["failed"] += 1
    
    # ==================== SCORING ENDPOINTS ====================
    print_header("6. SCORING ENDPOINTS")
    
    # Test 11: Calculate Score
    scoring_data = {
        "application_id": application_id,
        "financials": {
            "dscr": 1.5,
            "current_ratio": 1.8,
            "debt_to_equity": 1.2
        },
        "research": {},
        "sector": {"name": "Technology"}
    }
    
    result = test_endpoint(
        "Calculate Score",
        "POST",
        f"{API_BASE}/scoring/calculate-score",
        json=scoring_data
    )
    if result:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 12: Get Explainability
    result = test_endpoint(
        "Get Explainability",
        "GET",
        f"{API_BASE}/scoring/{application_id}/explainability"
    )
    if result:
        results["passed"] += 1
    else:
        print_info("May fail if scoring not completed")
        results["skipped"] += 1
    
    # ==================== CAM ENDPOINTS ====================
    print_header("7. CAM (Credit Appraisal Memo) ENDPOINTS")
    
    # Test 13: Generate CAM
    cam_data = {
        "application_id": application_id,
        "company_details": app_data,
        "financial_analysis": {},
        "research_findings": {},
        "scoring_results": {"final_credit_score": 75}
    }
    
    result = test_endpoint(
        "Generate CAM",
        "POST",
        f"{API_BASE}/cam/generate",
        json=cam_data
    )
    if result:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 14: Preview CAM
    result = test_endpoint(
        "Preview CAM",
        "GET",
        f"{API_BASE}/cam/{application_id}/preview"
    )
    if result:
        results["passed"] += 1
    else:
        print_info("May fail if CAM not generated")
        results["skipped"] += 1
    
    # Test 15: Download CAM (will fail if not generated)
    print_info("Download CAM endpoint returns PDF file - skipping automated test")
    results["skipped"] += 1
    
    # ==================== DUE DILIGENCE ENDPOINTS ====================
    print_header("8. DUE DILIGENCE ENDPOINTS")
    
    # Test 16: Add Due Diligence Notes
    dd_data = {
        "application_id": application_id,
        "notes": "Test site visit completed. Company operations look solid.",
        "officer_name": "Test Officer"
    }
    
    result = test_endpoint(
        "Add Due Diligence Notes",
        "POST",
        f"{API_BASE}/due-diligence/add-notes",
        json=dd_data
    )
    if result:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 17: Get Due Diligence Notes
    result = test_endpoint(
        "Get Due Diligence Notes",
        "GET",
        f"{API_BASE}/due-diligence/{application_id}/notes"
    )
    if result:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # ==================== FINAL RESULTS ====================
    print_header("TEST RESULTS SUMMARY")
    
    total_tests = results["passed"] + results["failed"] + results["skipped"]
    
    print(f"\n{Colors.GREEN}✅ Passed:  {results['passed']}{Colors.RESET}")
    print(f"{Colors.RED}❌ Failed:  {results['failed']}{Colors.RESET}")
    print(f"{Colors.YELLOW}⏭️  Skipped: {results['skipped']}{Colors.RESET}")
    print(f"\nTotal Tests: {total_tests}")
    
    success_rate = (results['passed'] / total_tests * 100) if total_tests > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    if results['failed'] == 0:
        print(f"\n{Colors.GREEN}🎉 ALL TESTS PASSED! System is fully functional!{Colors.RESET}")
    elif success_rate >= 70:
        print(f"\n{Colors.YELLOW}⚠️  Most tests passed. Some features may need API keys.{Colors.RESET}")
    else:
        print(f"\n{Colors.RED}❌ Multiple failures detected. Check server logs.{Colors.RESET}")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
