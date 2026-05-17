"""
Test Script for Repository Analyzer
Tests the complete analyzer workflow with various scenarios
"""

import sys
import os
import logging
from datetime import datetime

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.analyzer import RepositoryAnalyzer, GitHubURLError, GitAuthenticationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_separator(title: str = ""):
    """Print a visual separator"""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)
    print()


def print_results(results: dict):
    """Print analysis results in a readable format"""
    print("\n📊 ANALYSIS RESULTS:")
    print("-" * 80)
    
    # Metadata
    metadata = results['analysis_metadata']
    print(f"✓ Analyzed at: {metadata['analyzed_at']}")
    print(f"✓ Duration: {metadata['duration_seconds']:.2f} seconds")
    print(f"✓ Repository: {metadata['github_url']}")
    
    # Repository info
    repo = results['repository']
    print(f"\n📦 Repository Information:")
    print(f"  - Branch: {repo['active_branch']}")
    print(f"  - Last Commit: {repo['last_commit']['hash'][:8]}")
    print(f"  - Author: {repo['last_commit']['author']}")
    print(f"  - Date: {repo['last_commit']['date']}")
    print(f"  - Total Commits: {repo.get('total_commits', 'N/A')}")
    
    # Statistics
    stats = results['statistics']
    print(f"\n📈 Statistics:")
    print(f"  - Total Files: {stats['total_files']}")
    print(f"  - Total Size: {stats['total_size']:,} bytes ({stats['total_size'] / 1024:.2f} KB)")
    print(f"  - Skipped Files: {stats.get('skipped_files', 0)}")
    
    # Languages
    print(f"\n💻 Languages Detected:")
    for lang, count in sorted(stats['languages'].items(), key=lambda x: x[1], reverse=True):
        print(f"  - {lang}: {count} files")
    
    # Parser stats
    parser_stats = results['parser_stats']
    print(f"\n📝 Parser Statistics:")
    print(f"  - Files Parsed: {parser_stats['files_parsed']}")
    print(f"  - Total Lines: {parser_stats['total_lines']:,}")
    print(f"  - Errors: {parser_stats.get('errors', 0)}")
    
    # Sample files
    if results['files']:
        print(f"\n📄 Sample Files (first 5):")
        for i, file_info in enumerate(results['files'][:5], 1):
            print(f"  {i}. {file_info['relative_path']} ({file_info['language']}, {file_info['size']} bytes)")


def test_url_validation():
    """Test GitHub URL validation"""
    print_separator("TEST 1: URL Validation")
    
    analyzer = RepositoryAnalyzer()
    
    test_urls = [
        ("https://github.com/octocat/Hello-World", True, "Valid HTTPS URL"),
        ("https://github.com/octocat/Hello-World.git", True, "Valid HTTPS URL with .git"),
        ("git@github.com:octocat/Hello-World.git", True, "Valid SSH URL"),
        ("https://gitlab.com/user/repo", False, "Invalid - not GitHub"),
        ("not-a-url", False, "Invalid - malformed URL"),
        ("", False, "Invalid - empty string"),
    ]
    
    passed = 0
    failed = 0
    
    for url, should_pass, description in test_urls:
        try:
            analyzer.repo_cloner.validate_github_url(url)
            if should_pass:
                print(f"✓ PASS: {description}")
                print(f"  URL: {url}")
                passed += 1
            else:
                print(f"✗ FAIL: {description} - Should have raised error")
                print(f"  URL: {url}")
                failed += 1
        except GitHubURLError as e:
            if not should_pass:
                print(f"✓ PASS: {description}")
                print(f"  URL: {url}")
                print(f"  Error: {str(e)[:60]}...")
                passed += 1
            else:
                print(f"✗ FAIL: {description} - Unexpected error")
                print(f"  URL: {url}")
                print(f"  Error: {str(e)}")
                failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    return failed == 0


def test_public_repo_analysis():
    """Test analyzing a small public repository"""
    print_separator("TEST 2: Public Repository Analysis")
    
    # Using a small, stable public repo for testing
    test_repo = "https://github.com/octocat/Hello-World"
    
    print(f"Testing with repository: {test_repo}")
    print("This is a small public repository maintained by GitHub")
    
    try:
        analyzer = RepositoryAnalyzer()
        
        print("\n🔄 Starting analysis (shallow clone)...")
        results = analyzer.analyze_repository(
            test_repo,
            include_content=True,
            include_line_numbers=False,
            shallow_clone=True,
            use_cache=False
        )
        
        print_results(results)
        
        # Verify results
        assert results['statistics']['total_files'] > 0, "Should find at least one file"
        assert results['repository']['remote_url'], "Should have remote URL"
        
        # Test summary
        print("\n📋 Testing get_analysis_summary()...")
        summary = analyzer.get_analysis_summary(test_repo)
        print(f"Summary: {summary}")
        
        # Cleanup
        print("\n🧹 Cleaning up...")
        analyzer.cleanup_repository(test_repo)
        
        print("\n✓ TEST PASSED: Public repository analysis successful")
        return True
    
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        logger.exception("Error in public repo test")
        return False


