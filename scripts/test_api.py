"""
API Testing Script
Comprehensive tests for all Flask API endpoints
"""

import requests
import time
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

API_BASE_URL = 'http://localhost:5000'

# ANSI color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_test(name, status, message=''):
    """Print test result with color"""
    check = '[PASS]' if status else '[FAIL]'
    if status:
        print(f"{GREEN}{check}{RESET} {name}")
        if message:
            print(f"  {message}")
    else:
        print(f"{RED}{check}{RESET} {name}")
        if message:
            print(f"  {RED}{message}{RESET}")


def print_section(title):
    """Print section header"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")


def test_api_root():
    """Test API root endpoint"""
    print_section("Testing API Root Endpoint")
    
    try:
        response = requests.get(f'{API_BASE_URL}/')
        
        if response.status_code == 200:
            data = response.json()
            print_test("GET /", True, f"API: {data.get('name', 'N/A')}")
            return True
        else:
            print_test("GET /", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("GET /", False, f"Error: {str(e)}")
        return False


def test_health_endpoint():
    """Test health check endpoint"""
    print_section("Testing Health Check Endpoint")
    
    try:
        response = requests.get(f'{API_BASE_URL}/api/health')
        
        if response.status_code in [200, 503]:
            data = response.json()
            status = data.get('status', 'unknown')
            components = data.get('components', {})
            
            print_test("GET /api/health", True, f"Status: {status}")
            print(f"  Components:")
            for comp, comp_status in components.items():
                color = GREEN if comp_status == 'healthy' else YELLOW
                print(f"    - {comp}: {color}{comp_status}{RESET}")
            return True
        else:
            print_test("GET /api/health", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("GET /api/health", False, f"Error: {str(e)}")
        return False


def test_regulations_endpoint():
    """Test regulations list endpoint"""
    print_section("Testing Regulations Endpoint")
    
    try:
        response = requests.get(f'{API_BASE_URL}/api/regulations')
        
        if response.status_code == 200:
            data = response.json()
            regulations = data.get('regulations', [])
            print_test("GET /api/regulations", True, 
                      f"Found {len(regulations)} regulations")
            
            # Print first few regulations
            for reg in regulations[:3]:
                print(f"  - {reg['name']} ({reg['id']})")
            
            return True
        else:
            print_test("GET /api/regulations", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("GET /api/regulations", False, f"Error: {str(e)}")
        return False


def test_analyze_endpoint(test_repo_url='https://github.com/octocat/Hello-World'):
    """Test repository analysis endpoint"""
    print_section("Testing Analysis Endpoint")
    
    print(f"{YELLOW}Note: This will start a real analysis. It may take a few minutes.{RESET}")
    print(f"Testing with repository: {test_repo_url}\n")
    
    try:
        # Start analysis
        print("Starting analysis...")
        response = requests.post(
            f'{API_BASE_URL}/api/analyze',
            json={'github_url': test_repo_url},
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 202:
            data = response.json()
            analysis_id = data.get('analysis_id')
            print_test("POST /api/analyze", True, f"Analysis ID: {analysis_id}")
            
            # Test status polling
            return test_status_polling(analysis_id)
        else:
            print_test("POST /api/analyze", False, 
                      f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        print_test("POST /api/analyze", False, f"Error: {str(e)}")
        return False


def test_status_polling(analysis_id, max_wait=300):
    """Test status polling for an analysis"""
    print("\nPolling analysis status...")
    
    start_time = time.time()
    last_progress = -1
    
    try:
        while time.time() - start_time < max_wait:
            response = requests.get(f'{API_BASE_URL}/api/status/{analysis_id}')
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                progress = data.get('progress', 0)
                message = data.get('message', '')
                
                # Print progress updates
                if progress != last_progress:
                    print(f"  Progress: {progress}% - {message}")
                    last_progress = progress
                
                if status == 'completed':
                    print_test("Analysis completed", True)
                    return test_results_endpoint(analysis_id)
                elif status == 'failed':
                    error = data.get('error', 'Unknown error')
                    print_test("Analysis failed", False, error)
                    return False
                
                time.sleep(2)  # Poll every 2 seconds
            else:
                print_test("GET /api/status", False, f"Status: {response.status_code}")
                return False
        
        print_test("Analysis timeout", False, f"Exceeded {max_wait}s")
        return False
        
    except Exception as e:
        print_test("Status polling", False, f"Error: {str(e)}")
        return False


def test_results_endpoint(analysis_id):
    """Test results retrieval endpoint"""
    print_section("Testing Results Endpoint")
    
    try:
        response = requests.get(f'{API_BASE_URL}/api/results/{analysis_id}')
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', {})
            summary = results.get('summary', {})
            
            print_test("GET /api/results", True)
            print(f"  Files analyzed: {summary.get('files_analyzed', 0)}")
            print(f"  Total issues: {summary.get('total_issues', 0)}")
            print(f"  Critical: {summary.get('critical_issues', 0)}")
            print(f"  High: {summary.get('high_issues', 0)}")
            print(f"  Medium: {summary.get('medium_issues', 0)}")
            print(f"  Low: {summary.get('low_issues', 0)}")
            
            # Test report downloads
            return test_report_downloads(analysis_id)
        else:
            print_test("GET /api/results", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_test("GET /api/results", False, f"Error: {str(e)}")
        return False


def test_report_downloads(analysis_id):
    """Test report download endpoints"""
    print_section("Testing Report Downloads")
    
    formats = ['json', 'html', 'markdown', 'text']
    all_passed = True
    
    for fmt in formats:
        try:
            response = requests.get(f'{API_BASE_URL}/api/reports/{analysis_id}/{fmt}')
            
            if response.status_code == 200:
                size = len(response.content)
                print_test(f"GET /api/reports/.../{ fmt}", True, f"Size: {size} bytes")
            else:
                print_test(f"GET /api/reports/.../{fmt}", False, 
                          f"Status: {response.status_code}")
                all_passed = False
                
        except Exception as e:
            print_test(f"GET /api/reports/.../{fmt}", False, f"Error: {str(e)}")
            all_passed = False
    
    return all_passed


def test_history_endpoint():
    """Test analysis history endpoint"""
    print_section("Testing History Endpoint")
    
    try:
        response = requests.get(f'{API_BASE_URL}/api/history?limit=5')
        
        if response.status_code == 200:
            data = response.json()
            analyses = data.get('analyses', [])
            print_test("GET /api/history", True, f"Found {len(analyses)} analyses")
            
            for analysis in analyses[:3]:
                print(f"  - {analysis.get('repository_url', 'N/A')} "
                      f"({analysis.get('status', 'N/A')})")
            
            return True
        else:
            print_test("GET /api/history", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_test("GET /api/history", False, f"Error: {str(e)}")
        return False


def test_error_handling():
    """Test error handling"""
    print_section("Testing Error Handling")
    
    tests_passed = 0
    total_tests = 0
    
    # Test invalid endpoint
    total_tests += 1
    try:
        response = requests.get(f'{API_BASE_URL}/api/invalid')
        if response.status_code == 404:
            print_test("404 handling", True)
            tests_passed += 1
        else:
            print_test("404 handling", False, f"Expected 404, got {response.status_code}")
    except Exception as e:
        print_test("404 handling", False, str(e))
    
    # Test invalid analysis ID
    total_tests += 1
    try:
        response = requests.get(f'{API_BASE_URL}/api/status/invalid-id')
        if response.status_code == 404:
            print_test("Invalid analysis ID handling", True)
            tests_passed += 1
        else:
            print_test("Invalid analysis ID handling", False, 
                      f"Expected 404, got {response.status_code}")
    except Exception as e:
        print_test("Invalid analysis ID handling", False, str(e))
    
    # Test missing required field
    total_tests += 1
    try:
        response = requests.post(
            f'{API_BASE_URL}/api/analyze',
            json={},
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code == 400:
            print_test("Missing field validation", True)
            tests_passed += 1
        else:
            print_test("Missing field validation", False, 
                      f"Expected 400, got {response.status_code}")
    except Exception as e:
        print_test("Missing field validation", False, str(e))
    
    # Test invalid GitHub URL
    total_tests += 1
    try:
        response = requests.post(
            f'{API_BASE_URL}/api/analyze',
            json={'github_url': 'not-a-github-url'},
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code == 400:
            print_test("Invalid URL validation", True)
            tests_passed += 1
        else:
            print_test("Invalid URL validation", False, 
                      f"Expected 400, got {response.status_code}")
    except Exception as e:
        print_test("Invalid URL validation", False, str(e))
    
    return tests_passed == total_tests


def run_all_tests(include_analysis=False):
    """Run all API tests"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Compliance Guardian API Test Suite{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"\nAPI Base URL: {API_BASE_URL}\n")
    
    results = []
    
    # Basic endpoint tests
    results.append(("API Root", test_api_root()))
    results.append(("Health Check", test_health_endpoint()))
    results.append(("Regulations List", test_regulations_endpoint()))
    results.append(("Error Handling", test_error_handling()))
    
    # Optional: Full analysis test (takes time)
    if include_analysis:
        results.append(("Full Analysis Flow", test_analyze_endpoint()))
    else:
        print(f"\n{YELLOW}Skipping full analysis test (use --full to include){RESET}")
    
    # History test (should work even without running analysis)
    results.append(("History", test_history_endpoint()))
    
    # Print summary
    print_section("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{GREEN}PASSED{RESET}" if result else f"{RED}FAILED{RESET}"
        print(f"  {name}: {status}")
    
    print(f"\n{BLUE}Total: {passed}/{total} tests passed{RESET}")
    
    if passed == total:
        print(f"{GREEN}All tests passed!{RESET}\n")
        return 0
    else:
        print(f"{RED}Some tests failed.{RESET}\n")
        return 1


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Compliance Guardian API')
    parser.add_argument('--full', action='store_true', 
                       help='Include full analysis test (takes several minutes)')
    parser.add_argument('--url', default='http://localhost:5000',
                       help='API base URL (default: http://localhost:5000)')
    
    args = parser.parse_args()
    API_BASE_URL = args.url
    
    exit_code = run_all_tests(include_analysis=args.full)
    sys.exit(exit_code)

# Made with Bob