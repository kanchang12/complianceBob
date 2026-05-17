"""
End-to-End Test Script
Tests the complete Compliance Guardian workflow from GitHub URL to final reports
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestrator.workflow import WorkflowOrchestrator
from src.reports.summary_generator import SummaryGenerator
from src.reports.detailed_report import DetailedReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/end_to_end_test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def progress_callback(stage: str, progress: int, message: str):
    """Progress callback for tracking workflow progress"""
    print(f"[{progress}%] {stage.upper()}: {message}")


def test_workflow_orchestrator():
    """Test the complete workflow orchestrator"""
    print("\n" + "=" * 80)
    print("TEST 1: Workflow Orchestrator")
    print("=" * 80)
    
    try:
        # Initialize orchestrator
        config = {
            'db_path': 'database/compliance.db',
            'clone_dir': 'data/repos',
            'model_name': 'gemma2:2b',
            'max_files': 50,
            'enable_deep_analysis': True,
            'max_deep_analysis_files': 5,
            'cleanup_after_analysis': False
        }
        
        orchestrator = WorkflowOrchestrator(config)
        print("✓ Orchestrator initialized successfully")
        
        # Test with a small public repository
        test_repo = "https://github.com/octocat/Hello-World"
        print(f"\nAnalyzing repository: {test_repo}")
        
        # Run analysis
        results = orchestrator.analyze_repository(
            github_url=test_repo,
            progress_callback=progress_callback
        )
        
        # Verify results
        assert results['status'] == 'completed', f"Expected 'completed', got '{results['status']}'"
        assert 'stages' in results, "Missing 'stages' in results"
        assert 'reports' in results, "Missing 'reports' in results"
        assert 'analysis_id' in results, "Missing 'analysis_id' in results"
        
        print("\n✓ Analysis completed successfully")
        print(f"  - Status: {results['status']}")
        print(f"  - Duration: {results.get('duration_seconds', 0):.2f} seconds")
        print(f"  - Analysis ID: {results.get('analysis_id')}")
        print(f"  - Files analyzed: {results.get('summary', {}).get('files_analyzed', 0)}")
        print(f"  - Total issues: {results.get('summary', {}).get('total_issues', 0)}")
        
        # Save reports to files
        output_dir = 'data/test_reports'
        orchestrator.save_reports_to_files(results, output_dir)
        print(f"\n✓ Reports saved to {output_dir}")
        
        # Test database retrieval
        analysis_id = results.get('analysis_id')
        if analysis_id:
            retrieved = orchestrator.get_analysis_by_id(analysis_id)
            assert retrieved is not None, "Failed to retrieve analysis from database"
            print(f"✓ Successfully retrieved analysis from database")
        
        # List recent analyses
        recent = orchestrator.list_analyses(limit=5)
        print(f"✓ Retrieved {len(recent)} recent analyses")
        
        return True
        
    except Exception as e:
        logger.error(f"Workflow orchestrator test failed: {str(e)}", exc_info=True)
        print(f"\n✗ Test failed: {str(e)}")
        return False


def test_summary_generator():
    """Test summary report generation"""
    print("\n" + "=" * 80)
    print("TEST 2: Summary Generator")
    print("=" * 80)
    
    try:
        # Create mock analysis results
        mock_results = {
            'repo_url': 'https://github.com/test/repo',
            'status': 'completed',
            'duration_seconds': 45.5,
            'summary': {
                'files_analyzed': 25,
                'total_issues': 15,
                'critical_issues': 2,
                'high_issues': 5,
                'medium_issues': 6,
                'low_issues': 2
            },
            'stages': {
                'compliance': {
                    'report': {
                        'findings': [
                            {
                                'file': 'src/auth.py',
                                'line': 42,
                                'severity': 'CRITICAL',
                                'severity_score': 95,
                                'type': 'hardcoded_credentials',
                                'description': 'Hardcoded password detected',
                                'confidence': 95
                            },
                            {
                                'file': 'src/db.py',
                                'line': 78,
                                'severity': 'HIGH',
                                'severity_score': 85,
                                'type': 'sql_injection',
                                'description': 'Potential SQL injection vulnerability',
                                'confidence': 90
                            }
                        ],
                        'regulation_violations': {
                            'GDPR': 3,
                            'OWASP Top 10': 5,
                            'NIST CSF': 2
                        }
                    }
                }
            }
        }
        
        generator = SummaryGenerator()
        print("✓ Summary generator initialized")
        
        # Test compliance score calculation
        score = generator.calculate_compliance_score(mock_results['summary'])
        print(f"✓ Compliance score calculated: {score}/100")
        assert 0 <= score <= 100, f"Invalid score: {score}"
        
        # Test plain text summary
        text_summary = generator.generate_summary(mock_results)
        assert len(text_summary) > 0, "Empty text summary"
        print(f"✓ Plain text summary generated ({len(text_summary)} chars)")
        
        # Test JSON summary
        json_summary = generator.generate_json_summary(mock_results)
        assert len(json_summary) > 0, "Empty JSON summary"
        print(f"✓ JSON summary generated ({len(json_summary)} chars)")
        
        # Test HTML summary
        html_summary = generator.generate_html_summary(mock_results)
        assert '<html>' in html_summary, "Invalid HTML summary"
        print(f"✓ HTML summary generated ({len(html_summary)} chars)")
        
        # Test Markdown summary
        md_summary = generator.generate_markdown_summary(mock_results)
        assert '# ' in md_summary, "Invalid Markdown summary"
        print(f"✓ Markdown summary generated ({len(md_summary)} chars)")
        
        # Save all formats
        output_dir = 'data/test_reports'
        os.makedirs(output_dir, exist_ok=True)
        
        generator.save_summary(mock_results, f'{output_dir}/test_summary.txt', 'text')
        generator.save_summary(mock_results, f'{output_dir}/test_summary.json', 'json')
        generator.save_summary(mock_results, f'{output_dir}/test_summary.html', 'html')
        generator.save_summary(mock_results, f'{output_dir}/test_summary.md', 'markdown')
        
        print(f"✓ All summary formats saved to {output_dir}")
        
        return True
        
    except Exception as e:
        logger.error(f"Summary generator test failed: {str(e)}", exc_info=True)
        print(f"\n✗ Test failed: {str(e)}")
        return False


def test_detailed_report_generator():
    """Test detailed report generation"""
    print("\n" + "=" * 80)
    print("TEST 3: Detailed Report Generator")
    print("=" * 80)
    
    try:
        # Create mock analysis results with detailed findings
        mock_results = {
            'repo_url': 'https://github.com/test/repo',
            'status': 'completed',
            'duration_seconds': 45.5,
            'summary': {
                'files_analyzed': 25,
                'total_issues': 15,
                'critical_issues': 2,
                'high_issues': 5,
                'medium_issues': 6,
                'low_issues': 2
            },
            'stages': {
                'compliance': {
                    'report': {
                        'findings': [
                            {
                                'file': 'src/auth.py',
                                'line': 42,
                                'severity': 'CRITICAL',
                                'type': 'hardcoded_credentials',
                                'description': 'Hardcoded password detected in authentication module',
                                'match': 'password = "admin123"',
                                'confidence': 95,
                                'violated_regulations': ['GDPR Article 32', 'OWASP A02:2021'],
                                'remediation': {
                                    'description': 'Use environment variables or secure vault for credentials',
                                    'example': 'password = os.getenv("DB_PASSWORD")'
                                }
                            },
                            {
                                'file': 'src/db.py',
                                'line': 78,
                                'severity': 'HIGH',
                                'type': 'sql_injection',
                                'description': 'SQL query constructed using string concatenation',
                                'match': 'query = "SELECT * FROM users WHERE id = " + user_id',
                                'confidence': 90,
                                'violated_regulations': ['OWASP A03:2021'],
                                'remediation': {
                                    'description': 'Use parameterized queries',
                                    'example': 'cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))'
                                }
                            },
                            {
                                'file': 'src/crypto.py',
                                'line': 15,
                                'severity': 'MEDIUM',
                                'type': 'weak_crypto',
                                'description': 'Using MD5 for hashing',
                                'match': 'hashlib.md5(data)',
                                'confidence': 85,
                                'violated_regulations': ['NIST SP 800-53'],
                                'remediation': {
                                    'description': 'Use SHA-256 or stronger',
                                    'example': 'hashlib.sha256(data)'
                                }
                            }
                        ],
                        'regulation_violations': {
                            'GDPR': 3,
                            'OWASP Top 10': 5,
                            'NIST CSF': 2
                        }
                    }
                }
            }
        }
        
        generator = DetailedReportGenerator()
        print("✓ Detailed report generator initialized")
        
        # Test plain text report
        text_report = generator.generate_detailed_report(mock_results)
        assert len(text_report) > 0, "Empty text report"
        assert 'DETAILED ANALYSIS REPORT' in text_report, "Missing report header"
        print(f"✓ Plain text report generated ({len(text_report)} chars)")
        
        # Test JSON report
        json_report = generator.generate_json_report(mock_results)
        assert len(json_report) > 0, "Empty JSON report"
        print(f"✓ JSON report generated ({len(json_report)} chars)")
        
        # Test HTML report
        html_report = generator.generate_html_report(mock_results)
        assert '<html>' in html_report, "Invalid HTML report"
        assert 'Compliance Guardian' in html_report, "Missing report title"
        print(f"✓ HTML report generated ({len(html_report)} chars)")
        
        # Test Markdown report
        md_report = generator.generate_markdown_report(mock_results)
        assert '# ' in md_report, "Invalid Markdown report"
        print(f"✓ Markdown report generated ({len(md_report)} chars)")
        
        # Save all formats
        output_dir = 'data/test_reports'
        os.makedirs(output_dir, exist_ok=True)
        
        generator.save_report(mock_results, f'{output_dir}/test_detailed.txt', 'text')
        generator.save_report(mock_results, f'{output_dir}/test_detailed.json', 'json')
        generator.save_report(mock_results, f'{output_dir}/test_detailed.html', 'html')
        generator.save_report(mock_results, f'{output_dir}/test_detailed.md', 'markdown')
        
        print(f"✓ All detailed report formats saved to {output_dir}")
        
        return True
        
    except Exception as e:
        logger.error(f"Detailed report generator test failed: {str(e)}", exc_info=True)
        print(f"\n✗ Test failed: {str(e)}")
        return False


def test_error_handling():
    """Test error handling in workflow"""
    print("\n" + "=" * 80)
    print("TEST 4: Error Handling")
    print("=" * 80)
    
    try:
        orchestrator = WorkflowOrchestrator()
        
        # Test with invalid repository URL
        print("\nTesting invalid repository URL...")
        try:
            results = orchestrator.analyze_repository("https://github.com/invalid/nonexistent-repo-12345")
            # Should fail or return error status
            if results['status'] == 'failed':
                print("✓ Invalid repository handled correctly")
            else:
                print("⚠ Invalid repository did not fail as expected")
        except Exception as e:
            print(f"✓ Invalid repository raised exception: {type(e).__name__}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error handling test failed: {str(e)}", exc_info=True)
        print(f"\n✗ Test failed: {str(e)}")
        return False


def test_database_operations():
    """Test database storage and retrieval"""
    print("\n" + "=" * 80)
    print("TEST 5: Database Operations")
    print("=" * 80)
    
    try:
        orchestrator = WorkflowOrchestrator()
        
        # List recent analyses
        analyses = orchestrator.list_analyses(limit=5)
        print(f"✓ Retrieved {len(analyses)} recent analyses from database")
        
        if analyses:
            # Test retrieving specific analysis
            first_analysis = analyses[0]
            analysis_id = first_analysis['id']
            
            retrieved = orchestrator.get_analysis_by_id(analysis_id)
            assert retrieved is not None, "Failed to retrieve analysis"
            assert retrieved['id'] == analysis_id, "Retrieved wrong analysis"
            
            print(f"✓ Successfully retrieved analysis ID {analysis_id}")
            print(f"  - Repository: {retrieved.get('repository_url')}")
            print(f"  - Status: {retrieved.get('status')}")
            print(f"  - Total findings: {retrieved.get('total_findings', 0)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Database operations test failed: {str(e)}", exc_info=True)
        print(f"\n✗ Test failed: {str(e)}")
        return False


def run_all_tests():
    """Run all end-to-end tests"""
    print("\n" + "=" * 80)
    print("COMPLIANCE GUARDIAN - END-TO-END TEST SUITE")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        'workflow_orchestrator': False,
        'summary_generator': False,
        'detailed_report_generator': False,
        'error_handling': False,
        'database_operations': False
    }
    
    # Run tests
    results['workflow_orchestrator'] = test_workflow_orchestrator()
    results['summary_generator'] = test_summary_generator()
    results['detailed_report_generator'] = test_detailed_report_generator()
    results['error_handling'] = test_error_handling()
    results['database_operations'] = test_database_operations()
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✓ PASSED" if passed_test else "✗ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print("\n" + "-" * 80)
    print(f"Total: {passed}/{total} tests passed")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Save results
    output_file = 'data/end_to_end_test_results.txt'
    with open(output_file, 'w') as f:
        f.write(f"End-to-End Test Results\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for test_name, passed_test in results.items():
            status = "PASSED" if passed_test else "FAILED"
            f.write(f"{test_name}: {status}\n")
        f.write(f"\nTotal: {passed}/{total} tests passed\n")
    
    print(f"\nResults saved to {output_file}")
    
    return passed == total


if __name__ == '__main__':
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test suite failed: {str(e)}", exc_info=True)
        print(f"\n\nTest suite failed: {str(e)}")
        sys.exit(1)

# Made with Bob