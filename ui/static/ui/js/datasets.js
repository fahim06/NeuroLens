/**
 * NeuroLens UI - Datasets JavaScript
 * Handles dataset upload and management
 */

document.addEventListener('DOMContentLoaded', async () => {
    const { requireAuth, apiRequest, apiUpload, showToast, updateUserDisplay, formatDate, formatFileSize } = window.NeuroLens;

    // Check authentication
    if (!requireAuth()) return;

    // Update user display
    updateUserDisplay();

    // DOM Elements
    const uploadForm = document.getElementById('uploadForm');
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadPreview = document.getElementById('uploadPreview');
    const previewImage = document.getElementById('previewImage');
    const fileName = document.getElementById('fileName');
    const uploadBtn = document.getElementById('uploadBtn');
    const refreshBtn = document.getElementById('refreshBtn');
    const datasetsContainer = document.getElementById('datasetsContainer');

    let selectedFile = null;

    // ========================================
    // File Upload Area
    // ========================================

    uploadArea.addEventListener('click', () => {
        fileInput.click();
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

    fileInput.addEventListener('change', (e) => {
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

        // Validate file size (10MB max)
        if (file.size > 10 * 1024 * 1024) {
            showToast('File size must be less than 10MB', 'error');
            return;
        }

        selectedFile = file;

        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            fileName.textContent = `${file.name} (${formatFileSize(file.size)})`;
            uploadPreview.classList.add('visible');
        };
        reader.readAsDataURL(file);

        showToast('File selected', 'success');
    }

    // ========================================
    // Upload Form Submission
    // ========================================

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const nameInput = document.getElementById('datasetName');
        const name = nameInput.value.trim();

        if (!name) {
            showToast('Please enter a dataset name', 'error');
            return;
        }

        if (!selectedFile) {
            showToast('Please select a file', 'error');
            return;
        }

        uploadBtn.classList.add('loading');
        uploadBtn.disabled = true;

        try {
            const formData = new FormData();
            formData.append('name', name);
            formData.append('file', selectedFile);

            const response = await apiUpload('/datasets/', formData);

            if (response && response.ok) {
                showToast('Dataset uploaded successfully!', 'success');
                
                // Reset form
                nameInput.value = '';
                selectedFile = null;
                uploadPreview.classList.remove('visible');
                fileInput.value = '';

                // Reload datasets
                await loadDatasets();
            } else if (response) {
                const error = await response.json();
                showToast(error.detail || 'Upload failed', 'error');
            }
        } catch (error) {
            console.error('Upload error:', error);
            showToast('Upload failed. Please try again.', 'error');
        } finally {
            uploadBtn.classList.remove('loading');
            uploadBtn.disabled = false;
        }
    });

    // ========================================
    // Load Datasets
    // ========================================

    async function loadDatasets() {
        try {
            const response = await apiRequest('/datasets/');

            if (response && response.ok) {
                const data = await response.json();
                const datasets = Array.isArray(data) ? data : (data.results || []);
                renderDatasets(datasets);
            }
        } catch (error) {
            console.error('Failed to load datasets:', error);
            showToast('Failed to load datasets', 'error');
        }
    }

    function renderDatasets(datasets) {
        if (!datasets || datasets.length === 0) {
            datasetsContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">
                        <i class="fa-solid fa-folder-open"></i>
                    </div>
                    <h3 class="empty-title">No datasets yet</h3>
                    <p class="empty-text">Upload your first dataset to get started</p>
                </div>
            `;
            return;
        }

        const tableHTML = `
            <div class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Created</th>
                            <th>Size</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${datasets.map(dataset => `
                            <tr data-id="${dataset.id}">
                                <td>
                                    <i class="fa-solid fa-database" style="margin-right: 8px; color: var(--nl-primary);"></i>
                                    ${dataset.name}
                                </td>
                                <td>${formatDate(dataset.created_at)}</td>
                                <td>${dataset.file_size ? formatFileSize(dataset.file_size) : '-'}</td>
                                <td>
                                    <span class="badge ${dataset.status === 'active' ? 'success' : 'info'}">
                                        ${dataset.status || 'active'}
                                    </span>
                                </td>
                                <td>
                                    <button class="btn btn-secondary delete-btn" data-id="${dataset.id}" 
                                            style="padding: 6px 12px; font-size: 11px;">
                                        <i class="fa-solid fa-trash"></i>
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        datasetsContainer.innerHTML = tableHTML;

        // Add delete handlers
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = btn.dataset.id;
                if (confirm('Are you sure you want to delete this dataset?')) {
                    await deleteDataset(id);
                }
            });
        });
    }

    async function deleteDataset(id) {
        try {
            const response = await apiRequest(`/datasets/${id}/`, {
                method: 'DELETE'
            });

            if (response && (response.ok || response.status === 204)) {
                showToast('Dataset deleted successfully', 'success');
                await loadDatasets();
            } else if (response) {
                const error = await response.json();
                showToast(error.detail || 'Delete failed', 'error');
            }
        } catch (error) {
            console.error('Delete error:', error);
            showToast('Delete failed', 'error');
        }
    }

    // ========================================
    // Refresh Button
    // ========================================

    refreshBtn.addEventListener('click', async () => {
        refreshBtn.disabled = true;
        await loadDatasets();
        refreshBtn.disabled = false;
        showToast('Datasets refreshed', 'info');
    });

    // ========================================
    // Initialize
    // ========================================

    await loadDatasets();
});
