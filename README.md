# NeuroLens — AI-Powered Image Classification

*Deep learning–based image classifier with Django REST API*

<p align="center">
  AI-powered image classification using convolutional neural networks
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-4.0.0--alpha-blue" />
  <img src="https://img.shields.io/badge/python-3.12-green" />
  <img src="https://img.shields.io/badge/framework-Django 6.0 | DRF-purple" />
  <img src="https://img.shields.io/badge/license-MIT-orange" />
</p>

---

## 🎯 Overview

NeuroLens is an AI platform for image classification, featuring:

- **Django REST Backend** — Production-ready API with DRF
- **JWT Authentication** — Secure token-based auth with roles
- **ML Integration** — TensorFlow-based CNN with service isolation
- **Role-Based Access** — Admin, Beta User, and Viewer roles
- **Clean Architecture** — Service layer pattern for ML isolation

## 🏗️ Architecture

```
neurolens/
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
| `/api/inference/predict/` | POST | JWT | Run prediction |
| `/api/inference/history/` | GET | JWT | View prediction history |

### Example Prediction Request

```bash
curl -X POST http://localhost:8000/api/inference/predict/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"image_data": "<base64_encoded_image>"}'
```

## 🔐 Roles & Permissions

| Role | Permissions |
|------|-------------|
| `admin` | Full access to all resources |
| `beta_user` | Access to beta features, own datasets |
| `viewer` | Read-only access to own datasets |

## 📦 Conda Environments

| Environment | Purpose |
|-------------|---------|
| `neurolens-django` | Django API runtime |
| `neurolens-ml` | ML inference with TensorFlow |
| `neurolens-dev` | Development tools (pytest, ruff) |

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

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Reset & Foundation | ✅ Complete |
| 1 | Core Architecture | ✅ Complete |
| 2 | JWT Authentication | ✅ Complete |
| 3 | Core REST APIs | ✅ Complete |
| 4 | ML Integration | ✅ Complete |
| 5 | Beta Stabilization | 🔄 Next |
| 6 | Beta Release | ⏳ Pending |
| 7 | Final Release | ⏳ Pending |

---

<div align="center">

**NeuroLens v4.0.0-alpha** — Django REST Rebuild

*Built for reliability, scalability, and security*

</div>
