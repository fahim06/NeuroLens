// ========================================
// Animated Login Page - Enhanced JavaScript
// Adapted for Django Integration
// ========================================

// DOM Elements
const container = document.getElementById("container");
const loginBtn = document.getElementById("login");
const registerBtn = document.getElementById("register");
const themeToggle = document.getElementById("themeToggle");
const toastContainer = document.getElementById("toastContainer");

// Forms
const signInForm = document.getElementById("signInForm");
const signUpForm = document.getElementById("signUpForm");

// Password toggles
const passwordToggles = document.querySelectorAll(".password-toggle");

// Password strength elements
const signUpPassword = document.getElementById("signUpPassword");
const signUpConfirmPassword = document.getElementById("signUpConfirmPassword");
const passwordStrength = document.getElementById("passwordStrength");
const strengthFill = document.getElementById("strengthFill");
const strengthText = document.getElementById("strengthText");

// ========================================
// Utility Functions
// ========================================

/**
 * Debounce function - delays execution until after wait ms have elapsed
 * since the last time the debounced function was invoked.
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Rate limiter - prevents function from being called more than once per interval
 */
function createRateLimiter(intervalMs = 2000) {
    let lastCall = 0;
    let isLimited = false;

    return {
        canProceed() {
            const now = Date.now();
            if (now - lastCall >= intervalMs) {
                lastCall = now;
                isLimited = false;
                return true;
            }
            isLimited = true;
            return false;
        },
        isCurrentlyLimited() {
            return isLimited;
        },
        getRemainingTime() {
            return Math.max(0, intervalMs - (Date.now() - lastCall));
        }
    };
}

/**
 * Convert snake_case to camelCase
 */
function snakeToCamel(str) {
    return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}

// Create rate limiters for forms (2 second cooldown)
const signInRateLimiter = createRateLimiter(2000);
const signUpRateLimiter = createRateLimiter(2000);

// ========================================
// Django CSRF Token Helper
// ========================================

function getCsrfToken() {
    const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    return csrfInput ? csrfInput.value : '';
}

// ========================================
// Theme Management
// ========================================

function initTheme() {
    const savedTheme = localStorage.getItem("theme") || "light";
    document.documentElement.setAttribute("data-theme", savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute("data-theme");
    const newTheme = currentTheme === "dark" ? "light" : "dark";

    document.documentElement.setAttribute("data-theme", newTheme);
    localStorage.setItem("theme", newTheme);
    updateThemeIcon(newTheme);

    showToast(`${newTheme === "dark" ? "Dark" : "Light"} mode enabled`, "info");
}

function updateThemeIcon(theme) {
    const icon = themeToggle.querySelector("i");
    icon.className = theme === "dark" ? "fa-solid fa-sun" : "fa-solid fa-moon";
}

themeToggle.addEventListener("click", toggleTheme);
initTheme();

// ========================================
// Panel Toggle (Sign In / Sign Up)
// ========================================

registerBtn.addEventListener("click", () => {
    container.classList.add("active");
});

loginBtn.addEventListener("click", () => {
    container.classList.remove("active");
});

// ========================================
// Password Visibility Toggle
// ========================================

passwordToggles.forEach(toggle => {
    toggle.addEventListener("click", (e) => {
        e.preventDefault();
        const input = toggle.parentElement.querySelector("input");
        const icon = toggle.querySelector("i");

        if (input.type === "password") {
            input.type = "text";
            icon.className = "fa-solid fa-eye-slash";
        } else {
            input.type = "password";
            icon.className = "fa-solid fa-eye";
        }
    });
});

// ========================================
// Password Strength Indicator (Debounced)
// ========================================

function checkPasswordStrength(password) {
    let strength = 0;

    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;

    if (strength <= 2) return "weak";
    if (strength <= 4) return "medium";
    return "strong";
}

function updatePasswordStrength(password) {
    if (password.length === 0) {
        passwordStrength.classList.remove("visible");
        return;
    }

    passwordStrength.classList.add("visible");
    const strength = checkPasswordStrength(password);

    strengthFill.className = "strength-fill " + strength;
    strengthText.className = "strength-text " + strength;

    const labels = {
        weak: "Weak password",
        medium: "Medium strength",
        strong: "Strong password"
    };

    strengthText.textContent = labels[strength];
}

// Debounced password strength checker (150ms delay for performance)
const debouncedPasswordStrength = debounce((password) => {
    updatePasswordStrength(password);
}, 150);

signUpPassword.addEventListener("input", (e) => {
    debouncedPasswordStrength(e.target.value);
});

// ========================================
// Form Validation
// ========================================

const validators = {
    name: (value) => {
        if (!value.trim()) return "Name is required";
        if (value.trim().length < 2) return "Name must be at least 2 characters";
        return "";
    },
    username: (value) => {
        if (!value.trim()) return "Username is required";
        if (value.trim().length < 3) return "Username must be at least 3 characters";
        if (!/^[a-zA-Z0-9_]+$/.test(value)) return "Only letters, numbers, and underscores";
        return "";
    },
    email: (value) => {
        if (!value.trim()) return "Email is required";
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) return "Please enter a valid email";
        return "";
    },
    password: (value) => {
        if (!value) return "Password is required";
        if (value.length < 6) return "Password must be at least 6 characters";
        return "";
    },
    confirmPassword: (value) => {
        if (!value) return "Please confirm your password";
        const password = document.getElementById("signUpPassword")?.value;
        if (value !== password) return "Passwords do not match";
        return "";
    }
};

