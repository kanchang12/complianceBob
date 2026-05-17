"""
Test Script for Compliance Checker
Tests quick scanner, deep analyzer, rules engine, and end-to-end compliance checking
"""

import sys
import os
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.checker import ComplianceChecker, QuickScanner, DeepAnalyzer, RulesEngine
from src.rag import VectorStore, Embedder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Sample code files with known violations
SAMPLE_FILES = {
    'vulnerable_auth.py': '''
# Authentication module with security issues
import hashlib
import random

# VIOLATION: Hardcoded password
DB_PASSWORD = "admin123"
API_KEY = "sk-1234567890abcdef"

def authenticate_user(username, password):
    # VIOLATION: MD5 usage
    password_hash = hashlib.md5(password.encode()).hexdigest()
    
    # VIOLATION: SQL injection via string concatenation
    query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password_hash + "'"
    
    return execute_query(query)

def generate_token():
    # VIOLATION: Weak random for security
    token = str(random.random())
    return token

def execute_query(query):
    # Mock function
    pass
''',
    
    'data_handler.py': '''
# Data handling with privacy issues
import logging

def process_user_data(user):
    # VIOLATION: Logging PII
    logging.info(f"Processing user: {user['email']}")
    logging.info(f"SSN: {user['ssn']}")
    
    # VIOLATION: Credit card in code
    test_card = "4532-1234-5678-9010"
    
    return user

def unsafe_deserialization(data):
    # VIOLATION: Unsafe eval
    result = eval(data)
    return result

def execute_command(cmd):
    # VIOLATION: Shell injection
    import os
    os.system(cmd)
''',
    
    'web_app.py': '''
# Web application with OWASP vulnerabilities
from flask import Flask, request

app = Flask(__name__)

@app.route('/search')
def search():
    query = request.args.get('q')
    # VIOLATION: XSS vulnerability
    return f"<html><body>Results for: {query}</body></html>"

@app.route('/file')
def get_file():
    filename = request.args.get('name')
    # VIOLATION: Path traversal
    with open(f"./files/{filename}", 'r') as f:
        return f.read()

@app.route('/api/data', methods=['POST'])
def api_endpoint():
    # VIOLATION: No authentication on POST endpoint
    data = request.json
    return {"status": "ok"}

# VIOLATION: Debug mode in production
if __name__ == '__main__':
    app.run(debug=True)
''',
    
    'crypto_utils.py': '''
# Cryptography utilities with weak algorithms
import hashlib
from Crypto.Cipher import DES

def hash_password(password):
    # VIOLATION: SHA1 usage
    return hashlib.sha1(password.encode()).hexdigest()

def encrypt_data(data, key):
    # VIOLATION: DES encryption
    cipher = DES.new(key, DES.MODE_ECB)
    return cipher.encrypt(data)

# VIOLATION: Hardcoded IV
INITIALIZATION_VECTOR = "1234567890abcdef"

def secure_hash(data):
    # Good practice - SHA256
    return hashlib.sha256(data.encode()).hexdigest()
''',
    
    'safe_code.py': '''
# Example of secure code
import os
import hashlib
from flask import Flask, request
from functools import wraps

app = Flask(__name__)

# Good: Environment variable
DB_PASSWORD = os.environ.get('DB_PASSWORD')
API_KEY = os.environ.get('API_KEY')

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Good: Authentication decorator
        token = request.headers.get('Authorization')
        if not verify_token(token):
            return {"error": "Unauthorized"}, 401
        return f(*args, **kwargs)
    return decorated

def hash_password(password):
    # Good: SHA256 usage
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/api/data', methods=['POST'])
@require_auth
def api_endpoint():
    # Good: Authentication required
    data = request.json
    return {"status": "ok"}

def verify_token(token):
    # Mock verification
    return True
'''
}


def create_test_files():
    """Create test files in a temporary directory"""
    test_dir = Path(__file__).parent.parent / 'data' / 'test_code'
    test_dir.mkdir(parents=True, exist_ok=True)
    
    created_files = []
    for filename, content in SAMPLE_FILES.items():
        file_path = test_dir / filename
        file_path.write_text(content)
        created_files.append({
            'path': str(file_path),
            'content': content,
            'name': filename
        })
        logger.info(f"Created test file: {filename}")
    
    return created_files


