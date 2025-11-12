// VGAudiophile Frontend Application
const API_BASE = '/api';

let currentPage = 0;
const pageSize = 20;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    initializeSearch();
    initializeScan();
    loadSoundtracks();
    loadStats();
    loadScanHistory();
});

// Tab switching
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;
            
            // Update buttons
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Update content
            tabContents.forEach(content => content.classList.remove('active'));
            document.getElementById(`${tabName}-tab`).classList.add('active');
            
            // Load data for active tab
            if (tabName === 'browse') {
                loadSoundtracks();
            } else if (tabName === 'stats') {
                loadStats();
            } else if (tabName === 'scan') {
                loadScanHistory();
            }
        });
    });
}

// Search functionality
function initializeSearch() {
    const searchButton = document.getElementById('search-button');
    const searchInput = document.getElementById('search-input');
    
    searchButton.addEventListener('click', () => {
        currentPage = 0;
        loadSoundtracks();
    });
    
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            currentPage = 0;
            loadSoundtracks();
        }
    });
    
    // Pagination
    document.getElementById('prev-page').addEventListener('click', () => {
        if (currentPage > 0) {
            currentPage--;
            loadSoundtracks();
        }
    });
    
    document.getElementById('next-page').addEventListener('click', () => {
        currentPage++;
        loadSoundtracks();
    });
}

// Load soundtracks
async function loadSoundtracks() {
    const list = document.getElementById('soundtracks-list');
    list.innerHTML = '<div class="loading">Loading soundtracks...</div>';
    
    const search = document.getElementById('search-input').value;
    const releaseType = document.getElementById('release-type-filter').value;
    const sourceType = document.getElementById('source-type-filter').value;
    
    const params = new URLSearchParams({
        skip: (currentPage * pageSize).toString(),
        limit: pageSize.toString()
    });
    
    if (search) params.append('search', search);
    if (releaseType) params.append('release_type', releaseType);
    if (sourceType) params.append('source_type', sourceType);
    
    try {
        const response = await fetch(`${API_BASE}/soundtracks?${params}`);
        if (!response.ok) throw new Error('Failed to load soundtracks');
        
        const soundtracks = await response.json();
        
        if (soundtracks.length === 0) {
            list.innerHTML = '<div class="loading">No soundtracks found.</div>';
            return;
        }
        
        list.innerHTML = soundtracks.map(st => createSoundtrackCard(st)).join('');
        
        // Update pagination
        document.getElementById('page-info').textContent = `Page ${currentPage + 1}`;
        document.getElementById('prev-page').disabled = currentPage === 0;
        document.getElementById('next-page').disabled = soundtracks.length < pageSize;
        
        // Add click handlers
        document.querySelectorAll('.soundtrack-card').forEach(card => {
            card.addEventListener('click', () => {
                const id = card.dataset.id;
                showSoundtrackDetails(id);
            });
        });
    } catch (error) {
        list.innerHTML = `<div class="error">Error loading soundtracks: ${error.message}</div>`;
    }
}

// Create soundtrack card
function createSoundtrackCard(soundtrack) {
    const artists = soundtrack.artists.map(a => a.name).join(', ') || 'Unknown Artist';
    const duration = soundtrack.duration ? formatDuration(soundtrack.duration) : '';
    const gameName = soundtrack.game_name ? ` • ${soundtrack.game_name}` : '';
    
    return `
        <div class="soundtrack-card" data-id="${soundtrack.id}">
            <h3>${escapeHtml(soundtrack.title)}</h3>
            <div class="meta">${escapeHtml(artists)}</div>
            ${soundtrack.album ? `<div class="meta">Album: ${escapeHtml(soundtrack.album)}</div>` : ''}
            ${duration ? `<div class="meta">Duration: ${duration}</div>` : ''}
            ${gameName ? `<div class="meta">${escapeHtml(gameName)}</div>` : ''}
            <span class="badge">${soundtrack.release_type}</span>
        </div>
    `;
}

