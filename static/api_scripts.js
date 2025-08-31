/**
 * JavaScript for Vectorized CPT API Testing Interface
 * Handles all interactive functionality for testing microservices
 */

// Global state
let currentApiKey = null;
let isApiConfigured = false;

// Tab switching functionality
function switchTab(event, tabName) {
    // Hide all tab panels
    const tabPanels = document.querySelectorAll('.tab-panel');
    tabPanels.forEach(panel => panel.classList.remove('active'));
    
    // Remove active class from all tabs
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => tab.classList.remove('active'));
    
    // Show selected tab panel and activate tab
    document.getElementById(tabName).classList.add('active');
    event.target.classList.add('active');
}

// API Key Management
function showApiKeyModal() {
    document.getElementById('apiKeyModal').style.display = 'block';
}

function hideApiKeyModal() {
    document.getElementById('apiKeyModal').style.display = 'none';
    document.getElementById('apiKeyInput').value = '';
}

async function configureApiKey(event) {
    event.preventDefault();
    
    const apiKey = document.getElementById('apiKeyInput').value.trim();
    if (!apiKey) {
        showError('Please enter an API key');
        return;
    }
    
    try {
        const response = await fetch('/api/configure', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ api_key: apiKey })
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentApiKey = apiKey;
            isApiConfigured = true;
            updateApiStatus('connected', `Key: ${apiKey.substring(0, 20)}...`);
            showSuccess('API key configured successfully! Gateway connection verified.');
            hideApiKeyModal();
            
            // Refresh health and usage if on those tabs
            refreshHealthStatus();
            refreshUsageStats();
        } else {
            showError(`API key configuration failed: ${result.error}`);
        }
    } catch (error) {
        showError(`Configuration failed: ${error.message}`);
    }
}

function updateApiStatus(status, text) {
    const indicator = document.getElementById('apiStatusIndicator');
    indicator.className = `status-indicator status-${status}`;
    
    if (status === 'connected') {
        indicator.textContent = '✅ API Connected';
    } else if (status === 'disconnected') {
        indicator.textContent = '❌ API Disconnected';
    } else {
        indicator.textContent = '⚠️ API Key Required';
    }
}

// Complete Workflow Functions
async function runCompleteWorkflow(event) {
    event.preventDefault();
    
    if (!isApiConfigured) {
        showError('Please configure an API key first');
        showApiKeyModal();
        return;
    }
    
    const text = document.getElementById('workflowText').value.trim();
    const maxResults = document.getElementById('maxResults').value;
    
    if (!text) {
        showError('Please enter medical note text');
        return;
    }
    
    const loadingDiv = document.getElementById('workflowLoading');
    const resultsDiv = document.getElementById('workflowResults');
    
    loadingDiv.classList.add('show');
    resultsDiv.style.display = 'none';
    
    try {
        const response = await fetch('/api/workflow', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                max_results: parseInt(maxResults),
                api_key: currentApiKey
            })
        });
        
        const result = await response.json();
        
        loadingDiv.classList.remove('show');
        displayWorkflowResults(result, resultsDiv);
        resultsDiv.style.display = 'block';
        
    } catch (error) {
        loadingDiv.classList.remove('show');
        showError(`Workflow failed: ${error.message}`);
    }
}

function displayWorkflowResults(result, container) {
    if (!result.success) {
        container.innerHTML = `
            <div class="error">
                <h3>❌ Workflow Failed</h3>
                <p>${result.error}</p>
            </div>
        `;
        return;
    }
    
    const processingTime = result.total_processing_time_ms || 0;
    const servicesUsed = result.services_used || [];
    
    container.innerHTML = `
        <div class="success">
            <h3>✅ Workflow Completed Successfully</h3>
            <p>Processing time: ${processingTime}ms | Services used: ${servicesUsed.join(', ')}</p>
        </div>
        
        <div class="workflow-step">
            <h4>
                📝 Step 1: Text Extraction
                <span class="step-status status-completed">✅ Completed</span>
            </h4>
            <div class="code-block">${result.step1_extracted_text || 'N/A'}</div>
        </div>
        
        <div class="workflow-step">
            <h4>
                🤖 Step 2: AI Procedure Extraction  
                <span class="step-status status-completed">✅ Completed</span>
            </h4>
            <div class="code-block">${result.step2_extracted_procedures || 'N/A'}</div>
        </div>
        
        <div class="workflow-step">
            <h4>
                🔍 Step 3: CPT Code Search Results
                <span class="step-status status-completed">✅ ${(result.step3_cpt_results || []).length} codes found</span>
            </h4>
            ${displayCPTResults(result.step3_cpt_results || [])}
        </div>
        
        ${result.step4_comprehensive_codes ? `
        <div class="workflow-step">
            <h4>
                🏥 Step 4: Comprehensive Medical Coding
                <span class="step-status status-completed">✅ Enhanced analysis</span>
            </h4>
            ${displayComprehensiveResults(result.step4_comprehensive_codes)}
        </div>
        ` : ''}
    `;
}

