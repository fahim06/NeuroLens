/**
 * NeuroLens UI - Dashboard JavaScript
 * Handles dashboard statistics and activity
 */

document.addEventListener('DOMContentLoaded', async () => {
    const { requireAuth, apiRequest, showToast, updateUserDisplay, formatDate } = window.NeuroLens;

    // Check authentication
    if (!requireAuth()) return;

    // Update user display
    updateUserDisplay();

    // ========================================
    // Load Dashboard Data
    // ========================================

    async function loadDashboardData() {
        // Load system health
        try {
            const healthResponse = await fetch('/api/health/');
            if (healthResponse.ok) {
                const healthData = await healthResponse.json();
                document.getElementById('systemStatus').textContent = 
                    healthData.status === 'healthy' ? 'Online' : 'Offline';
            }
        } catch (error) {
            document.getElementById('systemStatus').textContent = 'Offline';
        }

        // Load datasets count
        try {
            const datasetsResponse = await apiRequest('/datasets/');
            if (datasetsResponse && datasetsResponse.ok) {
                const datasets = await datasetsResponse.json();
                document.getElementById('totalDatasets').textContent = 
                    Array.isArray(datasets) ? datasets.length : (datasets.count || 0);
            }
        } catch (error) {
            console.error('Failed to load datasets:', error);
        }

        // Load inference history
        try {
            const historyResponse = await apiRequest('/inference/history/');
            if (historyResponse && historyResponse.ok) {
                const history = await historyResponse.json();
                const historyData = Array.isArray(history) ? history : (history.results || []);
                
                document.getElementById('totalInferences').textContent = historyData.length;
                
                // Count pending
                const pending = historyData.filter(item => 
                    item.status === 'pending' || item.status === 'processing'
                ).length;
                document.getElementById('pendingTasks').textContent = pending;

                // Render history
                renderHistory(historyData.slice(0, 10));
            }
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    }

    // ========================================
    // Render History
    // ========================================

    function renderHistory(history) {
        const container = document.getElementById('historyContainer');
        
        if (!history || history.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">
                        <i class="fa-solid fa-clock-rotate-left"></i>
                    </div>
                    <h3 class="empty-title">No recent activity</h3>
                    <p class="empty-text">Your inference history will appear here</p>
                </div>
            `;
            return;
        }

        const tableHTML = `
            <div class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Status</th>
                            <th>Prediction</th>
                            <th>Confidence</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${history.map(item => `
                            <tr>
                                <td>${formatDate(item.created_at)}</td>
                                <td>
                                    <span class="badge ${getStatusClass(item.status)}">
                                        ${item.status}
                                    </span>
                                </td>
                                <td>${item.predicted_class || '-'}</td>
                                <td>${item.confidence ? (item.confidence * 100).toFixed(1) + '%' : '-'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        container.innerHTML = tableHTML;
    }

    function getStatusClass(status) {
        switch (status) {
            case 'completed': return 'success';
            case 'pending':
            case 'processing': return 'warning';
            case 'failed': return 'error';
            default: return 'info';
        }
    }

    // ========================================
    // Initialize
    // ========================================

    await loadDashboardData();
});