// Show soundtrack details
async function showSoundtrackDetails(id) {
    const modal = document.getElementById('soundtrack-modal');
    const modalBody = document.getElementById('modal-body');
    const modalTitle = document.getElementById('modal-title');
    
    modal.style.display = 'block';
    modalBody.innerHTML = '<div class="loading">Loading details...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/soundtracks/${id}`);
        if (!response.ok) throw new Error('Failed to load soundtrack details');
        
        const soundtrack = await response.json();
        
        modalTitle.textContent = soundtrack.title;
        modalBody.innerHTML = createSoundtrackDetails(soundtrack);
        
        // Add enrich button handler
        const enrichButton = document.getElementById('enrich-button');
        if (enrichButton) {
            enrichButton.addEventListener('click', () => enrichSoundtrack(id));
        }
    } catch (error) {
        modalBody.innerHTML = `<div class="error">Error loading details: ${error.message}</div>`;
    }
}

// Create soundtrack details HTML
function createSoundtrackDetails(soundtrack) {
    const artists = soundtrack.artists.map(a => a.name).join(', ') || 'Unknown Artist';
    const duration = soundtrack.duration ? formatDuration(soundtrack.duration) : 'N/A';
    const fileSize = soundtrack.file_size ? formatFileSize(soundtrack.file_size) : 'N/A';
    
    return `
        <div class="detail-row">
            <div class="detail-label">Artists</div>
            <div class="detail-value">${escapeHtml(artists)}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">Game</div>
            <div class="detail-value">${escapeHtml(soundtrack.game_name || 'N/A')}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">Album</div>
            <div class="detail-value">${escapeHtml(soundtrack.album || 'N/A')}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">Release Type</div>
            <div class="detail-value">${soundtrack.release_type}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">Source Type</div>
            <div class="detail-value">${soundtrack.source_type}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">Year</div>
            <div class="detail-value">${soundtrack.year || 'N/A'}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">Genre</div>
            <div class="detail-value">${escapeHtml(soundtrack.genre || 'N/A')}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">Duration</div>
            <div class="detail-value">${duration}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">File Size</div>
            <div class="detail-value">${fileSize}</div>
        </div>
        ${soundtrack.file_path ? `
        <div class="detail-row">
            <div class="detail-label">File Path</div>
            <div class="detail-value"><code>${escapeHtml(soundtrack.file_path)}</code></div>
        </div>
        ` : ''}
        ${soundtrack.description ? `
        <div class="detail-row">
            <div class="detail-label">Description</div>
            <div class="detail-value">${escapeHtml(soundtrack.description)}</div>
        </div>
        ` : ''}
        <div class="detail-row">
            <button id="enrich-button" style="padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 6px; cursor: pointer;">
                Enrich Metadata
            </button>
        </div>
    `;
}