function validateField(input, validatorKey) {
    const inputGroup = input.closest(".input-group");
    const errorElement = inputGroup.querySelector(".error-message");
    const error = validators[validatorKey](input.value);

    if (error) {
        inputGroup.classList.remove("success");
        inputGroup.classList.add("error");
        errorElement.textContent = error;
        return false;
    } else {
        inputGroup.classList.remove("error");
        errorElement.textContent = "";
        // Add success state if field has value
        if (input.value.trim()) {
            inputGroup.classList.add("success");
        } else {
            inputGroup.classList.remove("success");
        }
        return true;
    }
}

function validateForm(form, fields) {
    let isValid = true;

    fields.forEach(({ id, validator }) => {
        const input = form.querySelector(`#${id}`);
        if (input && !validateField(input, validator)) {
            isValid = false;
        }
    });

    return isValid;
}

// Add real-time validation on blur
document.querySelectorAll('.input-group input').forEach(input => {
    input.addEventListener('blur', () => {
        const id = input.id;
        let validatorKey = '';

        if (id.toLowerCase().includes('confirmpassword')) {
            validatorKey = 'confirmPassword';
        } else if (id.toLowerCase().includes('name') && !id.toLowerCase().includes('username')) {
            validatorKey = 'name';
        } else if (id.toLowerCase().includes('username')) {
            validatorKey = 'username';
        } else if (id.toLowerCase().includes('email')) {
            validatorKey = 'email';
        } else if (id.toLowerCase().includes('password')) {
            validatorKey = 'password';
        }

        if (validatorKey) {
            validateField(input, validatorKey);
        }
    });

    // Clear error on input
    input.addEventListener('input', () => {
        const inputGroup = input.closest('.input-group');
        if (inputGroup.classList.contains('error') || inputGroup.classList.contains('success')) {
            inputGroup.classList.remove('error', 'success');
            inputGroup.querySelector('.error-message').textContent = '';
        }
    });
});

// Real-time confirm password validation when typing
signUpConfirmPassword?.addEventListener('input', debounce(() => {
    const confirmValue = signUpConfirmPassword.value;
    const passwordValue = signUpPassword.value;

    if (confirmValue && passwordValue && confirmValue !== passwordValue) {
        const inputGroup = signUpConfirmPassword.closest('.input-group');
        inputGroup.classList.add('error');
        inputGroup.querySelector('.error-message').textContent = 'Passwords do not match';
    }
}, 300));

// ========================================
// Form Submission - Django Integration
// ========================================

signInForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    // Rate limiting check
    if (!signInRateLimiter.canProceed()) {
        const remaining = Math.ceil(signInRateLimiter.getRemainingTime() / 1000);
        showToast(`Please wait ${remaining}s before trying again`, "error");
        return;
    }

    const fields = [
        {id: "signInUsername", validator: "username"},
        { id: "signInPassword", validator: "password" }
    ];

    if (!validateForm(signInForm, fields)) {
        showToast("Please fix the errors above", "error");
        return;
    }

    const button = signInForm.querySelector(".btn-primary");
    button.classList.add("loading");
    button.disabled = true;

    try {
        const formData = new FormData(signInForm);
        
        const response = await fetch('/login/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        });

        const data = await response.json();

        if (data.success) {
            // Check remember me
            const rememberMe = document.getElementById("rememberMe");
            if (rememberMe.checked) {
                localStorage.setItem("rememberMe", "true");
            } else {
                localStorage.removeItem("rememberMe");
            }

            // Clear system info hidden preference on new login
            localStorage.removeItem("systemInfoHidden");

            showToast("Welcome back! Signing you in...", "success");
            
            // Redirect after success
            setTimeout(() => {
                window.location.href = data.redirect || '/dashboard/';
            }, 500);
        } else {
            // Show errors
            if (data.errors) {
                if (data.errors.general) {
                    showToast(data.errors.general, "error");
                }
                if (data.errors.username) {
                    const usernameGroup = signInForm.querySelector('#signInUsername').closest('.input-group');
                    usernameGroup.classList.remove('success'); // Remove success state
                    usernameGroup.classList.add('error');
                    usernameGroup.querySelector('.error-message').textContent = data.errors.username;
                }
                if (data.errors.password) {
                    const passwordGroup = signInForm.querySelector('#signInPassword').closest('.input-group');
                    passwordGroup.classList.remove('success'); // Remove success state
                    passwordGroup.classList.add('error');
                    passwordGroup.querySelector('.error-message').textContent = data.errors.password;
                }
            } else {
                showToast("Invalid credentials. Please try again.", "error");
            }
        }
    } catch (error) {
        console.error('Sign in error:', error);
        showToast("An error occurred. Please try again.", "error");
    } finally {
        button.classList.remove("loading");
        button.disabled = false;
    }
});

signUpForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    // Rate limiting check
    if (!signUpRateLimiter.canProceed()) {
        const remaining = Math.ceil(signUpRateLimiter.getRemainingTime() / 1000);
        showToast(`Please wait ${remaining}s before trying again`, "error");
        return;
    }

    const fields = [
        { id: "signUpName", validator: "name" },
        { id: "signUpUsername", validator: "username" },
        { id: "signUpEmail", validator: "email" },
        { id: "signUpPassword", validator: "password" },
        { id: "signUpConfirmPassword", validator: "confirmPassword" }
    ];

    if (!validateForm(signUpForm, fields)) {
        showToast("Please fix the errors above", "error");
        return;
    }

    const button = signUpForm.querySelector(".btn-primary");
    button.classList.add("loading");
    button.disabled = true;

    try {
        const formData = new FormData(signUpForm);

        const response = await fetch('/login/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        });

        const data = await response.json();

        if (data.success) {
            // Clear system info hidden preference for new user
            localStorage.removeItem("systemInfoHidden");

            showToast("Account created successfully!", "success");

            // Switch to sign in after successful registration
            setTimeout(() => {
                container.classList.remove("active");
                // Pre-fill email
                document.getElementById('signInEmail').value = document.getElementById('signUpEmail').value;
            }, 1000);
        } else {
            // Show errors
            if (data.errors) {
                Object.entries(data.errors).forEach(([field, message]) => {
                    if (field === 'general') {
                        showToast(message, "error");
                    } else {
                        // Convert field name to camelCase and create input ID
                        const camelField = snakeToCamel(field);
                        const inputId = 'signUp' + camelField.charAt(0).toUpperCase() + camelField.slice(1);
                        const inputElement = signUpForm.querySelector(`#${inputId}`);
                        if (inputElement) {
                            const inputGroup = inputElement.closest('.input-group');
                            inputGroup.classList.remove('success'); // Remove success state
                            inputGroup.classList.add('error');
                            inputGroup.querySelector('.error-message').textContent = message;
                        }
                    }
                });
            } else {
                showToast("Registration failed. Please try again.", "error");
            }
        }
    } catch (error) {
        console.error('Sign up error:', error);
        showToast("An error occurred. Please try again.", "error");
    } finally {
        button.classList.remove("loading");
        button.disabled = false;
    }
});

// ========================================
// Toast Notifications
// ========================================

function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;

    const icons = {
        success: "fa-check-circle",
        error: "fa-exclamation-circle",
        info: "fa-info-circle"
    };

    // Create elements safely to prevent XSS
    const icon = document.createElement("i");
    icon.className = `fa-solid ${icons[type]}`;

    const span = document.createElement("span");
    span.textContent = message; // Safe: uses textContent, not innerHTML

    toast.appendChild(icon);
    toast.appendChild(span);

    toastContainer.appendChild(toast);

    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.classList.add("hide");
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ========================================
// Remember Me - Load saved preference
// ========================================

function loadRememberMe() {
    const remembered = localStorage.getItem("rememberMe");
    if (remembered === "true") {
        const checkbox = document.getElementById("rememberMe");
        if (checkbox) checkbox.checked = true;
    }
}

loadRememberMe();

// ========================================
// Keyboard Navigation
// ========================================

document.addEventListener("keydown", (e) => {
    // Enter key submits the active form
    if (e.key === "Enter" && e.target.tagName === "INPUT") {
        const form = e.target.closest("form");
        if (form) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                e.preventDefault();
                submitBtn.click();
            }
        }
    }

    // Escape key closes any focused input
    if (e.key === "Escape") {
        document.activeElement.blur();
    }
});

// ========================================
// Social Icon Hover Effects (Ripple)
// ========================================

document.querySelectorAll('.social-icons a').forEach(icon => {
    icon.addEventListener('click', (e) => {
        e.preventDefault();
        showToast("Social login coming soon!", "info");
    });
});

// ========================================
// Forgot Password Link
// ========================================

document.getElementById('forgotPassword')?.addEventListener('click', (e) => {
    e.preventDefault();
    showToast("Password reset feature coming soon!", "info");
});

// ========================================
// Debug: Log security features status
// ========================================

console.log("✨ NeuroLens Login Page loaded successfully!");
console.log("🔒 Security features enabled:");
console.log("   - Django CSRF Token Protection");
console.log("   - Rate Limiting (2s cooldown)");
console.log("   - Input Validation");
console.log("   - XSS Prevention");
console.log("   - Password Strength Checker (debounced)");
