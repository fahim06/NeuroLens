# NeuroLens — AI-Powered Image Classification

*Deep learning–based image classifier with Django REST API & React Frontend*

<p align="center">
  AI-powered image classification using convolutional neural networks
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-4.0.0--alpha-blue" />
  <img src="https://img.shields.io/badge/python-3.12-green" />
  <img src="https://img.shields.io/badge/framework-Django 6.0 | DRF-purple" />
  <img src="https://img.shields.io/badge/frontend-React 18 | Vite-cyan" />
  <img src="https://img.shields.io/badge/license-MIT-orange" />
</p>

---

## 🎯 Overview

NeuroLens is an AI platform for image classification, featuring:

- **Django REST Backend** — Production-ready API with DRF
- **React Frontend** — Modern TypeScript SPA with Vite
- **JWT Authentication** — Secure token-based auth with roles
- **ML Integration** — TensorFlow-based CNN with service isolation
- **Role-Based Access** — Admin, Beta User, and Viewer roles
- **Clean Architecture** — Service layer pattern for ML isolation

## 🏗️ Architecture

```
neurolens/
├── frontend/          # React SPA (Vite + TypeScript)
│   ├── src/
│   │   ├── components/  # Reusable UI components
│   │   ├── pages/       # Route pages
│   │   ├── services/    # API client
│   │   └── styles/      # CSS with theming
├── core/              # Health checks, base utilities
├── users/             # User profiles, roles, permissions
├── datasets/          # Dataset management
├── inference/         # Prediction API, service layer
├── ml/                # ML runtime (isolated from Django)
│   └── runtime/       # Model loader, predictor engine
├── neurolens/         # Django settings
├── assets/            # Model weights, static files
└── envs/              # Conda environment files
```

## ⚙️ Quick Start

### Prerequisites

- Python 3.12+
- Conda (for environment management)

### Environment Setup

```bash
# Clone and checkout rebuild branch
git clone https://github.com/fahim06/NeuroLens.git
cd NeuroLens
git checkout django-rebuild

# Create Django environment
conda env create -f envs/neurolens-django.yml
conda activate neurolens-django

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start the server
python manage.py runserver
```

### ML Environment (Optional)

For real ML inference (not mock mode):

```bash
# Create ML environment with TensorFlow
conda env create -f envs/neurolens-ml.yml
conda activate neurolens-ml

# Test model loading
python -c "from ml.runtime.predictor import ml_predictor; print(ml_predictor.health_check())"
```

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start dev server (proxies to Django backend)
npm run dev
```

Frontend will be available at `http://localhost:5173`

## 📡 API Endpoints

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/token/` | POST | Get JWT access/refresh tokens |
| `/api/auth/token/refresh/` | POST | Refresh access token |

### Health Checks

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health/` | GET | System health check |
| `/api/inference/health/` | GET | ML predictor health |

### Datasets

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/datasets/` | GET | JWT | List user datasets |
| `/api/datasets/` | POST | JWT | Create dataset |
| `/api/datasets/<id>/` | GET | JWT | Get dataset details |
| `/api/datasets/<id>/` | DELETE | JWT | Delete dataset |

### Inference

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/inference/predict/` | POST | JWT | Run prediction (sync) |
| `/api/inference/predict/async/` | POST | JWT | Run prediction (async) |
| `/api/inference/<id>/status/` | GET | JWT | Check async request status |
| `/api/inference/history/` | GET | JWT | View prediction history |

### Example Prediction Request

```bash
# Synchronous prediction
curl -X POST http://localhost:8000/api/inference/predict/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"image_data": "<base64_encoded_image>"}'

# Asynchronous prediction (requires Redis)
curl -X POST http://localhost:8000/api/inference/predict/async/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"image_data": "<base64_encoded_image>"}'
```

### Running with Celery (Optional)

For async inference, start Redis and Celery:

```bash
# Start Redis (macOS)
brew services start redis

# Start Celery worker
celery -A neurolens worker --loglevel=info
```

## 🔐 Roles & Permissions

| Role        | Permissions                           |
|-------------|---------------------------------------|
| `admin`     | Full access to all resources          |
| `beta_user` | Access to beta features, own datasets |
| `viewer`    | Read-only access to own datasets      |

## 📦 Conda Environments

| Environment        | Purpose                          |
|--------------------|----------------------------------|
| `neurolens-django` | Django API runtime               |
| `neurolens-ml`     | ML inference with TensorFlow     |
| `neurolens-dev`    | Development tools (pytest, ruff) |

## 🧪 Testing

```bash
# Run Django tests
conda activate neurolens-django
python manage.py test

# Run ML tests
conda activate neurolens-ml
python -c "from ml.runtime.predictor import ml_predictor; print(ml_predictor.health_check())"
```

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

## 📋 Django Rebuild Status

| Phase | Description            | Status     |
|-------|------------------------|------------|
| 0     | Reset & Foundation     | ✅ Complete |
| 1     | Core Architecture      | ✅ Complete |
| 2     | JWT Authentication     | ✅ Complete |
| 3     | Core REST APIs         | ✅ Complete |
| 4     | ML Integration         | ✅ Complete |
| 5     | Beta Stabilization     | ✅ Complete |
| 6     | Beta Release           | ✅ Complete |
| 7     | Full Responsive UI/UX  | ✅ Complete |
| 8     | Final Release          | ⏳ Pending  |

---

## 🎨 Beta UI/UX Interface (Phase 7)

NeuroLens includes a fully responsive web interface for beta testing.

### Features

- **Animated Login Page** — Floating particles, gradient background, smooth transitions
- **Responsive Dashboard** — Stats cards, quick actions, recent activity
- **Dataset Management** — Drag-and-drop upload, file preview, progress tracking
- **AI Inference** — Run analysis with 2-second polling for status updates
- **Profile Settings** — Theme toggle, account management, API access

### Design System

- **Mobile-First** — Optimized for all screen sizes (320px to 1920px+)
- **Dark/Light Mode** — User-selectable theme with persistence
- **CSS Architecture** — Separated into 4 modular files:
  - `base.css` — Variables, reset, typography, components
  - `layout.css` — Page structure, sidebar, cards
  - `animations.css` — Transitions, keyframes, effects
  - `responsive.css` — All breakpoints, touch optimization

### Access the UI

```bash
# Start the server
python manage.py runserver

# Open browser to:
# http://localhost:8000/ui/login/
```

### Pages

| Route | Description |
|-------|-------------|
| `/ui/login/` | Animated login with JWT auth |
| `/ui/dashboard/` | Overview stats and quick actions |
| `/ui/datasets/` | Upload and manage datasets |
| `/ui/inference/` | Run AI analysis with polling |
| `/ui/profile/` | Settings and account management |

### Technology Stack

- Pure HTML5 + CSS3 + Vanilla JavaScript
- No frontend frameworks (React, Vue, etc.)
- Django templates with `{% load static %}`
- Font Awesome 6.4 for icons
- LocalStorage for token management

---

## Beta Readiness

Asynchronous inference enabled.
System stabilized for beta users.
Phase 5 complete.

---

<div align="center">

**NeuroLens v4.0.0-beta** — Django REST Rebuild

*Built for reliability, scalability, and security*

</div>
