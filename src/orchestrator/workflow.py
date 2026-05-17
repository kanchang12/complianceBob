"""
Workflow Orchestrator Module
Coordinates the entire compliance checking workflow
"""

from typing import Dict, List, Optional, Callable
import logging
import sqlite3
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from ..rag.pdf_processor import PDFProcessor
from ..rag.embedder import Embedder
from ..rag.vector_store import VectorStore
from ..analyzer.repo_cloner import RepoCloner
from ..analyzer.file_parser import FileParser
from ..checker.checker import ComplianceChecker
from ..reports.summary_generator import SummaryGenerator
from ..reports.detailed_report import DetailedReportGenerator

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """Orchestrates the complete compliance checking workflow"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize workflow orchestrator
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Initialize all components
        logger.info("Initializing Compliance Guardian components...")
        
        self.pdf_processor = PDFProcessor()
        self.embedder = Embedder()
        self.vector_store = VectorStore(
            db_path=self.config.get('db_path', 'database/compliance.db')
        )
        self.repo_cloner = RepoCloner(
            clone_dir=self.config.get('clone_dir', 'data/repos')
        )
        self.file_parser = FileParser()
        self.compliance_checker = ComplianceChecker(
            vector_store=self.vector_store,
            embedder=self.embedder,
            model_name=self.config.get('model_name', 'gemma2:2b')
        )
        self.summary_generator = SummaryGenerator()
        self.detailed_report_generator = DetailedReportGenerator()
        
        # Database connection
        self.db_path = self.config.get('db_path', 'database/compliance.db')
        
        logger.info("All components initialized successfully")
    
    def process_compliance_documents(self, pdf_paths: List[str]) -> Dict:
        """
        Process compliance PDF documents and store in vector database
        
        Args:
            pdf_paths: List of paths to PDF documents
            
        Returns:
            Processing results
        """
        logger.info(f"Processing {len(pdf_paths)} compliance documents...")
        
        results = {
            'processed': 0,
            'failed': 0,
            'total_chunks': 0,
            'documents': []
        }
        
        for pdf_path in pdf_paths:
            try:
                # Extract text from PDF
                logger.info(f"Processing {pdf_path}")
                text = self.pdf_processor.extract_text(pdf_path)
                
                # Chunk the text
                chunks = self.pdf_processor.chunk_text(text)
                
                # Create embeddings
                embeddings = self.embedder.embed_batch(chunks)
                
                # Store in vector database
                embeddings_data = [
                    (pdf_path, chunk, embedding, {'source': pdf_path})
                    for chunk, embedding in zip(chunks, embeddings)
                ]
                self.vector_store.store_embeddings_batch(embeddings_data)
                
                results['processed'] += 1
                results['total_chunks'] += len(chunks)
                results['documents'].append({
                    'path': pdf_path,
                    'chunks': len(chunks),
                    'status': 'success'
                })
                
                logger.info(f"Successfully processed {pdf_path}: {len(chunks)} chunks")
                
            except Exception as e:
                logger.error(f"Failed to process {pdf_path}: {str(e)}")
                results['failed'] += 1
                results['documents'].append({
                    'path': pdf_path,
                    'status': 'failed',
                    'error': str(e)
                })
        
        logger.info(f"Document processing complete: {results['processed']} succeeded, "
                   f"{results['failed']} failed")
        
        return results
    
    def analyze_repository(
        self,
        github_url: str,
        token: Optional[str] = None,
        regulations: Optional[List[str]] = None,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Complete workflow: clone repo, scan, analyze, generate reports, and store results
        
        Args:
            github_url: GitHub repository URL
            token: Optional GitHub token for private repos
            regulations: Optional list of specific regulations to check
            progress_callback: Optional callback function(stage, progress, message)
            
        Returns:
            Complete analysis results with reports
        """
        start_time = datetime.now()
        logger.info(f"Starting compliance analysis for {github_url}")
        
        results = {
            'repo_url': github_url,
            'start_time': start_time.isoformat(),
            'status': 'in_progress',
            'stages': {},
            'analysis_id': None
        }
        
        repo_path = None
        
        try:
            # Stage 1: Clone repository
            self._update_progress(progress_callback, 'clone', 10, 'Cloning repository...')
            logger.info("Stage 1: Cloning repository...")
            repo_path = self.repo_cloner.clone_repository(github_url, token=token)
            repo_info = self.repo_cloner.get_repo_info(repo_path)
            results['stages']['clone'] = {
                'status': 'success',
                'repo_path': repo_path,
                'repo_info': repo_info
            }
            
            # Stage 2: Parse files
            self._update_progress(progress_callback, 'parse', 30, 'Parsing repository files...')
            logger.info("Stage 2: Parsing repository files...")
            files_info = self.file_parser.scan_repository(repo_path)
            
            # Limit files for performance
            max_files = self.config.get('max_files', 100)
            files_to_parse = files_info[:max_files]
            
            parsed_files = self.file_parser.parse_files_batch(
                [f['path'] for f in files_to_parse]
            )
            results['stages']['parse'] = {
                'status': 'success',
                'total_files': len(files_info),
                'parsed_files': len(parsed_files)
            }
            
            # Stage 3: Compliance checking
            self._update_progress(progress_callback, 'check', 50, 'Running compliance checks...')
            logger.info("Stage 3: Running compliance checks...")
            
            compliance_report = self.compliance_checker.check_compliance(
                parsed_files,
                regulations=regulations,
                enable_deep_analysis=self.config.get('enable_deep_analysis', True),
                max_deep_analysis_files=self.config.get('max_deep_analysis_files', 10)
            )
            
            results['stages']['compliance'] = {
                'status': 'success',
                'report': compliance_report
            }
            
            # Stage 4: Generate reports
            self._update_progress(progress_callback, 'report', 70, 'Generating reports...')
            logger.info("Stage 4: Generating reports...")
            
            # Prepare analysis results for report generation
            analysis_for_reports = {
                'repo_url': github_url,
                'status': 'completed',
                'duration_seconds': (datetime.now() - start_time).total_seconds(),
                'stages': results['stages'],
                'summary': self._build_summary(compliance_report, results['stages'])
            }
            
            # Generate summary report
            summary_text = self.summary_generator.generate_summary(analysis_for_reports)
            summary_json = self.summary_generator.generate_json_summary(analysis_for_reports)
            
            # Generate detailed report
            detailed_text = self.detailed_report_generator.generate_detailed_report(analysis_for_reports)
            detailed_json = self.detailed_report_generator.generate_json_report(analysis_for_reports)
            detailed_html = self.detailed_report_generator.generate_html_report(analysis_for_reports)
            
            results['reports'] = {
                'summary': {
                    'text': summary_text,
                    'json': summary_json
                },
                'detailed': {
                    'text': detailed_text,
                    'json': detailed_json,
                    'html': detailed_html
                }
            }
            
            # Stage 5: Store results in database
            self._update_progress(progress_callback, 'store', 90, 'Storing results in database...')
            logger.info("Stage 5: Storing results in database...")
            analysis_id = self._store_analysis_results(github_url, results, compliance_report)
            results['analysis_id'] = analysis_id
            
            # Stage 6: Cleanup temporary files (optional)
            if self.config.get('cleanup_after_analysis', False):
                self._update_progress(progress_callback, 'cleanup', 95, 'Cleaning up temporary files...')
                logger.info("Stage 6: Cleaning up temporary files...")
                if repo_path:
                    self.repo_cloner.cleanup_repository(repo_path)
            
            # Finalize
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            results['status'] = 'completed'
            results['end_time'] = end_time.isoformat()
            results['duration_seconds'] = duration
            results['summary'] = self._build_summary(compliance_report, results['stages'])
            
            self._update_progress(progress_callback, 'complete', 100, 'Analysis complete!')
            logger.info(f"Analysis completed in {duration:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}", exc_info=True)
            results['status'] = 'failed'
            results['error'] = str(e)
            results['end_time'] = datetime.now().isoformat()
            
            # Try to cleanup on error
            if repo_path and os.path.exists(repo_path):
                try:
                    self.repo_cloner.cleanup_repository(repo_path)
                except:
                    pass
        
        return results
    
    def _update_progress(self, callback: Optional[Callable], stage: str, progress: int, message: str):
        """Update progress via callback if provided"""
        if callback:
            try:
                callback(stage, progress, message)
            except Exception as e:
                logger.warning(f"Progress callback error: {str(e)}")
    
    def _build_summary(self, compliance_report: Dict, stages: Dict) -> Dict:
        """
        Build summary from compliance report and stages
        
        Args:
            compliance_report: Compliance check report
            stages: Analysis stages results
            
        Returns:
            Summary dictionary
        """
        summary = compliance_report.get('summary', {})
        
        return {
            'files_analyzed': stages.get('parse', {}).get('parsed_files', 0),
            'total_issues': summary.get('total_findings', 0),
            'critical_issues': summary.get('by_severity', {}).get('CRITICAL', 0),
            'high_issues': summary.get('by_severity', {}).get('HIGH', 0),
            'medium_issues': summary.get('by_severity', {}).get('MEDIUM', 0),
            'low_issues': summary.get('by_severity', {}).get('LOW', 0),
            'by_type': summary.get('by_type', {}),
            'requires_immediate_action': summary.get('requires_immediate_action', 0)
        }
    
    def _store_analysis_results(self, repo_url: str, results: Dict, compliance_report: Dict) -> int:
        """
        Store analysis results in database
        
        Args:
            repo_url: Repository URL
            results: Analysis results
            compliance_report: Compliance report
            
        Returns:
            Analysis ID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert analysis record
            cursor.execute('''
                INSERT INTO analyses (
                    repository_url, status, started_at, completed_at,
                    total_files, total_findings, critical_count, high_count,
                    medium_count, low_count, results_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                repo_url,
                results.get('status', 'completed'),
                results.get('start_time'),
                results.get('end_time'),
                results.get('summary', {}).get('files_analyzed', 0),
                results.get('summary', {}).get('total_issues', 0),
                results.get('summary', {}).get('critical_issues', 0),
                results.get('summary', {}).get('high_issues', 0),
                results.get('summary', {}).get('medium_issues', 0),
                results.get('summary', {}).get('low_issues', 0),
                json.dumps(results)
            ))
            
            analysis_id = cursor.lastrowid
            
            # Insert findings
            findings = compliance_report.get('findings', [])
            for finding in findings:
                cursor.execute('''
                    INSERT INTO findings (
                        analysis_id, file_path, line_number, severity,
                        finding_type, description, code_snippet, remediation
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    analysis_id,
                    finding.get('file', ''),
                    finding.get('line', 0),
                    finding.get('severity', 'MEDIUM'),
                    finding.get('type', 'unknown'),
                    finding.get('description', ''),
                    finding.get('match', '')[:500],  # Limit snippet length
                    json.dumps(finding.get('remediation', {}))
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Stored analysis results with ID: {analysis_id}")
            return analysis_id
            
        except Exception as e:
            logger.error(f"Error storing analysis results: {str(e)}")
            raise
    
    def get_analysis_by_id(self, analysis_id: int) -> Optional[Dict]:
        """
        Retrieve analysis results by ID
        
        Args:
            analysis_id: Analysis ID
            
        Returns:
            Analysis results or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM analyses WHERE id = ?', (analysis_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Convert to dict
            analysis = dict(row)
            
            # Parse JSON results
            if analysis.get('results_json'):
                analysis['results'] = json.loads(analysis['results_json'])
            
            # Get findings
            cursor.execute('SELECT * FROM findings WHERE analysis_id = ?', (analysis_id,))
            findings = [dict(row) for row in cursor.fetchall()]
            analysis['findings'] = findings
            
            conn.close()
            return analysis
            
        except Exception as e:
            logger.error(f"Error retrieving analysis: {str(e)}")
            return None
    
    def list_analyses(self, limit: int = 10) -> List[Dict]:
        """
        List recent analyses
        
        Args:
            limit: Maximum number of analyses to return
            
        Returns:
            List of analysis summaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, repository_url, status, started_at, completed_at,
                       total_files, total_findings, critical_count, high_count
                FROM analyses
                ORDER BY started_at DESC
                LIMIT ?
            ''', (limit,))
            
            analyses = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return analyses
            
        except Exception as e:
            logger.error(f"Error listing analyses: {str(e)}")
            return []
    
    def save_reports_to_files(self, results: Dict, output_dir: str):
        """
        Save generated reports to files
        
        Args:
            results: Analysis results with reports
            output_dir: Directory to save reports
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            reports = results.get('reports', {})
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save summary reports
            if 'summary' in reports:
                summary_text_path = os.path.join(output_dir, f'summary_{timestamp}.txt')
                with open(summary_text_path, 'w', encoding='utf-8') as f:
                    f.write(reports['summary']['text'])
                logger.info(f"Saved summary text to {summary_text_path}")
                
                summary_json_path = os.path.join(output_dir, f'summary_{timestamp}.json')
                with open(summary_json_path, 'w', encoding='utf-8') as f:
                    f.write(reports['summary']['json'])
                logger.info(f"Saved summary JSON to {summary_json_path}")
            
            # Save detailed reports
            if 'detailed' in reports:
                detailed_text_path = os.path.join(output_dir, f'detailed_{timestamp}.txt')
                with open(detailed_text_path, 'w', encoding='utf-8') as f:
                    f.write(reports['detailed']['text'])
                logger.info(f"Saved detailed text to {detailed_text_path}")
                
                detailed_json_path = os.path.join(output_dir, f'detailed_{timestamp}.json')
                with open(detailed_json_path, 'w', encoding='utf-8') as f:
                    f.write(reports['detailed']['json'])
                logger.info(f"Saved detailed JSON to {detailed_json_path}")
                
                detailed_html_path = os.path.join(output_dir, f'detailed_{timestamp}.html')
                with open(detailed_html_path, 'w', encoding='utf-8') as f:
                    f.write(reports['detailed']['html'])
                logger.info(f"Saved detailed HTML to {detailed_html_path}")
            
        except Exception as e:
            logger.error(f"Error saving reports: {str(e)}")
            raise
    
    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up resources...")
        try:
            self.vector_store.close()
            self.repo_cloner.cleanup_all()
            logger.info("Cleanup complete")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

# Made with Bob
