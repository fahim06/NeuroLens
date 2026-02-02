/**
 * NeuroLens - Loader Component
 * Loading spinner with optional overlay
 */

import React from 'react';

interface LoaderProps {
  size?: 'sm' | 'md' | 'lg';
  overlay?: boolean;
  text?: string;
}

const Loader: React.FC<LoaderProps> = ({ size = 'md', overlay = false, text }) => {
  const sizeMap = {
    sm: 24,
    md: 40,
    lg: 60,
  };

  const spinnerStyle: React.CSSProperties = {
    width: sizeMap[size],
    height: sizeMap[size],
    border: `${size === 'sm' ? 2 : 3}px solid var(--surface-variant)`,
    borderTopColor: 'var(--primary)',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  };

  if (overlay) {
    return (
      <div className="loading-overlay visible">
        <div style={{ textAlign: 'center' }}>
          <div style={spinnerStyle}></div>
          {text && (
            <p style={{ marginTop: 16, color: 'white', fontSize: 14 }}>{text}</p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
      <div style={spinnerStyle}></div>
      {text && <span style={{ color: 'var(--secondary)', fontSize: 14 }}>{text}</span>}
    </div>
  );
};

export default Loader;