// Enrich soundtrack metadata
async function enrichSoundtrack(id) {
    const enrichButton = document.getElementById('enrich-button');
    enrichButton.disabled = true;
    enrichButton.textContent = 'Enriching...';
    
    try {
        const response = await fetch(`${API_BASE}/soundtracks/${id}/enrich`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        
        if (!response.ok) throw new Error('Failed to enrich metadata');
        
        const soundtrack = await response.json();
        
        // Reload details
        const modalBody = document.getElementById('modal-body');
        const modalTitle = document.getElementById('modal-title');
        modalTitle.textContent = soundtrack.title;
        modalBody.innerHTML = createSoundtrackDetails(soundtrack);
        
        // Re-attach event handler
        document.getElementById('enrich-button').addEventListener('click', () => enrichSoundtrack(id));
        
        alert('Metadata enriched successfully!');
    } catch (error) {
        alert(`Error enriching metadata: ${error.message}`);
    } finally {
        enrichButton.disabled = false;
        enrichButton.textContent = 'Enrich Metadata';
    }
}

// Scan functionality
function initializeScan() {
    const scanButton = document.getElementById('scan-button');
    scanButton.addEventListener('click', () => {
        const directory = document.getElementById('scan-directory').value;
        if (!directory) {
            alert('Please enter a directory path');
            return;
        }
        startScan(directory);
    });
    
    // Clear all data button
    const clearAllButton = document.getElementById('clear-all-button');
    clearAllButton.addEventListener('click', () => {
        if (confirm('Are you sure you want to delete ALL data? This cannot be undone!')) {
            clearAllData();
        }
    });
}

// Start scan
let currentScanId = null;
let scanPollInterval = null;

async function startScan(directory) {
    const statusDiv = document.getElementById('scan-status');
    statusDiv.className = 'scan-status active running';
    statusDiv.innerHTML = '<div class="scan-progress">Starting scan...</div>';
    
    // Clear any existing poll interval
    if (scanPollInterval) {
        clearInterval(scanPollInterval);
    }
    
    try {
        const response = await fetch(`${API_BASE}/scan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ directory })
        });
        
        if (!response.ok) throw new Error('Failed to start scan');
        
        const scanResult = await response.json();
        currentScanId = scanResult.id;
        
        // Start polling for updates
        pollScanStatus(currentScanId);
        
        // Also reload scan history
        loadScanHistory();
    } catch (error) {
        statusDiv.className = 'scan-status active failed';
        statusDiv.textContent = `Scan failed: ${error.message}`;
    }
}

// Poll scan status
async function pollScanStatus(scanId) {
    const statusDiv = document.getElementById('scan-status');
    
    const poll = async () => {
        try {
            const response = await fetch(`${API_BASE}/scan/${scanId}`);
            if (!response.ok) throw new Error('Failed to get scan status');
            
            const scan = await response.json();
            
            // Update status display
            const totalProcessed = (scan.files_added || 0) + (scan.files_updated || 0);
            const totalFiles = scan.files_scanned || 0;
            const progressPercent = totalFiles > 0 
                ? Math.min(100, Math.round((totalProcessed / totalFiles) * 100))
                : 0;
            
            let statusHTML = `
                <div class="scan-progress">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <span><strong>Status:</strong> ${scan.status}</span>
                        <span><strong>Total Files:</strong> ${totalFiles || 'Finding files...'}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <span><strong>Added:</strong> ${scan.files_added || 0}</span>
                        <span><strong>Updated:</strong> ${scan.files_updated || 0}</span>
                    </div>
            `;
            
            if (scan.status === 'running' && totalFiles > 0) {
                statusHTML += `
                    <div style="background: #e0e0e0; border-radius: 4px; height: 20px; margin-top: 10px; overflow: hidden;">
                        <div style="background: #667eea; height: 100%; width: ${progressPercent}%; transition: width 0.3s;"></div>
                    </div>
                    <div style="margin-top: 5px; font-size: 0.9em; color: #666;">
                        Processing files... (${totalProcessed} of ${totalFiles} processed, ${progressPercent}%)
                    </div>
                `;
            } else if (scan.status === 'running') {
                statusHTML += `
                    <div style="margin-top: 10px; font-size: 0.9em; color: #666;">
                        Discovering audio files...
                    </div>
                `;
            }
            
            statusHTML += '</div>';
            
            if (scan.errors) {
                const errorCount = scan.errors.split('\n').length;
                statusHTML += `<div style="margin-top: 10px; color: #d32f2f; font-size: 0.9em;">Errors: ${errorCount}</div>`;
            }
            
            statusDiv.innerHTML = statusHTML;
            
            // Update status class
            if (scan.status === 'completed') {
                statusDiv.className = 'scan-status active completed';
                if (scanPollInterval) {
                    clearInterval(scanPollInterval);
                    scanPollInterval = null;
                }
                // Reload data
                loadSoundtracks();
                loadStats();
                loadScanHistory();
            } else if (scan.status === 'failed') {
                statusDiv.className = 'scan-status active failed';
                if (scanPollInterval) {
                    clearInterval(scanPollInterval);
                    scanPollInterval = null;
                }
                loadScanHistory();
            }
        } catch (error) {
            console.error('Error polling scan status:', error);
        }
    };
    
    // Poll immediately, then every 2 seconds
    poll();
    scanPollInterval = setInterval(poll, 2000);
}

// Clear all data
async function clearAllData() {
    const clearButton = document.getElementById('clear-all-button');
    clearButton.disabled = true;
    clearButton.textContent = 'Clearing...';
    
    try {
        const response = await fetch(`${API_BASE}/admin/clear-all`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to clear data');
        
        const result = await response.json();
        
        alert('All data cleared successfully!');
        
        // Reload data
        loadSoundtracks();
        loadStats();
        loadScanHistory();
    } catch (error) {
        alert(`Error clearing data: ${error.message}`);
    } finally {
        clearButton.disabled = false;
        clearButton.textContent = 'Clear All Data';
    }
}

// Load scan history
async function loadScanHistory() {
    const list = document.getElementById('scan-history-list');
    list.innerHTML = '<div class="loading">Loading scan history...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/scan-history?limit=10`);
        if (!response.ok) throw new Error('Failed to load scan history');
        
        const scans = await response.json();
        
        if (scans.length === 0) {
            list.innerHTML = '<div class="loading">No scan history.</div>';
            return;
        }
        
        list.innerHTML = scans.map(scan => {
            let errorsHtml = '';
            if (scan.errors) {
                const errorLines = scan.errors.split('\n').filter(line => line.trim());
                errorsHtml = `
                    <div style="margin-top: 10px; padding: 10px; background: #fff3cd; border-left: 3px solid #ffc107; border-radius: 4px;">
                        <strong>Errors:</strong>
                        <pre style="margin-top: 5px; font-size: 0.85em; white-space: pre-wrap; word-wrap: break-word;">${escapeHtml(scan.errors)}</pre>
                    </div>
                `;
            }
            
            return `
                <div class="scan-history-item">
                    <h4>${escapeHtml(scan.directory_path)}</h4>
                    <p><strong>Status:</strong> ${scan.status}</p>
                    <p><strong>Scanned:</strong> ${scan.files_scanned} | <strong>Added:</strong> ${scan.files_added} | <strong>Updated:</strong> ${scan.files_updated}</p>
                    <p><strong>Started:</strong> ${new Date(scan.started_at).toLocaleString()}</p>
                    ${scan.completed_at ? `<p><strong>Completed:</strong> ${new Date(scan.completed_at).toLocaleString()}</p>` : ''}
                    ${errorsHtml}
                </div>
            `;
        }).join('');
    } catch (error) {
        list.innerHTML = `<div class="error">Error loading scan history: ${error.message}</div>`;
    }
}

// Load statistics
async function loadStats() {
    const content = document.getElementById('stats-content');
    content.innerHTML = '<div class="loading">Loading statistics...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/stats`);
        if (!response.ok) throw new Error('Failed to load statistics');
        
        const stats = await response.json();
        
        const totalDuration = stats.total_duration ? formatDuration(stats.total_duration) : 'N/A';
        const totalSize = stats.total_size ? formatFileSize(stats.total_size) : 'N/A';
        
        content.innerHTML = `
            <div class="stat-card">
                <h3>${stats.total_soundtracks}</h3>
                <p>Total Soundtracks</p>
            </div>
            <div class="stat-card">
                <h3>${stats.total_artists}</h3>
                <p>Total Artists</p>
            </div>
            <div class="stat-card">
                <h3>${totalDuration}</h3>
                <p>Total Duration</p>
            </div>
            <div class="stat-card">
                <h3>${totalSize}</h3>
                <p>Total Size</p>
            </div>
        `;
    } catch (error) {
        content.innerHTML = `<div class="error">Error loading statistics: ${error.message}</div>`;
    }
}

// Modal close
document.querySelector('.close').addEventListener('click', () => {
    document.getElementById('soundtrack-modal').style.display = 'none';
});

window.addEventListener('click', (e) => {
    const modal = document.getElementById('soundtrack-modal');
    if (e.target === modal) {
        modal.style.display = 'none';
    }
});

// Utility functions
function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

function formatFileSize(bytes) {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    
    return `${size.toFixed(2)} ${units[unitIndex]}`;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

