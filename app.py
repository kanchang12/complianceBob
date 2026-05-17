"""
Flask API Application
Complete REST API for Compliance Guardian with background processing
"""

from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flasgger import Swagger
import logging
import os
import sys
import threading
import uuid
import time
import json
import sqlite3
from datetime import datetime
from typing import Dict, Optional
from functools import wraps
from io import BytesIO

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.orchestrator.workflow import WorkflowOrchestrator
from src.reports.summary_generator import SummaryGenerator
from src.reports.detailed_report import DetailedReportGenerator
from config import (
    API_CONFIG, DATABASE_CONFIG, REPO_CONFIG, RAG_CONFIG, 
    AI_MODEL_CONFIG, COMPLIANCE_CATEGORIES
)

logger = logging.getLogger(__name__)

# Global storage for analysis jobs (in production, use Redis or similar)
analysis_jobs = {}
analysis_lock = threading.Lock()


class AnalysisJob:
    """Represents an analysis job with status tracking"""
    
    def __init__(self, analysis_id: str, github_url: str, token: Optional[str] = None, 
                 regulations: Optional[list] = None):
        self.analysis_id = analysis_id
        self.github_url = github_url
        self.token = token
        self.regulations = regulations
        self.status = 'pending'
        self.progress = 0
        self.current_stage = 'initializing'
        self.message = 'Analysis queued'
        self.results = None
        self.error = None
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
    
    def to_dict(self) -> Dict:
        """Convert job to dictionary"""
        return {
            'analysis_id': self.analysis_id,
            'github_url': self.github_url,
            'status': self.status,
            'progress': self.progress,
            'current_stage': self.current_stage,
            'message': self.message,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error': self.error
        }


def validate_github_url(url: str) -> bool:
    """Validate GitHub URL format"""
    if not url:
        return False
    return url.startswith('https://github.com/') or url.startswith('http://github.com/')


def validate_token(token: str) -> bool:
    """Validate GitHub token format (basic check)"""
    if not token:
        return True  # Token is optional
    return len(token) >= 20  # GitHub tokens are typically longer


def sanitize_input(text: str, max_length: int = 500) -> str:
    """Sanitize user input"""
    if not text:
        return ""
    # Remove potentially dangerous characters
    text = text.strip()
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    return text


def require_analysis_id(f):
    """Decorator to validate analysis_id exists"""
    @wraps(f)
    def decorated_function(analysis_id, *args, **kwargs):
        with analysis_lock:
            if analysis_id not in analysis_jobs:
                return jsonify({'error': 'Analysis not found'}), 404
        return f(analysis_id, *args, **kwargs)
    return decorated_function


