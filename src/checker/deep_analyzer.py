"""
Deep Analyzer Module
Performs AI-powered compliance analysis using OpenAI and RAG system
"""

import logging
from typing import List, Dict, Optional
import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logger = logging.getLogger(__name__)


class DeepAnalyzer:
    """Performs deep AI-powered compliance analysis"""
    
    def __init__(self, model_name: str = "gpt-4o-mini", vector_store=None, embedder=None):
        """
        Initialize deep analyzer
        
        Args:
            model_name: Name of the OpenAI model to use
            vector_store: VectorStore instance for RAG
            embedder: Embedder instance for RAG
        """
        self.model_name = model_name
        self.vector_store = vector_store
        self.embedder = embedder
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=api_key)
        logger.info(f"Initialized DeepAnalyzer with model: {model_name}")
    
    def _get_relevant_regulations(self, code_snippet: str, finding: Dict) -> List[str]:
        """
        Retrieve relevant regulations from RAG system
        
        Args:
            code_snippet: Code to analyze
            finding: Quick scan finding with context
            
        Returns:
            List of relevant regulation texts
        """
        if not self.vector_store or not self.embedder:
            logger.debug("RAG system not available, using default rules")
            return self._get_default_regulations(finding)
        
        try:
            # Create query based on finding type and description
            query = f"{finding.get('description', '')} {finding.get('type', '')} {code_snippet[:200]}"
            
            # Get embedding
            query_embedding = self.embedder.embed_text(query)
            
            # Search for relevant regulations
            results = self.vector_store.search_similar(query_embedding, top_k=3)
            
            regulations = []
            for result in results:
                reg_text = result.get('chunk_text', '')
                if reg_text and len(reg_text) > 50:  # Filter out too short chunks
                    regulations.append(reg_text)
            
            return regulations if regulations else self._get_default_regulations(finding)
            
        except Exception as e:
            logger.error(f"Error retrieving regulations from RAG: {str(e)}")
            return self._get_default_regulations(finding)
    
    def _get_default_regulations(self, finding: Dict) -> List[str]:
        """
        Get default regulations based on finding type
        
        Args:
            finding: Quick scan finding
            
        Returns:
            List of relevant regulation texts
        """
        finding_type = finding.get('type', '')
        
        regulations_map = {
            'secrets': [
                "OWASP A02:2021 - Cryptographic Failures: Hardcoded credentials must never be stored in source code.",
                "NIST SP 800-53 IA-5: Authenticators must be protected against unauthorized disclosure.",
                "PCI DSS Requirement 8.2.1: Do not use vendor-supplied defaults for system passwords."
            ],
            'sql_injection': [
                "OWASP A03:2021 - Injection: Use parameterized queries to prevent SQL injection.",
                "CWE-89: SQL Injection vulnerabilities allow attackers to interfere with database queries.",
                "NIST SP 800-53 SI-10: Validate all input to prevent injection attacks."
            ],
            'insecure_crypto': [
                "NIST SP 800-131A: MD5 and SHA-1 are deprecated and must not be used for security.",
                "OWASP A02:2021 - Cryptographic Failures: Use strong, up-to-date cryptographic algorithms.",
                "PCI DSS Requirement 4.1: Use strong cryptography for transmission of cardholder data."
            ],
            'privacy': [
                "GDPR Article 32: Implement appropriate security measures including pseudonymization.",
                "CCPA Section 1798.100: Businesses must not collect or disclose personal information without notice.",
                "HIPAA Security Rule 164.312(a)(2)(iv): Implement encryption for ePHI."
            ],
            'authentication': [
                "OWASP A07:2021 - Identification and Authentication Failures: Implement secure authentication.",
                "NIST SP 800-63B: Use multi-factor authentication for sensitive operations.",
                "PCI DSS Requirement 8: Implement strong access control measures."
            ],
            'owasp': [
                "OWASP Top 10 2021: Follow secure coding practices to prevent common vulnerabilities.",
                "CWE Top 25: Address the most dangerous software weaknesses.",
                "SANS Top 25: Implement defenses against the most critical security errors."
            ]
        }
        
        return regulations_map.get(finding_type, [
            "General Security Best Practice: Follow secure coding guidelines.",
            "Defense in Depth: Implement multiple layers of security controls.",
            "Principle of Least Privilege: Grant minimum necessary access rights."
        ])
    
    def _analyze_with_ai(self, code_snippet: str, regulations: List[str], 
                        finding: Dict) -> Dict:
        """
        Analyze code using OpenAI
        
        Args:
            code_snippet: Code to analyze
            regulations: Relevant regulations
            finding: Quick scan finding
            
        Returns:
            Analysis results
        """
        try:
            # Build prompt
            prompt = self._build_analysis_prompt(code_snippet, regulations, finding)
            
            # Call OpenAI
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a security compliance expert analyzing code for violations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse response
            analysis = self._parse_ai_response(response.choices[0].message.content, finding)
            analysis['ai_powered'] = True
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}")
            return self._fallback_analysis(code_snippet, regulations, finding)
    
    def _fallback_analysis(self, code_snippet: str, regulations: List[str], 
                          finding: Dict) -> Dict:
        """
        Fallback analysis when AI is not available
        
        Args:
            code_snippet: Code to analyze
            regulations: Relevant regulations
            finding: Quick scan finding
            
        Returns:
            Analysis results
        """
        severity = finding.get('severity', 'MEDIUM')
        description = finding.get('description', 'Security issue detected')
        
        # Generate basic analysis based on pattern matching
        analysis = {
            'has_violation': True,
            'severity': severity,
            'description': description,
            'explanation': f"Pattern-based detection: {description}. Manual review recommended.",
            'violated_regulations': regulations[:2] if regulations else [],
            'confidence': 70,  # Lower confidence for fallback
            'remediation': self._get_remediation_suggestion(finding),
            'ai_powered': False,
            'finding': finding
        }
        
        return analysis
    
    def _get_remediation_suggestion(self, finding: Dict) -> str:
        """
        Get remediation suggestion based on finding type
        
        Args:
            finding: Quick scan finding
            
        Returns:
            Remediation suggestion
        """
        finding_type = finding.get('type', '')
        pattern = finding.get('pattern', '')
        
        remediation_map = {
            'hardcoded_password': "Store passwords in environment variables or secure vaults (e.g., AWS Secrets Manager, HashiCorp Vault).",
            'api_key': "Use environment variables or configuration management systems to store API keys securely.",
            'secret_key': "Move secrets to secure storage and reference them at runtime.",
            'string_concatenation': "Use parameterized queries or prepared statements instead of string concatenation.",
            'f_string_sql': "Replace f-strings with parameterized queries using database library's parameter binding.",
            'md5_usage': "Replace MD5 with SHA-256 or SHA-3 for cryptographic hashing.",
            'sha1_usage': "Replace SHA-1 with SHA-256 or stronger algorithms.",
            'eval_usage': "Remove eval() and use safer alternatives like ast.literal_eval() or explicit parsing.",
            'exec_usage': "Avoid exec() entirely. Refactor code to use explicit function calls.",
            'xss_vulnerability': "Use proper output encoding and Content Security Policy (CSP) headers.",
            'path_traversal': "Validate and sanitize file paths. Use os.path.join() and check against allowed directories."
        }
        
        return remediation_map.get(pattern, 
            "Review the code manually and apply security best practices. Consult relevant compliance documentation.")
    
    def _build_analysis_prompt(self, code_snippet: str, regulations: List[str],
                               finding: Dict) -> str:
        regs_text = "\n\n".join(f"[REGULATION EXCERPT]:\n{reg[:400]}" for reg in regulations[:3])

        prompt = f"""You are a regulatory compliance auditor. Your job is to check whether code complies with the specific regulatory policy text provided below.

CODE UNDER AUDIT:
```
{code_snippet}
```

REGULATORY POLICY TEXT (from official compliance documents):
{regs_text}

Using ONLY the regulatory text above as your authority, answer:
1. Does this code violate any of the stated regulatory requirements? (YES/NO)
2. Which specific article, section, or requirement is violated? (cite exactly, e.g. "GDPR Article 5(1)(f)", "HIPAA 164.312(a)(1)", "PCI-DSS Requirement 3.4")
3. What is the compliance risk? (CRITICAL/HIGH/MEDIUM/LOW)
4. What specific policy requirement is NOT being met by this code? (not generic security advice — cite the regulation)
5. What change is needed to achieve compliance with that specific requirement?

Format your response exactly as:
VIOLATION: [YES/NO]
REGULATION: [exact article/section/requirement]
RISK: [CRITICAL/HIGH/MEDIUM/LOW]
EXPLANATION: [what specific policy requirement the code fails to meet]
FIX: [concrete change to achieve compliance with that requirement]
"""
        return prompt

    def _build_policy_scan_prompt(self, file_content: str, regulations: List[str], file_path: str) -> str:
        regs_text = "\n\n".join(f"[POLICY TEXT]:\n{reg[:500]}" for reg in regulations[:4])
        filename = file_path.split('/')[-1].split('\\')[-1]

        prompt = f"""You are a regulatory compliance auditor reviewing source code for policy violations.

FILE: {filename}

SOURCE CODE:
```
{file_content[:3000]}
```

REGULATORY POLICY TEXT (from official compliance documents — GDPR, HIPAA, PCI-DSS, NIST, ISO27001, CCPA):
{regs_text}

Review this code against the policy text above. Look specifically for:
- Personal data or PII handled without consent mechanisms
- Health, financial, or payment data without required encryption or access controls
- Missing audit logging where regulations require it
- Data collected or stored beyond what regulations permit
- Missing privacy notices, data subject rights mechanisms, or breach notification hooks
- Credentials, tokens, or secrets exposed in violation of data protection rules
- Any other direct violation of the policy text provided

List each policy violation found. If the code is compliant, say so.

For each violation, respond with one block:
VIOLATION: YES
REGULATION: [exact article/section, e.g. GDPR Article 5, HIPAA 164.312, PCI-DSS Req 3]
RISK: [CRITICAL/HIGH/MEDIUM/LOW]
EXPLANATION: [what the regulation requires and what this code does instead]
FIX: [what must change to comply]
---
If no violations: VIOLATION: NO
"""
        return prompt
    
    def _parse_ai_response(self, response: str, finding: Dict) -> Dict:
        """
        Parse AI response into structured format
        
        Args:
            response: Raw AI response
            finding: Original finding
            
        Returns:
            Structured analysis
        """
        analysis = {
            'has_violation': False,
            'severity': finding.get('severity', 'MEDIUM'),
            'description': finding.get('description', ''),
            'explanation': '',
            'violated_regulations': [],
            'confidence': 80,
            'remediation': '',
            'raw_response': response,
            'finding': finding
        }
        
        # Parse structured response
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('VIOLATION:'):
                violation = line.replace('VIOLATION:', '').strip().upper()
                analysis['has_violation'] = 'YES' in violation
            elif line.startswith('REGULATION:'):
                reg = line.replace('REGULATION:', '').strip()
                if reg and reg != 'N/A':
                    analysis['violated_regulations'].append(reg)
            elif line.startswith('RISK:'):
                risk = line.replace('RISK:', '').strip().upper()
                if risk in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                    analysis['severity'] = risk
            elif line.startswith('EXPLANATION:'):
                analysis['explanation'] = line.replace('EXPLANATION:', '').strip()
            elif line.startswith('FIX:'):
                analysis['remediation'] = line.replace('FIX:', '').strip()
        
        # If no explanation parsed, use the whole response
        if not analysis['explanation']:
            analysis['explanation'] = response[:300]
        
        # If no remediation, use default
        if not analysis['remediation']:
            analysis['remediation'] = self._get_remediation_suggestion(finding)
        
        return analysis
    
    def analyze_file_for_policy_compliance(self, file_info: Dict) -> List[Dict]:
        """
        Analyze a full file for regulatory policy violations using RAG.
        This is independent of the security quick scanner — it checks the code
        directly against the actual policy text retrieved from the regulation documents.
        """
        file_path = file_info.get('path', 'unknown')
        file_content = file_info.get('content', '')

        if not file_content or len(file_content.strip()) < 50:
            return []

        try:
            # Use the file content as the RAG query to find relevant regulation sections
            query = f"data protection privacy personal data consent encryption access control audit logging {file_content[:300]}"
            query_embedding = self.embedder.embed_text(query)
            results = self.vector_store.search_similar(query_embedding, top_k=4)

            regulations = [r.get('chunk_text', '') for r in results if len(r.get('chunk_text', '')) > 100]
            if not regulations:
                regulations = self._get_default_regulations({'type': 'privacy'})

            prompt = self._build_policy_scan_prompt(file_content, regulations, file_path)

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a regulatory compliance auditor. Cite specific articles and sections from the provided policy text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )

            return self._parse_policy_scan_response(response.choices[0].message.content, file_path)

        except Exception as e:
            logger.error(f"Policy compliance scan failed for {file_path}: {str(e)}")
            return []

    def _parse_policy_scan_response(self, response: str, file_path: str) -> List[Dict]:
        """Parse the multi-violation policy scan response into a list of findings."""
        findings = []
        blocks = response.split('---')

        for block in blocks:
            block = block.strip()
            if not block:
                continue

            finding = {
                'file': file_path,
                'line': 0,
                'type': 'policy_violation',
                'pattern': 'policy_violation',
                'severity': 'HIGH',
                'confidence': 85,
                'has_violation': False,
                'violated_regulations': [],
                'description': '',
                'explanation': '',
                'remediation': '',
                'ai_powered': True,
                'source': 'policy_scan'
            }

            for line in block.split('\n'):
                line = line.strip()
                if line.startswith('VIOLATION:'):
                    finding['has_violation'] = 'YES' in line.upper()
                elif line.startswith('REGULATION:'):
                    reg = line.replace('REGULATION:', '').strip()
                    if reg and reg != 'N/A':
                        finding['violated_regulations'].append(reg)
                        finding['description'] = f"Policy violation: {reg}"
                elif line.startswith('RISK:'):
                    risk = line.replace('RISK:', '').strip().upper()
                    if risk in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                        finding['severity'] = risk
                elif line.startswith('EXPLANATION:'):
                    finding['explanation'] = line.replace('EXPLANATION:', '').strip()
                    if not finding['description']:
                        finding['description'] = finding['explanation'][:100]
                elif line.startswith('FIX:'):
                    finding['remediation'] = line.replace('FIX:', '').strip()

            if finding['has_violation'] and finding['violated_regulations']:
                findings.append(finding)

        return findings

    def analyze_suspicious_section(self, section: Dict) -> Dict:
        """
        Analyze a suspicious code section
        
        Args:
            section: Suspicious section from quick scanner
            
        Returns:
            Detailed analysis
        """
        code = section.get('code', '')
        finding = section.get('finding', {})
        
        # Get relevant regulations from RAG
        regulations = self._get_relevant_regulations(code, finding)
        
        # Perform AI analysis
        analysis = self._analyze_with_ai(code, regulations, finding)
        
        # Add section context
        analysis['file'] = section.get('file', 'unknown')
        analysis['start_line'] = section.get('start_line', 0)
        analysis['end_line'] = section.get('end_line', 0)
        
        return analysis
    
    def analyze_sections_batch(self, sections: List[Dict]) -> List[Dict]:
        """
        Analyze multiple suspicious sections
        
        Args:
            sections: List of suspicious sections
            
        Returns:
            List of detailed analyses
        """
        analyses = []
        
        for i, section in enumerate(sections):
            try:
                logger.info(f"Deep analyzing section {i+1}/{len(sections)}")
                analysis = self.analyze_suspicious_section(section)
                
                # Only include if violation confirmed
                if analysis.get('has_violation', False):
                    analyses.append(analysis)
                    
            except Exception as e:
                logger.error(f"Error analyzing section: {str(e)}")
                continue
        
        logger.info(f"Deep analysis completed: {len(analyses)} violations confirmed")
        return analyses
    
    def generate_summary(self, analyses: List[Dict]) -> Dict:
        """
        Generate summary of deep analysis results
        
        Args:
            analyses: List of analysis results
            
        Returns:
            Summary dictionary
        """
        summary = {
            'total_analyzed': len(analyses),
            'violations_found': sum(1 for a in analyses if a.get('has_violation')),
            'by_severity': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
            'by_type': {},
            'ai_powered': any(a.get('ai_powered', False) for a in analyses),
            'average_confidence': 0
        }
        
        total_confidence = 0
        for analysis in analyses:
            # Count by severity
            severity = analysis.get('severity', 'MEDIUM').upper()
            if severity in summary['by_severity']:
                summary['by_severity'][severity] += 1
            
            # Count by type
            finding = analysis.get('finding', {})
            finding_type = finding.get('type', 'unknown')
            summary['by_type'][finding_type] = summary['by_type'].get(finding_type, 0) + 1
            
            # Sum confidence
            total_confidence += analysis.get('confidence', 0)
        
        if analyses:
            summary['average_confidence'] = total_confidence / len(analyses)
        
        return summary

# Made with Bob