function displayCPTResults(results) {
    if (!results || results.length === 0) {
        return '<p>No CPT codes found</p>';
    }
    
    return `
        <div class="cpt-results">
            ${results.map(result => `
                <div class="cpt-card">
                    <div>
                        <span class="cpt-code">CPT ${result.cpt_code}</span>
                        <span class="similarity-score">${((result.similarity_score || 0) * 100).toFixed(1)}%</span>
                    </div>
                    <div style="margin-top: 8px;">
                        <strong>${result.description || 'No description'}</strong>
                    </div>
                    ${result.category ? `<div style="color: #666; font-size: 0.9em; margin-top: 4px;">Category: ${result.category}</div>` : ''}
                </div>
            `).join('')}
        </div>
    `;
}

function displayComprehensiveResults(comprehensive) {
    let html = '';
    
    if (comprehensive.anesthesia_codes && comprehensive.anesthesia_codes.length > 0) {
        html += `
            <h5>💉 Anesthesia Codes</h5>
            <div style="display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap;">
                ${comprehensive.anesthesia_codes.map(code => 
                    `<span class="cpt-code" style="background: #9c27b0;">${code.code} - ${code.description}</span>`
                ).join('')}
            </div>
        `;
    }
    
    if (comprehensive.modifiers && comprehensive.modifiers.length > 0) {
        html += `
            <h5>🔧 Modifiers</h5>
            <div style="display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap;">
                ${comprehensive.modifiers.map(modifier => 
                    `<span class="cpt-code" style="background: #ff9800;">${modifier.modifier} - ${modifier.description}</span>`
                ).join('')}
            </div>
        `;
    }
    
    if (comprehensive.related_codes && comprehensive.related_codes.length > 0) {
        html += `
            <h5>🔗 Related Diagnostic Codes</h5>
            <div style="display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap;">
                ${comprehensive.related_codes.map(code => 
                    `<span class="cpt-code" style="background: #607d8b;">${code.code} - ${code.description}</span>`
                ).join('')}
            </div>
        `;
    }
    
    if (comprehensive.billing_summary) {
        html += `
            <h5>💰 Billing Summary</h5>
            <div class="code-block">${JSON.stringify(comprehensive.billing_summary, null, 2)}</div>
        `;
    }
    
    return html || '<p>No comprehensive coding data available</p>';
}

// Individual Service Testing Functions
async function testExtractProcedures(event) {
    event.preventDefault();
    
    if (!isApiConfigured) {
        showError('Please configure an API key first');
        return;
    }
    
    const text = document.getElementById('extractText').value.trim();
    if (!text) {
        showError('Please enter text to extract procedures from');
        return;
    }
    
    try {
        const response = await fetch('/api/test/extract', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: text, api_key: currentApiKey })
        });
        
        const result = await response.json();
        const resultsDiv = document.getElementById('extractResults');
        
        if (result.success) {
            resultsDiv.innerHTML = `
                <div class="success" style="margin-top: 15px;">
                    <h4>✅ Extraction Successful</h4>
                    <div class="code-block">${JSON.stringify(result.data, null, 2)}</div>
                </div>
            `;
        } else {
            resultsDiv.innerHTML = `
                <div class="error" style="margin-top: 15px;">
                    <h4>❌ Extraction Failed</h4>
                    <p>${result.error}</p>
                </div>
            `;
        }
    } catch (error) {
        document.getElementById('extractResults').innerHTML = `
            <div class="error" style="margin-top: 15px;">
                <h4>❌ Request Failed</h4>
                <p>${error.message}</p>
            </div>
        `;
    }
}