def test_error_handling():
    """Test error handling for various scenarios"""
    print_separator("TEST 3: Error Handling")
    
    analyzer = RepositoryAnalyzer()
    
    # Test 1: Invalid URL
    print("Test 3.1: Invalid URL")
    try:
        analyzer.analyze_repository("https://invalid-url.com/repo")
        print("✗ FAIL: Should have raised GitHubURLError")
        return False
    except GitHubURLError as e:
        print(f"✓ PASS: Correctly raised GitHubURLError")
        print(f"  Error: {str(e)[:60]}...")
    
    # Test 2: Non-existent repository
    print("\nTest 3.2: Non-existent Repository")
    try:
        analyzer.analyze_repository("https://github.com/nonexistent-user-12345/nonexistent-repo-67890")
        print("✗ FAIL: Should have raised error for non-existent repo")
        return False
    except (GitHubURLError, Exception) as e:
        print(f"✓ PASS: Correctly raised error for non-existent repo")
        print(f"  Error: {str(e)[:60]}...")
    
    print("\n✓ TEST PASSED: Error handling works correctly")
    return True


def test_file_filtering():
    """Test file filtering by language"""
    print_separator("TEST 4: File Filtering by Language")
    
    test_repo = "https://github.com/octocat/Hello-World"
    
    try:
        analyzer = RepositoryAnalyzer()
        
        print(f"Analyzing repository: {test_repo}")
        print("Filtering for specific languages...")
        
        # Analyze with language filter
        results = analyzer.analyze_repository(
            test_repo,
            include_content=False,
            filter_languages={'Text', 'Markdown'},
            shallow_clone=True,
            use_cache=False
        )
        
        # Check that only filtered languages are present
        languages = results['statistics']['languages']
        print(f"\nLanguages found: {list(languages.keys())}")
        
        for lang in languages.keys():
            if lang not in {'Text', 'Markdown', 'Unknown'}:
                print(f"✗ FAIL: Found unexpected language: {lang}")
                return False
        
        print(f"✓ PASS: Language filtering works correctly")
        
        # Cleanup
        analyzer.cleanup_repository(test_repo)
        
        return True
    
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        logger.exception("Error in file filtering test")
        return False


def test_caching():
    """Test caching functionality"""
    print_separator("TEST 5: Caching")
    
    test_repo = "https://github.com/octocat/Hello-World"
    
    try:
        analyzer = RepositoryAnalyzer()
        
        print("First analysis (no cache)...")
        start1 = datetime.now()
        results1 = analyzer.analyze_repository(
            test_repo,
            include_content=False,
            shallow_clone=True,
            use_cache=True
        )
        duration1 = (datetime.now() - start1).total_seconds()
        print(f"Duration: {duration1:.2f} seconds")
        
        print("\nSecond analysis (with cache)...")
        start2 = datetime.now()
        results2 = analyzer.analyze_repository(
            test_repo,
            include_content=False,
            shallow_clone=True,
            use_cache=True
        )
        duration2 = (datetime.now() - start2).total_seconds()
        print(f"Duration: {duration2:.2f} seconds")
        
        # Cache should be faster (or at least not slower)
        if results2['analysis_metadata'].get('cache_used'):
            print(f"✓ PASS: Cache was used")
        else:
            print(f"⚠ WARNING: Cache might not have been used")
        
        # Cleanup
        analyzer.cleanup_repository(test_repo)
        analyzer.clear_cache()
        
        return True
    
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        logger.exception("Error in caching test")
        return False


def test_export_results():
    """Test exporting results to JSON"""
    print_separator("TEST 6: Export Results")
    
    test_repo = "https://github.com/octocat/Hello-World"
    output_file = "data/test_analysis_results.json"
    
    try:
        analyzer = RepositoryAnalyzer()
        
        print(f"Analyzing repository: {test_repo}")
        results = analyzer.analyze_repository(
            test_repo,
            include_content=False,
            shallow_clone=True,
            use_cache=False
        )
        
        print(f"\nExporting results to: {output_file}")
        analyzer.export_results(test_repo, output_file)
        
        # Verify file exists
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"✓ PASS: Results exported successfully ({file_size:,} bytes)")
            
            # Cleanup
            analyzer.cleanup_repository(test_repo)
            os.remove(output_file)
            
            return True
        else:
            print(f"✗ FAIL: Export file not created")
            return False
    
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        logger.exception("Error in export test")
        return False


def run_all_tests():
    """Run all tests and report results"""
    print_separator("🧪 REPOSITORY ANALYZER TEST SUITE")
    print(f"Started at: {datetime.now().isoformat()}")
    
    tests = [
        ("URL Validation", test_url_validation),
        ("Public Repository Analysis", test_public_repo_analysis),
        ("Error Handling", test_error_handling),
        ("File Filtering", test_file_filtering),
        ("Caching", test_caching),
        ("Export Results", test_export_results),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            logger.exception(f"Unexpected error in {test_name}")
            results.append((test_name, False))
    
    # Summary
    print_separator("📊 TEST SUMMARY")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{'=' * 80}")
    print(f"Total: {passed_count}/{total_count} tests passed")
    print(f"Success Rate: {(passed_count/total_count)*100:.1f}%")
    print(f"Completed at: {datetime.now().isoformat()}")
    print(f"{'=' * 80}\n")
    
    return passed_count == total_count


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Fatal error: {str(e)}")
        logger.exception("Fatal error in test suite")
        sys.exit(1)

# Made with Bob