def create_app(config=None):
    """
    Create and configure Flask application
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Configuration
    app.config['MAX_CONTENT_LENGTH'] = API_CONFIG.get('max_content_length', 16 * 1024 * 1024)
    app.config['JSON_SORT_KEYS'] = False
    
    # Enable CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["https://impossible-kitty-onewebonly-ffa22349.koyeb.app", "https://impossible-kitty-onewebonly-ffa22349.koyeb.app:*"],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })
    
    # Rate limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200000 per day", "5000 per hour"],
        storage_uri="memory://"
    )
    
    # Swagger API documentation
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs"
    }
    
    swagger_template = {
        "info": {
            "title": "Compliance Guardian API",
            "description": "REST API for automated compliance checking",
            "version": "1.0.0"
        },
        "schemes": ["http", "https"],
    }
    
    Swagger(app, config=swagger_config, template=swagger_template)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize orchestrator
    orchestrator_config = {
        'db_path': DATABASE_CONFIG['db_path'],
        'clone_dir': REPO_CONFIG['clone_dir'],
        'model_name': AI_MODEL_CONFIG.get('model_name', 'gpt-4o-mini'),
        'max_files': REPO_CONFIG['max_files'],
        'enable_deep_analysis': True,
        'max_deep_analysis_files': 10,
        'cleanup_after_analysis': True
    }
    
    orchestrator = WorkflowOrchestrator(orchestrator_config)
    
    # ==================== API Endpoints ====================
    
    @app.route('/')
    def index():
        """
        Serve landing page
        ---
        responses:
          200:
            description: Landing page HTML
        """
        landing_path = os.path.join(os.path.dirname(__file__), 'frontend', 'landing.html')
        try:
            with open(landing_path, 'r', encoding='utf-8') as f:
                return f.read(), 200, {'Content-Type': 'text/html'}
        except FileNotFoundError:
            return jsonify({
                'name': 'Compliance Guardian API',
                'version': '1.0.0',
                'status': 'running',
                'documentation': '/api/docs',
                'endpoints': {
                    'health': '/api/health',
                    'analyze': '/api/analyze',
                    'status': '/api/status/<analysis_id>',
                    'results': '/api/results/<analysis_id>',
                    'reports': '/api/reports/<analysis_id>/<format>',
                    'regulations': '/api/regulations',
                    'history': '/api/history'
                }
            })
    
    @app.route('/<path:filename>')
    def serve_static(filename):
        """
        Serve static files from frontend directory
        """
        frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
        file_path = os.path.join(frontend_dir, filename)
        
        # Security check - ensure file is within frontend directory
        if not os.path.abspath(file_path).startswith(os.path.abspath(frontend_dir)):
            return jsonify({'error': 'Access denied'}), 403
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            try:
                # Determine content type
                if filename.endswith('.css'):
                    mimetype = 'text/css'
                elif filename.endswith('.js'):
                    mimetype = 'application/javascript'
                elif filename.endswith('.html'):
                    mimetype = 'text/html'
                elif filename.endswith('.json'):
                    mimetype = 'application/json'
                elif filename.endswith('.png'):
                    mimetype = 'image/png'
                elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
                    mimetype = 'image/jpeg'
                elif filename.endswith('.svg'):
                    mimetype = 'image/svg+xml'
                else:
                    mimetype = 'text/plain'
                
                with open(file_path, 'rb') as f:
                    return f.read(), 200, {'Content-Type': mimetype}
            except Exception as e:
                logger.error(f"Error serving file {filename}: {str(e)}")
                return jsonify({'error': 'File read error'}), 500
        
        # If file not found, return 404 (but don't interfere with API routes)
        return jsonify({'error': 'File not found'}), 404
    
    @app.route('/api/health')
    @limiter.exempt
    def health():
        """
        Health check endpoint
        ---
        responses:
          200:
            description: System health status
        """
        try:
            # Check database connection
            conn = sqlite3.connect(DATABASE_CONFIG['db_path'])
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            conn.close()
            db_status = 'healthy'
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            db_status = 'unhealthy'
        
        health_status = {
            'status': 'healthy' if db_status == 'healthy' else 'degraded',
            'timestamp': datetime.now().isoformat(),
            'components': {
                'database': db_status,
                'api': 'healthy'
            },
            'active_analyses': len([j for j in analysis_jobs.values() if j.status == 'analyzing'])
        }
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return jsonify(health_status), status_code
    
    @app.route('/api/analyze', methods=['POST'])
    @limiter.limit("10 per hour")
    def analyze_repository():
        """
        Start repository analysis
        ---
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              required:
                - github_url
              properties:
                github_url:
                  type: string
                  description: GitHub repository URL
                token:
                  type: string
                  description: Optional GitHub token for private repos
                regulations:
                  type: array
                  items:
                    type: string
                  description: Optional list of specific regulations to check
        responses:
          202:
            description: Analysis started
          400:
            description: Invalid request
          429:
            description: Rate limit exceeded
        """
        try:
            data = request.get_json()
            
            if not data or 'github_url' not in data:
                return jsonify({'error': 'github_url is required'}), 400
            
            github_url = sanitize_input(data['github_url'], 500)
            token = data.get('token')
            regulations = data.get('regulations', [])
            
            # Validate inputs
            if not validate_github_url(github_url):
                return jsonify({'error': 'Invalid GitHub URL format'}), 400
            
            if token and not validate_token(token):
                return jsonify({'error': 'Invalid GitHub token format'}), 400
            
            # Generate unique analysis ID
            analysis_id = str(uuid.uuid4())
            
            # Create job
            job = AnalysisJob(analysis_id, github_url, token, regulations)
            
            with analysis_lock:
                analysis_jobs[analysis_id] = job
            
            # Start analysis in background thread
            thread = threading.Thread(
                target=run_analysis,
                args=(analysis_id, orchestrator),
                daemon=True
            )
            thread.start()
            
            logger.info(f"Started analysis {analysis_id} for {github_url}")
            
            return jsonify({
                'status': 'accepted',
                'analysis_id': analysis_id,
                'message': 'Analysis started',
                'status_url': f'/api/status/{analysis_id}',
                'results_url': f'/api/results/{analysis_id}'
            }), 202
        
        except Exception as e:
            logger.error(f"Error starting analysis: {str(e)}")
            return jsonify({'error': 'Failed to start analysis', 'details': str(e)}), 500
    
    @app.route('/api/status/<analysis_id>')
    @limiter.limit("5000 per hour")
    @require_analysis_id
    def get_status(analysis_id):
        """
        Get analysis status
        ---
        parameters:
          - name: analysis_id
            in: path
            type: string
            required: true
        responses:
          200:
            description: Analysis status
          404:
            description: Analysis not found
        """
        with analysis_lock:
            job = analysis_jobs[analysis_id]
            return jsonify(job.to_dict())
    
    @app.route('/api/results/<analysis_id>')
    @require_analysis_id
    def get_results(analysis_id):
        """
        Get analysis results
        ---
        parameters:
          - name: analysis_id
            in: path
            type: string
            required: true
        responses:
          200:
            description: Analysis results
          404:
            description: Analysis not found
          425:
            description: Analysis not completed yet
        """
        with analysis_lock:
            job = analysis_jobs[analysis_id]
            
            if job.status != 'completed':
                return jsonify({
                    'error': 'Analysis not completed',
                    'status': job.status,
                    'progress': job.progress
                }), 425
            
            if job.error:
                return jsonify({
                    'error': 'Analysis failed',
                    'details': job.error
                }), 500
            
            return jsonify({
                'status': 'success',
                'analysis_id': analysis_id,
                'results': job.results
            })
    
    @app.route('/api/reports/<analysis_id>/<format>')
    @require_analysis_id
    def download_report(analysis_id, format):
        """
        Download analysis report
        ---
        parameters:
          - name: analysis_id
            in: path
            type: string
            required: true
          - name: format
            in: path
            type: string
            required: true
            enum: [json, html, markdown, text]
        responses:
          200:
            description: Report file
          404:
            description: Analysis not found
          400:
            description: Invalid format
        """
        with analysis_lock:
            job = analysis_jobs[analysis_id]
            
            if job.status != 'completed' or not job.results:
                return jsonify({'error': 'Results not available'}), 425
        
        # Generate report based on format
        try:
            if format == 'json':
                content = json.dumps(job.results, indent=2)
                mimetype = 'application/json'
                filename = f'compliance_report_{analysis_id}.json'
            
            elif format == 'html':
                detailed_gen = DetailedReportGenerator()
                content = detailed_gen.generate_html_report(job.results)
                mimetype = 'text/html'
                filename = f'compliance_report_{analysis_id}.html'
            
            elif format == 'markdown':
                content = generate_markdown_report(job.results)
                mimetype = 'text/markdown'
                filename = f'compliance_report_{analysis_id}.md'
            
            elif format == 'text':
                summary_gen = SummaryGenerator()
                content = summary_gen.generate_summary(job.results)
                mimetype = 'text/plain'
                filename = f'compliance_report_{analysis_id}.txt'
            
            else:
                return jsonify({'error': 'Invalid format. Use: json, html, markdown, or text'}), 400
            
            # Create file-like object
            file_obj = BytesIO(content.encode('utf-8'))
            file_obj.seek(0)
            
            return send_file(
                file_obj,
                mimetype=mimetype,
                as_attachment=True,
                download_name=filename
            )
        
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return jsonify({'error': 'Failed to generate report', 'details': str(e)}), 500
    
    @app.route('/api/regulations')
    def list_regulations():
        """
        List available compliance regulations
        ---
        responses:
          200:
            description: List of regulations
        """
        regulations = []
        for key, value in COMPLIANCE_CATEGORIES.items():
            regulations.append({
                'id': key,
                'name': value['name'],
                'severity': value['severity'],
                'keywords': value['keywords']
            })
        
        return jsonify({
            'regulations': regulations,
            'total': len(regulations)
        })
    
    @app.route('/api/history')
    def get_history():
        """
        Get analysis history
        ---
        parameters:
          - name: limit
            in: query
            type: integer
            default: 10
        responses:
          200:
            description: Analysis history
        """
        limit = request.args.get('limit', 10, type=int)
        limit = min(limit, 100)  # Max 100 results
        
        try:
            analyses = orchestrator.list_analyses(limit=limit)
            return jsonify({
                'analyses': analyses,
                'total': len(analyses)
            })
        except Exception as e:
            logger.error(f"Error fetching history: {str(e)}")
            return jsonify({'error': 'Failed to fetch history'}), 500
    
    # ==================== Error Handlers ====================
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        """Handle rate limit errors"""
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': str(e.description)
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        logger.error(f"Internal error: {str(error)}")
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        """Handle request too large errors"""
        return jsonify({'error': 'Request too large'}), 413
    
    return app


def run_analysis(analysis_id: str, orchestrator: WorkflowOrchestrator):
    """
    Run analysis in background thread
    
    Args:
        analysis_id: Analysis job ID
        orchestrator: Workflow orchestrator instance
    """
    with analysis_lock:
        job = analysis_jobs[analysis_id]
        job.status = 'analyzing'
        job.started_at = datetime.now()
    
    def progress_callback(stage: str, progress: int, message: str):
        """Update job progress"""
        with analysis_lock:
            job.current_stage = stage
            job.progress = progress
            job.message = message
            logger.info(f"Analysis {analysis_id}: {stage} - {progress}% - {message}")
    
    try:
        # Run analysis
        results = orchestrator.analyze_repository(
            github_url=job.github_url,
            token=job.token,
            regulations=job.regulations,
            progress_callback=progress_callback
        )
        
        with analysis_lock:
            job.results = results
            job.status = 'completed'
            job.progress = 100
            job.message = 'Analysis completed successfully'
            job.completed_at = datetime.now()
        
        logger.info(f"Analysis {analysis_id} completed successfully")
    
    except Exception as e:
        logger.error(f"Analysis {analysis_id} failed: {str(e)}", exc_info=True)
        with analysis_lock:
            job.status = 'failed'
            job.error = str(e)
            job.message = f'Analysis failed: {str(e)}'
            job.completed_at = datetime.now()


def generate_markdown_report(results: Dict) -> str:
    """Generate markdown format report"""
    md = []
    md.append("# Compliance Guardian Analysis Report\n")
    md.append(f"**Repository:** {results.get('repo_url', 'N/A')}\n")
    md.append(f"**Analysis Date:** {results.get('start_time', 'N/A')}\n")
    md.append(f"**Status:** {results.get('status', 'N/A')}\n\n")
    
    summary = results.get('summary', {})
    md.append("## Summary\n")
    md.append(f"- **Files Analyzed:** {summary.get('files_analyzed', 0)}\n")
    md.append(f"- **Total Issues:** {summary.get('total_issues', 0)}\n")
    md.append(f"- **Critical Issues:** {summary.get('critical_issues', 0)}\n")
    md.append(f"- **High Issues:** {summary.get('high_issues', 0)}\n")
    md.append(f"- **Medium Issues:** {summary.get('medium_issues', 0)}\n")
    md.append(f"- **Low Issues:** {summary.get('low_issues', 0)}\n\n")
    
    # Add findings
    compliance_report = results.get('stages', {}).get('compliance', {}).get('report', {})
    findings = compliance_report.get('findings', [])
    
    if findings:
        md.append("## Findings\n")
        for i, finding in enumerate(findings[:20], 1):  # Top 20 findings
            md.append(f"### {i}. {finding.get('type', 'Unknown')} - {finding.get('severity', 'N/A')}\n")
            md.append(f"**File:** {finding.get('file', 'N/A')}\n")
            md.append(f"**Line:** {finding.get('line', 'N/A')}\n")
            md.append(f"**Description:** {finding.get('description', 'No description')}\n\n")
    
    return ''.join(md)


if __name__ == '__main__':
    app = create_app()
    app.run(
        host=API_CONFIG.get('host', '0.0.0.0'),
        port=API_CONFIG.get('port', 5000),
        debug=API_CONFIG.get('debug', True),
        threaded=True
    )

# Made with Bob
