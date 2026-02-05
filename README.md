# NeuroLens — Multi-Domain AI Detection Platform

*Deep learning–based multi-domain detection with Django REST API & Tailwind UI*

<p align="center">
  AI-powered detection for humans, animals, biological classification, medical imaging, and plant analysis
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.12--alpha-blue" />
  <a href="https://github.com/fahim06/NeuroLens/actions/workflows/ci.yml">
    <img src="https://github.com/fahim06/NeuroLens/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI" />
  </a>
  <img src="https://img.shields.io/badge/python-3.12-green" />
  <img src="https://img.shields.io/badge/framework-Django 6.0 | DRF-purple" />
  <img src="https://img.shields.io/badge/frontend-Django Templates | Tailwind-cyan" />
  <img src="https://img.shields.io/badge/license-MIT-orange" />
</p>

---

## 🎯 Overview

NeuroLens is an AI platform for multi-domain image detection and classification, featuring:

- **Django REST Backend** — Production-ready API with DRF
- **Django Templates + Tailwind** — Zero-build CSS UI
- **JWT Authentication** — Secure token-based auth with roles
- **Multi-Domain Detection** — 5 detection types with unified API
- **Role-Based Access** — Admin, Beta User, and Viewer roles
- **Model Registry** — Extensible model architecture for new detection types

## 🧠 Supported Detection Types

| Detection Type     | Description                | Model        |
|--------------------|----------------------------|--------------|
| 🧑 Human vs Animal | Binary detection           | Custom CNN   |
| 🐾 Animal Category | Species classification     | Custom CNN   |
| 🧬 Biological      | Kingdom → Species taxonomy | Hierarchical |
| 🧠 Brain Tumor     | Medical MRI analysis       | VGG16        |
| 🍊 Citrus          | Plant genus identification | MobileNet    |

## 🏗️ Architecture

```
neurolens/
├── ui/                # Django Templates + Tailwind CSS
│   ├── templates/     # HTML templates
│   ├── static/        # CSS, JS assets
│   └── views.py       # View functions
├── core/              # Health checks, base utilities
├── users/             # User profiles, roles, permissions
├── datasets/          # Dataset management
├── inference/         # Prediction API, service layer
├── ml/                # ML runtime (isolated from Django)
│   ├── registry.py    # Model registry for detection types
│   ├── models/        # Detection model implementations
│   │   ├── animal_detector/
│   │   ├── bio_classifier/
│   │   ├── brain_tumor/
│   │   └── citrus_classifier/
│   └── inference_engine.py  # Unified inference interface
├── neurolens/         # Django settings
└── assets/            # Model weights, static files
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

| Endpoint                   | Method | Description                   |
|----------------------------|--------|-------------------------------|
| `/api/auth/token/`         | POST   | Get JWT access/refresh tokens |
| `/api/auth/token/refresh/` | POST   | Refresh access token          |

### Health Checks

| Endpoint                 | Method | Description         |
|--------------------------|--------|---------------------|
| `/api/health/`           | GET    | System health check |
| `/api/inference/health/` | GET    | ML predictor health |

### Datasets

| Endpoint              | Method | Auth | Description         |
|-----------------------|--------|------|---------------------|
| `/api/datasets/`      | GET    | JWT  | List user datasets  |
| `/api/datasets/`      | POST   | JWT  | Create dataset      |
| `/api/datasets/<id>/` | GET    | JWT  | Get dataset details |
| `/api/datasets/<id>/` | DELETE | JWT  | Delete dataset      |

### Inference

| Endpoint                        | Method | Auth | Description                |
|---------------------------------|--------|------|----------------------------|
| `/api/inference/predict/`       | POST   | JWT  | Run prediction (sync)      |
| `/api/inference/predict/async/` | POST   | JWT  | Run prediction (async)     |
| `/api/inference/<id>/status/`   | GET    | JWT  | Check async request status |
| `/api/inference/history/`       | GET    | JWT  | View prediction history    |

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

| Phase | Description           | Status     |
|-------|-----------------------|------------|
| 0     | Reset & Foundation    | ✅ Complete |
| 1     | Core Architecture     | ✅ Complete |
| 2     | JWT Authentication    | ✅ Complete |
| 3     | Core REST APIs        | ✅ Complete |
| 4     | ML Integration        | ✅ Complete |
| 5     | Beta Stabilization    | ✅ Complete |
| 6     | Beta Release          | ✅ Complete |
| 7     | Full Responsive UI/UX | ✅ Complete |
| 8     | React Migration       | ✅ Complete |
| 9     | CI/CD Implementation  | ✅ Complete |

---

## 🎨 React Frontend (Phase 8)

NeuroLens includes a modern React SPA for the production interface.

### Features

- **Animated Login/Signup** — Glassmorphism design, password strength meter
- **Responsive Dashboard** — Stats cards, health status, quick actions
- **Dataset Management** — Upload modal, CRUD operations, file list
- **AI Inference** — Run analysis with polling for status updates
- **JWT Authentication** — Axios interceptors, token refresh, protected routes

### Technology Stack

- **React 18+** with TypeScript
- **Vite** for fast builds
- **React Router** for navigation
- **Axios** for API calls with JWT interceptors
- **CSS3** with modular architecture

### Access the Frontend

```bash
# Start backend
python manage.py runserver

# Start frontend (development)
cd frontend
npm run dev

# Open browser to:
# http://localhost:5173/
```

### Pages

| Route        | Description                         |
|--------------|-------------------------------------|
| `/login`     | Animated login with JWT auth        |
| `/signup`    | Registration with password strength |
| `/dashboard` | Overview stats and quick actions    |
| `/datasets`  | Upload and manage datasets          |
| `/inference` | Run AI analysis with polling        |

---

## Beta Readiness

Asynchronous inference enabled.
System stabilized for beta users.
Phase 5 complete.

---

<div align="center">

**Built for reliability, scalability, and security**

</div>