def test_quick_scanner():
    """Test the quick scanner"""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Quick Scanner")
    logger.info("="*60)
    
    scanner = QuickScanner()
    test_files = create_test_files()
    
    # Scan all files
    findings = scanner.scan_files_batch(test_files)
    
    logger.info(f"\nQuick scan found {len(findings)} potential issues")
    
    # Generate summary
    summary = scanner.generate_summary(findings)
    logger.info(f"\nSummary:")
    logger.info(f"  Total findings: {summary['total_findings']}")
    logger.info(f"  By severity: {summary['by_severity']}")
    logger.info(f"  By type: {summary['by_type']}")
    logger.info(f"  Affected files: {summary['affected_files']}")
    
    # Show sample findings
    logger.info(f"\nSample findings (first 5):")
    for i, finding in enumerate(findings[:5], 1):
        logger.info(f"\n  {i}. {finding['description']}")
        logger.info(f"     File: {Path(finding['file']).name}:{finding['line']}")
        logger.info(f"     Severity: {finding['severity']}")
        logger.info(f"     Type: {finding['type']}")
    
    return findings, test_files


def test_rules_engine(findings):
    """Test the rules engine"""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Rules Engine")
    logger.info("="*60)
    
    rules_engine = RulesEngine()
    
    # Test rule matching
    logger.info("\nTesting rule matching for sample findings:")
    for finding in findings[:3]:
        rule_match = rules_engine.match_rule_to_finding(finding)
        logger.info(f"\n  Pattern: {finding['pattern']}")
        logger.info(f"  Matched regulations: {len(rule_match['matched_regulations'])}")
        for reg in rule_match['matched_regulations'][:2]:
            logger.info(f"    - {reg['regulation']}: {reg['name']}")
    
    # Test severity scoring
    logger.info("\nTesting severity scoring:")
    for finding in findings[:3]:
        severity, score = rules_engine.calculate_severity_score(finding)
        logger.info(f"  {finding['pattern']}: {severity} (score: {score})")
    
    # Test remediation templates
    logger.info("\nTesting remediation templates:")
    for finding in findings[:3]:
        remediation = rules_engine.get_remediation_template(finding)
        logger.info(f"\n  {finding['pattern']}:")
        logger.info(f"    Title: {remediation['title']}")
        logger.info(f"    Priority: {remediation['priority']}")
        logger.info(f"    Steps: {len(remediation['steps'])} steps")
    
    # Test compliance validation
    logger.info("\nTesting compliance validation:")
    required_regs = ['OWASP', 'GDPR', 'PCI_DSS']
    validation = rules_engine.validate_compliance(findings, required_regs)
    logger.info(f"  Compliant: {validation['compliant']}")
    logger.info(f"  Critical violations: {validation['critical_violations']}")
    logger.info(f"  High violations: {validation['high_violations']}")
    logger.info(f"  Violations by regulation: {list(validation['violations_by_regulation'].keys())}")


def test_deep_analyzer(test_files, findings):
    """Test the deep analyzer"""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: Deep Analyzer")
    logger.info("="*60)
    
    # Initialize without RAG for testing
    analyzer = DeepAnalyzer(model_name="gemma2:2b")
    
    logger.info(f"\nDeep analyzer initialized")
    logger.info(f"  Ollama available: {analyzer.ollama_available}")
    logger.info(f"  Model: {analyzer.model_name}")
    
    # Get suspicious sections from first file
    scanner = QuickScanner()
    file_info = test_files[0]
    file_findings = [f for f in findings if Path(f['file']).name == file_info['name']]
    
    sections = scanner.get_suspicious_sections(file_findings[:3], file_info)
    logger.info(f"\nExtracted {len(sections)} suspicious sections")
    
    # Analyze sections
    if sections:
        logger.info("\nAnalyzing suspicious sections...")
        analyses = analyzer.analyze_sections_batch(sections[:2])  # Limit to 2 for testing
        
        logger.info(f"\nDeep analysis results: {len(analyses)} violations confirmed")
        
        for i, analysis in enumerate(analyses, 1):
            logger.info(f"\n  Analysis {i}:")
            logger.info(f"    File: {Path(analysis['file']).name}")
            logger.info(f"    Lines: {analysis['start_line']}-{analysis['end_line']}")
            logger.info(f"    Severity: {analysis['severity']}")
            logger.info(f"    Has violation: {analysis['has_violation']}")
            logger.info(f"    Confidence: {analysis['confidence']}%")
            logger.info(f"    AI powered: {analysis['ai_powered']}")
            if analysis.get('explanation'):
                logger.info(f"    Explanation: {analysis['explanation'][:100]}...")
    else:
        logger.info("\nNo suspicious sections to analyze")


