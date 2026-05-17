"""
Quick Scanner Module
Performs initial file-level compliance scanning with comprehensive pattern detection
"""

import re
from typing import List, Dict, Set, Tuple
import logging

logger = logging.getLogger(__name__)


class QuickScanner:
    """Performs quick pattern-based compliance scanning"""
    
    # Hardcoded secrets patterns
    SECRETS_PATTERNS = {
        'hardcoded_password': {
            'pattern': r'(?i)(password|passwd|pwd)\s*[=:]\s*["\'][^"\']{3,}["\']',
            'severity': 'CRITICAL',
            'description': 'Hardcoded password detected'
        },
        'api_key': {
            'pattern': r'(?i)(api[_-]?key|apikey|access[_-]?key)\s*[=:]\s*["\'][^"\']{10,}["\']',
            'severity': 'CRITICAL',
            'description': 'Hardcoded API key detected'
        },
        'secret_key': {
            'pattern': r'(?i)(secret[_-]?key|secretkey|secret)\s*[=:]\s*["\'][^"\']{10,}["\']',
            'severity': 'CRITICAL',
            'description': 'Hardcoded secret key detected'
        },
        'private_key': {
            'pattern': r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----',
            'severity': 'CRITICAL',
            'description': 'Private key embedded in code'
        },
        'aws_key': {
            'pattern': r'(?i)(AKIA[0-9A-Z]{16})',
            'severity': 'CRITICAL',
            'description': 'AWS access key detected'
        },
        'github_token': {
            'pattern': r'(?i)(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59})',
            'severity': 'CRITICAL',
            'description': 'GitHub token detected'
        },
        'jwt_token': {
            'pattern': r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*',
            'severity': 'HIGH',
            'description': 'JWT token detected'
        },
        'generic_secret': {
            'pattern': r'(?i)(token|bearer|auth)\s*[=:]\s*["\'][a-zA-Z0-9_\-]{20,}["\']',
            'severity': 'HIGH',
            'description': 'Generic authentication token detected'
        }
    }
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = {
        'string_concatenation': {
            'pattern': r'(?i)(execute|exec|query|sql)\s*\(\s*["\'].*[\+&].*["\']',
            'severity': 'CRITICAL',
            'description': 'SQL injection via string concatenation'
        },
        'format_string': {
            'pattern': r'(?i)(execute|exec|query)\s*\(\s*["\'].*%s.*["\'].*%',
            'severity': 'CRITICAL',
            'description': 'SQL injection via format string'
        },
        'f_string_sql': {
            'pattern': r'(?i)(execute|exec|query)\s*\(\s*f["\'].*\{.*\}.*["\']',
            'severity': 'CRITICAL',
            'description': 'SQL injection via f-string'
        },
        'raw_input_sql': {
            'pattern': r'(?i)(SELECT|INSERT|UPDATE|DELETE).*FROM.*WHERE.*input\(',
            'severity': 'HIGH',
            'description': 'SQL query with user input'
        }
    }
    
    # Insecure cryptography patterns
    CRYPTO_PATTERNS = {
        'md5_usage': {
            'pattern': r'(?i)\b(md5|hashlib\.md5)\s*\(',
            'severity': 'HIGH',
            'description': 'Insecure MD5 hash algorithm used'
        },
        'sha1_usage': {
            'pattern': r'(?i)\b(sha1|hashlib\.sha1)\s*\(',
            'severity': 'HIGH',
            'description': 'Insecure SHA1 hash algorithm used'
        },
        'des_usage': {
            'pattern': r'(?i)\b(DES|TripleDES|DES3)\b',
            'severity': 'CRITICAL',
            'description': 'Insecure DES encryption algorithm used'
        },
        'weak_random': {
            'pattern': r'(?i)\b(random\.random|Math\.random)\s*\(',
            'severity': 'MEDIUM',
            'description': 'Weak random number generator for security'
        },
        'hardcoded_iv': {
            'pattern': r'(?i)(iv|initialization.?vector)\s*=\s*["\'][^"\']+["\']',
            'severity': 'HIGH',
            'description': 'Hardcoded initialization vector'
        }
    }
    
    # Data privacy patterns (PII)
    PRIVACY_PATTERNS = {
        'email_logging': {
            'pattern': r'(?i)(log|print|console)\s*\(.*[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}',
            'severity': 'MEDIUM',
            'description': 'Email address in logging statement'
        },
        'ssn': {
            'pattern': r'\b\d{3}-\d{2}-\d{4}\b',
            'severity': 'HIGH',
            'description': 'Social Security Number detected'
        },
        'credit_card': {
            'pattern': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            'severity': 'CRITICAL',
            'description': 'Credit card number detected'
        },
        'phone_logging': {
            'pattern': r'(?i)(log|print)\s*\(.*\d{3}[-.]?\d{3}[-.]?\d{4}',
            'severity': 'MEDIUM',
            'description': 'Phone number in logging statement'
        },
        'ip_logging': {
            'pattern': r'(?i)(log|print)\s*\(.*\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',
            'severity': 'LOW',
            'description': 'IP address in logging statement'
        }
    }
    
    # Authentication/Authorization patterns
    AUTH_PATTERNS = {
        'eval_usage': {
            'pattern': r'(?i)\beval\s*\(',
            'severity': 'CRITICAL',
            'description': 'Dangerous eval() usage - code injection risk'
        },
        'exec_usage': {
            'pattern': r'(?i)\bexec\s*\(',
            'severity': 'CRITICAL',
            'description': 'Dangerous exec() usage - code injection risk'
        },
        'pickle_usage': {
            'pattern': r'(?i)\bpickle\.loads?\s*\(',
            'severity': 'HIGH',
            'description': 'Unsafe pickle deserialization'
        },
        'yaml_unsafe': {
            'pattern': r'(?i)yaml\.load\s*\([^,)]*\)',
            'severity': 'HIGH',
            'description': 'Unsafe YAML loading without SafeLoader'
        },
        'shell_injection': {
            'pattern': r'(?i)(os\.system|subprocess\.call|subprocess\.run).*shell\s*=\s*True',
            'severity': 'CRITICAL',
            'description': 'Shell injection vulnerability'
        },
        'no_auth_check': {
            'pattern': r'(?i)@app\.route.*methods.*POST(?!.*@login_required|.*@auth)',
            'severity': 'HIGH',
            'description': 'POST endpoint without authentication'
        }
    }
    
    # OWASP Top 10 patterns
    OWASP_PATTERNS = {
        'xss_vulnerability': {
            'pattern': r'(?i)(innerHTML|outerHTML|document\.write)\s*=',
            'severity': 'HIGH',
            'description': 'Potential XSS vulnerability'
        },
        'path_traversal': {
            'pattern': r'(?i)(open|file|read).*\.\./|\.\.',
            'severity': 'HIGH',
            'description': 'Potential path traversal vulnerability'
        },
        'xxe_vulnerability': {
            'pattern': r'(?i)xml\.etree\.ElementTree\.parse(?!.*defusedxml)',
            'severity': 'HIGH',
            'description': 'XML External Entity (XXE) vulnerability'
        },
        'insecure_deserialization': {
            'pattern': r'(?i)(json\.loads|pickle\.loads|yaml\.load)\s*\(\s*request\.',
            'severity': 'HIGH',
            'description': 'Insecure deserialization of user input'
        },
        'debug_mode': {
            'pattern': r'(?i)(debug\s*=\s*True|DEBUG\s*=\s*True|app\.run.*debug)',
            'severity': 'MEDIUM',
            'description': 'Debug mode enabled in production'
        }
    }
    
    # Compliance keywords
    COMPLIANCE_KEYWORDS = {
        'gdpr': ['gdpr', 'data protection', 'right to be forgotten', 'data subject', 'consent'],
        'hipaa': ['hipaa', 'phi', 'protected health information', 'medical record', 'patient data'],
        'pci': ['pci', 'payment card', 'cardholder data', 'credit card', 'cvv'],
        'sox': ['sox', 'sarbanes', 'financial reporting', 'audit trail'],
        'ccpa': ['ccpa', 'california consumer', 'do not sell', 'personal information'],
        'owasp': ['owasp', 'injection', 'broken authentication', 'xss', 'csrf'],
        'nist': ['nist', 'cybersecurity framework', 'access control', 'incident response']
    }
    
    def __init__(self):
        """Initialize quick scanner"""
        self.findings = []
    
    def _should_skip_finding(self, pattern_name: str, file_path: str, context_line: str, match_text: str) -> bool:
        """
        Determine if a finding should be skipped based on context
        
        Args:
            pattern_name: Name of the pattern that matched
            file_path: Path to the file
            context_line: Line containing the match
            match_text: The matched text
            
        Returns:
            True if finding should be skipped, False otherwise
        """
        # Skip credit card patterns in markdown files, documentation, and test files
        if pattern_name == 'credit_card':
            # Skip markdown and documentation files
            if file_path.endswith(('.md', '.txt', '.rst', '.doc', '.docx', '.pdf')):
                return True
            
            # Skip test files and directories
            if any(x in file_path.lower() for x in ['test', 'spec', 'mock', 'fixture', 'example', 'sample']):
                return True
            
            # Skip common test credit card numbers (Stripe test numbers)
            test_cards = [
                '4242424242424242',  # Visa
                '4000056655665556',  # Visa (debit)
                '5555555555554444',  # Mastercard
                '2223003122003222',  # Mastercard (2-series)
                '5200828282828210',  # Mastercard (debit)
                '378282246310005',   # American Express
                '371449635398431',   # American Express
                '6011111111111117',  # Discover
                '6011000990139424',  # Discover
                '3056930009020004',  # Diners Club
                '36227206271667',    # Diners Club (14 digit)
                '3566002020360505',  # JCB
            ]
            
            # Remove spaces and dashes from match
            clean_match = re.sub(r'[\s-]', '', match_text)
            if clean_match in test_cards:
                return True
            
            # Skip if in comments or documentation strings
            context_lower = context_line.lower()
            if any(x in context_lower for x in ['#', '//', '/*', '*/', '"""', "'''", 'example', 'test', 'stripe', 'demo']):
                return True
        
        return False
    
    def _scan_pattern_category(self, content: str, file_path: str,
                               patterns: Dict, category: str) -> List[Dict]:
        """
        Scan content for a category of patterns
        
        Args:
            content: File content to scan
            file_path: Path to the file
            patterns: Dictionary of patterns with metadata
            category: Category name (e.g., 'secrets', 'sql_injection')
            
        Returns:
            List of findings
        """
        findings = []
        
        for pattern_name, pattern_info in patterns.items():
            try:
                pattern = pattern_info['pattern']
                matches = re.finditer(pattern, content, re.MULTILINE)
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    
                    # Get context (line containing the match)
                    lines = content.split('\n')
                    context_line = lines[line_num - 1] if line_num <= len(lines) else ''
                    match_text = match.group(0)
                    
                    # Check if this finding should be skipped
                    if self._should_skip_finding(pattern_name, file_path, context_line, match_text):
                        continue
                    
                    findings.append({
                        'type': category,
                        'severity': pattern_info['severity'],
                        'pattern': pattern_name,
                        'file': file_path,
                        'line': line_num,
                        'match': match_text[:100],  # Limit match length
                        'context': context_line.strip()[:200],
                        'description': pattern_info['description'],
                        'confidence': 85  # Base confidence for pattern matching
                    })
            except Exception as e:
                logger.warning(f"Error scanning pattern {pattern_name}: {str(e)}")
                continue
        
        return findings
    
    def scan_file(self, file_info: Dict) -> List[Dict]:
        """
        Perform quick scan on a single file
        
        Args:
            file_info: Dictionary with file information including content
            
        Returns:
            List of findings with suspicious code sections
        """
        findings = []
        content = file_info.get('content', '')
        file_path = file_info.get('path', 'unknown')
        
        if not content:
            return findings
        
        # Scan for hardcoded secrets
        findings.extend(self._scan_pattern_category(
            content, file_path, self.SECRETS_PATTERNS, 'secrets'
        ))
        
        # Scan for SQL injection vulnerabilities
        findings.extend(self._scan_pattern_category(
            content, file_path, self.SQL_INJECTION_PATTERNS, 'sql_injection'
        ))
        
        # Scan for insecure cryptography
        findings.extend(self._scan_pattern_category(
            content, file_path, self.CRYPTO_PATTERNS, 'insecure_crypto'
        ))
        
        # Scan for data privacy issues
        findings.extend(self._scan_pattern_category(
            content, file_path, self.PRIVACY_PATTERNS, 'privacy'
        ))
        
        # Scan for authentication/authorization issues
        findings.extend(self._scan_pattern_category(
            content, file_path, self.AUTH_PATTERNS, 'authentication'
        ))
        
        # Scan for OWASP Top 10 patterns
        findings.extend(self._scan_pattern_category(
            content, file_path, self.OWASP_PATTERNS, 'owasp'
        ))
        
        # Scan for compliance keywords
        content_lower = content.lower()
        for compliance_type, keywords in self.COMPLIANCE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in content_lower:
                    findings.append({
                        'type': 'compliance_keyword',
                        'severity': 'INFO',
                        'pattern': compliance_type,
                        'file': file_path,
                        'line': 0,
                        'match': keyword,
                        'context': '',
                        'description': f'Compliance keyword found: {compliance_type}',
                        'confidence': 50  # Lower confidence for keyword matches
                    })
                    break  # Only report once per compliance type per file
        
        logger.info(f"Quick scan of {file_path}: found {len(findings)} potential issues")
        return findings
    
    def scan_files_batch(self, files_info: List[Dict]) -> List[Dict]:
        """
        Scan multiple files
        
        Args:
            files_info: List of file information dictionaries
            
        Returns:
            List of all findings
        """
        all_findings = []
        
        for file_info in files_info:
            try:
                findings = self.scan_file(file_info)
                all_findings.extend(findings)
            except Exception as e:
                logger.error(f"Error scanning file {file_info.get('path')}: {str(e)}")
                continue
        
        logger.info(f"Quick scan completed. Found {len(all_findings)} potential issues")
        return all_findings
    
    def get_high_priority_files(self, findings: List[Dict]) -> List[str]:
        """
        Get list of files with high-priority findings
        
        Args:
            findings: List of findings
            
        Returns:
            List of file paths with high-priority issues
        """
        high_priority_files = set()
        
        for finding in findings:
            severity = finding.get('severity', '').upper()
            if severity in ['CRITICAL', 'HIGH']:
                high_priority_files.add(finding['file'])
        
        return list(high_priority_files)
    
    def get_suspicious_sections(self, findings: List[Dict], file_info: Dict) -> List[Dict]:
        """
        Extract suspicious code sections for deep analysis
        
        Args:
            findings: List of findings for a file
            file_info: File information including content
            
        Returns:
            List of suspicious sections with context
        """
        sections = []
        content = file_info.get('content', '')
        lines = content.split('\n')
        
        for finding in findings:
            line_num = finding.get('line', 0)
            if line_num == 0:
                continue
            
            # Extract section with context (5 lines before and after)
            start_line = max(0, line_num - 6)
            end_line = min(len(lines), line_num + 5)
            section_lines = lines[start_line:end_line]
            
            sections.append({
                'file': finding['file'],
                'start_line': start_line + 1,
                'end_line': end_line,
                'code': '\n'.join(section_lines),
                'finding': finding
            })
        
        return sections
    
    def generate_summary(self, findings: List[Dict]) -> Dict:
        """
        Generate summary of scan results
        
        Args:
            findings: List of findings
            
        Returns:
            Summary dictionary
        """
        summary = {
            'total_findings': len(findings),
            'by_severity': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFO': 0},
            'by_type': {},
            'affected_files': set()
        }
        
        for finding in findings:
            # Count by severity
            severity = finding.get('severity', 'INFO').upper()
            if severity in summary['by_severity']:
                summary['by_severity'][severity] += 1
            
            # Count by type
            finding_type = finding.get('type', 'unknown')
            summary['by_type'][finding_type] = summary['by_type'].get(finding_type, 0) + 1
            
            # Track affected files
            summary['affected_files'].add(finding['file'])
        
        summary['affected_files'] = len(summary['affected_files'])
        
        return summary

# Made with Bob