async function testCPTSearch(event) {
    event.preventDefault();
    
    if (!isApiConfigured) {
        showError('Please configure an API key first');
        return;
    }
    
    const text = document.getElementById('searchText').value.trim();
    if (!text) {
        showError('Please enter procedure description to search');
        return;
    }
    
    try {
        const response = await fetch('/api/test/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: text, max_results: 10, api_key: currentApiKey })
        });
        
        const result = await response.json();
        const resultsDiv = document.getElementById('searchResults');
        
        if (result.success && result.data.results) {
            resultsDiv.innerHTML = `
                <div class="success" style="margin-top: 15px;">
                    <h4>✅ Found ${result.data.results.length} CPT Codes</h4>
                    ${displayCPTResults(result.data.results)}
                </div>
            `;
        } else {
            resultsDiv.innerHTML = `
                <div class="error" style="margin-top: 15px;">
                    <h4>❌ Search Failed</h4>
                    <p>${result.error || 'No results found'}</p>
                </div>
            `;
        }
    } catch (error) {
        document.getElementById('searchResults').innerHTML = `
            <div class="error" style="margin-top: 15px;">
                <h4>❌ Request Failed</h4>
                <p>${error.message}</p>
            </div>
        `;
    }
}

async function testComprehensiveCoding(event) {
    event.preventDefault();
    
    if (!isApiConfigured) {
        showError('Please configure an API key first');
        return;
    }
    
    const primaryCodes = document.getElementById('primaryCodes').value.trim();
    const medicalText = document.getElementById('medicalText').value.trim();
    
    if (!primaryCodes || !medicalText) {
        showError('Please fill in all required fields');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('primary_codes', primaryCodes);
        formData.append('medical_text', medicalText);
        formData.append('original_note', medicalText);
        formData.append('api_key', currentApiKey);
        
        const response = await fetch('/api/test/coding', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        const resultsDiv = document.getElementById('codingResults');
        
        if (result.success) {
            resultsDiv.innerHTML = `
                <div class="success" style="margin-top: 15px;">
                    <h4>✅ Comprehensive Coding Complete</h4>
                    ${displayComprehensiveResults(result.data)}
                </div>
            `;
        } else {
            resultsDiv.innerHTML = `
                <div class="error" style="margin-top: 15px;">
                    <h4>❌ Coding Failed</h4>
                    <p>${result.error}</p>
                </div>
            `;
        }
    } catch (error) {
        document.getElementById('codingResults').innerHTML = `
            <div class="error" style="margin-top: 15px;">
                <h4>❌ Request Failed</h4>
                <p>${error.message}</p>
            </div>
        `;
    }
}

// PDF Processing Functions
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        const dropZone = document.getElementById('pdfDropZone');
        dropZone.innerHTML = `
            <div>
                📄 ${file.name} selected
                <br>
                <small>Size: ${(file.size / 1024 / 1024).toFixed(2)} MB</small>
            </div>
        `;
    }
}

// Drag and drop functionality
document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('pdfDropZone');
    
    if (dropZone) {
        dropZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        
        dropZone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        });
        
        dropZone.addEventListener('drop', function(e) {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                document.getElementById('pdfFile').files = files;
                handleFileSelect({ target: { files: files } });
            }
        });
    }
});

