# NeuroLens — Multi-Domain AI Detection Platform

*Deep learning–based multi-domain detection with Django REST API & Tailwind UI*

<p align="center">
  <img src="staticfiles/ui/images/logo.svg" alt="NeuroLens Logo" width="120" height="120" />
</p>

<p align="center">
  AI-powered detection for humans, animals, biological classification, medical imaging, and plant analysis
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.32--beta-yellow" />
  <a href="https://github.com/fahim06/NeuroLens/actions/workflows/CI-CD.yml">
    <img src="https://github.com/fahim06/NeuroLens/actions/workflows/CI-CD.yml/badge.svg?branch=django-rebuild" alt="CI/CD" />
  </a>
  <img src="https://img.shields.io/badge/python-3.12-green" />
  <img src="https://img.shields.io/badge/framework-Django 6.0 | DRF-purple" />
  <img src="https://img.shields.io/badge/frontend-Django Templates | Tailwind-cyan" />
  <img src="https://img.shields.io/badge/license-MIT-orange" />
</p>

---

## 🎯 Overview

NeuroLens is an AI platform for multi-domain image detection and classification, featuring:

- 🏗️ **Django REST Backend** — Production-ready API with DRF
- 🎨 **Django Templates + Tailwind** — Zero-build CSS UI
- 🔐 **JWT Authentication** — Secure token-based auth with roles
- 🧠 **Multi-Domain Detection** — 5 detection types with unified API
- 📚 **Model Registry** — Extensible model architecture for new detection types
- 🔍 **Auto-domain detection** — Automatically identifies image domain
- 🤖 **Auto-model selection** — Selects appropriate ML model per domain
- 🧬 **Biological classification output** — Hierarchical taxonomy for bio samples

## 🧠 Supported Detection Types

| Detection Type     | Description                | Model        |
|--------------------|----------------------------|--------------|
| 🧑 Human vs Animal | Binary detection           | Custom CNN   |
| 🐾 Animal Category | Species classification     | Custom CNN   |
| 🧬 Biological      | Kingdom → Species taxonomy | Hierarchical |
| 🧠 Brain Tumor     | Medical MRI analysis       | VGG16        |
| 🍊 Citrus          | Plant genus identification | MobileNet    |

## 🏗️ Architecture

### High-Level Architecture

```
┌─────────┐     ┌─────────────────────────────┐     ┌─────────────────┐     ┌─────────────────────────────────────────┐
│ Browser │ ──► │ Django Templates + Tailwind │ ──► │ Django REST API │ ──► │ Service Layer                          │
│         │     │ UI                          │     │                 │     │ (Router, Registry, Taxonomy)           │
└─────────┘     └─────────────────────────────┘     └─────────────────┘     └─────────────────────────────────────────┘
                                                                                      │
                                                                                      ▼
┌─────────────────────┐     ┌─────────────────────────────┐
│ Async Worker        │ ──► │ ML Runtime                  │
│ (Celery + Redis)    │     │ (Isolated Models)           │
└─────────────────────┘     └─────────────────────────────┘
```

#### Sequence Diagram (Inference Request)

```
User                    Controller                Service             ML Runtime      Database
  │                         │                        │                     │              │
  │───POST /api/inference──►│                        │                     │              │
  │                         │                        │                     │              │
  │                         │───validate_request()──►│                     │              │
  │                         │                        │                     │              │
  │                         │                        │───process_image()──►│              │
  │                         │                        │                     │              │
  │                         │                        │                     │◄───result────│
  │                         │                        │                     │              │
  │                         │                        │◄───save_result()────│              │
  │                         │                        │                     │              │
  │                         │◄───response────────────│                     │              │
  │                         │                        │                     │              │
  │◄───JSON Response───────►│                        │◄────────────────────│              │
```

### Website & User Experience (UX) Diagrams

#### User Flow Diagram

```
┌─────────────┐
│   Landing   │
│   Page      │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│   Login     │◄────┤  Register   │
│   Page      │     │   Page      │
└──────┬──────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│  Dashboard  │ ◄─────────────────┐
│  (Stats)    │                   │
└──────┬──────┘                   │
       │                          │
       ├─────────────┐            │
       │             ▼            │
       │    ┌─────────────┐       │
       │    │  Datasets   │       │
       │    │ Management  │ ──────┘
       │    └──────┬──────┘
       │           │
       ▼           ▼
┌─────────────┐    ┌─────────────┐
│  Inference  │    │   Upload    │
│   Results   │    │   Dataset   │
└─────────────┘    └─────────────┘
```

#### Wireframe Sketch (Dashboard)

```
┌─────────────────────────────────────────────────────────────┐
│ NeuroLens                    [Profile] [Logout]             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Welcome back, [User]!              [Upload Dataset]        │
│                                                             │
├─────────────────┬─────────────────┬─────────────────┬───────┤
│ Total Datasets  │ Active Models   │ Today's         │ Health│
│       12        │       5         │ Predictions     │  ✅   │
│                 │                 │      47         │       │
├─────────────────┬─────────────────┬─────────────────┬───────┤
│                                                             │
│ Recent Activity:                                            │
│ • Dataset "cats_vs_dogs" uploaded 2h ago                    │
│ • Inference completed on "medical_scan_001" 1h ago          │
│ • Model "brain_tumor_v2" deployed 30m ago                   │
│                                                             │
│ [View All Activity]                                         │
├─────────────────────────────────────────────────────────────┤
│ Quick Actions: [New Inference] [Manage Datasets] [Settings] │
└─────────────────────────────────────────────────────────────┘
```

