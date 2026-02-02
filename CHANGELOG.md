# Changelog

All notable changes to NeuroLens will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.0.0-dev.1] - 2026-02-02

### 🚀 Major Platform Rebuild

This is the pre-production development release of NeuroLens v3.0 — a complete platform rebuild.

### Added (3.0.0)

#### Backend
- **FastAPI Backend** — Complete API with async support
- **JWT Authentication** — Secure token-based auth with refresh tokens
- **RBAC System** — Role-based access control (Admin, Owner, Member, Viewer)
- **User & Org Management** — Multi-tenant organization support
- **Model Registry** — Version-controlled model management
- **Dataset Management** — CRUD operations for training datasets
- **Inference API** — Single and batch prediction endpoints

#### Machine Learning
- **ML Core Architecture** — Modular interfaces for models, trainers, evaluators
- **Training System** — Keras-based trainers with configurable augmentations
- **Inference Engine** — Batched processing with confidence calibration
- **Explainability** — GradCAM integration for model interpretability
- **Model Registry** — Metadata tracking and version control
- **MLOps Automation** — Validation gates, retraining triggers

#### Infrastructure
- **Docker Support** — Production-ready Dockerfiles
- **CI/CD Pipelines** — GitHub Actions for dev, feature, and main branches
- **Observability Stack** — Prometheus metrics, OpenTelemetry tracing
- **Grafana Dashboards** — Pre-built monitoring dashboards
- **Alert Rules** — SLO-based alerting configuration

#### Security
- **Password Security** — PBKDF2-SHA256 with 100k iterations
- **Token Security** — JWT with JTI for revocation
- **Rate Limiting** — Sliding window + token bucket algorithms
- **Input Validation** — SQL injection, XSS, path traversal detection
- **Audit Logging** — Tamper-resistant event chain
- **Secrets Management** — Environment validation, secrets scanning
- **Data Protection** — AES-256-GCM encryption, PII detection

#### Documentation
- Architecture overview
- API design guide
- ML contracts specification
- Compliance & security guide
- Scaling documentation

### Changed (3.0.0)

- Complete architecture redesign from monolith to modular platform
- New React frontend replacing Taipy
- Professional-grade codebase structure

### Removed (3.0.0)

- Legacy Taipy-based frontend
- Old classifier.py single-file application
- Jupyter notebooks (moved to separate research repo)

---

## [2.1.0] - 2026-01-26

### Added (2.1.0)

- 🔄 **Fluid Typography** - Text now scales smoothly across all screen sizes using CSS `clamp()`
- 📐 **Enhanced Responsive Grid** - Improved Taipy layout overrides for better mobile/desktop switching
- 📦 **Inline CSS Variables** - All design tokens now embedded directly in main.css

### Changed (2.1.0)

- 📱 **Improved Mobile Layout** - Cards now stack properly on mobile devices
- 🎨 **Better Image Responsiveness** - Preview images scale to 100% container width
- ⚡ **Optimized Padding** - Reduced excessive spacing for cleaner mobile experience
- 🔧 **Streamlined Codebase** - Removed unused files and variables

### Fixed (2.1.0)

- 🐛 Fixed broken UI caused by missing CSS variables import
- 🐛 Fixed layout overflow issues on small screens
- 🐛 Fixed prediction result text wrapping on mobile
- 🐛 Fixed confidence display alignment on narrow screens

### Removed (2.1.0)

- 🗑️ Removed `design-system.css` (merged into main.css)
- 🗑️ Removed `generate_favicons.py` (one-time use script)
- 🗑️ Removed duplicate favicon files from root directory

---

## [2.0.0] - 2026-01-26

### Added (2.0.0)

- 🎨 **Complete UI Redesign** - Premium glassmorphism design with gradient accents
- 📱 **Fully Responsive Design** - Works on mobile, tablet, laptop, and desktop (5 breakpoints)
- 🌙 **Dark Theme** - Beautiful dark mode interface
- ⚡ **Animation System** - Smooth transitions and micro-interactions
- 🔧 **Brand System** - Centralized branding configuration (`brand.json`)
- 📦 **Favicon Assets** - Multi-size favicon generation (16px to 512px)
- 🧪 **Unit Tests** - Test suite for classifier module
- 🔄 **CI/CD Pipeline** - GitHub Actions for automated testing
- 📄 **PWA Manifest** - Web app manifest for progressive web app support

### Changed (2.0.0)

- 🏗️ **Project Structure** - Reorganized files into `src/`, `assets/`, `tests/`, `notebooks/`
- 📝 **Documentation** - Comprehensive README with badges and detailed instructions
- 🎯 **UX Improvements** - Cleaner layout with better visual hierarchy
- 🔒 **Security Policy** - Added SECURITY.md with vulnerability reporting guidelines

### Technical (2.0.0)

- Taipy GUI framework for web interface
- TensorFlow/Keras for CNN model inference
- CSS custom properties for design system
- Responsive breakpoints: 320px, 480px, 768px, 1024px, 1280px, 1536px

---

## [1.0.0] - Initial Release

### Added (1.0.0)

- Basic image classification using CNN trained on CIFAR-10
- Simple Taipy GUI interface
- Support for PNG, JPG, JPEG image formats
- 10-class classification (airplane, automobile, bird, cat, deer, dog, frog, horse, ship, truck)

---

## Links

- [GitHub Repository](https://github.com/fahim06/NeuroLens)
- [Report Issues](https://github.com/fahim06/NeuroLens/issues)
