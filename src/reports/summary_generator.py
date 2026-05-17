"""
Summary Generator Module
Generates one-page executive summary reports
"""

from typing import Dict, List
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class SummaryGenerator:
    """Generates executive summary reports"""
    
    def __init__(self):
        """Initialize summary generator"""
        pass
    
    def calculate_compliance_score(self, summary: Dict) -> int:
        """
        Calculate overall compliance score (0-100)
        
        Args:
            summary: Summary dictionary with issue counts
            
        Returns:
            Compliance score (0-100)
        """
        critical = summary.get('critical_issues', 0)
        high = summary.get('high_issues', 0)
        medium = summary.get('medium_issues', 0)
        low = summary.get('low_issues', 0)
        
        # Start with perfect score
        score = 100
        
        # Deduct points based on severity
        score -= critical * 20  # Critical: -20 points each
        score -= high * 10      # High: -10 points each
        score -= medium * 5     # Medium: -5 points each
        score -= low * 2        # Low: -2 points each
        
        # Ensure score is between 0 and 100
        return max(0, min(100, score))
    
    def get_top_violations(self, compliance_report: Dict, limit: int = 5) -> List[Dict]:
        """
        Get top N most critical violations
        
        Args:
            compliance_report: Full compliance report
            limit: Number of violations to return
            
        Returns:
            List of top violations
        """
        findings = compliance_report.get('findings', [])
        
        # Sort by severity score (highest first)
        sorted_findings = sorted(
            findings,
            key=lambda x: x.get('severity_score', 0),
            reverse=True
        )
        
        # Return top N with essential info
        top_violations = []
        for finding in sorted_findings[:limit]:
            top_violations.append({
                'file': finding.get('file', 'unknown'),
                'line': finding.get('line', 0),
                'severity': finding.get('severity', 'MEDIUM'),
                'type': finding.get('type', 'unknown'),
                'description': finding.get('description', 'No description')[:100]
            })
        
        return top_violations
    
    def get_compliance_by_regulation(self, compliance_report: Dict) -> Dict[str, Dict]:
        """
        Get compliance status by regulation
        
        Args:
            compliance_report: Full compliance report
            
        Returns:
            Dictionary of regulation compliance status
        """
        regulation_violations = compliance_report.get('regulation_violations', {})
        
        compliance_by_reg = {}
        for regulation, count in regulation_violations.items():
            if count == 0:
                status = 'COMPLIANT'
                score = 100
            elif count <= 2:
                status = 'MINOR_ISSUES'
                score = 80
            elif count <= 5:
                status = 'MODERATE_ISSUES'
                score = 60
            else:
                status = 'MAJOR_ISSUES'
                score = 40
            
            compliance_by_reg[regulation] = {
                'violations': count,
                'status': status,
                'score': score
            }
        
        return compliance_by_reg
    
    def generate_summary(self, analysis_results: Dict) -> str:
        """
        Generate one-page executive summary in plain text
        
        Args:
            analysis_results: Complete analysis results
            
        Returns:
            Formatted summary as string
        """
        summary = analysis_results.get('summary', {})
        compliance_report = analysis_results.get('stages', {}).get('compliance', {}).get('report', {})
        
        # Calculate compliance score
        compliance_score = self.calculate_compliance_score(summary)
        
        # Get top violations
        top_violations = self.get_top_violations(compliance_report, limit=5)
        
        # Get compliance by regulation
        compliance_by_reg = self.get_compliance_by_regulation(compliance_report)
        
        report = []
        report.append("=" * 80)
        report.append("COMPLIANCE GUARDIAN - EXECUTIVE SUMMARY")
        report.append("=" * 80)
        report.append("")
        
        # Repository information
        report.append("REPOSITORY INFORMATION")
        report.append("-" * 80)
        report.append(f"Repository: {analysis_results.get('repo_url', 'N/A')}")
        report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Status: {analysis_results.get('status', 'N/A').upper()}")
        report.append(f"Duration: {analysis_results.get('duration_seconds', 0):.2f} seconds")
        report.append("")
        
        # Overall compliance score
        report.append("OVERALL COMPLIANCE SCORE")
        report.append("-" * 80)
        report.append(f"Score: {compliance_score}/100")
        report.append(self._get_score_bar(compliance_score))
        report.append(f"Rating: {self._get_score_rating(compliance_score)}")
        report.append("")
        
        # Overall statistics
        report.append("OVERALL STATISTICS")
        report.append("-" * 80)
        report.append(f"Files Analyzed: {summary.get('files_analyzed', 0)}")
        report.append(f"Total Issues Found: {summary.get('total_issues', 0)}")
        report.append("")
        
        # Issues by severity
        report.append("ISSUES BY SEVERITY")
        report.append("-" * 80)
        critical = summary.get('critical_issues', 0)
        high = summary.get('high_issues', 0)
        medium = summary.get('medium_issues', 0)
        low = summary.get('low_issues', 0)
        
        report.append(f"Critical: {critical:3d} {'🔴' * min(critical, 10)}")
        report.append(f"High:     {high:3d} {'🟠' * min(high, 10)}")
        report.append(f"Medium:   {medium:3d} {'🟡' * min(medium, 10)}")
        report.append(f"Low:      {low:3d} {'🟢' * min(low, 10)}")
        report.append("")
        
        # Top 5 critical violations
        if top_violations:
            report.append("TOP 5 CRITICAL VIOLATIONS")
            report.append("-" * 80)
            for i, violation in enumerate(top_violations, 1):
                report.append(f"{i}. [{violation['severity']}] {violation['file']}:{violation['line']}")
                report.append(f"   Type: {violation['type']}")
                report.append(f"   {violation['description']}")
                report.append("")
        
        # Compliance by regulation
        if compliance_by_reg:
            report.append("COMPLIANCE STATUS BY REGULATION")
            report.append("-" * 80)
            for regulation, info in compliance_by_reg.items():
                status_icon = '✓' if info['status'] == 'COMPLIANT' else '✗'
                report.append(f"{status_icon} {regulation}: {info['status']} ({info['violations']} violations)")
            report.append("")
        
        # Risk assessment
        risk_level = self._calculate_risk_level(summary)
        report.append("RISK ASSESSMENT")
        report.append("-" * 80)
        report.append(f"Overall Risk Level: {risk_level}")
        report.append("")
        
        # Recommended actions
        recommendations = self._generate_recommendations(summary, top_violations)
        report.append("RECOMMENDED ACTIONS")
        report.append("-" * 80)
        for i, rec in enumerate(recommendations, 1):
            report.append(f"{i}. {rec}")
        report.append("")
        
        report.append("=" * 80)
        report.append("For detailed line-by-line analysis, see the detailed report.")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def _get_score_bar(self, score: int) -> str:
        """Generate visual score bar"""
        filled = int(score / 5)  # 20 blocks for 100%
        empty = 20 - filled
        return f"[{'█' * filled}{'░' * empty}] {score}%"
    
    def _get_score_rating(self, score: int) -> str:
        """Get rating based on score"""
        if score >= 90:
            return "EXCELLENT - Minimal compliance issues"
        elif score >= 75:
            return "GOOD - Minor issues to address"
        elif score >= 60:
            return "FAIR - Moderate compliance concerns"
        elif score >= 40:
            return "POOR - Significant compliance issues"
        else:
            return "CRITICAL - Severe compliance violations"
    
    def _calculate_risk_level(self, summary: Dict) -> str:
        """
        Calculate overall risk level
        
        Args:
            summary: Summary dictionary
            
        Returns:
            Risk level string
        """
        critical = summary.get('critical_issues', 0)
        high = summary.get('high_issues', 0)
        medium = summary.get('medium_issues', 0)
        
        if critical > 0:
            return "🔴 CRITICAL - Immediate action required"
        elif high >= 5:
            return "🟠 HIGH - Urgent attention needed"
        elif high > 0 or medium >= 10:
            return "🟡 MEDIUM - Should be addressed soon"
        elif medium > 0:
            return "🟢 LOW - Monitor and plan remediation"
        else:
            return "✅ MINIMAL - No significant issues found"
    
    def _generate_recommendations(self, summary: Dict, top_violations: List[Dict]) -> List[str]:
        """
        Generate key recommendations based on findings
        
        Args:
            summary: Summary dictionary
            top_violations: List of top violations
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        critical = summary.get('critical_issues', 0)
        high = summary.get('high_issues', 0)
        medium = summary.get('medium_issues', 0)
        
        if critical > 0:
            recommendations.append(
                f"🚨 URGENT: Address {critical} critical security issues immediately to prevent data breaches"
            )
        
        if high > 0:
            recommendations.append(
                f"⚠️  HIGH PRIORITY: Remediate {high} high-severity compliance violations within 30 days"
            )
        
        if medium > 0:
            recommendations.append(
                f"📋 MEDIUM PRIORITY: Plan to address {medium} medium-severity issues in the next sprint"
            )
        
        # Specific recommendations based on violation types
        violation_types = {}
        for v in top_violations:
            vtype = v.get('type', 'unknown')
            violation_types[vtype] = violation_types.get(vtype, 0) + 1
        
        if 'hardcoded_credentials' in violation_types or 'hardcoded_password' in violation_types:
            recommendations.append("🔐 Implement secure secret management (e.g., environment variables, vault)")
        
        if 'sql_injection' in violation_types:
            recommendations.append("💉 Use parameterized queries to prevent SQL injection attacks")
        
        if 'weak_crypto' in violation_types:
            recommendations.append("🔒 Upgrade cryptographic algorithms to SHA-256 or stronger")
        
        # Generic recommendations
        if not recommendations or len(recommendations) < 3:
            recommendations.append("🔄 Implement automated compliance checking in CI/CD pipeline")
            recommendations.append("📚 Conduct regular security training for development team")
            recommendations.append("✅ Establish a compliance review process for all code changes")
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def generate_json_summary(self, analysis_results: Dict) -> str:
        """
        Generate summary in JSON format
        
        Args:
            analysis_results: Complete analysis results
            
        Returns:
            JSON string
        """
        summary = analysis_results.get('summary', {})
        compliance_report = analysis_results.get('stages', {}).get('compliance', {}).get('report', {})
        
        compliance_score = self.calculate_compliance_score(summary)
        top_violations = self.get_top_violations(compliance_report, limit=5)
        compliance_by_reg = self.get_compliance_by_regulation(compliance_report)
        
        summary_data = {
            'timestamp': datetime.now().isoformat(),
            'repository': analysis_results.get('repo_url'),
            'status': analysis_results.get('status'),
            'compliance_score': compliance_score,
            'score_rating': self._get_score_rating(compliance_score),
            'summary': summary,
            'top_violations': top_violations,
            'compliance_by_regulation': compliance_by_reg,
            'risk_level': self._calculate_risk_level(summary),
            'recommendations': self._generate_recommendations(summary, top_violations)
        }
        
        return json.dumps(summary_data, indent=2)
    
    def generate_html_summary(self, analysis_results: Dict) -> str:
        """
        Generate summary in HTML format with styling
        
        Args:
            analysis_results: Complete analysis results
            
        Returns:
            HTML string
        """
        summary = analysis_results.get('summary', {})
        compliance_report = analysis_results.get('stages', {}).get('compliance', {}).get('report', {})
        
        compliance_score = self.calculate_compliance_score(summary)
        top_violations = self.get_top_violations(compliance_report, limit=5)
        compliance_by_reg = self.get_compliance_by_regulation(compliance_report)
        
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append("  <meta charset='UTF-8'>")
        html.append("  <title>Compliance Guardian - Executive Summary</title>")
        html.append("  <style>")
        html.append("    body { font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; background: #f5f5f5; }")
        html.append("    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }")
        html.append("    h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }")
        html.append("    h2 { color: #34495e; margin-top: 30px; border-bottom: 2px solid #ecf0f1; padding-bottom: 5px; }")
        html.append("    .score-container { text-align: center; margin: 30px 0; }")
        html.append("    .score-circle { display: inline-block; width: 200px; height: 200px; border-radius: 50%; ")
        html.append(f"      background: conic-gradient(#3498db {compliance_score * 3.6}deg, #ecf0f1 0deg); ")
        html.append("      position: relative; }")
        html.append("    .score-inner { position: absolute; top: 20px; left: 20px; right: 20px; bottom: 20px; ")
        html.append("      background: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; ")
        html.append("      flex-direction: column; }")
        html.append("    .score-value { font-size: 48px; font-weight: bold; color: #2c3e50; }")
        html.append("    .score-label { font-size: 14px; color: #7f8c8d; }")
        html.append("    .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 20px 0; }")
        html.append("    .stat-card { background: #ecf0f1; padding: 20px; border-radius: 8px; text-align: center; }")
        html.append("    .stat-value { font-size: 32px; font-weight: bold; }")
        html.append("    .stat-label { font-size: 14px; color: #7f8c8d; margin-top: 5px; }")
        html.append("    .critical { color: #e74c3c; }")
        html.append("    .high { color: #e67e22; }")
        html.append("    .medium { color: #f39c12; }")
        html.append("    .low { color: #95a5a6; }")
        html.append("    .violation { margin: 15px 0; padding: 15px; background: #ecf0f1; border-left: 4px solid #3498db; }")
        html.append("    .recommendation { margin: 10px 0; padding: 10px; background: #e8f8f5; border-left: 4px solid #27ae60; }")
        html.append("    .regulation-status { margin: 10px 0; padding: 10px; background: #f8f9fa; }")
        html.append("    .compliant { color: #27ae60; }")
        html.append("    .non-compliant { color: #e74c3c; }")
        html.append("  </style>")
        html.append("</head>")
        html.append("<body>")
        html.append("  <div class='container'>")
        html.append("    <h1>🛡️ Compliance Guardian - Executive Summary</h1>")
        
        # Repository info
        html.append(f"    <p><strong>Repository:</strong> {analysis_results.get('repo_url', 'N/A')}</p>")
        html.append(f"    <p><strong>Analysis Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
        html.append(f"    <p><strong>Status:</strong> {analysis_results.get('status', 'N/A').upper()}</p>")
        
        # Compliance score
        html.append("    <h2>Overall Compliance Score</h2>")
        html.append("    <div class='score-container'>")
        html.append("      <div class='score-circle'>")
        html.append("        <div class='score-inner'>")
        html.append(f"          <div class='score-value'>{compliance_score}</div>")
        html.append("          <div class='score-label'>out of 100</div>")
        html.append("        </div>")
        html.append("      </div>")
        html.append(f"      <p><strong>{self._get_score_rating(compliance_score)}</strong></p>")
        html.append("    </div>")
        
        # Statistics
        html.append("    <h2>Issues by Severity</h2>")
        html.append("    <div class='stats-grid'>")
        html.append(f"      <div class='stat-card'><div class='stat-value critical'>{summary.get('critical_issues', 0)}</div><div class='stat-label'>Critical</div></div>")
        html.append(f"      <div class='stat-card'><div class='stat-value high'>{summary.get('high_issues', 0)}</div><div class='stat-label'>High</div></div>")
        html.append(f"      <div class='stat-card'><div class='stat-value medium'>{summary.get('medium_issues', 0)}</div><div class='stat-label'>Medium</div></div>")
        html.append(f"      <div class='stat-card'><div class='stat-value low'>{summary.get('low_issues', 0)}</div><div class='stat-label'>Low</div></div>")
        html.append("    </div>")
        
        # Top violations
        if top_violations:
            html.append("    <h2>Top 5 Critical Violations</h2>")
            for i, violation in enumerate(top_violations, 1):
                severity_class = violation['severity'].lower()
                html.append(f"    <div class='violation'>")
                html.append(f"      <strong class='{severity_class}'>[{violation['severity']}]</strong> ")
                html.append(f"      {violation['file']}:{violation['line']}<br>")
                html.append(f"      <em>Type: {violation['type']}</em><br>")
                html.append(f"      {violation['description']}")
                html.append("    </div>")
        
        # Compliance by regulation
        if compliance_by_reg:
            html.append("    <h2>Compliance Status by Regulation</h2>")
            for regulation, info in compliance_by_reg.items():
                status_class = 'compliant' if info['status'] == 'COMPLIANT' else 'non-compliant'
                html.append(f"    <div class='regulation-status'>")
                html.append(f"      <strong class='{status_class}'>{regulation}</strong>: {info['status']} ({info['violations']} violations)")
                html.append("    </div>")
        
        # Recommendations
        recommendations = self._generate_recommendations(summary, top_violations)
        html.append("    <h2>Recommended Actions</h2>")
        for rec in recommendations:
            html.append(f"    <div class='recommendation'>{rec}</div>")
        
        html.append("  </div>")
        html.append("</body>")
        html.append("</html>")
        
        return "\n".join(html)
    
    def generate_markdown_summary(self, analysis_results: Dict) -> str:
        """
        Generate summary in Markdown format
        
        Args:
            analysis_results: Complete analysis results
            
        Returns:
            Markdown string
        """
        summary = analysis_results.get('summary', {})
        compliance_report = analysis_results.get('stages', {}).get('compliance', {}).get('report', {})
        
        compliance_score = self.calculate_compliance_score(summary)
        top_violations = self.get_top_violations(compliance_report, limit=5)
        compliance_by_reg = self.get_compliance_by_regulation(compliance_report)
        
        md = []
        md.append("# 🛡️ Compliance Guardian - Executive Summary")
        md.append("")
        md.append("## Repository Information")
        md.append("")
        md.append(f"- **Repository:** {analysis_results.get('repo_url', 'N/A')}")
        md.append(f"- **Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md.append(f"- **Status:** {analysis_results.get('status', 'N/A').upper()}")
        md.append(f"- **Duration:** {analysis_results.get('duration_seconds', 0):.2f} seconds")
        md.append("")
        
        md.append("## Overall Compliance Score")
        md.append("")
        md.append(f"### {compliance_score}/100")
        md.append("")
        md.append(f"**Rating:** {self._get_score_rating(compliance_score)}")
        md.append("")
        
        md.append("## Issues by Severity")
        md.append("")
        md.append("| Severity | Count |")
        md.append("|----------|-------|")
        md.append(f"| 🔴 Critical | {summary.get('critical_issues', 0)} |")
        md.append(f"| 🟠 High | {summary.get('high_issues', 0)} |")
        md.append(f"| 🟡 Medium | {summary.get('medium_issues', 0)} |")
        md.append(f"| 🟢 Low | {summary.get('low_issues', 0)} |")
        md.append("")
        
        if top_violations:
            md.append("## Top 5 Critical Violations")
            md.append("")
            for i, violation in enumerate(top_violations, 1):
                md.append(f"### {i}. [{violation['severity']}] {violation['file']}:{violation['line']}")
                md.append("")
                md.append(f"- **Type:** {violation['type']}")
                md.append(f"- **Description:** {violation['description']}")
                md.append("")
        
        if compliance_by_reg:
            md.append("## Compliance Status by Regulation")
            md.append("")
            for regulation, info in compliance_by_reg.items():
                status_icon = '✅' if info['status'] == 'COMPLIANT' else '❌'
                md.append(f"- {status_icon} **{regulation}**: {info['status']} ({info['violations']} violations)")
            md.append("")
        
        md.append("## Risk Assessment")
        md.append("")
        md.append(f"**Overall Risk Level:** {self._calculate_risk_level(summary)}")
        md.append("")
        
        recommendations = self._generate_recommendations(summary, top_violations)
        md.append("## Recommended Actions")
        md.append("")
        for i, rec in enumerate(recommendations, 1):
            md.append(f"{i}. {rec}")
        md.append("")
        
        md.append("---")
        md.append("")
        md.append("*For detailed line-by-line analysis, see the detailed report.*")
        
        return "\n".join(md)
    
    def save_summary(self, analysis_results: Dict, output_path: str, format: str = 'text'):
        """
        Save summary to file
        
        Args:
            analysis_results: Complete analysis results
            output_path: Path to save the summary
            format: Output format ('text', 'json', 'html', 'markdown')
        """
        try:
            if format == 'json':
                content = self.generate_json_summary(analysis_results)
            elif format == 'html':
                content = self.generate_html_summary(analysis_results)
            elif format == 'markdown':
                content = self.generate_markdown_summary(analysis_results)
            else:
                content = self.generate_summary(analysis_results)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Summary saved to {output_path}")
        
        except Exception as e:
            logger.error(f"Error saving summary: {str(e)}")
            raise

# Made with Bob
