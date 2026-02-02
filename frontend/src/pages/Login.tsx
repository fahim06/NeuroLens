/**
 * NeuroLens - Animated Login Page
 * Publication-grade login with floating particles and glassmorphism
 */

import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { authAPI, TokenManager, UserManager } from '../services/api';
import Loader from '../components/Loader';

interface Particle {
  id: number;
  left: number;
  top: number;
  size: number;
  delay: number;
  duration: number;
}

const Login: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [particles, setParticles] = useState<Particle[]>([]);

  // Generate floating particles on mount
  useEffect(() => {
    const generated: Particle[] = Array.from({ length: 50 }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      top: Math.random() * 100,
      size: Math.random() * 10 + 2,
      delay: Math.random() * 5,
      duration: Math.random() * 10 + 10,
    }));
    setParticles(generated);
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await authAPI.login(formData.username, formData.password);
      TokenManager.setTokens(response.access, response.refresh);
      
      // Fetch user profile
      const profile = await authAPI.getProfile();
      UserManager.setUser(profile);

      // Redirect to intended page or dashboard
      const from = (location.state as any)?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    } catch (err: any) {
      const message = err.response?.data?.detail || 
                      err.response?.data?.error || 
                      'Invalid credentials. Please try again.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      {/* Animated Background Particles */}
      <div className="particles-container">
        {particles.map((p) => (
          <span
            key={p.id}
            className="particle"
            style={{
              left: `${p.left}%`,
              top: `${p.top}%`,
              width: `${p.size}px`,
              height: `${p.size}px`,
              animationDelay: `${p.delay}s`,
              animationDuration: `${p.duration}s`,
            }}
          />
        ))}
      </div>

      {/* Login Card */}
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo">
            <img src="/favicon.svg" alt="NeuroLens" />
          </div>
          <h1>Welcome Back</h1>
          <p>Sign in to continue to NeuroLens</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {error && (
            <div className="alert alert-error fade-in">
              <i className="fa-solid fa-exclamation-circle"></i>
              <span>{error}</span>
            </div>
          )}

          <div className="input-group">
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              autoComplete="username"
              placeholder=" "
            />
            <label htmlFor="username">
              <i className="fa-solid fa-user"></i>
              <span>Username</span>
            </label>
          </div>

          <div className="input-group">
            <input
              type={showPassword ? 'text' : 'password'}
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              autoComplete="current-password"
              placeholder=" "
            />
            <label htmlFor="password">
              <i className="fa-solid fa-lock"></i>
              <span>Password</span>
            </label>
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPassword(!showPassword)}
              tabIndex={-1}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              <i className={`fa-solid ${showPassword ? 'fa-eye-slash' : 'fa-eye'}`}></i>
            </button>
          </div>

          <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
            {loading ? (
              <>
                <Loader size="sm" />
                <span>Signing in...</span>
              </>
            ) : (
              <>
                <i className="fa-solid fa-right-to-bracket"></i>
                <span>Sign In</span>
              </>
            )}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Don't have an account? <Link to="/signup">Create one</Link>
          </p>
        </div>

        <div className="auth-divider">
          <span>Demo Credentials</span>
        </div>

        <div className="demo-credentials">
          <code>demo / demo1234</code>
        </div>
      </div>

      <style>{`
        .auth-container {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, var(--primary-600) 0%, var(--primary-900) 100%);
          position: relative;
          overflow: hidden;
          padding: var(--spacing-4);
        }

        .particles-container {
          position: absolute;
          inset: 0;
          overflow: hidden;
          pointer-events: none;
        }

        .particle {
          position: absolute;
          background: rgba(255, 255, 255, 0.15);
          border-radius: 50%;
          animation: float linear infinite;
        }

        .auth-card {
          background: rgba(255, 255, 255, 0.1);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: var(--radius-xl);
          padding: var(--spacing-8);
          width: 100%;
          max-width: 420px;
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
          animation: fadeIn 0.5s ease-out;
          z-index: 1;
        }

        .auth-header {
          text-align: center;
          margin-bottom: var(--spacing-6);
        }

        .auth-logo {
          width: 64px;
          height: 64px;
          margin: 0 auto var(--spacing-4);
          background: rgba(255, 255, 255, 0.2);
          border-radius: var(--radius-lg);
          display: flex;
          align-items: center;
          justify-content: center;
          padding: var(--spacing-3);
        }

        .auth-logo img {
          width: 100%;
          height: 100%;
          object-fit: contain;
        }

        .auth-header h1 {
          color: white;
          font-size: var(--text-2xl);
          font-weight: 700;
          margin-bottom: var(--spacing-2);
        }

        .auth-header p {
          color: rgba(255, 255, 255, 0.7);
          font-size: var(--text-sm);
        }

        .auth-form {
          display: flex;
          flex-direction: column;
          gap: var(--spacing-4);
        }

        .auth-form .input-group {
          position: relative;
        }

        .auth-form .input-group input {
          width: 100%;
          padding: var(--spacing-4) var(--spacing-4) var(--spacing-4) var(--spacing-12);
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: var(--radius-md);
          color: white;
          font-size: var(--text-base);
          transition: all var(--transition-fast);
        }

        .auth-form .input-group input::placeholder {
          color: transparent;
        }

        .auth-form .input-group input:focus {
          outline: none;
          border-color: rgba(255, 255, 255, 0.5);
          background: rgba(255, 255, 255, 0.15);
        }

        .auth-form .input-group label {
          position: absolute;
          left: var(--spacing-4);
          top: 50%;
          transform: translateY(-50%);
          display: flex;
          align-items: center;
          gap: var(--spacing-2);
          color: rgba(255, 255, 255, 0.6);
          font-size: var(--text-sm);
          pointer-events: none;
          transition: all var(--transition-fast);
        }

        .auth-form .input-group input:focus + label,
        .auth-form .input-group input:not(:placeholder-shown) + label {
          top: 0;
          left: var(--spacing-3);
          transform: translateY(-50%) scale(0.85);
          background: var(--primary-700);
          padding: 0 var(--spacing-2);
          border-radius: var(--radius-sm);
          color: white;
        }

        .password-toggle {
          position: absolute;
          right: var(--spacing-3);
          top: 50%;
          transform: translateY(-50%);
          background: none;
          border: none;
          color: rgba(255, 255, 255, 0.6);
          cursor: pointer;
          padding: var(--spacing-2);
          transition: color var(--transition-fast);
        }

        .password-toggle:hover {
          color: white;
        }

        .auth-form .btn-block {
          width: 100%;
          padding: var(--spacing-4);
          display: flex;
          align-items: center;
          justify-content: center;
          gap: var(--spacing-2);
          font-size: var(--text-base);
          font-weight: 600;
          margin-top: var(--spacing-2);
        }

        .alert {
          display: flex;
          align-items: center;
          gap: var(--spacing-2);
          padding: var(--spacing-3) var(--spacing-4);
          border-radius: var(--radius-md);
          font-size: var(--text-sm);
        }

        .alert-error {
          background: rgba(239, 68, 68, 0.2);
          border: 1px solid rgba(239, 68, 68, 0.3);
          color: #fca5a5;
        }

        .auth-footer {
          text-align: center;
          margin-top: var(--spacing-6);
          color: rgba(255, 255, 255, 0.7);
          font-size: var(--text-sm);
        }

        .auth-footer a {
          color: white;
          font-weight: 600;
          text-decoration: none;
          transition: opacity var(--transition-fast);
        }

        .auth-footer a:hover {
          opacity: 0.8;
        }

        .auth-divider {
          display: flex;
          align-items: center;
          margin: var(--spacing-4) 0;
        }

        .auth-divider::before,
        .auth-divider::after {
          content: '';
          flex: 1;
          height: 1px;
          background: rgba(255, 255, 255, 0.2);
        }

        .auth-divider span {
          padding: 0 var(--spacing-3);
          color: rgba(255, 255, 255, 0.5);
          font-size: var(--text-xs);
          text-transform: uppercase;
          letter-spacing: 0.1em;
        }

        .demo-credentials {
          text-align: center;
        }

        .demo-credentials code {
          background: rgba(255, 255, 255, 0.1);
          padding: var(--spacing-2) var(--spacing-4);
          border-radius: var(--radius-md);
          color: rgba(255, 255, 255, 0.8);
          font-family: var(--font-mono);
          font-size: var(--text-sm);
        }

        @media (max-width: 479px) {
          .auth-card {
            padding: var(--spacing-6);
          }

          .auth-header h1 {
            font-size: var(--text-xl);
          }
        }
      `}</style>
    </div>
  );
};

export default Login;
