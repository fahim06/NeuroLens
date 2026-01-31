# NeuroLens v3.0 - Phase 1 Architecture Documentation

## Overview

This document describes the platform core architecture for NeuroLens v3.0, an AI-powered medical image analysis
platform.

## Architecture Philosophy

- **API-first**: All functionality exposed through well-defined APIs
- **Model-agnostic**: Support multiple ML frameworks and model types
- **Service-oriented**: Modular monolith ready for microservices
- **ML as subsystem**: Clean separation between API and ML layers
- **Frontend as consumer**: UI consumes APIs, doesn't drive architecture
- **Reproducibility > speed**: Deterministic, versioned pipelines
- **Observability-first**: Built-in monitoring and tracing

## High-Level Architecture

```
┌──────────────┐
│  React App   │
│  (Frontend)  │
└──────┬───────┘
       │ REST / JSON
       ▼
┌──────────────────────┐
│     FastAPI API      │
│  (Gateway + Auth)    │
└──────┬───────────────┘
       │
       ├── Inference Service
       ├── Training Service
       ├── Model Registry
       ├── Monitoring
       │
       ▼
┌──────────────────────┐
│      ML Core         │
│ (Models + Pipelines) │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│   Storage Layer      │
│ - Datasets           │
│ - Models             │
│ - Metadata           │
└──────────────────────┘
```

## Directory Structure

```
neuroLens/
├── backend/
│   └── app/
│       ├── api/           # API layer (FastAPI routes)
│       │   └── v1/        # Versioned API endpoints
│       ├── core/          # Core config and utilities
│       ├── ml/            # ML contracts and preprocessing
│       ├── models/        # Database models (future)
│       ├── schemas/       # Pydantic request/response schemas
│       ├── services/      # Business logic layer
│       ├── workers/       # Background task workers
│       └── main.py        # Application entry point
├── frontend/
│   └── src/               # React application
├── ml/
│   ├── datasets/          # Dataset management
│   ├── evaluation/        # Model evaluation
│   ├── experiments/       # MLflow experiments
│   ├── registry/          # Model registry
│   └── training/          # Training pipelines
├── infra/
│   ├── compose/           # Docker Compose files
│   ├── docker/            # Dockerfiles
│   └── k8s/               # Kubernetes manifests
├── docs/                  # Documentation
├── envs/                  # Environment configs
└── tests/                 # Test suite
```

## Service Boundaries

### API Layer (FastAPI)

- Authentication & Authorization
- Request validation
- Rate limiting
- API versioning (`/api/v1/*`, `/api/v2/*`)
- Request routing to services

### Services Layer

- Business logic implementation
- Service-to-service communication
- No direct database/ML access

### ML Core

- Training pipelines
- Inference execution
- Feature extraction
- Model explainability
- **No UI/API logic**

### Data Layer

- Dataset ingestion & validation
- Data versioning (hash-based)
- Feature storage

## API Contract Strategy

- **Protocol**: REST with JSON
- **Versioning**: `/api/v1/*`
- **Documentation**: Auto-generated OpenAPI
- **Validation**: Strict Pydantic schemas
- **Principle**: No business logic in controllers

## Configuration Strategy

- **Local secrets**: `.env` files
- **Config management**: Pydantic Settings
- **Environments**: Development, Testing, Production
- **CI secrets**: GitHub Secrets
- **Rule**: No secrets in code

## Versioning Strategy

| Component | Strategy                        |
|-----------|---------------------------------|
| API       | URL path (`/api/v1`, `/api/v2`) |
| Models    | Semantic versioning             |
| Datasets  | Hash-based                      |
| Features  | Schema versioning               |
| Frontend  | Semantic versioning             |

## Coding Standards

- **Formatter**: Black (line-length 88)
- **Linter**: Ruff
- **Type Checker**: MyPy (strict mode)
- **Docstrings**: Required for public APIs
- **Pre-commit**: Enforced hooks

## Naming Conventions

| Context    | Convention | Example              |
|------------|------------|----------------------|
| Python     | snake_case | `inference_service`  |
| URLs       | kebab-case | `/api/v1/model-info` |
| JavaScript | camelCase  | `modelInfo`          |
| Classes    | PascalCase | `InferenceService`   |

## Data Flows

### Inference Flow

```
User → React → FastAPI → Inference Service → ML Core → Model → Result
```

### Training Flow

```
Dataset → Validation → Feature Pipeline → Training → Evaluation → Registry
```

## Getting Started

1. Copy `.env.example` to `.env`
2. Install dependencies: `pip install -e ".[all]"`
3. Run the API: `uvicorn app.main:app --reload`
4. Access docs: http://localhost:8000/docs
