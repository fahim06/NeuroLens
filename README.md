# NeuroLens — AI-Powered Image Classification

*Deep learning–based image classifier*

<p align="center">
  <img src="assets/logo.png" alt="NeuroLens Logo" width="180"/>
</p>

<p align="center">
  AI-powered image classification using convolutional neural networks
</p>

<p align="center">
  <a href="https://github.com/fahim06/NeuroLens/actions/workflows/ci.yml">
    <img src="https://github.com/fahim06/NeuroLens/actions/workflows/ci.yml/badge.svg" />
  </a>
  <img src="https://img.shields.io/badge/version-3.0.0--dev.1-blue" />
  <img src="https://img.shields.io/badge/python-3.10 | 3.11-green" />
  <img src="https://img.shields.io/badge/framework-FastAPI | React-purple" />
  <img src="https://img.shields.io/badge/license-MIT-orange" />
</p>

---

## 🎯 Overview

NeuroLens is a production-ready AI platform for medical image analysis, featuring:

- **FastAPI Backend** — High-performance async API with comprehensive security
- **React Frontend** — Modern, responsive user interface
- **ML Pipeline** — Transfer learning–based models with automated training
- **MLOps Automation** — CI/CD, model registry, validation gates
- **Enterprise Security** — RBAC, JWT auth, audit logging, compliance readiness

## 🏗️ Architecture

```
neurolens/
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── api/       # REST API endpoints (v1)
│   │   ├── core/      # Security, config, logging
│   │   ├── models/    # Database models
│   │   ├── services/  # Business logic
│   │   └── schemas/   # Pydantic schemas
│   └── tests/
├── frontend/          # React application
│   └── src/
├── ml/                # Machine learning core
│   ├── core/          # Interfaces, schemas, registry
│   ├── training/      # Trainers, augmentations, configs
│   ├── inference/     # Engine, batching, explainability
│   ├── pipelines/     # Train, evaluate, infer workflows
│   └── ops/           # Validation gates, retraining triggers
├── infra/             # Infrastructure
│   ├── docker/        # Dockerfiles
│   ├── compose/       # Docker Compose configs
│   ├── observability/ # Metrics, tracing, logging
│   ├── dashboards/    # Grafana dashboards
│   └── alerts/        # Prometheus alert rules
├── docs/              # Documentation
└── tests/             # Integration tests
```

## ⚙️ Quick Start

### Prerequisites

- Python 3.11+
- Conda (recommended for environment management)
- Node.js 18+ (for frontend)

### Environment Setup

```bash
# Clone the repository
git clone https://github.com/fahim06/NeuroLens.git
cd NeuroLens

# Create and activate conda environment
conda env create -f envs/neurolens-dev.yml
conda activate neurolens-dev

# Install Python dependencies
pip install -e .

# Start the backend
cd backend
uvicorn app.main:app --reload

# In another terminal, start the frontend
cd frontend
npm install
npm run dev
```

## 📦 Components

### Backend API

| Endpoint Group      | Description                       |
|---------------------|-----------------------------------|
| `/api/v1/auth`      | Authentication & token management |
| `/api/v1/users`     | User management                   |
| `/api/v1/orgs`      | Organization management           |
| `/api/v1/models`    | Model registry & versioning       |
| `/api/v1/datasets`  | Dataset management                |
| `/api/v1/inference` | Prediction endpoints              |
| `/api/v1/health`    | Health checks & readiness         |

### ML Pipeline

- **Training**: Keras-based trainers with augmentation pipelines
- **Inference**: Batched processing with confidence calibration
- **Explainability**: GradCAM visualizations
- **Model Registry**: Version control with validation gates

### Security Features

- PBKDF2-SHA256 password hashing (100k iterations)
- JWT tokens with JTI for revocation
- Role-based access control (RBAC)
- Rate limiting (sliding window + token bucket)
- Input validation (SQL injection, XSS, path traversal)
- Audit logging with tamper detection

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run security tests
python tests/test_security_standalone.py

# Run with coverage
pytest --cov=backend tests/
```

## 📊 Observability

- **Metrics**: Prometheus-compatible metrics
- **Tracing**: OpenTelemetry integration
- **Logging**: Structured JSON logging
- **Dashboards**: Grafana dashboards included
- **Alerts**: SLO-based alerting rules

## 📋 Development Status

| Phase | Component             | Status     |
|-------|-----------------------|------------|
| 1     | Platform Core         | ✅ Complete |
| 2     | Backend API           | ✅ Complete |
| 3     | Frontend React        | ✅ Complete |
| 4     | ML Core               | ✅ Complete |
| 5     | Training System       | ✅ Complete |
| 6     | Inference System      | ✅ Complete |
| 7     | Data Pipeline         | ✅ Complete |
| 8     | MLOps Automation      | ✅ Complete |
| 9     | Product Layer         | ✅ Complete |
| 10    | Monitoring & Scaling  | ✅ Complete |
| 11    | Security & Compliance | ✅ Complete |
| 12    | Dev Release           | ✅ Complete |

## 📄 Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Design Guide](docs/API_DESIGN.md)
- [ML Contracts](docs/ML_CONTRACTS.md)
- [Compliance & Security](docs/COMPLIANCE.md)
- [Scaling Guide](docs/SCALING.md)

## 🔒 Security

For security issues, please see [SECURITY.md](SECURITY.md).

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

## Backend Status

Django REST backend initialized.
Phase 1 complete: Core architecture & health API.

## Security Status

JWT authentication enabled.
Role-based API access enforced.
Phase 2 complete.

## API Status

Core REST APIs implemented.
Inference endpoint stubbed via service layer.
Phase 3 complete.

---

<div align="center">

**NeuroLens v3.0.0-dev.1** — Pre-Production Release

*Built for reliability, scalability, and security*

</div>

---

## Project Status

Django REST rebuild in progress.  
Current phase: **Phase 3 — Core REST APIs**
