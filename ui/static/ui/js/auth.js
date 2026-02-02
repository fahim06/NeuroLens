/**
 * NeuroLens UI - Authentication JavaScript
 * Handles login form and JWT token management
 */

document.addEventListener('DOMContentLoaded', () => {
    const { TokenManager, showToast } = window.NeuroLens;

    // If already authenticated, redirect to dashboard
    if (TokenManager.isAuthenticated()) {
        window.location.href = '/ui/dashboard/';
        return;
    }

    // DOM Elements
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const loginBtn = document.getElementById('loginBtn');
    const passwordToggle = document.querySelector('.password-toggle');

    // ========================================
    // Password Toggle
    // ========================================

    if (passwordToggle) {
        passwordToggle.addEventListener('click', (e) => {
            e.preventDefault();
            const icon = passwordToggle.querySelector('i');

            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                icon.className = 'fa-solid fa-eye-slash';
            } else {
                passwordInput.type = 'password';
                icon.className = 'fa-solid fa-eye';
            }
        });
    }

    // ========================================
    // Form Validation
    // ========================================

    function validateField(input, errorId) {
        const errorElement = document.getElementById(errorId);
        const inputGroup = input.closest('.input-group');

        if (!input.value.trim()) {
            inputGroup.classList.add('error');
            errorElement.textContent = `${input.placeholder || 'Field'} is required`;
            return false;
        }

        inputGroup.classList.remove('error');
        errorElement.textContent = '';
        return true;
    }

    function validateForm() {
        const isUsernameValid = validateField(usernameInput, 'usernameError');
        const isPasswordValid = validateField(passwordInput, 'passwordError');
        return isUsernameValid && isPasswordValid;
    }

    // Clear errors on input
    [usernameInput, passwordInput].forEach(input => {
        input.addEventListener('input', () => {
            const inputGroup = input.closest('.input-group');
            if (inputGroup.classList.contains('error')) {
                inputGroup.classList.remove('error');
                const errorId = input.id + 'Error';
                document.getElementById(errorId).textContent = '';
            }
        });
    });

    // ========================================
    // Login Form Submission
    // ========================================

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!validateForm()) {
            showToast('Please fill in all fields', 'error');
            return;
        }

        // Show loading state
        loginBtn.classList.add('loading');
        loginBtn.disabled = true;

        try {
            const response = await fetch('/api/auth/token/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: usernameInput.value.trim(),
                    password: passwordInput.value,
                }),
            });

            const data = await response.json();

            if (response.ok) {
                // Store tokens
                TokenManager.setTokens(data.access, data.refresh);

                // Store user data
                window.NeuroLens.setUserData({
                    username: usernameInput.value.trim(),
                    role: 'Member'
                });

                showToast('Login successful! Redirecting...', 'success');

                // Redirect to dashboard
                setTimeout(() => {
                    window.location.href = '/ui/dashboard/';
                }, 1000);
            } else {
                // Handle specific errors
                if (response.status === 401) {
                    showToast('Invalid username or password', 'error');
                } else if (data.detail) {
                    showToast(data.detail, 'error');
                } else {
                    showToast('Login failed. Please try again.', 'error');
                }
            }
        } catch (error) {
            console.error('Login error:', error);
            showToast('Network error. Please check your connection.', 'error');
        } finally {
            loginBtn.classList.remove('loading');
            loginBtn.disabled = false;
        }
    });

    // ========================================
    // Keyboard Navigation
    // ========================================

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.target.tagName === 'INPUT') {
            e.preventDefault();
            loginForm.dispatchEvent(new Event('submit'));
        }
    });
});
