/**
 * NeuroLens - Datasets Page
 * Dataset list, upload, and management interface
 */

import React, { useState, useEffect, useRef } from 'react';
import Navbar from '../components/Navbar';
import Loader from '../components/Loader';
import { datasetsAPI, type Dataset } from '../services/api';
import { useToast } from '../components/Toast';

const Datasets: React.FC = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadForm, setUploadForm] = useState({ name: '', description: '' });
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { showToast } = useToast();

  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    try {
      const data = await datasetsAPI.list();
      setDatasets(data);
    } catch (error) {
      showToast('Failed to load datasets', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const validFiles = files.filter((f) =>
      ['image/jpeg', 'image/png', 'application/dicom'].includes(f.type) ||
      f.name.endsWith('.dcm')
    );
    setSelectedFiles(validFiles);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    const validFiles = files.filter((f) =>
      ['image/jpeg', 'image/png'].includes(f.type) || f.name.endsWith('.dcm')
    );
    setSelectedFiles(validFiles);
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFiles.length) {
      showToast('Please select files to upload', 'warning');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('name', uploadForm.name);
      formData.append('description', uploadForm.description);
      selectedFiles.forEach((file) => formData.append('files', file));

      await datasetsAPI.create(formData, (progressEvent) => {
        const percent = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
        setUploadProgress(percent);
      });

      showToast('Dataset uploaded successfully', 'success');
      setShowUploadModal(false);
      setUploadForm({ name: '', description: '' });
      setSelectedFiles([]);
      fetchDatasets();
    } catch (error: any) {
      const message = error.response?.data?.error || 'Failed to upload dataset';
      showToast(message, 'error');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await datasetsAPI.delete(id);
      showToast('Dataset deleted successfully', 'success');
      setDatasets((prev) => prev.filter((d) => d.id !== id));
      setDeleteConfirm(null);
    } catch (error) {
      showToast('Failed to delete dataset', 'error');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className="app-layout">
      <Navbar />
      <main className="main-content">
        <div className="page-header">
          <div className="page-header-content">
            <h1>Datasets</h1>
            <p>Manage your retinal image datasets</p>
          </div>
          <div className="page-header-actions">
            <button className="btn btn-primary" onClick={() => setShowUploadModal(true)}>
              <i className="fa-solid fa-upload"></i>
              <span>Upload Dataset</span>
            </button>
          </div>
        </div>

        {loading ? (
          <div className="loading-state">
            <Loader size="lg" text="Loading datasets..." />
          </div>
        ) : datasets.length === 0 ? (
          <div className="empty-state card">
            <div className="empty-icon">
              <i className="fa-solid fa-database"></i>
            </div>
            <h3>No Datasets Yet</h3>
            <p>Upload your first retinal image dataset to get started with AI analysis.</p>
            <button className="btn btn-primary" onClick={() => setShowUploadModal(true)}>
              <i className="fa-solid fa-upload"></i>
              <span>Upload Your First Dataset</span>
            </button>
          </div>
        ) : (
          <div className="datasets-grid">
            {datasets.map((dataset) => (
              <div key={dataset.id} className="dataset-card card">
                <div className="dataset-header">
                  <div className="dataset-icon">
                    <i className="fa-solid fa-folder-open"></i>
                  </div>
                  <div className="dataset-info">
                    <h3>{dataset.name}</h3>
                    <span className={`status-badge status-${dataset.status}`}>
                      {dataset.status}
                    </span>
                  </div>
                  <div className="dataset-actions">
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={() => setDeleteConfirm(dataset.id)}
                      aria-label="Delete dataset"
                    >
                      <i className="fa-solid fa-trash"></i>
                    </button>
                  </div>
                </div>
                <p className="dataset-description">
                  {dataset.description || 'No description provided'}
                </p>
                <div className="dataset-meta">
                  <span>
                    <i className="fa-solid fa-images"></i>
                    {dataset.file_count} images
                  </span>
                  <span>
                    <i className="fa-solid fa-calendar"></i>
                    {formatDate(dataset.created_at)}
                  </span>
                </div>

                {deleteConfirm === dataset.id && (
                  <div className="delete-confirm">
                    <p>Delete this dataset?</p>
                    <div className="confirm-actions">
                      <button className="btn btn-ghost btn-sm" onClick={() => setDeleteConfirm(null)}>
                        Cancel
                      </button>
                      <button className="btn btn-danger btn-sm" onClick={() => handleDelete(dataset.id)}>
                        Delete
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Upload Modal */}
        {showUploadModal && (
          <div className="modal-overlay" onClick={() => !uploading && setShowUploadModal(false)}>
            <div className="modal" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>Upload Dataset</h2>
                <button
                  className="btn btn-ghost"
                  onClick={() => !uploading && setShowUploadModal(false)}
                  disabled={uploading}
                >
                  <i className="fa-solid fa-times"></i>
                </button>
              </div>
              <form onSubmit={handleUpload}>
                <div className="modal-body">
                  <div className="form-group">
                    <label htmlFor="name">Dataset Name</label>
                    <input
                      type="text"
                      id="name"
                      value={uploadForm.name}
                      onChange={(e) => setUploadForm((prev) => ({ ...prev, name: e.target.value }))}
                      placeholder="Enter dataset name"
                      required
                      disabled={uploading}
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="description">Description (Optional)</label>
                    <textarea
                      id="description"
                      value={uploadForm.description}
                      onChange={(e) => setUploadForm((prev) => ({ ...prev, description: e.target.value }))}
                      placeholder="Enter dataset description"
                      rows={3}
                      disabled={uploading}
                    />
                  </div>
                  <div
                    className={`drop-zone ${selectedFiles.length ? 'has-files' : ''}`}
                    onDrop={handleDrop}
                    onDragOver={(e) => e.preventDefault()}
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={handleFileSelect}
                      multiple
                      accept=".jpg,.jpeg,.png,.dcm"
                      hidden
                      disabled={uploading}
                    />
                    {selectedFiles.length ? (
                      <div className="selected-files">
                        <i className="fa-solid fa-check-circle"></i>
                        <span>{selectedFiles.length} files selected</span>
                        <small>Click to change selection</small>
                      </div>
                    ) : (
                      <>
                        <i className="fa-solid fa-cloud-upload-alt"></i>
                        <span>Drag & drop files or click to browse</span>
                        <small>Supports JPEG, PNG, DICOM</small>
                      </>
                    )}
                  </div>
                  {uploading && (
                    <div className="upload-progress">
                      <div className="progress-bar">
                        <div className="progress-fill" style={{ width: `${uploadProgress}%` }} />
                      </div>
                      <span>{uploadProgress}% uploaded</span>
                    </div>
                  )}
                </div>
                <div className="modal-footer">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => setShowUploadModal(false)}
                    disabled={uploading}
                  >
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary" disabled={uploading || !selectedFiles.length}>
                    {uploading ? (
                      <>
                        <Loader size="sm" />
                        <span>Uploading...</span>
                      </>
                    ) : (
                      <>
                        <i className="fa-solid fa-upload"></i>
                        <span>Upload</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>

      <style>{`
        .app-layout {
          display: flex;
          min-height: 100vh;
          background: var(--bg-primary);
        }

        .main-content {
          flex: 1;
          padding: var(--spacing-6);
          margin-left: 260px;
          max-width: calc(100% - 260px);
        }

        .page-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: var(--spacing-6);
          gap: var(--spacing-4);
        }

        .page-header-content h1 {
          font-size: var(--text-2xl);
          font-weight: 700;
          color: var(--text-primary);
          margin-bottom: var(--spacing-1);
        }

        .page-header-content p {
          color: var(--text-secondary);
          font-size: var(--text-sm);
        }

        .loading-state {
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 400px;
        }

        .empty-state {
          text-align: center;
          padding: var(--spacing-12);
        }

        .empty-icon {
          width: 80px;
          height: 80px;
          margin: 0 auto var(--spacing-4);
          background: var(--bg-tertiary);
          border-radius: var(--radius-full);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: var(--text-3xl);
          color: var(--text-tertiary);
        }

        .empty-state h3 {
          font-size: var(--text-lg);
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--spacing-2);
        }

        .empty-state p {
          color: var(--text-secondary);
          margin-bottom: var(--spacing-6);
          max-width: 400px;
          margin-left: auto;
          margin-right: auto;
        }

        .datasets-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
          gap: var(--spacing-4);
        }

        .dataset-card {
          padding: var(--spacing-5);
          position: relative;
        }

        .dataset-header {
          display: flex;
          align-items: flex-start;
          gap: var(--spacing-3);
          margin-bottom: var(--spacing-3);
        }

        .dataset-icon {
          width: 40px;
          height: 40px;
          background: var(--primary-100);
          color: var(--primary-600);
          border-radius: var(--radius-md);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: var(--text-lg);
          flex-shrink: 0;
        }

        [data-theme="dark"] .dataset-icon {
          background: var(--primary-900);
        }

        .dataset-info {
          flex: 1;
          min-width: 0;
        }

        .dataset-info h3 {
          font-size: var(--text-base);
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--spacing-1);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .status-badge {
          font-size: var(--text-xs);
          padding: var(--spacing-1) var(--spacing-2);
          border-radius: var(--radius-sm);
          font-weight: 500;
          text-transform: uppercase;
        }

        .status-ready {
          background: var(--success-100);
          color: var(--success-700);
        }

        .status-processing {
          background: var(--warning-100);
          color: var(--warning-700);
        }

        .status-error {
          background: var(--danger-100);
          color: var(--danger-700);
        }

        .dataset-description {
          color: var(--text-secondary);
          font-size: var(--text-sm);
          margin-bottom: var(--spacing-4);
          line-height: 1.5;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }

        .dataset-meta {
          display: flex;
          gap: var(--spacing-4);
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .dataset-meta span {
          display: flex;
          align-items: center;
          gap: var(--spacing-1);
        }

        .delete-confirm {
          position: absolute;
          inset: 0;
          background: var(--bg-secondary);
          border-radius: var(--radius-lg);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: var(--spacing-3);
        }

        .delete-confirm p {
          color: var(--text-primary);
          font-weight: 500;
        }

        .confirm-actions {
          display: flex;
          gap: var(--spacing-2);
        }

        .btn-danger {
          background: var(--danger-500);
          color: white;
        }

        .btn-danger:hover {
          background: var(--danger-600);
        }

        .modal-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          padding: var(--spacing-4);
        }

        .modal {
          background: var(--bg-secondary);
          border-radius: var(--radius-xl);
          width: 100%;
          max-width: 500px;
          max-height: 90vh;
          overflow-y: auto;
          box-shadow: var(--shadow-xl);
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: var(--spacing-5);
          border-bottom: 1px solid var(--border-default);
        }

        .modal-header h2 {
          font-size: var(--text-lg);
          font-weight: 600;
          color: var(--text-primary);
        }

        .modal-body {
          padding: var(--spacing-5);
          display: flex;
          flex-direction: column;
          gap: var(--spacing-4);
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: var(--spacing-2);
        }

        .form-group label {
          font-size: var(--text-sm);
          font-weight: 500;
          color: var(--text-secondary);
        }

        .form-group input,
        .form-group textarea {
          padding: var(--spacing-3);
          background: var(--bg-primary);
          border: 1px solid var(--border-default);
          border-radius: var(--radius-md);
          color: var(--text-primary);
          font-size: var(--text-base);
          transition: border-color var(--transition-fast);
        }

        .form-group input:focus,
        .form-group textarea:focus {
          outline: none;
          border-color: var(--primary-500);
        }

        .drop-zone {
          border: 2px dashed var(--border-default);
          border-radius: var(--radius-lg);
          padding: var(--spacing-8);
          text-align: center;
          cursor: pointer;
          transition: all var(--transition-fast);
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: var(--spacing-2);
          color: var(--text-secondary);
        }

        .drop-zone:hover {
          border-color: var(--primary-500);
          background: var(--primary-50);
        }

        [data-theme="dark"] .drop-zone:hover {
          background: var(--primary-900);
        }

        .drop-zone i {
          font-size: var(--text-3xl);
          color: var(--primary-500);
        }

        .drop-zone small {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .drop-zone.has-files {
          border-color: var(--success-500);
          background: var(--success-50);
        }

        [data-theme="dark"] .drop-zone.has-files {
          background: rgba(34, 197, 94, 0.1);
        }

        .drop-zone.has-files i {
          color: var(--success-500);
        }

        .selected-files {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: var(--spacing-1);
        }

        .upload-progress {
          display: flex;
          flex-direction: column;
          gap: var(--spacing-2);
        }

        .progress-bar {
          height: 8px;
          background: var(--bg-tertiary);
          border-radius: var(--radius-full);
          overflow: hidden;
        }

        .progress-fill {
          height: 100%;
          background: var(--primary-500);
          transition: width 0.3s ease;
        }

        .upload-progress span {
          font-size: var(--text-sm);
          color: var(--text-secondary);
          text-align: center;
        }

        .modal-footer {
          display: flex;
          justify-content: flex-end;
          gap: var(--spacing-3);
          padding: var(--spacing-5);
          border-top: 1px solid var(--border-default);
        }

        @media (max-width: 899px) {
          .main-content {
            margin-left: 0;
            max-width: 100%;
            padding-bottom: 80px;
          }

          .page-header {
            flex-direction: column;
          }
        }

        @media (max-width: 599px) {
          .datasets-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default Datasets;