async function processPDF(event) {
    event.preventDefault();
    
    if (!isApiConfigured) {
        showError('Please configure an API key first');
        return;
    }
    
    const fileInput = document.getElementById('pdfFile');
    const additionalText = document.getElementById('pdfAdditionalText').value.trim();
    
    if (!fileInput.files[0] && !additionalText) {
        showError('Please select a PDF file or enter additional text');
        return;
    }
    
    const loadingDiv = document.getElementById('pdfLoading');
    const resultsDiv = document.getElementById('pdfResults');
    
    loadingDiv.classList.add('show');
    resultsDiv.style.display = 'none';
    
    try {
        const formData = new FormData();
        if (fileInput.files[0]) {
            formData.append('pdf_file', fileInput.files[0]);
        }
        formData.append('text', additionalText);
        formData.append('max_results', '20');
        formData.append('api_key', currentApiKey);
        
        const response = await fetch('/api/workflow/pdf', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        loadingDiv.classList.remove('show');
        displayWorkflowResults(result, resultsDiv);
        resultsDiv.style.display = 'block';
        
    } catch (error) {
        loadingDiv.classList.remove('show');
        showError(`PDF processing failed: ${error.message}`);
    }
}

function clearPDF() {
    document.getElementById('pdfFile').value = '';
    document.getElementById('pdfAdditionalText').value = '';
    document.getElementById('pdfDropZone').innerHTML = `
        <div>
            📄 Click to select or drag & drop a PDF file
            <br>
            <small>Supported: Medical notes, discharge summaries, operative reports</small>
        </div>
    `;
    document.getElementById('pdfResults').style.display = 'none';
}

// Health Dashboard Functions
async function refreshHealthStatus() {
    if (!isApiConfigured) {
        document.getElementById('healthDashboard').innerHTML = `
            <div class="service-card">
                <div class="service-header">
                    <span class="service-name">API Key Required</span>
                    <span class="service-status status-warning">⚠️ Configure</span>
                </div>
                <div>Please configure an API key to view service health status.</div>
            </div>
        `;
        return;
    }
    
    try {
        const response = await fetch('/api/health');
        const result = await response.json();
        
        const dashboard = document.getElementById('healthDashboard');
        
        if (result.success === false) {
            dashboard.innerHTML = `
                <div class="service-card">
                    <div class="service-header">
                        <span class="service-name">Health Check Failed</span>
                        <span class="service-status service-unhealthy">❌ Error</span>
                    </div>
                    <div>${result.error}</div>
                </div>
            `;
            return;
        }
        
        const services = result.services_status || {};
        const gatewayStatus = result.gateway_status || 'unknown';
        
        let html = `
            <div class="service-card">
                <div class="service-header">
                    <span class="service-name">API Gateway</span>
                    <span class="service-status service-${gatewayStatus === 'healthy' ? 'healthy' : 'unhealthy'}">
                        ${gatewayStatus === 'healthy' ? '✅ Healthy' : '❌ Unhealthy'}
                    </span>
                </div>
                <div>
                    <strong>Services:</strong> ${result.total_services || 0} total, ${result.healthy_services || 0} healthy<br>
                    <strong>Last Check:</strong> ${new Date().toLocaleTimeString()}
                </div>
            </div>
        `;
        
        Object.entries(services).forEach(([serviceName, serviceData]) => {
            const status = serviceData.status || 'unknown';
            const statusClass = status === 'healthy' ? 'service-healthy' : 
                               status === 'degraded' ? 'service-degraded' : 'service-unhealthy';
            const statusIcon = status === 'healthy' ? '✅' : 
                              status === 'degraded' ? '⚠️' : '❌';
            
            html += `
                <div class="service-card">
                    <div class="service-header">
                        <span class="service-name">${serviceName.replace('_', ' ').toUpperCase()}</span>
                        <span class="service-status ${statusClass}">${statusIcon} ${status.toUpperCase()}</span>
                    </div>
                    <div>
                        <strong>Endpoint:</strong> ${serviceData.endpoint || 'N/A'}<br>
                        ${serviceData.error ? `<strong>Error:</strong> ${serviceData.error}<br>` : ''}
                        ${serviceData.details ? `<strong>Details:</strong> ${JSON.stringify(serviceData.details)}<br>` : ''}
                    </div>
                </div>
            `;
        });
        
        dashboard.innerHTML = html;
        
    } catch (error) {
        document.getElementById('healthDashboard').innerHTML = `
            <div class="service-card">
                <div class="service-header">
                    <span class="service-name">Health Check Failed</span>
                    <span class="service-status service-unhealthy">❌ Error</span>
                </div>
                <div>Failed to fetch health status: ${error.message}</div>
            </div>
        `;
    }
}

// Usage Statistics Functions
async function refreshUsageStats() {
    if (!isApiConfigured) {
        document.getElementById('usageStats').innerHTML = `
            <div class="service-card">
                <div class="service-header">
                    <span class="service-name">Usage Statistics</span>
                </div>
                <div>Configure an API key to view usage statistics</div>
            </div>
        `;
        return;
    }
    
    try {
        const response = await fetch('/api/usage');
        const stats = await response.json();
        
        const container = document.getElementById('usageStats');
        
        if (response.ok) {
            container.innerHTML = `
                <div class="service-card">
                    <div class="service-header">
                        <span class="service-name">API Usage Statistics</span>
                        <span class="service-status service-healthy">📊 Active</span>
                    </div>
                    <div>
                        <strong>Total Requests:</strong> ${stats.total_requests || 0}<br>
                        <strong>This Hour:</strong> ${stats.requests_this_hour || 0}<br>
                        <strong>Successful:</strong> ${stats.successful_requests || 0}<br>
                        <strong>Failed:</strong> ${stats.failed_requests || 0}<br>
                        <strong>Avg Response Time:</strong> ${(stats.average_response_time_ms || 0).toFixed(2)}ms<br>
                        <strong>Success Rate:</strong> ${stats.total_requests > 0 ? 
                            ((stats.successful_requests / stats.total_requests) * 100).toFixed(1) : 0}%
                    </div>
                </div>
                
                <div class="service-card">
                    <div class="service-header">
                        <span class="service-name">Rate Limiting</span>
                        <span class="service-status service-healthy">⏱️ Active</span>
                    </div>
                    <div>
                        <strong>Current Usage:</strong> ${stats.requests_this_hour || 0}/1000 per hour<br>
                        <strong>Remaining:</strong> ${1000 - (stats.requests_this_hour || 0)} requests<br>
                        <strong>Usage:</strong> ${((stats.requests_this_hour || 0) / 1000 * 100).toFixed(1)}% of limit
                    </div>
                </div>
            `;
        } else {
            container.innerHTML = `
                <div class="service-card">
                    <div class="service-header">
                        <span class="service-name">Usage Statistics</span>
                        <span class="service-status service-unhealthy">❌ Error</span>
                    </div>
                    <div>Failed to load usage statistics: ${stats.detail || 'Unknown error'}</div>
                </div>
            `;
        }
    } catch (error) {
        document.getElementById('usageStats').innerHTML = `
            <div class="service-card">
                <div class="service-header">
                    <span class="service-name">Usage Statistics</span>
                    <span class="service-status service-unhealthy">❌ Error</span>
                </div>
                <div>Failed to fetch usage statistics: ${error.message}</div>
            </div>
        `;
    }
}

// Utility Functions
function showError(message) {
    // Create temporary error notification
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.style.position = 'fixed';
    errorDiv.style.top = '20px';
    errorDiv.style.right = '20px';
    errorDiv.style.zIndex = '1000';
    errorDiv.style.maxWidth = '400px';
    errorDiv.innerHTML = `
        <strong>Error:</strong> ${message}
        <button onclick="this.parentElement.remove()" style="float: right; background: none; border: none; color: inherit; cursor: pointer;">×</button>
    `;
    
    document.body.appendChild(errorDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (errorDiv.parentElement) {
            errorDiv.remove();
        }
    }, 5000);
}

function showSuccess(message) {
    // Create temporary success notification
    const successDiv = document.createElement('div');
    successDiv.className = 'success';
    successDiv.style.position = 'fixed';
    successDiv.style.top = '20px';
    successDiv.style.right = '20px';
    successDiv.style.zIndex = '1000';
    successDiv.style.maxWidth = '400px';
    successDiv.innerHTML = `
        <strong>Success:</strong> ${message}
        <button onclick="this.parentElement.remove()" style="float: right; background: none; border: none; color: inherit; cursor: pointer;">×</button>
    `;
    
    document.body.appendChild(successDiv);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (successDiv.parentElement) {
            successDiv.remove();
        }
    }, 3000);
}

// Initialize API status on page load
document.addEventListener('DOMContentLoaded', function() {
    // Check if API is already configured (server-side rendered)
    const statusIndicator = document.getElementById('apiStatusIndicator');
    if (statusIndicator && statusIndicator.textContent.includes('Connected')) {
        isApiConfigured = true;
        // Extract API key from page if available - this would need to be passed from server
    }
    
    // Close modal when clicking outside
    window.onclick = function(event) {
        const modal = document.getElementById('apiKeyModal');
        if (event.target === modal) {
            hideApiKeyModal();
        }
    }
});