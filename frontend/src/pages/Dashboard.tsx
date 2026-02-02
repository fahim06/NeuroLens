/**
 * NeuroLens - Dashboard Page
 * Main dashboard with stats, health status, and feature cards
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Loader from '../components/Loader';
import { statsAPI, healthAPI, UserManager } from '../services/api';

interface Stats {
  total_datasets: number;
  total_inferences: number;
  pending_inferences: number;
  completed_inferences: number;
  failed_inferences: number;
}

interface HealthStatus {
  status: string;
  database: string;
  cache: string;
  celery: string;
  ml_model: string;
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const user = UserManager.getUser();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsData, healthData] = await Promise.all([
          statsAPI.getDashboardStats(),
          healthAPI.getHealth().catch(() => null),
        ]);
        setStats(statsData);
        setHealth(healthData);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'connected':
      case 'loaded':
        return 'var(--success-500)';
      case 'degraded':
      case 'warning':
        return 'var(--warning-500)';
      default:
        return 'var(--danger-500)';
    }
  };

  const statCards = [
    {
      label: 'Datasets',
      value: stats?.total_datasets ?? 0,
      icon: 'fa-database',
      color: 'var(--primary-500)',
      link: '/datasets',
    },
    {
      label: 'Total Inferences',
      value: stats?.total_inferences ?? 0,
      icon: 'fa-brain',
      color: 'var(--info-500)',
      link: '/inference',
    },
    {
      label: 'Completed',
      value: stats?.completed_inferences ?? 0,
      icon: 'fa-check-circle',
      color: 'var(--success-500)',
      link: '/inference',
    },
    {
      label: 'Pending',
      value: stats?.pending_inferences ?? 0,
      icon: 'fa-clock',
      color: 'var(--warning-500)',
      link: '/inference',
    },
  ];

  const features = [
    {
      title: 'Upload Retinal Images',
      description: 'Upload fundus images in JPEG, PNG, or DICOM format for AI analysis.',
      icon: 'fa-upload',
      link: '/datasets',
      action: 'Upload Images',
    },
    {
      title: 'Run Inference',
      description: 'Get instant AI-powered predictions for diabetic retinopathy screening.',
      icon: 'fa-wand-magic-sparkles',
      link: '/inference',
      action: 'Start Analysis',
    },
    {
      title: 'View Results',
      description: 'Review detailed analysis results with explainability heatmaps.',
      icon: 'fa-chart-pie',
      link: '/inference',
      action: 'View Results',
    },
  ];

  return (
    <div className="app-layout">
      <Navbar />
      <main className="main-content">
        <div className="page-header">
          <div className="page-header-content">
            <h1>
              Welcome back, <span className="text-primary">{user?.username || 'User'}</span>
            </h1>
            <p>Here's an overview of your NeuroLens activity</p>
          </div>
          <div className="page-header-actions">
            <Link to="/inference" className="btn btn-primary">
              <i className="fa-solid fa-plus"></i>
              <span>New Inference</span>
            </Link>
          </div>
        </div>

        {loading ? (
          <div className="loading-state">
            <Loader size="lg" text="Loading dashboard..." />
          </div>
        ) : (
          <>
            {/* Stats Grid */}
            <div className="stats-grid">
              {statCards.map((stat, index) => (
                <Link to={stat.link} key={index} className="stat-card">
                  <div className="stat-icon" style={{ background: `${stat.color}20`, color: stat.color }}>
                    <i className={`fa-solid ${stat.icon}`}></i>
                  </div>
                  <div className="stat-info">
                    <span className="stat-value">{stat.value}</span>
                    <span className="stat-label">{stat.label}</span>
                  </div>
                </Link>
              ))}
            </div>

            {/* Health Status */}
            {health && (
              <div className="card health-card">
                <div className="card-header">
                  <h3>
                    <i className="fa-solid fa-heartbeat"></i>
                    System Health
                  </h3>
                  <span
                    className="health-badge"
                    style={{ background: `${getStatusColor(health.status)}20`, color: getStatusColor(health.status) }}
                  >
                    {health.status}
                  </span>
                </div>
                <div className="health-grid">
                  <div className="health-item">
                    <i className="fa-solid fa-database" style={{ color: getStatusColor(health.database) }}></i>
                    <span>Database</span>
                    <span className="health-status" style={{ color: getStatusColor(health.database) }}>
                      {health.database}
                    </span>
                  </div>
                  <div className="health-item">
                    <i className="fa-solid fa-server" style={{ color: getStatusColor(health.cache) }}></i>
                    <span>Cache</span>
                    <span className="health-status" style={{ color: getStatusColor(health.cache) }}>
                      {health.cache}
                    </span>
                  </div>
                  <div className="health-item">
                    <i className="fa-solid fa-gears" style={{ color: getStatusColor(health.celery) }}></i>
                    <span>Workers</span>
                    <span className="health-status" style={{ color: getStatusColor(health.celery) }}>
                      {health.celery}
                    </span>
                  </div>
                  <div className="health-item">
                    <i className="fa-solid fa-brain" style={{ color: getStatusColor(health.ml_model) }}></i>
                    <span>ML Model</span>
                    <span className="health-status" style={{ color: getStatusColor(health.ml_model) }}>
                      {health.ml_model}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Feature Cards */}
            <div className="section-header">
              <h2>Quick Actions</h2>
            </div>
            <div className="features-grid">
              {features.map((feature, index) => (
                <div className="feature-card card" key={index}>
                  <div className="feature-icon">
                    <i className={`fa-solid ${feature.icon}`}></i>
                  </div>
                  <h3>{feature.title}</h3>
                  <p>{feature.description}</p>
                  <Link to={feature.link} className="btn btn-secondary">
                    {feature.action}
                    <i className="fa-solid fa-arrow-right"></i>
                  </Link>
                </div>
              ))}
            </div>
          </>
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

        .text-primary {
          color: var(--primary-600);
        }

        .loading-state {
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 400px;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: var(--spacing-4);
          margin-bottom: var(--spacing-6);
        }

        .stat-card {
          background: var(--bg-secondary);
          border: 1px solid var(--border-default);
          border-radius: var(--radius-lg);
          padding: var(--spacing-5);
          display: flex;
          align-items: center;
          gap: var(--spacing-4);
          text-decoration: none;
          transition: all var(--transition-fast);
        }

        .stat-card:hover {
          border-color: var(--primary-300);
          transform: translateY(-2px);
          box-shadow: var(--shadow-md);
        }

        .stat-icon {
          width: 48px;
          height: 48px;
          border-radius: var(--radius-md);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: var(--text-xl);
        }

        .stat-info {
          display: flex;
          flex-direction: column;
        }

        .stat-value {
          font-size: var(--text-2xl);
          font-weight: 700;
          color: var(--text-primary);
          line-height: 1;
        }

        .stat-label {
          font-size: var(--text-sm);
          color: var(--text-secondary);
          margin-top: var(--spacing-1);
        }

        .health-card {
          margin-bottom: var(--spacing-6);
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: var(--spacing-4) var(--spacing-5);
          border-bottom: 1px solid var(--border-default);
        }

        .card-header h3 {
          display: flex;
          align-items: center;
          gap: var(--spacing-2);
          font-size: var(--text-base);
          font-weight: 600;
          color: var(--text-primary);
        }

        .health-badge {
          padding: var(--spacing-1) var(--spacing-3);
          border-radius: var(--radius-full);
          font-size: var(--text-xs);
          font-weight: 600;
          text-transform: uppercase;
        }

        .health-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: var(--spacing-4);
          padding: var(--spacing-5);
        }

        .health-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: var(--spacing-2);
          text-align: center;
        }

        .health-item i {
          font-size: var(--text-xl);
        }

        .health-item span:first-of-type {
          color: var(--text-secondary);
          font-size: var(--text-sm);
        }

        .health-status {
          font-size: var(--text-xs);
          font-weight: 600;
          text-transform: uppercase;
        }

        .section-header {
          margin-bottom: var(--spacing-4);
        }

        .section-header h2 {
          font-size: var(--text-lg);
          font-weight: 600;
          color: var(--text-primary);
        }

        .features-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: var(--spacing-4);
        }

        .feature-card {
          padding: var(--spacing-6);
          text-align: center;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: var(--spacing-3);
        }

        .feature-icon {
          width: 64px;
          height: 64px;
          background: linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 100%);
          border-radius: var(--radius-lg);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-size: var(--text-2xl);
          margin-bottom: var(--spacing-2);
        }

        .feature-card h3 {
          font-size: var(--text-base);
          font-weight: 600;
          color: var(--text-primary);
        }

        .feature-card p {
          font-size: var(--text-sm);
          color: var(--text-secondary);
          line-height: 1.5;
          margin-bottom: var(--spacing-2);
        }

        .feature-card .btn {
          margin-top: auto;
          display: flex;
          align-items: center;
          gap: var(--spacing-2);
        }

        @media (max-width: 1199px) {
          .stats-grid {
            grid-template-columns: repeat(2, 1fr);
          }

          .health-grid {
            grid-template-columns: repeat(2, 1fr);
          }

          .features-grid {
            grid-template-columns: repeat(2, 1fr);
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
          .stats-grid {
            grid-template-columns: 1fr;
          }

          .health-grid {
            grid-template-columns: repeat(2, 1fr);
          }

          .features-grid {
            grid-template-columns: 1fr;
          }

          .page-header-content h1 {
            font-size: var(--text-xl);
          }
        }
      `}</style>
    </div>
  );
};

export default Dashboard;
