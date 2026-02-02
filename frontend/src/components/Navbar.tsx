/**
 * NeuroLens - Navbar Component
 * Sidebar navigation for authenticated pages
 */

import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { TokenManager, UserManager } from '../services/api';
import logo from '../assets/logo.svg';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const user = UserManager.getUser();
  const [isOpen, setIsOpen] = useState(false);

  const handleLogout = () => {
    TokenManager.clearTokens();
    UserManager.clearUser();
    navigate('/login');
  };

  const toggleTheme = () => {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
  };

  const closeSidebar = () => setIsOpen(false);

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        className="mobile-menu-btn"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Toggle menu"
      >
        <i className={`fa-solid ${isOpen ? 'fa-times' : 'fa-bars'}`}></i>
      </button>

      {/* Overlay for mobile */}
      <div
        className={`sidebar-overlay ${isOpen ? 'visible' : ''}`}
        onClick={closeSidebar}
      />

      {/* Sidebar */}
      <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
        {/* Header */}
        <div className="sidebar-header">
          <div className="logo">
            <img src={logo} alt="NeuroLens" width={40} height={40} />
            <span>NeuroLens</span>
          </div>
          <span className="badge info">Beta</span>
        </div>

        {/* Navigation */}
        <nav className="sidebar-nav">
          <NavLink
            to="/dashboard"
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            onClick={closeSidebar}
          >
            <i className="fa-solid fa-chart-line"></i>
            <span>Dashboard</span>
          </NavLink>
          <NavLink
            to="/datasets"
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            onClick={closeSidebar}
          >
            <i className="fa-solid fa-database"></i>
            <span>Datasets</span>
          </NavLink>
          <NavLink
            to="/inference"
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            onClick={closeSidebar}
          >
            <i className="fa-solid fa-wand-magic-sparkles"></i>
            <span>Inference</span>
          </NavLink>
        </nav>

        {/* Footer */}
        <div className="sidebar-footer">
          <button
            className="theme-toggle"
            onClick={toggleTheme}
            aria-label="Toggle theme"
          >
            <i className="fa-solid fa-moon"></i>
          </button>
          <div className="user-card">
            <div className="user-avatar">
              {user?.username?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="user-info">
              <span className="user-name">{user?.username || 'User'}</span>
              <span className="user-role">{user?.role || 'Beta User'}</span>
            </div>
            <button
              className="logout-btn"
              onClick={handleLogout}
              aria-label="Logout"
            >
              <i className="fa-solid fa-right-from-bracket"></i>
            </button>
          </div>
        </div>
      </aside>

      {/* Styles */}
      <style>{`
        .mobile-menu-btn {
          display: none;
          position: fixed;
          top: var(--spacing-4);
          left: var(--spacing-4);
          z-index: 1001;
          width: 44px;
          height: 44px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-default);
          border-radius: var(--radius-md);
          color: var(--text-primary);
          font-size: var(--text-lg);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .mobile-menu-btn:hover {
          background: var(--bg-tertiary);
        }

        @media (max-width: 899px) {
          .mobile-menu-btn {
            display: flex;
            align-items: center;
            justify-content: center;
          }
        }

        .sidebar {
          position: fixed;
          top: 0;
          left: 0;
          width: 260px;
          height: 100vh;
          background: var(--bg-secondary);
          border-right: 1px solid var(--border-default);
          display: flex;
          flex-direction: column;
          z-index: 1000;
          transition: transform 0.3s ease;
        }

        @media (max-width: 899px) {
          .sidebar {
            transform: translateX(-100%);
          }

          .sidebar.open {
            transform: translateX(0);
          }
        }

        .sidebar-overlay {
          display: none;
        }

        @media (max-width: 899px) {
          .sidebar-overlay {
            display: block;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 999;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s;
          }

          .sidebar-overlay.visible {
            opacity: 1;
            visibility: visible;
          }
        }

        .sidebar-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: var(--spacing-5);
          border-bottom: 1px solid var(--border-default);
        }

        .logo {
          display: flex;
          align-items: center;
          gap: var(--spacing-3);
          font-size: 1.25rem;
          font-weight: 600;
          color: var(--text-primary);
        }

        .sidebar-nav {
          flex: 1;
          padding: var(--spacing-4);
          display: flex;
          flex-direction: column;
          gap: var(--spacing-1);
        }

        .nav-item {
          display: flex;
          align-items: center;
          gap: var(--spacing-3);
          padding: var(--spacing-3) var(--spacing-4);
          border-radius: var(--radius-md);
          color: var(--text-secondary);
          text-decoration: none;
          transition: all 0.2s;
        }

        .nav-item:hover {
          background: var(--bg-tertiary);
          color: var(--text-primary);
        }

        .nav-item.active {
          background: var(--primary-100);
          color: var(--primary-700);
        }

        [data-theme="dark"] .nav-item.active {
          background: var(--primary-900);
          color: var(--primary-300);
        }

        .nav-item i {
          font-size: 18px;
          width: 24px;
          text-align: center;
        }

        .sidebar-footer {
          padding: var(--spacing-4);
          border-top: 1px solid var(--border-default);
        }

        .sidebar-footer .theme-toggle {
          width: 100%;
          padding: var(--spacing-3);
          margin-bottom: var(--spacing-3);
          background: var(--bg-tertiary);
          border: none;
          border-radius: var(--radius-md);
          color: var(--text-secondary);
          cursor: pointer;
          transition: all 0.2s;
        }

        .sidebar-footer .theme-toggle:hover {
          background: var(--primary-100);
          color: var(--primary-600);
        }

        [data-theme="dark"] .sidebar-footer .theme-toggle:hover {
          background: var(--primary-900);
          color: var(--primary-300);
        }

        .user-card {
          display: flex;
          align-items: center;
          gap: var(--spacing-3);
          padding: var(--spacing-3);
          background: var(--bg-tertiary);
          border-radius: var(--radius-md);
        }

        .user-avatar {
          width: 40px;
          height: 40px;
          border-radius: var(--radius-full);
          background: linear-gradient(135deg, var(--primary-500), var(--primary-700));
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
        }

        .user-info {
          flex: 1;
          display: flex;
          flex-direction: column;
        }

        .user-name {
          font-size: 14px;
          font-weight: 500;
          color: var(--text-primary);
        }

        .user-role {
          font-size: 11px;
          color: var(--text-tertiary);
        }

        .logout-btn {
          background: none;
          border: none;
          color: var(--text-secondary);
          cursor: pointer;
          padding: var(--spacing-2);
          border-radius: var(--radius-sm);
          transition: all 0.2s;
        }

        .logout-btn:hover {
          background: var(--danger-100);
          color: var(--danger-600);
        }

        [data-theme="dark"] .logout-btn:hover {
          background: rgba(239, 68, 68, 0.2);
          color: var(--danger-400);
        }
      `}</style>
    </>
  );
};

export default Navbar;
