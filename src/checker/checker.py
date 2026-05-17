"""
Compliance Checker Module
Main orchestrator that combines quick scanning, deep analysis, and rules engine
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from .quick_scanner import QuickScanner
from .deep_analyzer import DeepAnalyzer
from .rules_engine import RulesEngine

logger = logging.getLogger(__name__)


class ComplianceChecker:
    """
    Main compliance checker that orchestrates the hybrid analysis workflow
    """
    
    def __init__(self, vector_store=None, embedder=None, model_name: str = "gemma2:2b"):
        """
        Initialize compliance checker
        
        Args:
            vector_store: VectorStore instance for RAG
            embedder: Embedder instance for RAG
            model_name: Ollama model name for deep analysis
        """
        self.quick_scanner = QuickScanner()
        self.deep_analyzer = DeepAnalyzer(
            model_name=model_name,
            vector_store=vector_store,
            embedder=embedder
        )
        self.rules_engine = RulesEngine(
            vector_store=vector_store,
            embedder=embedder
        )
        
        logger.info("ComplianceChecker initialized with hybrid analysis")
    
    def check_compliance(self, parsed_files: List[Dict], 
                        regulations: Optional[List[str]] = None,
                        enable_deep_analysis: bool = True,
                        max_deep_analysis_files: int = 10) -> Dict:
        """
        Perform comprehensive compliance check on parsed files
        
        Args:
            parsed_files: List of parsed file dictionaries with content
            regulations: Optional list of specific regulations to check
            enable_deep_analysis: Whether to perform deep AI analysis
            max_deep_analysis_files: Maximum files for deep analysis
            
        Returns:
            Comprehensive compliance report
        """
        logger.info(f"Starting compliance check on {len(parsed_files)} files")
        start_time = datetime.now()
        
        # Phase 1: Quick Scan
        logger.info("Phase 1: Quick scanning all files...")
        quick_findings = self._phase1_quick_scan(parsed_files)
        
        # Phase 2: Deep Analysis (if enabled)
        deep_analyses = []
        if enable_deep_analysis and quick_findings:
            logger.info("Phase 2: Deep analyzing suspicious sections...")
            deep_analyses = self._phase2_deep_analysis(
                parsed_files, 
                quick_findings,
                max_deep_analysis_files
            )
        
        # Phase 3: Rules Engine Assessment
        logger.info("Phase 3: Applying rules engine for final assessment...")
        final_findings = self._phase3_rules_assessment(
            quick_findings,
            deep_analyses,
            regulations
        )

        # Phase 4: RAG-based policy compliance scan on every file
        logger.info("Phase 4: Scanning all files for regulatory policy violations...")
        policy_findings = self._phase4_policy_compliance_scan(parsed_files)
        final_findings.extend(policy_findings)
        logger.info(f"Policy scan added {len(policy_findings)} compliance findings")

        # Generate comprehensive report
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        report = self._generate_report(
            parsed_files,
            quick_findings,
            deep_analyses,
            final_findings,
            regulations,
            duration
        )
        
        logger.info(f"Compliance check completed in {duration:.2f}s")
        return report
    
    def _phase1_quick_scan(self, parsed_files: List[Dict]) -> List[Dict]:
        """
        Phase 1: Quick pattern-based scanning
        
        Args:
            parsed_files: List of parsed files
            
        Returns:
            List of quick scan findings
        """
        findings = self.quick_scanner.scan_files_batch(parsed_files)
        
        logger.info(f"Quick scan found {len(findings)} potential issues")
        
        # Log summary by severity
        summary = self.quick_scanner.generate_summary(findings)
        logger.info(f"Severity breakdown: {summary['by_severity']}")
        
        return findings
    
    def _phase2_deep_analysis(self, parsed_files: List[Dict], 
                             quick_findings: List[Dict],
                             max_files: int) -> List[Dict]:
        """
        Phase 2: Deep AI-powered analysis of suspicious sections
        
        Args:
            parsed_files: List of parsed files
            quick_findings: Quick scan findings
            max_files: Maximum files to analyze deeply
            
        Returns:
            List of deep analysis results
        """
        # Get high-priority files
        high_priority_files = self.quick_scanner.get_high_priority_files(quick_findings)
        
        # Limit to max_files
        files_to_analyze = high_priority_files[:max_files]
        logger.info(f"Deep analyzing {len(files_to_analyze)} high-priority files")
        
        # Extract suspicious sections for each file
        all_sections = []
        for file_path in files_to_analyze:
            # Get file info
            file_info = next((f for f in parsed_files if f.get('path') == file_path), None)
            if not file_info:
                continue
            
            # Get findings for this file
            file_findings = [f for f in quick_findings if f.get('file') == file_path]
            
            # Extract suspicious sections
            sections = self.quick_scanner.get_suspicious_sections(file_findings, file_info)
            all_sections.extend(sections)
        
        logger.info(f"Extracted {len(all_sections)} suspicious sections for deep analysis")
        
        # Perform deep analysis on sections
        analyses = self.deep_analyzer.analyze_sections_batch(all_sections)
        
        logger.info(f"Deep analysis completed: {len(analyses)} violations confirmed")
        return analyses
    
    def _phase3_rules_assessment(self, quick_findings: List[Dict],
                                 deep_analyses: List[Dict],
                                 regulations: Optional[List[str]]) -> List[Dict]:
        """
        Phase 3: Apply rules engine for final assessment
        
        Args:
            quick_findings: Quick scan findings
            deep_analyses: Deep analysis results
            regulations: Required regulations
            
        Returns:
            List of final assessed findings
        """
        final_findings = []
        
        # Process quick findings
        for finding in quick_findings:
            # Match to rules
            rule_match = self.rules_engine.match_rule_to_finding(finding)
            
            # Find corresponding deep analysis if exists
            deep_analysis = None
            for analysis in deep_analyses:
                if (analysis.get('file') == finding.get('file') and
                    analysis.get('start_line', 0) <= finding.get('line', 0) <= analysis.get('end_line', 999999)):
                    deep_analysis = analysis
                    break
            
            # Calculate final severity
            severity, score = self.rules_engine.calculate_severity_score(finding, deep_analysis)
            
            # Get remediation template
            remediation = self.rules_engine.get_remediation_template(finding)
            
            # Extract regulation names from rule_match for easy access
            regulation_names = []
            for matched_reg in rule_match.get('matched_regulations', []):
                reg_name = matched_reg.get('name', matched_reg.get('regulation', ''))
                if reg_name:
                    regulation_names.append(reg_name)
            
            # Build final finding
            final_finding = {
                'file': finding.get('file'),
                'line': finding.get('line'),
                'type': finding.get('type'),
                'pattern': finding.get('pattern'),
                'severity': severity,
                'severity_score': score,
                'description': finding.get('description'),
                'context': finding.get('context', ''),
                'match': finding.get('match', ''),
                'confidence': finding.get('confidence', 85),
                'rule_match': rule_match,
                'remediation': remediation,
                'deep_analysis': deep_analysis,
                'has_deep_analysis': deep_analysis is not None,
                'violated_regulations': regulation_names  # Always include regulations from rule_match
            }
            
            # Add AI-specific info if deep analysis available
            if deep_analysis:
                # Merge AI-detected regulations with rule-based ones
                ai_regulations = deep_analysis.get('violated_regulations', [])
                if ai_regulations:
                    # Combine and deduplicate
                    all_regulations = list(set(regulation_names + ai_regulations))
                    final_finding['violated_regulations'] = all_regulations
                final_finding['ai_explanation'] = deep_analysis.get('explanation', '')
                final_finding['confidence'] = deep_analysis.get('confidence', 85)
            
            final_findings.append(final_finding)
        
        # Sort by severity score (highest first)
        final_findings.sort(key=lambda x: x['severity_score'], reverse=True)
        
        logger.info(f"Final assessment: {len(final_findings)} findings")
        return final_findings
    
    def _phase4_policy_compliance_scan(self, parsed_files: List[Dict]) -> List[Dict]:
        """
        Phase 4: Check every file directly against regulatory policy text via RAG.
        This catches compliance violations that have no security pattern signature —
        e.g. missing consent, unencrypted PII, missing audit logs, data retention violations.
        """
        policy_findings = []

        for file_info in parsed_files:
            file_path = file_info.get('path', '')
            # Skip non-code files that can't have policy violations
            if file_path.endswith(('.css', '.txt', '.toml', '.cfg', '.ini', '.md')):
                continue
            try:
                findings = self.deep_analyzer.analyze_file_for_policy_compliance(file_info)
                policy_findings.extend(findings)
            except Exception as e:
                logger.error(f"Policy scan failed for {file_path}: {str(e)}")

        return policy_findings

    def _generate_report(self, parsed_files: List[Dict],
                        quick_findings: List[Dict],
                        deep_analyses: List[Dict],
                        final_findings: List[Dict],
                        regulations: Optional[List[str]],
                        duration: float) -> Dict:
        """
        Generate comprehensive compliance report
        
        Args:
            parsed_files: Original parsed files
            quick_findings: Quick scan findings
            deep_analyses: Deep analysis results
            final_findings: Final assessed findings
            regulations: Required regulations
            duration: Analysis duration in seconds
            
        Returns:
            Comprehensive report dictionary
        """
        # Calculate statistics
        total_files = len(parsed_files)
        affected_files = len(set(f['file'] for f in final_findings))
        
        severity_counts = {
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0,
            'INFO': 0
        }
        
        type_counts = {}
        regulation_violations = {}
        
        for finding in final_findings:
            # Count by severity
            severity = finding.get('severity', 'MEDIUM')
            if severity in severity_counts:
                severity_counts[severity] += 1
            
            # Count by type
            finding_type = finding.get('type', 'unknown')
            type_counts[finding_type] = type_counts.get(finding_type, 0) + 1
            
            # Count regulation violations
            for reg in finding.get('violated_regulations', []):
                regulation_violations[reg] = regulation_violations.get(reg, 0) + 1
        
        # Validate compliance if regulations specified
        compliance_validation = None
        if regulations:
            compliance_validation = self.rules_engine.validate_compliance(
                final_findings,
                regulations
            )
        
        # Build report
        report = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': duration,
                'total_files_analyzed': total_files,
                'affected_files': affected_files,
                'analysis_phases': {
                    'quick_scan': True,
                    'deep_analysis': len(deep_analyses) > 0,
                    'rules_assessment': True
                }
            },
            'summary': {
                'total_findings': len(final_findings),
                'by_severity': severity_counts,
                'by_type': type_counts,
                'critical_issues': severity_counts['CRITICAL'],
                'high_issues': severity_counts['HIGH'],
                'requires_immediate_action': severity_counts['CRITICAL'] + severity_counts['HIGH']
            },
            'findings': final_findings,
            'quick_scan_summary': self.quick_scanner.generate_summary(quick_findings),
            'deep_analysis_summary': self.deep_analyzer.generate_summary(deep_analyses) if deep_analyses else None,
            'regulation_violations': regulation_violations,
            'compliance_validation': compliance_validation,
            'recommendations': self._generate_recommendations(final_findings, severity_counts)
        }
        
        return report
    
    def _generate_recommendations(self, findings: List[Dict], 
                                 severity_counts: Dict) -> List[str]:
        """
        Generate actionable recommendations based on findings
        
        Args:
            findings: List of findings
            severity_counts: Severity count dictionary
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Critical issues
        if severity_counts['CRITICAL'] > 0:
            recommendations.append(
                f"URGENT: Address {severity_counts['CRITICAL']} critical security issues immediately. "
                "These pose severe risks to data security and compliance."
            )
        
        # High priority issues
        if severity_counts['HIGH'] > 0:
            recommendations.append(
                f"HIGH PRIORITY: Resolve {severity_counts['HIGH']} high-severity issues. "
                "These should be addressed in the current sprint."
            )
        
        # Pattern-specific recommendations
        pattern_counts = {}
        for finding in findings:
            pattern = finding.get('pattern', '')
            if finding.get('severity') in ['CRITICAL', 'HIGH']:
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        # Top 3 patterns
        top_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        for pattern, count in top_patterns:
            if pattern == 'hardcoded_password':
                recommendations.append(
                    f"Found {count} hardcoded credentials. Implement secure secret management immediately."
                )
            elif pattern in ['string_concatenation', 'f_string_sql']:
                recommendations.append(
                    f"Found {count} SQL injection vulnerabilities. Use parameterized queries."
                )
            elif pattern in ['md5_usage', 'sha1_usage']:
                recommendations.append(
                    f"Found {count} instances of weak cryptography. Upgrade to SHA-256 or stronger."
                )
        
        # General recommendations
        if severity_counts['MEDIUM'] > 5:
            recommendations.append(
                "Consider implementing automated security scanning in CI/CD pipeline."
            )
        
        if not recommendations:
            recommendations.append(
                "No critical issues found. Continue following security best practices."
            )
        
        return recommendations
    
    def check_file(self, file_info: Dict, enable_deep_analysis: bool = True) -> Dict:
        """
        Check a single file for compliance issues
        
        Args:
            file_info: File information dictionary
            enable_deep_analysis: Whether to perform deep analysis
            
        Returns:
            Compliance report for the file
        """
        return self.check_compliance(
            [file_info],
            enable_deep_analysis=enable_deep_analysis,
            max_deep_analysis_files=1
        )
    
    def get_progress_callback(self):
        """
        Get a progress callback function for tracking analysis progress
        
        Returns:
            Progress callback function
        """
        progress = {'current': 0, 'total': 0, 'phase': ''}
        
        def callback(current: int, total: int, phase: str):
            progress['current'] = current
            progress['total'] = total
            progress['phase'] = phase
            logger.info(f"Progress: {phase} - {current}/{total}")
        
        return callback, progress

# Made with Bob