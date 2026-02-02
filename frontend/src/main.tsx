/**
 * NeuroLens - Application Entry Point
 */

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

// Styles
import './styles/base.css';
import './styles/animations.css';
import './styles/responsive.css';

import App from './App';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
