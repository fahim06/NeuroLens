/**
 * NeuroLens UI - Inference JavaScript
 * Handles image upload and AI inference
 */

document.addEventListener('DOMContentLoaded', async () => {
    const { requireAuth, apiUpload, apiRequest, showToast, updateUserDisplay, formatDate } = window.NeuroLens;

    // Check authentication
    if (!requireAuth()) return;

    // Update user display
    updateUserDisplay();

    // DOM Elements
    const inferenceForm = document.getElementById('inferenceForm');
    const uploadArea = document.getElementById('uploadArea');
    const imageInput = document.getElementById('imageInput');
    const uploadPreview = document.getElementById('uploadPreview');
    const previewImage = document.getElementById('previewImage');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const resultsPlaceholder = document.getElementById('resultsPlaceholder');
    const resultsContainer = document.getElementById('resultsContainer');
    const predictedClass = document.getElementById('predictedClass');
    const confidenceScore = document.getElementById('confidenceScore');
    const predictionsList = document.getElementById('predictionsList');
    const historyContainer = document.getElementById('historyContainer');

    let selectedFile = null;

    // Class labels for the 10-class model
    const classLabels = [
        'Class 0', 'Class 1', 'Class 2', 'Class 3', 'Class 4',
        'Class 5', 'Class 6', 'Class 7', 'Class 8', 'Class 9'
    ];

    // ========================================
    // File Upload Area
    // ========================================

    uploadArea.addEventListener('click', () => {
        imageInput.click();
    });

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });

    imageInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    function handleFileSelect(file) {
        // Validate file type
        if (!file.type.startsWith('image/')) {
            showToast('Please select an image file', 'error');
            return;
        }

        // Validate file size (5MB max for inference)
        if (file.size > 5 * 1024 * 1024) {
            showToast('File size must be less than 5MB', 'error');
            return;
        }

        selectedFile = file;

        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            uploadPreview.classList.add('visible');
        };
        reader.readAsDataURL(file);

        // Enable analyze button
        analyzeBtn.disabled = false;
        showToast('Image selected', 'success');
    }

    // ========================================
    // Inference Form Submission
    // ========================================

    inferenceForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!selectedFile) {
            showToast('Please select an image', 'error');
            return;
        }

        analyzeBtn.classList.add('loading');
        analyzeBtn.disabled = true;

        try {
            const formData = new FormData();
            formData.append('image', selectedFile);

            const response = await apiUpload('/inference/predict/', formData);

            if (response && response.ok) {
                const result = await response.json();
                displayResults(result);
                showToast('Analysis complete!', 'success');
                
                // Reload history
                await loadHistory();
            } else if (response) {
                const error = await response.json();
                showToast(error.detail || error.error || 'Inference failed', 'error');
            }
        } catch (error) {
            console.error('Inference error:', error);
            showToast('Inference failed. Please try again.', 'error');
        } finally {
            analyzeBtn.classList.remove('loading');
            analyzeBtn.disabled = false;
        }
    });

    // ========================================
    // Display Results
    // ========================================

    function displayResults(result) {
        // Hide placeholder, show results
        resultsPlaceholder.style.display = 'none';
        resultsContainer.classList.add('visible');

        // Main prediction
        const predicted = result.predicted_class !== undefined ? result.predicted_class : 0;
        const confidence = result.confidence !== undefined ? result.confidence : 0;

        predictedClass.textContent = classLabels[predicted] || `Class ${predicted}`;
        confidenceScore.textContent = `Confidence: ${(confidence * 100).toFixed(1)}%`;

        // All predictions
        if (result.probabilities && Array.isArray(result.probabilities)) {
            const predictions = result.probabilities.map((prob, idx) => ({
                label: classLabels[idx] || `Class ${idx}`,
                probability: prob
            })).sort((a, b) => b.probability - a.probability);

            predictionsList.innerHTML = predictions.slice(0, 5).map(pred => `
                <div class="prediction-item">
                    <span class="prediction-label">${pred.label}</span>
                    <div class="prediction-bar">
                        <div class="prediction-fill" style="width: ${pred.probability * 100}%"></div>
                    </div>
                    <span class="prediction-value">${(pred.probability * 100).toFixed(1)}%</span>
                </div>
            `).join('');
        } else {
            predictionsList.innerHTML = '';
        }
    }

    // ========================================
    // Load History
    // ========================================

    async function loadHistory() {
        try {
            const response = await apiRequest('/inference/history/');

            if (response && response.ok) {
                const data = await response.json();
                const history = Array.isArray(data) ? data : (data.results || []);
                renderHistory(history.slice(0, 10));
            }
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    }

    function renderHistory(history) {
        if (!history || history.length === 0) {
            historyContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">
                        <i class="fa-solid fa-clock-rotate-left"></i>
                    </div>
                    <h3 class="empty-title">No history yet</h3>
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
                                <td>${item.predicted_class !== null ? classLabels[item.predicted_class] || `Class ${item.predicted_class}` : '-'}</td>
                                <td>${item.confidence ? (item.confidence * 100).toFixed(1) + '%' : '-'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        historyContainer.innerHTML = tableHTML;
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

    await loadHistory();
});