def test_compliance_checker():
    """Test the complete compliance checker"""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: End-to-End Compliance Checker")
    logger.info("="*60)
    
    # Create test files
    test_files = create_test_files()
    
    # Initialize checker (without RAG for testing)
    checker = ComplianceChecker()
    
    logger.info("\nRunning comprehensive compliance check...")
    
    # Run compliance check
    report = checker.check_compliance(
        test_files,
        regulations=['OWASP', 'GDPR', 'PCI_DSS'],
        enable_deep_analysis=True,
        max_deep_analysis_files=2
    )
    
    # Display results
    logger.info("\n" + "="*60)
    logger.info("COMPLIANCE CHECK RESULTS")
    logger.info("="*60)
    
    metadata = report['metadata']
    logger.info(f"\nMetadata:")
    logger.info(f"  Duration: {metadata['duration_seconds']:.2f}s")
    logger.info(f"  Files analyzed: {metadata['total_files_analyzed']}")
    logger.info(f"  Affected files: {metadata['affected_files']}")
    logger.info(f"  Analysis phases: {metadata['analysis_phases']}")
    
    summary = report['summary']
    logger.info(f"\nSummary:")
    logger.info(f"  Total findings: {summary['total_findings']}")
    logger.info(f"  By severity:")
    for severity, count in summary['by_severity'].items():
        if count > 0:
            logger.info(f"    {severity}: {count}")
    logger.info(f"  Requires immediate action: {summary['requires_immediate_action']}")
    
    logger.info(f"\nTop 5 Critical/High Findings:")
    for i, finding in enumerate(report['findings'][:5], 1):
        logger.info(f"\n  {i}. [{finding['severity']}] {finding['description']}")
        logger.info(f"     File: {Path(finding['file']).name}:{finding['line']}")
        logger.info(f"     Pattern: {finding['pattern']}")
        logger.info(f"     Confidence: {finding['confidence']}%")
        if finding.get('remediation'):
            logger.info(f"     Remediation: {finding['remediation']['title']}")
    
    logger.info(f"\nRecommendations:")
    for i, rec in enumerate(report['recommendations'], 1):
        logger.info(f"  {i}. {rec}")
    
    if report.get('compliance_validation'):
        validation = report['compliance_validation']
        logger.info(f"\nCompliance Validation:")
        logger.info(f"  Compliant: {validation['compliant']}")
        logger.info(f"  Critical violations: {validation['critical_violations']}")
        logger.info(f"  High violations: {validation['high_violations']}")
    
    return report


def main():
    """Run all tests"""
    logger.info("="*60)
    logger.info("COMPLIANCE CHECKER TEST SUITE")
    logger.info("="*60)
    
    try:
        # Test 1: Quick Scanner
        findings, test_files = test_quick_scanner()
        
        # Test 2: Rules Engine
        test_rules_engine(findings)
        
        # Test 3: Deep Analyzer
        test_deep_analyzer(test_files, findings)
        
        # Test 4: End-to-End
        report = test_compliance_checker()
        
        logger.info("\n" + "="*60)
        logger.info("ALL TESTS COMPLETED SUCCESSFULLY")
        logger.info("="*60)
        
        # Save report
        import json
        report_path = Path(__file__).parent.parent / 'data' / 'test_checker_report.json'
        
        # Convert sets to lists for JSON serialization
        def convert_sets(obj):
            if isinstance(obj, set):
                return list(obj)
            elif isinstance(obj, dict):
                return {k: convert_sets(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_sets(item) for item in obj]
            return obj
        
        report_serializable = convert_sets(report)
        
        with open(report_path, 'w') as f:
            json.dump(report_serializable, f, indent=2)
        
        logger.info(f"\nDetailed report saved to: {report_path}")
        
    except Exception as e:
        logger.error(f"\nTest failed with error: {str(e)}", exc_info=True)
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob