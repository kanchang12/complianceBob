// Compliance Guardian Frontend JavaScript
// Enhanced to work with complete Flask API backend

const API_BASE_URL = 'http://localhost:5000';

// DOM Elements
const analyzeForm = document.getElementById('analyzeForm');
const statusSection = document.getElementById('statusSection');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');
const statusMessage = document.getElementById('statusMessage');
const errorMessage = document.getElementById('errorMessage');

// Event Listeners
analyzeForm.addEventListener('submit', handleAnalyze);
document.getElementById('retryBtn').addEventListener('click', resetForm);
document.getElementById('downloadSummary').addEventListener('click', () => downloadReport('text'));
document.getElementById('downloadDetailed').addEventListener('click', () => downloadReport('html'));

let currentAnalysisId = null;
let currentResults = null;
let statusCheckInterval = null;

/**
 * Handle repository analysis
 */
async function handleAnalyze(e) {
    e.preventDefault();
    
    const repoUrl = document.getElementById('repoUrl').value.trim();
    
    if (!repoUrl) {
        showError('Please enter a valid repository URL');
        return;
    }
    
    // Validate GitHub URL
    if (!repoUrl.startsWith('https://github.com/') && !repoUrl.startsWith('http://github.com/')) {
        showError('Please enter a valid GitHub repository URL (e.g., https://github.com/user/repo)');
        return;
    }
    
    // Show status section
    hideAllSections();
    statusSection.style.display = 'block';
    updateStatus('Submitting analysis request...', 0);
    
    try {
        // Start analysis
        const response = await fetch(`${API_BASE_URL}/api/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                github_url: repoUrl
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `API error: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'accepted') {
            currentAnalysisId = data.analysis_id;
            updateStatus('Analysis started, checking status...', 5);
            
            // Start polling for status
            startStatusPolling();
        } else {
            throw new Error(data.error || 'Failed to start analysis');
        }
        
    } catch (error) {
        console.error('Analysis error:', error);
        showError(error.message);
        stopStatusPolling();
    }
}

/**
 * Start polling for analysis status
 */
function startStatusPolling() {
    // Clear any existing interval
    stopStatusPolling();
    
    // Poll every 2 seconds
    statusCheckInterval = setInterval(checkAnalysisStatus, 2000);
    
    // Check immediately
    checkAnalysisStatus();
}

/**
 * Stop polling for status
 */
function stopStatusPolling() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
        statusCheckInterval = null;
    }
}

/**
 * Check analysis status
 */
async function checkAnalysisStatus() {
    if (!currentAnalysisId) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/status/${currentAnalysisId}`);
        
        if (!response.ok) {
            throw new Error('Failed to check status');
        }
        
        const data = await response.json();
        
        // Update UI with current status
        const message = `${data.current_stage}: ${data.message}`;
        updateStatus(message, data.progress);
        
        // Check if completed
        if (data.status === 'completed') {
            stopStatusPolling();
            await fetchResults();
        } else if (data.status === 'failed') {
            stopStatusPolling();
            showError(data.error || 'Analysis failed');
        }
        
    } catch (error) {
        console.error('Status check error:', error);
        // Don't stop polling on temporary errors
    }
}

/**
 * Fetch analysis results
 */
async function fetchResults() {
    if (!currentAnalysisId) return;
    
    try {
        updateStatus('Fetching results...', 95);
        
        const response = await fetch(`${API_BASE_URL}/api/results/${currentAnalysisId}`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to fetch results');
        }
        
        const data = await response.json();
        
        if (data.status === 'success') {
            currentResults = data.results;
            displayResults(data.results);
        } else {
            throw new Error(data.error || 'Failed to get results');
        }
        
    } catch (error) {
        console.error('Results fetch error:', error);
        showError(error.message);
    }
}

/**
 * Update status message and progress
 */
function updateStatus(message, progress) {
    statusMessage.textContent = message;
    
    // Update progress bar if it exists
    const progressBar = document.querySelector('.progress-bar');
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
    }
}

/**
 * Display analysis results
 */
function displayResults(results) {
    hideAllSections();
    resultsSection.style.display = 'block';
    
    const summary = results.summary || {};
    
    // Update summary stats
    document.getElementById('filesAnalyzed').textContent = summary.files_analyzed || 0;
    document.getElementById('totalIssues').textContent = summary.total_issues || 0;
    
    // Update risk level
    const riskLevel = calculateRiskLevel(summary);
    const riskElement = document.getElementById('riskLevel');
    riskElement.textContent = riskLevel;
    riskElement.className = 'stat-value risk-level ' + riskLevel.toLowerCase();
    
    // Update severity counts
    document.getElementById('criticalCount').textContent = summary.critical_issues || 0;
    document.getElementById('highCount').textContent = summary.high_issues || 0;
    document.getElementById('mediumCount').textContent = summary.medium_issues || 0;
    document.getElementById('lowCount').textContent = summary.low_issues || 0;
    
    // Display findings
    displayFindings(results);
}

/**
 * Calculate risk level
 */
function calculateRiskLevel(summary) {
    const critical = summary.critical_issues || 0;
    const high = summary.high_issues || 0;
    const medium = summary.medium_issues || 0;
    
    if (critical > 0) return 'CRITICAL';
    if (high >= 5) return 'HIGH';
    if (high > 0 || medium >= 10) return 'MEDIUM';
    if (medium > 0) return 'LOW';
    return 'MINIMAL';
}

/**
 * Display findings list
 */
function displayFindings(results) {
    const findingsList = document.getElementById('findingsList');
    findingsList.innerHTML = '';
    
    // Get findings from compliance report
    const complianceReport = results.stages?.compliance?.report || {};
    const findings = complianceReport.findings || [];
    
    // Display top 10 findings
    const topFindings = findings.slice(0, 10);
    
    if (topFindings.length === 0) {
        findingsList.innerHTML = '<p class="no-findings">✓ No significant compliance issues found!</p>';
        return;
    }
    
    topFindings.forEach(finding => {
        const findingItem = document.createElement('div');
        findingItem.className = 'finding-item';
        
        const severity = finding.severity || 'info';
        const severityClass = severity.toLowerCase();
        
        findingItem.innerHTML = `
            <div class="finding-header">
                <span class="finding-file">${truncatePath(finding.file)}</span>
                <span class="finding-severity ${severityClass}">${severity.toUpperCase()}</span>
            </div>
            <div class="finding-description">${escapeHtml(finding.description || 'No description')}</div>
            <div class="finding-line">Line ${finding.line || 'N/A'} | Type: ${finding.type || 'N/A'}</div>
        `;
        
        findingsList.appendChild(findingItem);
    });
    
    // Add "show more" message if there are more findings
    if (findings.length > 10) {
        const moreMessage = document.createElement('p');
        moreMessage.className = 'more-findings';
        moreMessage.textContent = `+ ${findings.length - 10} more findings (download full report to see all)`;
        findingsList.appendChild(moreMessage);
    }
}

/**
 * Truncate file path for display
 */
function truncatePath(path) {
    if (!path) return 'Unknown';
    const parts = path.split(/[/\\]/);
    if (parts.length > 3) {
        return '.../' + parts.slice(-3).join('/');
    }
    return path;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Download report in specified format
 */
async function downloadReport(format) {
    if (!currentAnalysisId) {
        alert('No analysis results available');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/reports/${currentAnalysisId}/${format}`);
        
        if (!response.ok) {
            throw new Error('Failed to download report');
        }
        
        // Get filename from Content-Disposition header or use default
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `compliance_report.${format}`;
        if (contentDisposition) {
            const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition);
            if (matches != null && matches[1]) {
                filename = matches[1].replace(/['"]/g, '');
            }
        }
        
        // Download file
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
    } catch (error) {
        console.error('Download error:', error);
        alert('Failed to download report: ' + error.message);
    }
}

/**
 * Show error message
 */
function showError(message) {
    hideAllSections();
    errorSection.style.display = 'block';
    errorMessage.textContent = message;
    stopStatusPolling();
}

/**
 * Hide all sections
 */
function hideAllSections() {
    statusSection.style.display = 'none';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'none';
}

/**
 * Reset form
 */
function resetForm() {
    hideAllSections();
    document.getElementById('repoUrl').value = '';
    currentAnalysisId = null;
    currentResults = null;
    stopStatusPolling();
}

/**
 * Check API health on page load
 */
async function checkApiHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/health`);
        const data = await response.json();
        
        if (data.status !== 'healthy') {
            console.warn('API health check:', data);
        }
    } catch (error) {
        console.error('API health check failed:', error);
        console.warn('Make sure the Flask API is running on http://localhost:5000');
    }
}

// Check API health when page loads
window.addEventListener('load', checkApiHealth);

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    stopStatusPolling();
});

// Made with Bob
