/**
 * NeuroLens - Animated Signup Page
 * Publication-grade registration with floating particles and glassmorphism
 */

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
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

interface FormErrors {
  username?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
}

const Signup: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [serverError, setServerError] = useState<string | null>(null);
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

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (formData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
    setServerError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setLoading(true);
    setServerError(null);

    try {
      // Register user
      await authAPI.register(formData.username, formData.email, formData.password);

      // Auto-login after registration
      const loginResponse = await authAPI.login(formData.username, formData.password);
      TokenManager.setTokens(loginResponse.access, loginResponse.refresh);

      // Fetch user profile
      const profile = await authAPI.getProfile();
      UserManager.setUser(profile);

      navigate('/dashboard', { replace: true });
    } catch (err: any) {
      const data = err.response?.data;
      if (data) {
        // Handle field-specific errors from Django
        if (data.username) setErrors((prev) => ({ ...prev, username: data.username[0] }));
        if (data.email) setErrors((prev) => ({ ...prev, email: data.email[0] }));
        if (data.password) setErrors((prev) => ({ ...prev, password: data.password[0] }));
        if (data.detail || data.error) setServerError(data.detail || data.error);
        if (!data.username && !data.email && !data.password && !data.detail && !data.error) {
          setServerError('Registration failed. Please try again.');
        }
      } else {
        setServerError('Registration failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const getPasswordStrength = (): { strength: number; label: string; color: string } => {
    const { password } = formData;
    let strength = 0;
    
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;

    if (strength <= 1) return { strength, label: 'Weak', color: '#ef4444' };
    if (strength <= 2) return { strength, label: 'Fair', color: '#f59e0b' };
    if (strength <= 3) return { strength, label: 'Good', color: '#10b981' };
    return { strength, label: 'Strong', color: '#22c55e' };
  };

  const passwordStrength = getPasswordStrength();

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

      {/* Signup Card */}
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo">
            <img src="/favicon.svg" alt="NeuroLens" />
          </div>
          <h1>Create Account</h1>
          <p>Join NeuroLens for AI-powered retinal analysis</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {serverError && (
            <div className="alert alert-error fade-in">
              <i className="fa-solid fa-exclamation-circle"></i>
              <span>{serverError}</span>
            </div>
          )}

          <div className={`input-group ${errors.username ? 'has-error' : ''}`}>
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
            {errors.username && <span className="field-error">{errors.username}</span>}
          </div>

          <div className={`input-group ${errors.email ? 'has-error' : ''}`}>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              autoComplete="email"
              placeholder=" "
            />
            <label htmlFor="email">
              <i className="fa-solid fa-envelope"></i>
              <span>Email</span>
            </label>
            {errors.email && <span className="field-error">{errors.email}</span>}
          </div>

          <div className={`input-group ${errors.password ? 'has-error' : ''}`}>
            <input
              type={showPassword ? 'text' : 'password'}
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              autoComplete="new-password"
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
            {errors.password && <span className="field-error">{errors.password}</span>}
          </div>

          {formData.password && (
            <div className="password-strength fade-in">
              <div className="strength-bar">
                <div 
                  className="strength-fill" 
                  style={{ 
                    width: `${(passwordStrength.strength / 5) * 100}%`,
                    background: passwordStrength.color 
                  }}
                />
              </div>
              <span className="strength-label" style={{ color: passwordStrength.color }}>
                {passwordStrength.label}
              </span>
            </div>
          )}

          <div className={`input-group ${errors.confirmPassword ? 'has-error' : ''}`}>
            <input
              type={showConfirmPassword ? 'text' : 'password'}
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              autoComplete="new-password"
              placeholder=" "
            />
            <label htmlFor="confirmPassword">
              <i className="fa-solid fa-lock"></i>
              <span>Confirm Password</span>
            </label>
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              tabIndex={-1}
              aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
            >
              <i className={`fa-solid ${showConfirmPassword ? 'fa-eye-slash' : 'fa-eye'}`}></i>
            </button>
            {errors.confirmPassword && <span className="field-error">{errors.confirmPassword}</span>}
          </div>

          <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
            {loading ? (
              <>
                <Loader size="sm" />
                <span>Creating account...</span>
              </>
            ) : (
              <>
                <i className="fa-solid fa-user-plus"></i>
                <span>Create Account</span>
              </>
            )}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
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

        .auth-form .input-group.has-error input {
          border-color: #ef4444;
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

        .field-error {
          display: block;
          color: #fca5a5;
          font-size: var(--text-xs);
          margin-top: var(--spacing-1);
          padding-left: var(--spacing-1);
        }

        .password-strength {
          display: flex;
          align-items: center;
          gap: var(--spacing-3);
          margin-top: calc(-1 * var(--spacing-2));
        }

        .strength-bar {
          flex: 1;
          height: 4px;
          background: rgba(255, 255, 255, 0.2);
          border-radius: 2px;
          overflow: hidden;
        }

        .strength-fill {
          height: 100%;
          transition: width 0.3s ease, background 0.3s ease;
        }

        .strength-label {
          font-size: var(--text-xs);
          font-weight: 600;
          min-width: 50px;
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

export default Signup;
