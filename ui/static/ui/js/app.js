/**
 * NeuroLens UI - Main Application JavaScript
 * Centralized auth handling, API requests, and common utilities
 * 
 * Phase 7: Full Responsive UI/UX (Beta Interface)
 */

// ========================================
// Configuration
// ========================================

const API_BASE = '/api';
const POLLING_INTERVAL = 2000; // 2 seconds as per Phase 7 spec

// ========================================
// Token Management (Centralized)
// ========================================

const TokenManager = {
    /**
     * Get access token from localStorage
     */
    getAccess() {
        return localStorage.getItem('access_token');
    },

    /**
     * Get refresh token from localStorage
     */
    getRefresh() {
        return localStorage.getItem('refresh_token');
    },

    /**
     * Store tokens in localStorage
     */
    setTokens(access, refresh) {
        localStorage.setItem('access_token', access);
        if (refresh) {
            localStorage.setItem('refresh_token', refresh);
        }
    },

    /**
     * Clear all auth data (logout)
     */
    clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_data');
    },

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!this.getAccess();
    },

    /**
     * Redirect to login on 401 (centralized handling)
     */
    redirectToLogin() {
        this.clearTokens();
        window.location.href = '/ui/login/';
    }
};

// ========================================
// User Data Management
// ========================================

const UserManager = {
    /**
     * Get user data from localStorage
     */
    getData() {
        const data = localStorage.getItem('user_data');
        return data ? JSON.parse(data) : null;
    },

    /**
     * Store user data in localStorage
     */
    setData(data) {
        localStorage.setItem('user_data', JSON.stringify(data));
    },

    /**
     * Update user display in sidebar
     */
    updateDisplay() {
        const userData = this.getData();
        if (!userData) return;

        const userAvatar = document.getElementById('userAvatar');
        const userName = document.getElementById('userName');
        const userRole = document.getElementById('userRole');

        if (userAvatar && userData.username) {
            userAvatar.textContent = userData.username.charAt(0).toUpperCase();
        }
        if (userName) {
            userName.textContent = userData.username || 'User';
        }
        if (userRole) {
            userRole.textContent = userData.role || 'Beta User';
        }
    }
};

// ========================================
// API Request Helper
// ========================================

/**
 * Make authenticated API request
 * Automatically handles 401 by redirecting to login
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    // Attach token to all requests
    const token = TokenManager.getAccess();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(url, {
            ...options,
            headers,
        });

        // Redirect to login on 401
        if (response.status === 401) {
            TokenManager.redirectToLogin();
            return null;
        }

        return response;
    } catch (error) {
        console.error('API request failed:', error);
        showToast('Network error. Please try again.', 'error');
        return null;
    }
}

/**
 * Upload file with authentication
 */
async function apiUpload(endpoint, formData) {
    const url = `${API_BASE}${endpoint}`;
    
    const headers = {};
    const token = TokenManager.getAccess();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers,
            body: formData,
        });

        // Redirect to login on 401
        if (response.status === 401) {
            TokenManager.redirectToLogin();
            return null;
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
// Auth Check (for protected pages)
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
    if (!dateString) return '-';
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
    if (!bytes || bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getStatusClass(status) {
    switch (status) {
        case 'completed':
        case 'success':
        case 'active':
            return 'success';
        case 'pending':
        case 'processing':
            return 'warning';
        case 'failed':
        case 'error':
            return 'error';
        default:
            return 'info';
    }
}

// ========================================
// Polling Helper (2-second interval)
// ========================================

class StatusPoller {
    constructor(checkFn, onComplete, onError) {
        this.checkFn = checkFn;
        this.onComplete = onComplete;
        this.onError = onError;
        this.intervalId = null;
    }

    start() {
        // Initial check
        this.check();
        // Poll every 2 seconds
        this.intervalId = setInterval(() => this.check(), POLLING_INTERVAL);
    }

    async check() {
        try {
            const result = await this.checkFn();
            if (result.done) {
                this.stop();
                this.onComplete(result.data);
            }
        } catch (error) {
            this.stop();
            this.onError(error);
        }
    }

    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }
}

// ========================================
// Initialize on DOM Ready
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
        UserManager.updateDisplay();
    }
});

// ========================================
// Export for use in other scripts
// ========================================

window.NeuroLens = {
    // Auth
    TokenManager,
    UserManager,
    requireAuth,
    
    // API
    apiRequest,
    apiUpload,
    POLLING_INTERVAL,
    StatusPoller,
    
    // UI
    showToast,
    showLoading,
    hideLoading,
    
    // Utils
    formatDate,
    formatFileSize,
    getStatusClass
};
