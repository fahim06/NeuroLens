/**
 * NeuroLens UI - Main Application JavaScript
 * Common functionality shared across all pages
 */

// ========================================
// API Configuration
// ========================================

const API_BASE = '/api';

// ========================================
// Auth Token Management
// ========================================

const TokenManager = {
    getAccess() {
        return localStorage.getItem('access_token');
    },

    getRefresh() {
        return localStorage.getItem('refresh_token');
    },

    setTokens(access, refresh) {
        localStorage.setItem('access_token', access);
        localStorage.setItem('refresh_token', refresh);
    },

    clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_data');
    },

    isAuthenticated() {
        return !!this.getAccess();
    },

    async refresh() {
        const refreshToken = this.getRefresh();
        if (!refreshToken) {
            return false;
        }

        try {
            const response = await fetch(`${API_BASE}/auth/token/refresh/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh: refreshToken }),
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('access_token', data.access);
                return true;
            }
            return false;
        } catch (error) {
            console.error('Token refresh failed:', error);
            return false;
        }
    }
};

// ========================================
// API Request Helper
// ========================================

async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    // Add auth token if available
    const token = TokenManager.getAccess();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        let response = await fetch(url, {
            ...options,
            headers,
        });

        // If 401, try to refresh token and retry
        if (response.status === 401 && TokenManager.getRefresh()) {
            const refreshed = await TokenManager.refresh();
            if (refreshed) {
                headers['Authorization'] = `Bearer ${TokenManager.getAccess()}`;
                response = await fetch(url, {
                    ...options,
                    headers,
                });
            } else {
                // Refresh failed, redirect to login
                TokenManager.clearTokens();
                window.location.href = '/ui/login/';
                return null;
            }
        }

        return response;
    } catch (error) {
        console.error('API request failed:', error);
        showToast('Network error. Please try again.', 'error');
        return null;
    }
}

// For file uploads (FormData)
async function apiUpload(endpoint, formData) {
    const url = `${API_BASE}${endpoint}`;
    
    const headers = {};
    const token = TokenManager.getAccess();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        let response = await fetch(url, {
            method: 'POST',
            headers,
            body: formData,
        });

        // If 401, try to refresh token and retry
        if (response.status === 401 && TokenManager.getRefresh()) {
            const refreshed = await TokenManager.refresh();
            if (refreshed) {
                headers['Authorization'] = `Bearer ${TokenManager.getAccess()}`;
                response = await fetch(url, {
                    method: 'POST',
                    headers,
                    body: formData,
                });
            } else {
                TokenManager.clearTokens();
                window.location.href = '/ui/login/';
                return null;
            }
        }

        return response;
    } catch (error) {
        console.error('Upload failed:', error);
        showToast('Upload failed. Please try again.', 'error');
        return null;
    }
}

// ========================================
// Toast Notifications
// ========================================

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        info: 'fa-info-circle',
        warning: 'fa-exclamation-triangle'
    };

    const icon = document.createElement('i');
    icon.className = `fa-solid ${icons[type] || icons.info}`;

    const span = document.createElement('span');
    span.textContent = message;

    toast.appendChild(icon);
    toast.appendChild(span);
    container.appendChild(toast);

    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.classList.add('hide');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ========================================
// Theme Management
// ========================================

function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);

    showToast(`${newTheme === 'dark' ? 'Dark' : 'Light'} mode enabled`, 'info');
}

function updateThemeIcon(theme) {
    const themeToggle = document.getElementById('themeToggle');
    if (!themeToggle) return;

    const icon = themeToggle.querySelector('i');
    if (icon) {
        icon.className = theme === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
    }
}

// ========================================
// Loading Overlay
// ========================================

function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.add('visible');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.remove('visible');
    }
}

// ========================================
// User Data
// ========================================

function getUserData() {
    const data = localStorage.getItem('user_data');
    return data ? JSON.parse(data) : null;
}

function setUserData(data) {
    localStorage.setItem('user_data', JSON.stringify(data));
}

function updateUserDisplay() {
    const userData = getUserData();
    if (!userData) return;

    const userAvatar = document.getElementById('userAvatar');
    const userName = document.getElementById('userName');
    const userRole = document.getElementById('userRole');

    if (userAvatar) {
        userAvatar.textContent = userData.username ? userData.username.charAt(0).toUpperCase() : 'U';
    }
    if (userName) {
        userName.textContent = userData.username || 'User';
    }
    if (userRole) {
        userRole.textContent = userData.role || 'Member';
    }
}

// ========================================
// Logout Handler
// ========================================

function handleLogout() {
    TokenManager.clearTokens();
    showToast('Logged out successfully', 'success');
    setTimeout(() => {
        window.location.href = '/ui/login/';
    }, 500);
}

// ========================================
// Auth Check
// ========================================

function requireAuth() {
    if (!TokenManager.isAuthenticated()) {
        window.location.href = '/ui/login/';
        return false;
    }
    return true;
}

// ========================================
// Utility Functions
// ========================================

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// ========================================
// Initialize
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme
    initTheme();

    // Theme toggle handler
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }

    // Logout handler
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }

    // Update user display if authenticated
    if (TokenManager.isAuthenticated()) {
        updateUserDisplay();
    }
});

// Export for use in other scripts
window.NeuroLens = {
    TokenManager,
    apiRequest,
    apiUpload,
    showToast,
    showLoading,
    hideLoading,
    getUserData,
    setUserData,
    updateUserDisplay,
    requireAuth,
    formatDate,
    formatFileSize
};
