/**
 * NeuroLens - Inference Page
 * Submit inference requests, poll status, view results with explainability
 */

import React, { useState, useEffect, useRef } from 'react';
import Navbar from '../components/Navbar';
import Loader from '../components/Loader';
import { inferenceAPI, datasetsAPI, POLLING_INTERVAL, type Dataset, type InferenceResult } from '../services/api';
import { useToast } from '../components/Toast';

const Inference: React.FC = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [requests, setRequests] = useState<InferenceResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState<number | null>(null);
  const [activeRequest, setActiveRequest] = useState<InferenceResult | null>(null);
  const [showNewModal, setShowNewModal] = useState(false);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const { showToast } = useToast();

  useEffect(() => {
    fetchData();
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  useEffect(() => {
    // Poll for pending/processing requests
    const pendingRequests = requests.filter((r) => ['pending', 'processing'].includes(r.status));
    if (pendingRequests.length > 0) {
      pollingRef.current = setInterval(fetchRequests, POLLING_INTERVAL);
    } else {
      if (pollingRef.current) clearInterval(pollingRef.current);
    }
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [requests]);

  const fetchData = async () => {
    try {
      const [datasetsData, requestsData] = await Promise.all([
        datasetsAPI.list(),
        inferenceAPI.list(),
      ]);
      setDatasets(datasetsData);
      setRequests(requestsData);
    } catch (error) {
      showToast('Failed to load data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchRequests = async () => {
    try {
      const data = await inferenceAPI.list();
      setRequests(data);
    } catch (error) {
      console.error('Failed to poll requests:', error);
    }
  };

  const handleSubmit = async () => {
    if (!selectedDataset) {
      showToast('Please select a dataset', 'warning');
      return;
    }

    setSubmitting(true);
    try {
      await inferenceAPI.submit(selectedDataset);
      showToast('Inference request submitted', 'success');
      setShowNewModal(false);
      setSelectedDataset(null);
      fetchRequests();
    } catch (error: any) {
      const message = error.response?.data?.error || 'Failed to submit inference';
      showToast(message, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return 'fa-check-circle';
      case 'failed':
        return 'fa-times-circle';
      case 'processing':
        return 'fa-spinner fa-spin';
      default:
        return 'fa-clock';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'var(--success-500)';
      case 'failed':
        return 'var(--danger-500)';
      case 'processing':
        return 'var(--info-500)';
      default:
        return 'var(--warning-500)';
    }
  };

  const getSeverityLabel = (level: number): { label: string; color: string } => {
    const labels: Record<number, { label: string; color: string }> = {
      0: { label: 'No DR', color: 'var(--success-500)' },
      1: { label: 'Mild', color: 'var(--info-500)' },
      2: { label: 'Moderate', color: 'var(--warning-500)' },
      3: { label: 'Severe', color: 'var(--danger-400)' },
      4: { label: 'Proliferative', color: 'var(--danger-600)' },
    };
    return labels[level] || { label: 'Unknown', color: 'var(--text-tertiary)' };
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="app-layout">
      <Navbar />
      <main className="main-content">
        <div className="page-header">
          <div className="page-header-content">
            <h1>Inference</h1>
            <p>Run AI-powered diabetic retinopathy analysis</p>
          </div>
          <div className="page-header-actions">
            <button className="btn btn-primary" onClick={() => setShowNewModal(true)}>
              <i className="fa-solid fa-wand-magic-sparkles"></i>
              <span>New Inference</span>
            </button>
          </div>
        </div>

        {loading ? (
          <div className="loading-state">
            <Loader size="lg" text="Loading inference requests..." />
          </div>
        ) : requests.length === 0 ? (
          <div className="empty-state card">
            <div className="empty-icon">
              <i className="fa-solid fa-brain"></i>
            </div>
            <h3>No Inference Requests</h3>
            <p>Submit your first inference request to analyze retinal images with AI.</p>
            <button className="btn btn-primary" onClick={() => setShowNewModal(true)}>
              <i className="fa-solid fa-wand-magic-sparkles"></i>
              <span>Start Your First Analysis</span>
            </button>
          </div>
        ) : (
          <div className="inference-layout">
            {/* Request List */}
            <div className="request-list card">
              <div className="list-header">
                <h3>Inference Requests</h3>
                <span className="request-count">{requests.length}</span>
              </div>
              <div className="list-items">
                {requests.map((request) => (
                  <div
                    key={request.id}
                    className={`request-item ${activeRequest?.id === request.id ? 'active' : ''}`}
                    onClick={() => setActiveRequest(request)}
                  >
                    <div
                      className="request-status"
                      style={{ color: getStatusColor(request.status) }}
                    >
                      <i className={`fa-solid ${getStatusIcon(request.status)}`}></i>
                    </div>
                    <div className="request-info">
                      <span className="request-name">{request.dataset_name}</span>
                      <span className="request-time">{formatDate(request.created_at)}</span>
                    </div>
                    <span
                      className="request-badge"
                      style={{
                        background: `${getStatusColor(request.status)}20`,
                        color: getStatusColor(request.status),
                      }}
                    >
                      {request.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Results Panel */}
            <div className="results-panel">
              {activeRequest ? (
                <div className="results-card card">
                  <div className="results-header">
                    <div>
                      <h3>{activeRequest.dataset_name}</h3>
                      <span className="results-meta">
                        Request #{activeRequest.id} • {formatDate(activeRequest.created_at)}
                      </span>
                    </div>
                    <span
                      className="status-badge"
                      style={{
                        background: `${getStatusColor(activeRequest.status)}20`,
                        color: getStatusColor(activeRequest.status),
                      }}
                    >
                      {activeRequest.status}
                    </span>
                  </div>

                  {activeRequest.status === 'pending' || activeRequest.status === 'processing' ? (
                    <div className="processing-state">
                      <Loader size="lg" />
                      <h4>
                        {activeRequest.status === 'pending'
                          ? 'Waiting in queue...'
                          : 'Analyzing images...'}
                      </h4>
                      <p>This may take a few moments depending on dataset size.</p>
                    </div>
                  ) : activeRequest.status === 'failed' ? (
                    <div className="error-state">
                      <i className="fa-solid fa-exclamation-triangle"></i>
                      <h4>Analysis Failed</h4>
                      <p>{activeRequest.error_message || 'An unknown error occurred'}</p>
                    </div>
                  ) : activeRequest.results ? (
                    <div className="results-grid">
                      {activeRequest.results.map((result, index) => (
                        <div key={index} className="result-card">
                          <div className="result-header">
                            <span className="result-name">{result.image_name}</span>
                            <span
                              className="severity-badge"
                              style={{
                                background: `${getSeverityLabel(result.severity_level).color}20`,
                                color: getSeverityLabel(result.severity_level).color,
                              }}
                            >
                              {getSeverityLabel(result.severity_level).label}
                            </span>
                          </div>
                          <div className="result-body">
                            <div className="confidence-meter">
                              <div className="confidence-label">
                                <span>Confidence</span>
                                <span>{Math.round(result.confidence * 100)}%</span>
                              </div>
                              <div className="confidence-bar">
                                <div
                                  className="confidence-fill"
                                  style={{
                                    width: `${result.confidence * 100}%`,
                                    background: getSeverityLabel(result.severity_level).color,
                                  }}
                                />
                              </div>
                            </div>
                            <div className="prediction-text">
                              <strong>Prediction:</strong> {result.prediction}
                            </div>
                          </div>
                          {result.heatmap_url && (
                            <div className="result-heatmap">
                              <img src={result.heatmap_url} alt="Explainability heatmap" />
                              <span className="heatmap-label">Attention Heatmap</span>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="no-results">
                      <p>No results available</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="select-prompt card">
                  <i className="fa-solid fa-arrow-left"></i>
                  <p>Select an inference request to view details</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* New Inference Modal */}
        {showNewModal && (
          <div className="modal-overlay" onClick={() => !submitting && setShowNewModal(false)}>
            <div className="modal" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>New Inference Request</h2>
                <button
                  className="btn btn-ghost"
                  onClick={() => !submitting && setShowNewModal(false)}
                  disabled={submitting}
                >
                  <i className="fa-solid fa-times"></i>
                </button>
              </div>
              <div className="modal-body">
                <div className="form-group">
                  <label>Select Dataset</label>
                  {datasets.length === 0 ? (
                    <div className="no-datasets">
                      <p>No datasets available. Please upload a dataset first.</p>
                    </div>
                  ) : (
                    <div className="dataset-select-grid">
                      {datasets.map((dataset) => (
                        <div
                          key={dataset.id}
                          className={`dataset-option ${selectedDataset === dataset.id ? 'selected' : ''}`}
                          onClick={() => setSelectedDataset(dataset.id)}
                        >
                          <i className="fa-solid fa-folder"></i>
                          <span className="dataset-option-name">{dataset.name}</span>
                          <span className="dataset-option-count">{dataset.file_count} images</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowNewModal(false)}
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleSubmit}
                  disabled={submitting || !selectedDataset}
                >
                  {submitting ? (
                    <>
                      <Loader size="sm" />
                      <span>Submitting...</span>
                    </>
                  ) : (
                    <>
                      <i className="fa-solid fa-paper-plane"></i>
                      <span>Submit</span>
                    </>
                  )}
                </button>
              </div>
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

        .inference-layout {
          display: grid;
          grid-template-columns: 340px 1fr;
          gap: var(--spacing-4);
          align-items: start;
        }

        .request-list {
          position: sticky;
          top: var(--spacing-6);
        }

        .list-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: var(--spacing-4) var(--spacing-5);
          border-bottom: 1px solid var(--border-default);
        }

        .list-header h3 {
          font-size: var(--text-base);
          font-weight: 600;
          color: var(--text-primary);
        }

        .request-count {
          background: var(--bg-tertiary);
          padding: var(--spacing-1) var(--spacing-2);
          border-radius: var(--radius-sm);
          font-size: var(--text-xs);
          font-weight: 600;
          color: var(--text-secondary);
        }

        .list-items {
          max-height: calc(100vh - 280px);
          overflow-y: auto;
        }

        .request-item {
          display: flex;
          align-items: center;
          gap: var(--spacing-3);
          padding: var(--spacing-4) var(--spacing-5);
          cursor: pointer;
          border-bottom: 1px solid var(--border-default);
          transition: background var(--transition-fast);
        }

        .request-item:hover {
          background: var(--bg-tertiary);
        }

        .request-item.active {
          background: var(--primary-50);
          border-left: 3px solid var(--primary-500);
        }

        [data-theme="dark"] .request-item.active {
          background: var(--primary-900);
        }

        .request-status {
          font-size: var(--text-lg);
        }

        .request-info {
          flex: 1;
          min-width: 0;
          display: flex;
          flex-direction: column;
          gap: var(--spacing-1);
        }

        .request-name {
          font-size: var(--text-sm);
          font-weight: 500;
          color: var(--text-primary);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .request-time {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .request-badge {
          font-size: var(--text-xs);
          padding: var(--spacing-1) var(--spacing-2);
          border-radius: var(--radius-sm);
          font-weight: 500;
          text-transform: capitalize;
        }

        .results-panel {
          min-height: 400px;
        }

        .select-prompt {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: var(--spacing-3);
          min-height: 400px;
          color: var(--text-tertiary);
        }

        .select-prompt i {
          font-size: var(--text-2xl);
        }

        .results-card {
          padding: 0;
        }

        .results-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          padding: var(--spacing-5);
          border-bottom: 1px solid var(--border-default);
        }

        .results-header h3 {
          font-size: var(--text-lg);
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: var(--spacing-1);
        }

        .results-meta {
          font-size: var(--text-sm);
          color: var(--text-tertiary);
        }

        .status-badge {
          padding: var(--spacing-1) var(--spacing-3);
          border-radius: var(--radius-full);
          font-size: var(--text-xs);
          font-weight: 600;
          text-transform: uppercase;
        }

        .processing-state,
        .error-state,
        .no-results {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: var(--spacing-3);
          padding: var(--spacing-12);
          text-align: center;
        }

        .processing-state h4,
        .error-state h4 {
          font-size: var(--text-base);
          font-weight: 600;
          color: var(--text-primary);
        }

        .processing-state p,
        .error-state p {
          color: var(--text-secondary);
          font-size: var(--text-sm);
        }

        .error-state {
          color: var(--danger-500);
        }

        .error-state i {
          font-size: var(--text-3xl);
        }

        .results-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: var(--spacing-4);
          padding: var(--spacing-5);
        }

        .result-card {
          background: var(--bg-primary);
          border: 1px solid var(--border-default);
          border-radius: var(--radius-lg);
          overflow: hidden;
        }

        .result-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: var(--spacing-3) var(--spacing-4);
          background: var(--bg-tertiary);
        }

        .result-name {
          font-size: var(--text-sm);
          font-weight: 500;
          color: var(--text-primary);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .severity-badge {
          font-size: var(--text-xs);
          padding: var(--spacing-1) var(--spacing-2);
          border-radius: var(--radius-sm);
          font-weight: 600;
        }

        .result-body {
          padding: var(--spacing-4);
          display: flex;
          flex-direction: column;
          gap: var(--spacing-3);
        }

        .confidence-meter {
          display: flex;
          flex-direction: column;
          gap: var(--spacing-1);
        }

        .confidence-label {
          display: flex;
          justify-content: space-between;
          font-size: var(--text-xs);
          color: var(--text-secondary);
        }

        .confidence-bar {
          height: 6px;
          background: var(--bg-tertiary);
          border-radius: var(--radius-full);
          overflow: hidden;
        }

        .confidence-fill {
          height: 100%;
          transition: width 0.5s ease;
        }

        .prediction-text {
          font-size: var(--text-sm);
          color: var(--text-secondary);
        }

        .prediction-text strong {
          color: var(--text-primary);
        }

        .result-heatmap {
          position: relative;
          border-top: 1px solid var(--border-default);
        }

        .result-heatmap img {
          width: 100%;
          display: block;
        }

        .heatmap-label {
          position: absolute;
          bottom: var(--spacing-2);
          left: var(--spacing-2);
          background: rgba(0, 0, 0, 0.7);
          color: white;
          font-size: var(--text-xs);
          padding: var(--spacing-1) var(--spacing-2);
          border-radius: var(--radius-sm);
        }

        /* Modal Styles */
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
          max-width: 560px;
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
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: var(--spacing-3);
        }

        .form-group label {
          font-size: var(--text-sm);
          font-weight: 500;
          color: var(--text-secondary);
        }

        .no-datasets {
          text-align: center;
          padding: var(--spacing-8);
          color: var(--text-tertiary);
        }

        .dataset-select-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
          gap: var(--spacing-3);
        }

        .dataset-option {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: var(--spacing-2);
          padding: var(--spacing-4);
          background: var(--bg-primary);
          border: 2px solid var(--border-default);
          border-radius: var(--radius-lg);
          cursor: pointer;
          transition: all var(--transition-fast);
          text-align: center;
        }

        .dataset-option:hover {
          border-color: var(--primary-300);
        }

        .dataset-option.selected {
          border-color: var(--primary-500);
          background: var(--primary-50);
        }

        [data-theme="dark"] .dataset-option.selected {
          background: var(--primary-900);
        }

        .dataset-option i {
          font-size: var(--text-2xl);
          color: var(--primary-500);
        }

        .dataset-option-name {
          font-size: var(--text-sm);
          font-weight: 500;
          color: var(--text-primary);
        }

        .dataset-option-count {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .modal-footer {
          display: flex;
          justify-content: flex-end;
          gap: var(--spacing-3);
          padding: var(--spacing-5);
          border-top: 1px solid var(--border-default);
        }

        @media (max-width: 1023px) {
          .inference-layout {
            grid-template-columns: 1fr;
          }

          .request-list {
            position: static;
          }

          .list-items {
            max-height: 300px;
          }
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
          .results-grid {
            grid-template-columns: 1fr;
          }

          .dataset-select-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default Inference;
