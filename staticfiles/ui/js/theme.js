// ========================================
// Theme Management - Common functionality
// ========================================

/**
 * Initialize theme on page load
 */
function initTheme() {
    const savedTheme = localStorage.getItem("theme") || "light";
    document.documentElement.setAttribute("data-theme", savedTheme);
    updateThemeIcon(savedTheme);
}

/**
 * Toggle between light and dark themes
 */
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute("data-theme");
    const newTheme = currentTheme === "dark" ? "light" : "dark";

    document.documentElement.setAttribute("data-theme", newTheme);
    localStorage.setItem("theme", newTheme);
    updateThemeIcon(newTheme);

    // Show toast notification if available
    if (typeof showToast === 'function') {
        showToast(`${newTheme === "dark" ? "Dark" : "Light"} mode enabled`, "info");
    }
}

/**
 * Update the theme toggle icon
 */
function updateThemeIcon(theme) {
    const themeToggle = document.getElementById("themeToggle");
    if (themeToggle) {
        const icon = themeToggle.querySelector("i");
        if (icon) {
            icon.className = theme === "dark" ? "fa-solid fa-sun" : "fa-solid fa-moon";
        }
    }
}

// Initialize theme when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    initTheme();

    // Add click event listener to theme toggle button
    const themeToggle = document.getElementById("themeToggle");
    if (themeToggle) {
        themeToggle.addEventListener("click", toggleTheme);
    }
});