"""
Rules Engine Module
Manages compliance rules, severity scoring, and remediation suggestions
"""

from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class RulesEngine:
    """Manages compliance rules and context retrieval"""
    
    # Compliance rule categories with detailed mappings
    RULE_CATEGORIES = {
        'GDPR': {
            'name': 'General Data Protection Regulation',
            'severity_base': 'HIGH',
            'rules': {
                'data_protection': 'Article 32: Security of processing',
                'consent': 'Article 7: Conditions for consent',
                'data_minimization': 'Article 5(1)(c): Data minimization principle',
                'purpose_limitation': 'Article 5(1)(b): Purpose limitation',
                'storage_limitation': 'Article 5(1)(e): Storage limitation'
            }
        },
        'CCPA': {
            'name': 'California Consumer Privacy Act',
            'severity_base': 'HIGH',
            'rules': {
                'right_to_know': 'Section 1798.100: Right to know',
                'right_to_delete': 'Section 1798.105: Right to deletion',
                'right_to_opt_out': 'Section 1798.120: Right to opt-out',
                'non_discrimination': 'Section 1798.125: Non-discrimination'
            }
        },
        'NIST': {
            'name': 'NIST Cybersecurity Framework',
            'severity_base': 'MEDIUM',
            'rules': {
                'access_control': 'AC-2: Account Management',
                'authentication': 'IA-2: Identification and Authentication',
                'audit_logging': 'AU-2: Audit Events',
                'encryption': 'SC-8: Transmission Confidentiality',
                'incident_response': 'IR-4: Incident Handling'
            }
        },
        'OWASP': {
            'name': 'OWASP Top 10',
            'severity_base': 'HIGH',
            'rules': {
                'broken_access_control': 'A01:2021 - Broken Access Control',
                'cryptographic_failures': 'A02:2021 - Cryptographic Failures',
                'injection': 'A03:2021 - Injection',
                'insecure_design': 'A04:2021 - Insecure Design',
                'security_misconfiguration': 'A05:2021 - Security Misconfiguration',
                'vulnerable_components': 'A06:2021 - Vulnerable and Outdated Components',
                'auth_failures': 'A07:2021 - Identification and Authentication Failures',
                'data_integrity_failures': 'A08:2021 - Software and Data Integrity Failures',
                'logging_failures': 'A09:2021 - Security Logging and Monitoring Failures',
                'ssrf': 'A10:2021 - Server-Side Request Forgery'
            }
        },
        'PCI_DSS': {
            'name': 'Payment Card Industry Data Security Standard',
            'severity_base': 'CRITICAL',
            'rules': {
                'protect_cardholder_data': 'Requirement 3: Protect stored cardholder data',
                'encrypt_transmission': 'Requirement 4: Encrypt transmission of cardholder data',
                'secure_systems': 'Requirement 6: Develop and maintain secure systems',
                'access_control': 'Requirement 8: Identify and authenticate access',
                'monitor_access': 'Requirement 10: Track and monitor all access'
            }
        },
        'HIPAA': {
            'name': 'Health Insurance Portability and Accountability Act',
            'severity_base': 'CRITICAL',
            'rules': {
                'security_management': '164.308(a)(1): Security Management Process',
                'access_control': '164.312(a)(1): Access Control',
                'audit_controls': '164.312(b): Audit Controls',
                'integrity_controls': '164.312(c)(1): Integrity Controls',
                'transmission_security': '164.312(e)(1): Transmission Security'
            }
        },
        'SOX': {
            'name': 'Sarbanes-Oxley Act',
            'severity_base': 'HIGH',
            'rules': {
                'internal_controls': 'Section 404: Internal Controls',
                'audit_trail': 'Section 802: Audit Trail Requirements',
                'data_retention': 'Section 802: Document Retention',
                'access_controls': 'IT General Controls: Access Management'
            }
        },
        'ISO27001': {
            'name': 'ISO/IEC 27001',
            'severity_base': 'MEDIUM',
            'rules': {
                'access_control': 'A.9: Access Control',
                'cryptography': 'A.10: Cryptography',
                'physical_security': 'A.11: Physical and Environmental Security',
                'operations_security': 'A.12: Operations Security',
                'communications_security': 'A.13: Communications Security'
            }
        }
    }
    
    # Pattern to regulation mapping
    PATTERN_REGULATION_MAP = {
        'hardcoded_password': ['OWASP', 'NIST', 'PCI_DSS'],
        'api_key': ['OWASP', 'NIST', 'ISO27001'],
        'secret_key': ['OWASP', 'NIST', 'PCI_DSS'],
        'aws_key': ['OWASP', 'NIST', 'ISO27001'],
        'string_concatenation': ['OWASP', 'PCI_DSS', 'NIST'],
        'f_string_sql': ['OWASP', 'PCI_DSS'],
        'md5_usage': ['OWASP', 'NIST', 'PCI_DSS', 'HIPAA'],
        'sha1_usage': ['OWASP', 'NIST', 'PCI_DSS'],
        'des_usage': ['OWASP', 'NIST', 'PCI_DSS', 'HIPAA'],
        'email_logging': ['GDPR', 'CCPA', 'HIPAA'],
        'ssn': ['HIPAA', 'GDPR', 'CCPA'],
        'credit_card': ['PCI_DSS', 'GDPR', 'CCPA'],
        'eval_usage': ['OWASP', 'NIST'],
        'exec_usage': ['OWASP', 'NIST'],
        'xss_vulnerability': ['OWASP', 'NIST'],
        'path_traversal': ['OWASP', 'NIST'],
        'shell_injection': ['OWASP', 'NIST']
    }
    
    # Severity scoring matrix
    SEVERITY_SCORES = {
        'CRITICAL': 100,
        'HIGH': 75,
        'MEDIUM': 50,
        'LOW': 25,
        'INFO': 10
    }
    
    def __init__(self, vector_store=None, embedder=None):
        """
        Initialize rules engine
        
        Args:
            vector_store: VectorStore instance for retrieving compliance context
            embedder: Embedder instance for creating query embeddings
        """
        self.vector_store = vector_store
        self.embedder = embedder
        self.rules_cache = {}
        logger.info("RulesEngine initialized")
    
    def get_relevant_rules(self, code_snippet: str, finding: Dict, top_k: int = 5) -> List[str]:
        """
        Get relevant compliance rules for a code snippet using RAG
        
        Args:
            code_snippet: Code to analyze
            finding: Finding information
            top_k: Number of relevant rules to retrieve
            
        Returns:
            List of relevant compliance rules
        """
        if not self.vector_store or not self.embedder:
            logger.debug("Vector store or embedder not initialized. Using pattern-based rules.")
            return self._get_rules_by_pattern(finding)
        
        try:
            # Create query combining code and finding info
            query = f"{finding.get('description', '')} {finding.get('type', '')} {code_snippet[:300]}"
            
            # Create embedding for query
            query_embedding = self.embedder.embed_text(query)
            
            # Search for similar compliance text
            results = self.vector_store.search_similar(query_embedding, top_k=top_k)
            
            # Extract rules from results
            rules = []
            for result in results:
                chunk_text = result.get('chunk_text', '')
                if chunk_text and len(chunk_text) > 50:
                    rules.append(chunk_text)
            
            # Supplement with pattern-based rules
            pattern_rules = self._get_rules_by_pattern(finding)
            rules.extend(pattern_rules[:2])
            
            return rules[:top_k]
        
        except Exception as e:
            logger.error(f"Error retrieving relevant rules: {str(e)}")
            return self._get_rules_by_pattern(finding)
    
    def _get_rules_by_pattern(self, finding: Dict) -> List[str]:
        """
        Get rules based on finding pattern
        
        Args:
            finding: Finding information
            
        Returns:
            List of relevant rules
        """
        pattern = finding.get('pattern', '')
        finding_type = finding.get('type', '')
        
        # Get regulations for this pattern
        regulations = self.PATTERN_REGULATION_MAP.get(pattern, [])
        
        # If no specific pattern match, use type-based rules
        if not regulations:
            regulations = self._get_regulations_by_type(finding_type)
        
        # Build rule texts
        rules = []
        for reg in regulations[:3]:
            if reg in self.RULE_CATEGORIES:
                category = self.RULE_CATEGORIES[reg]
                rule_text = f"{category['name']}: {list(category['rules'].values())[0]}"
                rules.append(rule_text)
        
        return rules if rules else self._get_default_rules()
    
    def _get_regulations_by_type(self, finding_type: str) -> List[str]:
        """
        Get regulations based on finding type
        
        Args:
            finding_type: Type of finding
            
        Returns:
            List of regulation names
        """
        type_map = {
            'secrets': ['OWASP', 'NIST', 'PCI_DSS'],
            'sql_injection': ['OWASP', 'PCI_DSS', 'NIST'],
            'insecure_crypto': ['OWASP', 'NIST', 'PCI_DSS', 'HIPAA'],
            'privacy': ['GDPR', 'CCPA', 'HIPAA'],
            'authentication': ['OWASP', 'NIST', 'PCI_DSS'],
            'owasp': ['OWASP', 'NIST']
        }
        return type_map.get(finding_type, ['OWASP', 'NIST'])
    
    def _get_default_rules(self) -> List[str]:
        """
        Get default compliance rules when specific rules not available
        
        Returns:
            List of default rules
        """
        return [
            "OWASP A02:2021 - Cryptographic Failures: Protect sensitive data",
            "NIST SP 800-53 AC-2: Implement proper account management",
            "General Security: Follow secure coding best practices"
        ]
    
    def get_rules_by_category(self, category: str) -> List[str]:
        """
        Get rules for a specific compliance category
        
        Args:
            category: Compliance category (GDPR, HIPAA, PCI, etc.)
            
        Returns:
            List of rules for that category
        """
        category_upper = category.upper()
        if category_upper in self.RULE_CATEGORIES:
            cat_info = self.RULE_CATEGORIES[category_upper]
            return [f"{cat_info['name']}: {rule}" for rule in cat_info['rules'].values()]
        return []
    
    def get_all_categories(self) -> List[str]:
        """
        Get list of all compliance categories
        
        Returns:
            List of category names
        """
        return list(self.RULE_CATEGORIES.keys())
    
    def calculate_severity_score(self, finding: Dict, analysis: Optional[Dict] = None) -> Tuple[str, int]:
        """
        Calculate severity level and score for a finding
        
        Args:
            finding: Quick scan finding
            analysis: Optional deep analysis result
            
        Returns:
            Tuple of (severity_level, numeric_score)
        """
        # Start with finding severity
        base_severity = finding.get('severity', 'MEDIUM').upper()
        score = self.SEVERITY_SCORES.get(base_severity, 50)
        
        # Adjust based on pattern type
        pattern = finding.get('pattern', '')
        if pattern in ['hardcoded_password', 'api_key', 'credit_card', 'shell_injection']:
            score = min(100, score + 25)  # Boost critical patterns
        
        # Adjust based on deep analysis if available
        if analysis:
            if analysis.get('has_violation', False):
                score = min(100, score + 10)
            
            # Consider AI confidence
            confidence = analysis.get('confidence', 0)
            if confidence > 90:
                score = min(100, score + 5)
        
        # Determine final severity level
        if score >= 90:
            severity = 'CRITICAL'
        elif score >= 70:
            severity = 'HIGH'
        elif score >= 40:
            severity = 'MEDIUM'
        elif score >= 20:
            severity = 'LOW'
        else:
            severity = 'INFO'
        
        return severity, score
    
    def match_rule_to_finding(self, finding: Dict) -> Dict:
        """
        Match a finding to specific compliance rules
        
        Args:
            finding: Finding to match
            
        Returns:
            Rule match information
        """
        pattern = finding.get('pattern', '')
        finding_type = finding.get('type', '')
        
        # Get applicable regulations
        regulations = self.PATTERN_REGULATION_MAP.get(pattern, [])
        if not regulations:
            regulations = self._get_regulations_by_type(finding_type)
        
        # Build detailed rule match
        matched_rules = []
        for reg in regulations:
            if reg in self.RULE_CATEGORIES:
                category = self.RULE_CATEGORIES[reg]
                matched_rules.append({
                    'regulation': reg,
                    'name': category['name'],
                    'severity_base': category['severity_base'],
                    'applicable_rules': list(category['rules'].values())[:2]
                })
        
        return {
            'finding_pattern': pattern,
            'finding_type': finding_type,
            'matched_regulations': matched_rules,
            'total_regulations': len(matched_rules)
        }
    
    def get_remediation_template(self, finding: Dict) -> Dict:
        """
        Get remediation template for a finding
        
        Args:
            finding: Finding information
            
        Returns:
            Remediation template with steps
        """
        pattern = finding.get('pattern', '')
        
        remediation_templates = {
            'hardcoded_password': {
                'title': 'Remove Hardcoded Password',
                'steps': [
                    'Move password to environment variable',
                    'Use secure secret management (e.g., AWS Secrets Manager, HashiCorp Vault)',
                    'Implement proper access controls for secrets',
                    'Rotate the exposed password immediately'
                ],
                'code_example': 'password = os.environ.get("DB_PASSWORD")',
                'priority': 'CRITICAL'
            },
            'api_key': {
                'title': 'Secure API Key Storage',
                'steps': [
                    'Remove API key from source code',
                    'Store in environment variables or config management',
                    'Use API key rotation policies',
                    'Implement key usage monitoring'
                ],
                'code_example': 'api_key = os.environ.get("API_KEY")',
                'priority': 'CRITICAL'
            },
            'string_concatenation': {
                'title': 'Fix SQL Injection Vulnerability',
                'steps': [
                    'Replace string concatenation with parameterized queries',
                    'Use ORM or prepared statements',
                    'Validate and sanitize all user inputs',
                    'Implement input validation at application layer'
                ],
                'code_example': 'cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))',
                'priority': 'CRITICAL'
            },
            'md5_usage': {
                'title': 'Replace Weak Hash Algorithm',
                'steps': [
                    'Replace MD5 with SHA-256 or stronger',
                    'Use bcrypt or Argon2 for password hashing',
                    'Update existing hashes in database',
                    'Document cryptographic standards'
                ],
                'code_example': 'import hashlib; hash = hashlib.sha256(data.encode()).hexdigest()',
                'priority': 'HIGH'
            },
            'eval_usage': {
                'title': 'Remove Dangerous eval() Usage',
                'steps': [
                    'Remove eval() entirely',
                    'Use ast.literal_eval() for safe evaluation',
                    'Implement explicit parsing logic',
                    'Add input validation'
                ],
                'code_example': 'import ast; result = ast.literal_eval(user_input)',
                'priority': 'CRITICAL'
            }
        }
        
        template = remediation_templates.get(pattern, {
            'title': 'Security Remediation Required',
            'steps': [
                'Review the code manually',
                'Consult relevant compliance documentation',
                'Apply security best practices',
                'Test the fix thoroughly'
            ],
            'code_example': 'See documentation for specific guidance',
            'priority': 'MEDIUM'
        })
        
        return template
    
    def validate_compliance(self, findings: List[Dict], required_regulations: List[str]) -> Dict:
        """
        Validate if code complies with required regulations
        
        Args:
            findings: List of all findings
            required_regulations: List of required regulation names
            
        Returns:
            Compliance validation report
        """
        report = {
            'compliant': True,
            'required_regulations': required_regulations,
            'violations_by_regulation': {},
            'total_violations': len(findings),
            'critical_violations': 0,
            'high_violations': 0
        }
        
        for finding in findings:
            severity = finding.get('severity', 'MEDIUM').upper()
            if severity == 'CRITICAL':
                report['critical_violations'] += 1
                report['compliant'] = False
            elif severity == 'HIGH':
                report['high_violations'] += 1
                report['compliant'] = False
            
            # Map to regulations
            pattern = finding.get('pattern', '')
            regulations = self.PATTERN_REGULATION_MAP.get(pattern, [])
            
            for reg in regulations:
                if reg in required_regulations:
                    if reg not in report['violations_by_regulation']:
                        report['violations_by_regulation'][reg] = []
                    report['violations_by_regulation'][reg].append(finding)
        
        return report

# Made with Bob
