"""
Compliance Guardian Configuration
Central configuration file for all settings
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent.absolute()

# Database Configuration
DATABASE_CONFIG = {
    'db_path': os.path.join(BASE_DIR, 'database', 'compliance.db'),
    'schema_path': os.path.join(BASE_DIR, 'database', 'schema.sql')
}

# RAG Configuration
RAG_CONFIG = {
    'embedding_model': 'text-embedding-3-small',  # OpenAI embedding model
    'chunk_size': 1000,  # Characters per chunk
    'chunk_overlap': 200,  # Overlap between chunks
    'top_k_results': 5  # Number of similar chunks to retrieve
}

# AI Model Configuration
AI_MODEL_CONFIG = {
    # Primary provider: 'openai', 'anthropic', 'ollama'
    'provider': os.getenv('LLM_PROVIDER', 'ollama'),
    
    # OpenAI Configuration
    'openai_model': 'gpt-4o-mini',  # or 'gpt-4o' for best results
    'openai_api_key': os.getenv('OPENAI_API_KEY', ''),
    
    # Anthropic Configuration
    'anthropic_model': 'claude-3-5-sonnet-20241022',
    'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY', ''),
    
    # Ollama Configuration (local fallback)
    'ollama_model': 'llama3.1:8b',  # Upgraded from gemma2:2b
    
    # Common settings
    'temperature': 0.1,
    'max_tokens': 2000,
    'timeout': 300
}

# Repository Analysis Configuration
REPO_CONFIG = {
    'clone_dir': os.path.join(BASE_DIR, 'data', 'repos'),
    'max_files': 100,  # Maximum files to analyze
    'max_file_size': 1024 * 1024,  # 1MB max file size
    'supported_extensions': [
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
        '.cs', '.go', '.rb', '.php', '.swift', '.kt', '.rs', '.scala',
        '.html', '.css', '.sql', '.sh', '.yaml', '.yml', '.json', '.xml'
    ],
    'ignore_dirs': [
        'node_modules', '.git', '__pycache__', 'venv', 'env',
        '.venv', 'dist', 'build', 'target', '.idea', '.vscode',
        'vendor', 'coverage', '.pytest_cache', '.mypy_cache'
    ]
}

# Compliance Scanning Configuration
SCAN_CONFIG = {
    'quick_scan_enabled': True,
    'deep_analysis_enabled': True,
    'max_deep_analysis_files': 10,  # Limit deep analysis to top N files
    'chunk_size_for_analysis': 50  # Lines per chunk for deep analysis
}

# Security Patterns (for quick scan)
SECURITY_PATTERNS = {
    'hardcoded_password': r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']',
    'api_key': r'(?i)(api[_-]?key|apikey|access[_-]?key)\s*=\s*["\'][^"\']+["\']',
    'secret_key': r'(?i)(secret[_-]?key|secretkey)\s*=\s*["\'][^"\']+["\']',
    'private_key': r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----',
    'aws_key': r'(?i)(AKIA[0-9A-Z]{16})',
    'sql_injection': r'(?i)(execute|exec|query)\s*\(\s*["\'].*\+.*["\']',
    'eval_usage': r'(?i)\beval\s*\(',
    'exec_usage': r'(?i)\bexec\s*\(',
}

# Privacy Patterns (for quick scan)
PRIVACY_PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
    'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
}

# Compliance Categories
COMPLIANCE_CATEGORIES = {
    'gdpr': {
        'name': 'General Data Protection Regulation',
        'keywords': ['gdpr', 'data protection', 'right to be forgotten', 'data subject'],
        'severity': 'high'
    },
    'hipaa': {
        'name': 'Health Insurance Portability and Accountability Act',
        'keywords': ['hipaa', 'phi', 'protected health information', 'medical record'],
        'severity': 'critical'
    },
    'pci': {
        'name': 'Payment Card Industry Data Security Standard',
        'keywords': ['pci', 'payment card', 'cardholder data', 'credit card'],
        'severity': 'critical'
    },
    'sox': {
        'name': 'Sarbanes-Oxley Act',
        'keywords': ['sox', 'sarbanes', 'financial reporting', 'audit trail'],
        'severity': 'high'
    },
    'ccpa': {
        'name': 'California Consumer Privacy Act',
        'keywords': ['ccpa', 'california consumer', 'do not sell', 'personal information'],
        'severity': 'high'
    },
    'owasp': {
        'name': 'OWASP Top 10',
        'keywords': ['owasp', 'injection', 'broken authentication', 'xss'],
        'severity': 'high'
    },
    'nist': {
        'name': 'NIST Cybersecurity Framework',
        'keywords': ['nist', 'cybersecurity framework', 'access control'],
        'severity': 'medium'
    },
    'iso27001': {
        'name': 'ISO/IEC 27001',
        'keywords': ['iso 27001', 'information security', 'isms'],
        'severity': 'medium'
    }
}

# API Configuration
API_CONFIG = {
    'host': '0.0.0.0',
    'port': int(os.getenv('PORT', 5000)),
    'debug': True,
    'cors_enabled': True,
    'max_content_length': 16 * 1024 * 1024,  # 16MB max request size
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'log_file': os.path.join(BASE_DIR, 'logs', 'compliance_guardian.log'),
    'max_bytes': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5
}

# Report Configuration
REPORT_CONFIG = {
    'output_dir': os.path.join(BASE_DIR, 'reports'),
    'formats': ['text', 'json', 'html'],
    'include_summary': True,
    'include_detailed': True
}

# Performance Configuration
PERFORMANCE_CONFIG = {
    'max_workers': 4,  # For parallel processing
    'batch_size': 32,  # For batch embedding
    'cache_enabled': True,
    'cache_ttl': 3600  # 1 hour cache TTL
}

# Feature Flags
FEATURE_FLAGS = {
    'enable_rag': True,
    'enable_quick_scan': True,
    'enable_deep_analysis': True,
    'enable_reports': True,
    'enable_api': True,
    'enable_frontend': True
}

# Environment-specific overrides
ENV = os.getenv('ENVIRONMENT', 'development')

if ENV == 'production':
    API_CONFIG['debug'] = False
    LOGGING_CONFIG['level'] = 'WARNING'
    PERFORMANCE_CONFIG['cache_enabled'] = True
elif ENV == 'testing':
    DATABASE_CONFIG['db_path'] = ':memory:'
    API_CONFIG['debug'] = True
    LOGGING_CONFIG['level'] = 'DEBUG'

# Export all configurations
__all__ = [
    'BASE_DIR',
    'DATABASE_CONFIG',
    'RAG_CONFIG',
    'AI_MODEL_CONFIG',
    'REPO_CONFIG',
    'SCAN_CONFIG',
    'SECURITY_PATTERNS',
    'PRIVACY_PATTERNS',
    'COMPLIANCE_CATEGORIES',
    'API_CONFIG',
    'LOGGING_CONFIG',
    'REPORT_CONFIG',
    'PERFORMANCE_CONFIG',
    'FEATURE_FLAGS',
    'ENV'
]

# Made with Bob
