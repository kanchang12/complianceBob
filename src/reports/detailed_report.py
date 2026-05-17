"""
Detailed Report Generator Module
Generates comprehensive line-by-line compliance reports
"""

from typing import Dict, List, Optional
from datetime import datetime
import json
import logging
import html

logger = logging.getLogger(__name__)


class DetailedReportGenerator:
    """Generates detailed compliance reports"""
    
    def __init__(self):
        """Initialize detailed report generator"""
        self.severity_colors = {
            'CRITICAL': '#e74c3c',
            'HIGH': '#e67e22',
            'MEDIUM': '#f39c12',
            'LOW': '#95a5a6',
            'INFO': '#3498db'
        }
    
    def _get_code_snippet(self, file_content: str, line_number: int, context_lines: int = 3) -> Dict:
        """
        Extract code snippet with context
        
        Args:
            file_content: Full file content
            line_number: Target line number
            context_lines: Number of context lines before/after
            
        Returns:
            Dictionary with snippet info
        """
        lines = file_content.split('\n')
        start_line = max(0, line_number - context_lines - 1)
        end_line = min(len(lines), line_number + context_lines)
        
        snippet_lines = []
        for i in range(start_line, end_line):
            snippet_lines.append({
                'line_number': i + 1,
                'content': lines[i] if i < len(lines) else '',
                'is_target': (i + 1) == line_number
            })
        
        return {
            'start_line': start_line + 1,
            'end_line': end_line,
            'lines': snippet_lines
        }
    
    def _group_findings_by_file(self, findings: List[Dict]) -> Dict[str, List[Dict]]:
        """Group findings by file path"""
        grouped = {}
        for finding in findings:
            file_path = finding.get('file', 'unknown')
            if file_path not in grouped:
                grouped[file_path] = []
            grouped[file_path].append(finding)
        
        # Sort findings within each file by line number
        for file_path in grouped:
            grouped[file_path].sort(key=lambda x: x.get('line', 0))
        
        return grouped
    
    def _get_language_from_file(self, file_path: str) -> str:
        """Determine language from file extension"""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.cs': 'csharp',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml'
        }
        
        for ext, lang in ext_map.items():
            if file_path.endswith(ext):
                return lang
        
        return 'text'
    
    def generate_detailed_report(self, analysis_results: Dict) -> str:
        """
        Generate comprehensive detailed report in plain text
        
        Args:
            analysis_results: Complete analysis results
            
        Returns:
            Formatted detailed report as string
        """
        compliance_report = analysis_results.get('stages', {}).get('compliance', {}).get('report', {})
        findings = compliance_report.get('findings', [])
        
        report = []
        report.append("=" * 100)
        report.append("COMPLIANCE GUARDIAN - DETAILED ANALYSIS REPORT")
        report.append("=" * 100)
        report.append("")
        
        # Header information
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Repository: {analysis_results.get('repo_url', 'N/A')}")
        report.append(f"Analysis Status: {analysis_results.get('status', 'N/A')}")
        report.append(f"Duration: {analysis_results.get('duration_seconds', 0):.2f} seconds")
        report.append("")
        
        # Executive summary section
        report.extend(self._format_executive_summary(analysis_results))
        
        # Findings by file
        report.extend(self._format_findings_by_file(findings))
        
        # Appendix with regulations
        report.extend(self._format_regulations_appendix(compliance_report))
        
        report.append("=" * 100)
        report.append("END OF REPORT")
        report.append("=" * 100)
        
        return "\n".join(report)
    
    def _format_executive_summary(self, analysis_results: Dict) -> List[str]:
        """Format executive summary section"""
        lines = []
        lines.append("=" * 100)
        lines.append("EXECUTIVE SUMMARY")
        lines.append("=" * 100)
        lines.append("")
        
        summary = analysis_results.get('summary', {})
        
        lines.append(f"Files Analyzed: {summary.get('files_analyzed', 0)}")
        lines.append(f"Total Issues: {summary.get('total_issues', 0)}")
        lines.append("")
        
        lines.append("Issues by Severity:")
        lines.append(f"  Critical: {summary.get('critical_issues', 0)}")
        lines.append(f"  High:     {summary.get('high_issues', 0)}")
        lines.append(f"  Medium:   {summary.get('medium_issues', 0)}")
        lines.append(f"  Low:      {summary.get('low_issues', 0)}")
        lines.append("")
        
        return lines
    
    def _format_findings_by_file(self, findings: List[Dict]) -> List[str]:
        """Format findings grouped by file"""
        lines = []
        lines.append("=" * 100)
        lines.append("FINDINGS BY FILE")
        lines.append("=" * 100)
        lines.append("")
        
        grouped = self._group_findings_by_file(findings)
        
        for file_path, file_findings in grouped.items():
            lines.append("-" * 100)
            lines.append(f"FILE: {file_path}")
            lines.append(f"Total Issues: {len(file_findings)}")
            lines.append("-" * 100)
            lines.append("")
            
            for i, finding in enumerate(file_findings, 1):
                lines.append(f"Finding #{i}")
                lines.append(f"  Line: {finding.get('line', 'N/A')}")
                lines.append(f"  Severity: [{finding.get('severity', 'MEDIUM')}]")
                lines.append(f"  Type: {finding.get('type', 'unknown')}")
                lines.append(f"  Confidence: {finding.get('confidence', 85)}%")
                lines.append("")
                
                lines.append(f"  Description:")
                lines.append(f"    {finding.get('description', 'No description')}")
                lines.append("")
                
                # Code snippet
                if finding.get('match'):
                    lines.append(f"  Code Snippet:")
                    lines.append(f"    {finding.get('match', '')[:200]}")
                    lines.append("")
                
                # Violated regulations
                if finding.get('violated_regulations'):
                    lines.append(f"  Violated Regulations:")
                    for reg in finding.get('violated_regulations', []):
                        lines.append(f"    - {reg}")
                    lines.append("")
                
                # Remediation
                if finding.get('remediation'):
                    remediation = finding.get('remediation', {})
                    lines.append(f"  Remediation:")
                    if isinstance(remediation, dict):
                        lines.append(f"    {remediation.get('description', 'No remediation available')}")
                        if remediation.get('example'):
                            lines.append(f"    Example: {remediation.get('example')}")
                    else:
                        lines.append(f"    {remediation}")
                    lines.append("")
                
                lines.append("")
        
        return lines
    
    def _format_regulations_appendix(self, compliance_report: Dict) -> List[str]:
        """Format regulations appendix"""
        lines = []
        lines.append("=" * 100)
        lines.append("APPENDIX: REGULATIONS REFERENCED")
        lines.append("=" * 100)
        lines.append("")
        
        regulation_violations = compliance_report.get('regulation_violations', {})
        
        if regulation_violations:
            for regulation, count in regulation_violations.items():
                lines.append(f"- {regulation}: {count} violations")
        else:
            lines.append("No specific regulations referenced.")
        
        lines.append("")
        return lines
    
    def generate_json_report(self, analysis_results: Dict) -> str:
        """
        Generate detailed report in JSON format
        
        Args:
            analysis_results: Complete analysis results
            
        Returns:
            JSON string
        """
        compliance_report = analysis_results.get('stages', {}).get('compliance', {}).get('report', {})
        
        report_data = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'repository': analysis_results.get('repo_url'),
                'status': analysis_results.get('status'),
                'duration_seconds': analysis_results.get('duration_seconds')
            },
            'summary': analysis_results.get('summary', {}),
            'findings': compliance_report.get('findings', []),
            'findings_by_file': self._group_findings_by_file(compliance_report.get('findings', [])),
            'regulation_violations': compliance_report.get('regulation_violations', {}),
            'recommendations': compliance_report.get('recommendations', [])
        }
        
        return json.dumps(report_data, indent=2)
    
    def generate_html_report(self, analysis_results: Dict) -> str:
        """
        Generate detailed report in HTML format with syntax highlighting
        
        Args:
            analysis_results: Complete analysis results
            
        Returns:
            HTML string
        """
        compliance_report = analysis_results.get('stages', {}).get('compliance', {}).get('report', {})
        findings = compliance_report.get('findings', [])

        policy_findings = [f for f in findings if f.get('type') == 'policy_violation']
        security_findings = [f for f in findings if f.get('type') != 'policy_violation']

        grouped_policy = self._group_findings_by_file(policy_findings)
        grouped_security = self._group_findings_by_file(security_findings)

        html_parts = []
        html_parts.append("<!DOCTYPE html>")
        html_parts.append("<html>")
        html_parts.append("<head>")
        html_parts.append("  <meta charset='UTF-8'>")
        html_parts.append("  <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        html_parts.append("  <title>Compliance Guardian - Detailed Report</title>")
        html_parts.append("  <style>")
        html_parts.append(self._get_html_styles())
        html_parts.append("  </style>")
        html_parts.append("</head>")
        html_parts.append("<body>")
        html_parts.append("  <div class='container'>")

        # Header
        html_parts.append("    <header>")
        html_parts.append("      <h1>&#x1F6E1;&#xFE0F; Compliance Guardian - Detailed Analysis Report</h1>")
        html_parts.append(f"      <div class='metadata'>")
        html_parts.append(f"        <p><strong>Repository:</strong> {html.escape(analysis_results.get('repo_url', 'N/A'))}</p>")
        html_parts.append(f"        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
        html_parts.append(f"        <p><strong>Status:</strong> {html.escape(analysis_results.get('status', 'N/A').upper())}</p>")
        html_parts.append(f"        <p><strong>Duration:</strong> {analysis_results.get('duration_seconds', 0):.2f} seconds</p>")
        html_parts.append("      </div>")
        html_parts.append("    </header>")

        # Executive Summary
        html_parts.append(self._format_html_executive_summary(analysis_results, policy_findings, security_findings))

        # Section 1: Regulatory Compliance Violations
        html_parts.append("    <section class='section-header compliance-section-header'>")
        html_parts.append(f"      <h2>Section 1 &mdash; Regulatory Policy Violations ({len(policy_findings)} findings)</h2>")
        html_parts.append("      <p>Violations identified against official regulation documents: GDPR, HIPAA, PCI-DSS, NIST, ISO 27001, CCPA, OWASP.</p>")
        html_parts.append("    </section>")
        if grouped_policy:
            html_parts.append(self._format_html_findings(grouped_policy))
        else:
            html_parts.append("    <div class='no-findings'>No regulatory policy violations detected.</div>")

        # Section 2: Security Findings
        html_parts.append("    <section class='section-header security-section-header'>")
        html_parts.append(f"      <h2>Section 2 &mdash; Security Findings ({len(security_findings)} findings)</h2>")
        html_parts.append("      <p>Code-level security issues detected by pattern analysis and AI review.</p>")
        html_parts.append("    </section>")
        if grouped_security:
            html_parts.append(self._format_html_findings(grouped_security))
        else:
            html_parts.append("    <div class='no-findings'>No security issues detected.</div>")

        # Regulations Referenced
        html_parts.append(self._format_html_regulations(compliance_report))

        html_parts.append("  </div>")
        html_parts.append("  <script>")
        html_parts.append(self._get_html_scripts())
        html_parts.append("  </script>")
        html_parts.append("</body>")
        html_parts.append("</html>")

        return "\n".join(html_parts)
    
    def _get_html_styles(self) -> str:
        """Get CSS styles for HTML report"""
        return """
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; line-height: 1.6; }
    .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
    header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 10px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    header h1 { font-size: 32px; margin-bottom: 20px; }
    .metadata { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
    .metadata p { background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; }
    
    .summary-section { background: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .summary-section h2 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; margin-bottom: 20px; }
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; margin: 20px 0; }
    .stat-card { background: #ecf0f1; padding: 20px; border-radius: 8px; text-align: center; }
    .stat-value { font-size: 36px; font-weight: bold; margin-bottom: 5px; }
    .stat-label { font-size: 14px; color: #7f8c8d; }
    
    .toc { background: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .toc h2 { color: #2c3e50; margin-bottom: 20px; }
    .toc ul { list-style: none; }
    .toc li { padding: 8px 0; border-bottom: 1px solid #ecf0f1; }
    .toc a { color: #3498db; text-decoration: none; }
    .toc a:hover { text-decoration: underline; }
    
    .file-section { background: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .file-header { background: #34495e; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    .file-header h3 { font-size: 18px; }
    .file-stats { margin-top: 10px; font-size: 14px; opacity: 0.9; }
    
    .finding { background: #f8f9fa; border-left: 4px solid #3498db; padding: 20px; margin-bottom: 20px; border-radius: 5px; }
    .finding.critical { border-left-color: #e74c3c; }
    .finding.high { border-left-color: #e67e22; }
    .finding.medium { border-left-color: #f39c12; }
    .finding.low { border-left-color: #95a5a6; }
    
    .finding-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
    .finding-title { font-size: 18px; font-weight: bold; }
    .severity-badge { padding: 5px 15px; border-radius: 20px; color: white; font-size: 12px; font-weight: bold; }
    .severity-badge.critical { background: #e74c3c; }
    .severity-badge.high { background: #e67e22; }
    .severity-badge.medium { background: #f39c12; }
    .severity-badge.low { background: #95a5a6; }
    
    .finding-details { margin: 15px 0; }
    .finding-details dt { font-weight: bold; color: #2c3e50; margin-top: 10px; }
    .finding-details dd { margin-left: 20px; color: #555; }
    
    .code-snippet { background: #282c34; color: #abb2bf; padding: 15px; border-radius: 5px; overflow-x: auto; margin: 15px 0; font-family: 'Courier New', monospace; font-size: 14px; }
    .code-line { display: block; padding: 2px 0; }
    .code-line.highlight { background: rgba(231, 76, 60, 0.2); }
    .line-number { display: inline-block; width: 40px; color: #5c6370; text-align: right; margin-right: 15px; user-select: none; }
    
    .section-header { padding: 20px 30px; border-radius: 10px; margin-bottom: 10px; margin-top: 20px; }
    .compliance-section-header { background: linear-gradient(135deg, #6c3483, #8e44ad); color: white; }
    .compliance-section-header h2 { color: white; border: none; }
    .compliance-section-header p { opacity: 0.9; margin-top: 6px; }
    .security-section-header { background: linear-gradient(135deg, #1a5276, #2980b9); color: white; }
    .security-section-header h2 { color: white; border: none; }
    .security-section-header p { opacity: 0.9; margin-top: 6px; }
    .no-findings { background: white; padding: 20px 30px; border-radius: 10px; margin-bottom: 20px; color: #27ae60; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .summary-breakdown { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 20px; }
    .breakdown-box { padding: 15px 20px; border-radius: 8px; }
    .breakdown-box h4 { margin-bottom: 6px; font-size: 15px; }
    .breakdown-box p { font-size: 14px; color: #555; }
    .compliance-box { background: #f5eef8; border-left: 4px solid #8e44ad; }
    .security-box { background: #eaf4fb; border-left: 4px solid #2980b9; }
    .remediation { background: #e8f8f5; border-left: 4px solid #27ae60; padding: 15px; border-radius: 5px; margin: 15px 0; }
    .remediation h4 { color: #27ae60; margin-bottom: 10px; }
    .remediation ol { margin: 10px 0 10px 20px; }
    .remediation li { margin: 4px 0; }
    .remediation pre { background: #1e1e1e; color: #d4d4d4; padding: 10px; border-radius: 4px; margin-top: 10px; overflow-x: auto; }
    .remediation em { color: #555; font-size: 13px; }
    
    .regulations-list { list-style: none; }
    .regulations-list li { padding: 10px; background: #f8f9fa; margin: 5px 0; border-radius: 5px; }
    
    .filter-controls { margin: 20px 0; }
    .filter-btn { padding: 10px 20px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; background: #ecf0f1; color: #2c3e50; }
    .filter-btn.active { background: #3498db; color: white; }
    .filter-btn:hover { opacity: 0.8; }
    
    @media print {
      body { background: white; }
      .container { max-width: 100%; }
      .filter-controls { display: none; }
    }
"""
    
    def _get_html_scripts(self) -> str:
        """Get JavaScript for HTML report"""
        return """
    // Filter findings by severity
    function filterBySeverity(severity) {
      const findings = document.querySelectorAll('.finding');
      const buttons = document.querySelectorAll('.filter-btn');
      
      buttons.forEach(btn => btn.classList.remove('active'));
      event.target.classList.add('active');
      
      if (severity === 'all') {
        findings.forEach(f => f.style.display = 'block');
      } else {
        findings.forEach(f => {
          if (f.classList.contains(severity.toLowerCase())) {
            f.style.display = 'block';
          } else {
            f.style.display = 'none';
          }
        });
      }
    }
    
    // Smooth scroll to sections
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    });
"""
    
    def _format_html_executive_summary(self, analysis_results: Dict,
                                        policy_findings: list = None,
                                        security_findings: list = None) -> str:
        """Format executive summary in HTML"""
        import html as html_module
        summary = analysis_results.get('summary', {})
        policy_findings = policy_findings or []
        security_findings = security_findings or []

        policy_critical = sum(1 for f in policy_findings if f.get('severity') == 'CRITICAL')
        policy_high = sum(1 for f in policy_findings if f.get('severity') == 'HIGH')
        policy_medium = sum(1 for f in policy_findings if f.get('severity') == 'MEDIUM')
        sec_critical = sum(1 for f in security_findings if f.get('severity') == 'CRITICAL')
        sec_high = sum(1 for f in security_findings if f.get('severity') == 'HIGH')
        sec_medium = sum(1 for f in security_findings if f.get('severity') == 'MEDIUM')

        out = []
        out.append("    <section class='summary-section'>")
        out.append("      <h2>Executive Summary</h2>")
        out.append("      <div class='stats-grid'>")
        out.append(f"        <div class='stat-card'><div class='stat-value'>{summary.get('files_analyzed', 0)}</div><div class='stat-label'>Files Analyzed</div></div>")
        out.append(f"        <div class='stat-card compliance-stat'><div class='stat-value' style='color:#8e44ad;'>{len(policy_findings)}</div><div class='stat-label'>Policy Violations</div></div>")
        out.append(f"        <div class='stat-card security-stat'><div class='stat-value' style='color:#2980b9;'>{len(security_findings)}</div><div class='stat-label'>Security Findings</div></div>")
        out.append(f"        <div class='stat-card'><div class='stat-value' style='color:#e74c3c;'>{summary.get('critical_issues', 0)}</div><div class='stat-label'>Critical</div></div>")
        out.append(f"        <div class='stat-card'><div class='stat-value' style='color:#e67e22;'>{summary.get('high_issues', 0)}</div><div class='stat-label'>High</div></div>")
        out.append(f"        <div class='stat-card'><div class='stat-value' style='color:#f39c12;'>{summary.get('medium_issues', 0)}</div><div class='stat-label'>Medium</div></div>")
        out.append("      </div>")
        out.append("      <div class='summary-breakdown'>")
        out.append(f"        <div class='breakdown-box compliance-box'><h4>Regulatory Violations</h4><p>Critical: {policy_critical} &nbsp; High: {policy_high} &nbsp; Medium: {policy_medium}</p></div>")
        out.append(f"        <div class='breakdown-box security-box'><h4>Security Issues</h4><p>Critical: {sec_critical} &nbsp; High: {sec_high} &nbsp; Medium: {sec_medium}</p></div>")
        out.append("      </div>")
        out.append("    </section>")

        return "\n".join(out)
    
    def _format_html_toc(self, grouped_findings: Dict) -> str:
        """Format table of contents in HTML"""
        html = []
        html.append("    <section class='toc'>")
        html.append("      <h2>Table of Contents</h2>")
        html.append("      <div class='filter-controls'>")
        html.append("        <button class='filter-btn active' onclick='filterBySeverity(\"all\")'>All</button>")
        html.append("        <button class='filter-btn' onclick='filterBySeverity(\"critical\")'>Critical</button>")
        html.append("        <button class='filter-btn' onclick='filterBySeverity(\"high\")'>High</button>")
        html.append("        <button class='filter-btn' onclick='filterBySeverity(\"medium\")'>Medium</button>")
        html.append("        <button class='filter-btn' onclick='filterBySeverity(\"low\")'>Low</button>")
        html.append("      </div>")
        html.append("      <ul>")
        
        for file_path, findings in grouped_findings.items():
            file_id = file_path.replace('/', '_').replace('.', '_')
            import html as html_module
            html.append(f"        <li><a href='#{file_id}'>{html_module.escape(file_path)} ({len(findings)} issues)</a></li>")
        
        html.append("      </ul>")
        html.append("    </section>")
        
        return "\n".join(html)
    
    def _format_html_findings(self, grouped_findings: Dict) -> str:
        """Format findings in HTML"""
        import html as html_module
        html_lines = []
        
        for file_path, findings in grouped_findings.items():
            file_id = file_path.replace('/', '_').replace('.', '_')
            
            html_lines.append(f"    <section class='file-section' id='{file_id}'>")
            html_lines.append("      <div class='file-header'>")
            html_lines.append(f"        <h3>{html_module.escape(file_path)}</h3>")
            html_lines.append(f"        <div class='file-stats'>Total Issues: {len(findings)}</div>")
            html_lines.append("      </div>")
            
            for i, finding in enumerate(findings, 1):
                severity = finding.get('severity', 'MEDIUM').lower()
                
                html_lines.append(f"      <div class='finding {severity}'>")
                html_lines.append("        <div class='finding-header'>")
                html_lines.append(f"          <div class='finding-title'>Finding #{i}</div>")
                html_lines.append(f"          <span class='severity-badge {severity}'>{finding.get('severity', 'MEDIUM')}</span>")
                html_lines.append("        </div>")
                
                html_lines.append("        <dl class='finding-details'>")
                html_lines.append(f"          <dt>Line:</dt><dd>{finding.get('line', 'N/A')}</dd>")
                html_lines.append(f"          <dt>Type:</dt><dd>{html_module.escape(finding.get('type', 'unknown'))}</dd>")
                html_lines.append(f"          <dt>Confidence:</dt><dd>{finding.get('confidence', 85)}%</dd>")
                html_lines.append(f"          <dt>Description:</dt><dd>{html_module.escape(finding.get('description', 'No description'))}</dd>")
                if finding.get('explanation'):
                    html_lines.append(f"          <dt>Policy Detail:</dt><dd>{html_module.escape(finding.get('explanation', ''))}</dd>")
                
                # Add compliance regulations - use violated_regulations field
                violated_regulations = finding.get('violated_regulations', [])
                if violated_regulations:
                    html_lines.append(f"          <dt>Violated Regulations:</dt><dd><strong>{html_module.escape(', '.join(violated_regulations))}</strong></dd>")
                
                # Add rule match information for compliance context
                rule_match = finding.get('rule_match', {})
                if rule_match and rule_match.get('matched_regulations'):
                    compliance_info = []
                    for reg in rule_match.get('matched_regulations', []):
                        reg_name = reg.get('name', reg.get('regulation', ''))
                        if reg_name and reg_name not in violated_regulations:
                            compliance_info.append(reg_name)
                    if compliance_info:
                        html_lines.append(f"          <dt>Related Compliance:</dt><dd>{html_module.escape(', '.join(compliance_info))}</dd>")
                
                html_lines.append("        </dl>")
                
                # Code snippet
                if finding.get('match'):
                    html_lines.append("        <div class='code-snippet'>")
                    code_lines = finding.get('match', '').split('\n')[:10]
                    for line_num, line in enumerate(code_lines, finding.get('line', 1)):
                        escaped_line = html_module.escape(line)
                        html_lines.append(f"          <span class='code-line highlight'><span class='line-number'>{line_num}</span>{escaped_line}</span>")
                    html_lines.append("        </div>")
                
                # Remediation
                html_lines.append("        <div class='remediation'>")
                html_lines.append("          <h4>&#x1F527; Remediation</h4>")
                remediation = finding.get('remediation', {})
                deep_analysis = finding.get('deep_analysis') or {}
                ai_fix = deep_analysis.get('remediation', '')
                if isinstance(remediation, str) and remediation:
                    html_lines.append(f"          <p>{html_module.escape(remediation)}</p>")
                elif isinstance(remediation, dict) and remediation.get('title'):
                    html_lines.append(f"          <p><strong>{html_module.escape(remediation['title'])}</strong></p>")
                    steps = remediation.get('steps', [])
                    if steps:
                        html_lines.append("          <ol>")
                        for step in steps:
                            html_lines.append(f"            <li>{html_module.escape(step)}</li>")
                        html_lines.append("          </ol>")
                    if remediation.get('code_example'):
                        html_lines.append(f"          <pre><code>{html_module.escape(remediation['code_example'])}</code></pre>")
                    if ai_fix and isinstance(ai_fix, str):
                        html_lines.append(f"          <p><em>AI suggestion: {html_module.escape(ai_fix)}</em></p>")
                elif ai_fix and isinstance(ai_fix, str):
                    html_lines.append(f"          <p>{html_module.escape(ai_fix)}</p>")
                else:
                    html_lines.append("          <p>Review the code manually and apply security best practices.</p>")
                html_lines.append("        </div>")
                
                html_lines.append("      </div>")
            
            html_lines.append("    </section>")
        
        return "\n".join(html_lines)
    
    def _format_html_regulations(self, compliance_report: Dict) -> str:
        """Format regulations appendix in HTML"""
        import html as html_module
        html_lines = []
        html_lines.append("    <section class='summary-section'>")
        html_lines.append("      <h2>Regulations Referenced</h2>")
        
        regulation_violations = compliance_report.get('regulation_violations', {})
        
        if regulation_violations:
            html_lines.append("      <ul class='regulations-list'>")
            for regulation, count in regulation_violations.items():
                html_lines.append(f"        <li><strong>{html_module.escape(regulation)}</strong>: {count} violations</li>")
            html_lines.append("      </ul>")
        else:
            html_lines.append("      <p>No specific regulations referenced.</p>")
        
        html_lines.append("    </section>")
        
        return "\n".join(html_lines)
    
    def generate_markdown_report(self, analysis_results: Dict) -> str:
        """
        Generate detailed report in Markdown format
        
        Args:
            analysis_results: Complete analysis results
            
        Returns:
            Markdown string
        """
        compliance_report = analysis_results.get('stages', {}).get('compliance', {}).get('report', {})
        findings = compliance_report.get('findings', [])
        grouped_findings = self._group_findings_by_file(findings)
        
        md = []
        md.append("# 🛡️ Compliance Guardian - Detailed Analysis Report")
        md.append("")
        md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md.append(f"**Repository:** {analysis_results.get('repo_url', 'N/A')}")
        md.append(f"**Status:** {analysis_results.get('status', 'N/A').upper()}")
        md.append(f"**Duration:** {analysis_results.get('duration_seconds', 0):.2f} seconds")
        md.append("")
        
        # Executive Summary
        md.append("## Executive Summary")
        md.append("")
        summary = analysis_results.get('summary', {})
        md.append(f"- **Files Analyzed:** {summary.get('files_analyzed', 0)}")
        md.append(f"- **Total Issues:** {summary.get('total_issues', 0)}")
        md.append(f"- **Critical:** {summary.get('critical_issues', 0)}")
        md.append(f"- **High:** {summary.get('high_issues', 0)}")
        md.append(f"- **Medium:** {summary.get('medium_issues', 0)}")
        md.append(f"- **Low:** {summary.get('low_issues', 0)}")
        md.append("")
        
        # Findings by File
        md.append("## Findings by File")
        md.append("")
        
        for file_path, file_findings in grouped_findings.items():
            md.append(f"### 📄 {file_path}")
            md.append("")
            md.append(f"**Total Issues:** {len(file_findings)}")
            md.append("")
            
            for i, finding in enumerate(file_findings, 1):
                md.append(f"#### Finding #{i}")
                md.append("")
                md.append(f"- **Line:** {finding.get('line', 'N/A')}")
                md.append(f"- **Severity:** `{finding.get('severity', 'MEDIUM')}`")
                md.append(f"- **Type:** {finding.get('type', 'unknown')}")
                md.append(f"- **Confidence:** {finding.get('confidence', 85)}%")
                md.append("")
                md.append(f"**Description:** {finding.get('description', 'No description')}")
                md.append("")
                
                if finding.get('match'):
                    md.append("**Code Snippet:**")
                    md.append("```")
                    md.append(finding.get('match', '')[:200])
                    md.append("```")
                    md.append("")
                
                if finding.get('remediation'):
                    md.append("**Remediation:**")
                    remediation = finding.get('remediation', {})
                    if isinstance(remediation, dict):
                        md.append(remediation.get('description', 'No remediation available'))
                    else:
                        md.append(str(remediation))
                    md.append("")
                
                md.append("---")
                md.append("")
        
        # Regulations
        md.append("## Regulations Referenced")
        md.append("")
        regulation_violations = compliance_report.get('regulation_violations', {})
        if regulation_violations:
            for regulation, count in regulation_violations.items():
                md.append(f"- **{regulation}:** {count} violations")
        else:
            md.append("No specific regulations referenced.")
        md.append("")
        
        return "\n".join(md)
    
    def save_report(self, analysis_results: Dict, output_path: str, format: str = 'text'):
        """
        Save detailed report to file
        
        Args:
            analysis_results: Complete analysis results
            output_path: Path to save the report
            format: Output format ('text', 'json', 'html', 'markdown')
        """
        try:
            if format == 'json':
                content = self.generate_json_report(analysis_results)
            elif format == 'html':
                content = self.generate_html_report(analysis_results)
            elif format == 'markdown':
                content = self.generate_markdown_report(analysis_results)
            else:
                content = self.generate_detailed_report(analysis_results)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Detailed report saved to {output_path}")
        
        except Exception as e:
            logger.error(f"Error saving detailed report: {str(e)}")
            raise

# Made with Bob