### Data & System Architecture Diagrams

#### Database Schema Overview

```
┌─────────────────────────────────────────────────────┐
│                    PostgreSQL Database              │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────────────┐  ┌──────────────────┐          │
│  │   auth_user     │  │  users_profile   │          │
│  │                 │  │                  │          │
│  │ - id (PK)       │  │ - user_id (FK)   │          │
│  │ - username      │  │ - role           │          │
│  │ - email         │  │ - profile_pic    │          │
│  └─────────────────┘  └──────────────────┘          │
│           │                       │                 │
│           │ 1:N                   1:1               │
│           ▼                       │                 │
│  ┌─────────────────┐              │                 │
│  │   datasets      │◄─────────────┘                 │
│  │                 │                                │
│  │ - id (PK)       │                                │
│  │ - name          │                                │
│  │ - owner_id (FK) │                                │
│  └─────────────────┘                                │
│           │                                         │
│           │ 1:N                                     │
│           ▼                                         │
│  ┌─────────────────┐                                │
│  │ inference_req   │                                │
│  │                 │                                │
│  │ - id (PK)       │                                │
│  │ - user_id (FK)  │                                │
│  │ - dataset_id(FK)│                                │
│  │ - status        │                                │
│  └─────────────────┘                                │
└─────────────────────────────────────────────────────┘
```

#### System Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │   Frontend      │  │   Backend       │  │   Redis     │  │
│  │   (Nginx)       │  │   (Django)      │  │   Cache     │  │
│  │                 │  │                 │  │             │  │
│  │ - Static files  │  │ - API           │  │ - Sessions  │  │
│  │ - Templates     │  │ - Business logic│  │ - Tasks     │  │
│  │ - Routing       │  └─────────────────┘  └─────────────┘  │
│  └─────────────────┘                                        │
│           │                                                 │
│           │ HTTP                                            │
│           ▼                                                 │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │   PostgreSQL    │  │   ML Models     │                   │
│  │   Database      │  │   (Volume)      │                   │
│  │                 │  │                 │                   │
│  │ - User data     │  │ - Pre-trained   │                   │
│  │ - Datasets      │  │ - Checkpoints   │                   │
│  │ - Results       │  │ - Configs       │                   │
│  └─────────────────┘  └─────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### Project Structure

```
NeuroLens/
├── .env.example            # Environment template
├── docker-compose.yml      # Docker services configuration
├── manage.py               # Django management script
├── requirements.txt        # Python dependencies
├── dump.rdb                # Redis database dump
├── core/                   # Health checks, base utilities
├── users/                  # User profiles, roles, permissions
├── datasets/               # Dataset management
├── inference/              # Prediction API, service layer
│   └── services/           # Prediction services
├── ui/                     # Django Templates + Tailwind CSS
│   ├── templates/ui/       # HTML templates
│   └── static/ui/          # CSS, JS assets
├── ml/                     # ML runtime (isolated from Django)
│   ├── registry.py         # Model registry for detection types
│   ├── inference_engine.py # Unified inference interface
│   ├── models/             # Detection model implementations
│   ├── runtime/            # ML runtime components
│   └── services/           # ML services
├── neurolens/              # Django project settings
├── infra/                  # Infrastructure configs
├── media/                  # User uploaded media
├── staticfiles/            # Collected static files
├── logs/                   # Application logs
├── demo_images/            # Sample images for testing
└── tests/                  # Test suite
```

## ⚙️ Quick Start

```bash
# Clone repository
git clone https://github.com/fahim06/NeuroLens.git
cd NeuroLens

# Setup environment
cp .env.example .env

# Build and run with Docker
docker compose build
docker compose up
```

### Post-Setup Steps

After containers are running:

```bash
# Run migrations
docker compose exec backend python manage.py migrate

# Create superuser
docker compose exec backend python manage.py createsuperuser
```

### Access URLs

- **UI**: http://localhost:8000/
- **Admin**: http://localhost:8000/admin/

## 🌐 Pages

The NeuroLens UI provides a complete web interface built with Django Templates and Tailwind CSS:

- 🔐 **Login** — Animated login page with Tailwind + custom CSS
- 📊 **Dashboard** — System overview with stats and health status
- 📁 **Dataset Management** — Fully functional upload, CRUD operations, and file management
- 🤖 **Inference** — Auto-detection and classification interface

> The system does **not** require users to select models; detection is fully automated.

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

## 🎨 Branding

- `logo.svg` is the single source of brand identity
- Used for:
  - navbar
  - login page
  - dashboard
  - dataset page
  - favicon

## 🧪 Testing

```bash
# Run Django tests
docker compose exec backend python manage.py test

# Run ML tests
docker compose exec backend python -c "from ml.runtime.predictor import ml_predictor; print(ml_predictor.health_check())"
```

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
| 8     | Django UI Completion  | ✅ Complete |
| 9     | CI/CD Implementation  | ✅ Complete |

---

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

<div align="center">

**Built for reliability, scalability, and security**

</div>
