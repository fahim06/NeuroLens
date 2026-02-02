# NeuroLens v4.0.0-beta.2

**Status:** Beta  
**Release Date:** February 2, 2026  
**Branch:** dev

---

## 🎯 Overview

This is the first beta release of the NeuroLens Django REST rebuild. The system has been completely rebuilt from scratch using Django 6.0 and Django REST Framework.

---

## ✨ Features

### Core Platform
- **Django 6.0** backend with Django REST Framework
- **JWT authentication** via djangorestframework-simplejwt
- **Role-based access control** (admin, beta_user, viewer)
- **SQLite** for development (PostgreSQL-ready for production)

### API Endpoints
- Health checks (`/api/health/`, `/api/inference/health/`)
- Authentication (`/api/auth/token/`, `/api/auth/token/refresh/`)
- Datasets CRUD (`/api/datasets/`)
- Inference (`/api/inference/predict/`, `/api/inference/predict/async/`)

### ML Integration
- TensorFlow 2.20 runtime (isolated environment)
- Model loading with HDF5 weight support
- 10-class image classifier (32×32 input)
- Mock fallback when ML runtime unavailable

### Async Processing
- Celery + Redis for background tasks
- Async prediction endpoint
- Status tracking via `/api/inference/<id>/status/`
- Graceful degradation when Redis unavailable

---

## ⚠️ Known Limitations

- **No frontend UI** — API-only at this stage
- **No training workflows** — Inference only
- **Limited performance tuning** — Not optimized for production load
- **SQLite only** — PostgreSQL migration pending
- **Redis required** for async — Sync endpoint works without Redis

---

## 🔧 Setup Instructions

### Prerequisites
- Python 3.12+
- Conda
- Redis (optional, for async)

### Installation

```bash
# Clone and checkout dev
git clone https://github.com/fahim06/NeuroLens.git
cd NeuroLens
git checkout dev

# Create environment
conda env create -f envs/neurolens-django.yml
conda activate neurolens-django

# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Start server
python manage.py runserver
```

### With Async Support (Optional)

```bash
# Start Redis
brew services start redis

# Start Celery worker
celery -A neurolens worker --loglevel=info
```

---

## 📡 API Quick Start

### Get Token
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "yourpassword"}'
```

### Run Prediction
```bash
curl -X POST http://localhost:8000/api/inference/predict/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"image_data": "<base64_encoded_image>"}'
```

---

## 📋 Beta Testing Guidelines

### Who Can Access
- Invited beta testers only
- Limited to specific roles
- Rate-limited access

### Feedback
- Report issues via [GitHub Issues](https://github.com/fahim06/NeuroLens/issues)
- Use label: `beta-feedback`
- Include API endpoint, request/response, and steps to reproduce

### What to Test
1. Authentication flow
2. Dataset CRUD operations
3. Sync prediction accuracy
4. Async prediction reliability
5. Error handling and messages

---

## 📊 Build Information

| Component | Version |
|-----------|---------|
| Django | 6.0.1 |
| DRF | 3.16.1 |
| TensorFlow | 2.20.0 |
| Celery | 5.6.2 |
| Python | 3.12 |

---

## 🔄 Upgrade Path

This beta will be followed by:
- **Phase 7**: Bug fixes and feedback incorporation
- **v4.0.0-rc.1**: Release candidate
- **v4.0.0**: Production release

---

## 📝 Changelog

### v4.0.0-beta.1 (2026-02-02)

**Added**
- Complete Django REST backend rebuild
- JWT authentication with role-based access
- Dataset management API
- Sync and async inference endpoints
- ML runtime with TensorFlow 2.20
- Celery integration for background tasks
- Comprehensive logging

**Changed**
- Migrated from FastAPI to Django
- Simplified ML model loading
- New project structure

**Removed**
- Legacy FastAPI backend
- Complex MLOps pipelines (to be re-added later)
- Frontend (to be rebuilt)

---

> **Note:** This is a beta release. Expect bugs and breaking changes.
