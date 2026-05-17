-- Compliance Guardian Database Schema
-- SQLite database for storing embeddings and analysis results

-- Embeddings table for RAG system
CREATE TABLE IF NOT EXISTS embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding BLOB NOT NULL,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- Index for faster document lookups
CREATE INDEX IF NOT EXISTS idx_document_id ON embeddings(document_id);
CREATE INDEX IF NOT EXISTS idx_created_at ON embeddings(created_at);

-- Documents table for tracking processed compliance documents
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    document_type TEXT,
    total_chunks INTEGER DEFAULT 0,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'processed'
);

-- Analyses table (used by workflow orchestrator)
CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repository_url TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    total_files INTEGER DEFAULT 0,
    total_findings INTEGER DEFAULT 0,
    critical_count INTEGER DEFAULT 0,
    high_count INTEGER DEFAULT 0,
    medium_count INTEGER DEFAULT 0,
    low_count INTEGER DEFAULT 0,
    results_json TEXT
);

-- Index for analyses
CREATE INDEX IF NOT EXISTS idx_repository_url ON analyses(repository_url);
CREATE INDEX IF NOT EXISTS idx_started_at ON analyses(started_at);
CREATE INDEX IF NOT EXISTS idx_analyses_status ON analyses(status);

-- Analysis results table (legacy, kept for compatibility)
CREATE TABLE IF NOT EXISTS analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_url TEXT NOT NULL,
    repo_name TEXT,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,
    duration_seconds REAL,
    files_analyzed INTEGER DEFAULT 0,
    total_issues INTEGER DEFAULT 0,
    critical_issues INTEGER DEFAULT 0,
    high_issues INTEGER DEFAULT 0,
    medium_issues INTEGER DEFAULT 0,
    low_issues INTEGER DEFAULT 0,
    risk_level TEXT,
    results_json TEXT,
    summary_text TEXT
);

-- Index for analysis results
CREATE INDEX IF NOT EXISTS idx_repo_url ON analysis_results(repo_url);
CREATE INDEX IF NOT EXISTS idx_analysis_date ON analysis_results(analysis_date);
CREATE INDEX IF NOT EXISTS idx_status ON analysis_results(status);

-- Findings table for detailed issue tracking
CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    line_number INTEGER,
    finding_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    pattern TEXT,
    description TEXT,
    code_snippet TEXT,
    remediation TEXT,
    regulation TEXT,
    recommended_fix TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);

-- Index for findings
CREATE INDEX IF NOT EXISTS idx_analysis_id ON findings(analysis_id);
CREATE INDEX IF NOT EXISTS idx_severity ON findings(severity);
CREATE INDEX IF NOT EXISTS idx_finding_type ON findings(finding_type);

-- Compliance rules table
CREATE TABLE IF NOT EXISTS compliance_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name TEXT NOT NULL,
    category TEXT NOT NULL,
    regulation TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT DEFAULT 'medium',
    pattern TEXT,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for compliance rules
CREATE INDEX IF NOT EXISTS idx_category ON compliance_rules(category);
CREATE INDEX IF NOT EXISTS idx_regulation ON compliance_rules(regulation);
CREATE INDEX IF NOT EXISTS idx_active ON compliance_rules(active);

-- Insert default compliance rules
INSERT INTO compliance_rules (rule_name, category, regulation, description, severity, pattern) VALUES
('Hardcoded Credentials', 'security', 'OWASP', 'Detect hardcoded passwords and API keys', 'high', 'password|api_key|secret'),
('SQL Injection Risk', 'security', 'OWASP', 'Detect potential SQL injection vulnerabilities', 'critical', 'execute|query.*\+'),
('PII Exposure', 'privacy', 'GDPR', 'Detect potential exposure of personally identifiable information', 'high', 'email|ssn|credit_card'),
('Missing Encryption', 'security', 'NIST', 'Detect unencrypted sensitive data transmission', 'high', 'http://|ftp://'),
('Insufficient Logging', 'compliance', 'SOX', 'Detect missing audit logging', 'medium', 'audit|log'),
('Access Control', 'security', 'ISO27001', 'Detect missing access control checks', 'high', 'authenticate|authorize');

-- Statistics table for tracking system usage
CREATE TABLE IF NOT EXISTS statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metric_date DATE DEFAULT (date('now')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for statistics
CREATE INDEX IF NOT EXISTS idx_metric_name ON statistics(metric_name);
CREATE INDEX IF NOT EXISTS idx_metric_date ON statistics(metric_date);

-- View for analysis summary
CREATE VIEW IF NOT EXISTS analysis_summary AS
SELECT 
    a.id,
    a.repo_url,
    a.repo_name,
    a.analysis_date,
    a.status,
    a.total_issues,
    a.risk_level,
    COUNT(f.id) as finding_count,
    SUM(CASE WHEN f.severity = 'critical' THEN 1 ELSE 0 END) as critical_count,
    SUM(CASE WHEN f.severity = 'high' THEN 1 ELSE 0 END) as high_count,
    SUM(CASE WHEN f.severity = 'medium' THEN 1 ELSE 0 END) as medium_count,
    SUM(CASE WHEN f.severity = 'low' THEN 1 ELSE 0 END) as low_count
FROM analysis_results a
LEFT JOIN findings f ON a.id = f.analysis_id
GROUP BY a.id;

-- View for document statistics
CREATE VIEW IF NOT EXISTS document_statistics AS
SELECT 
    d.id,
    d.filename,
    d.document_type,
    d.total_chunks,
    d.processed_at,
    COUNT(e.id) as embedding_count
FROM documents d
LEFT JOIN embeddings e ON d.id = e.document_id
GROUP BY d.id;

-- Made with Bob
