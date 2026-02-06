# NeuroLens ML System

Multi-domain machine learning system for NeuroLens.

## Phase 0 — Architecture Foundation

This phase establishes the ML system architecture without implementing actual model training or inference logic.

### Architecture Overview

```
ml/
├── contracts/       # 🔒 Interfaces & schemas
├── registry/        # 📦 Model & dataset registry
├── services/        # 🧠 ML orchestration
├── runtime/         # ⚙️ Runtime helpers
├── errors.py        # ML-specific exceptions
└── models.py        # Django models (metadata only)
```

### Key Components

#### Contracts (`ml/contracts/`)

- **domain.py**: Domain enums and classification rules
- **inference.py**: Request/response schemas

#### Registry (`ml/registry/`)

- **models.py**: Model configurations and metadata
- **datasets.py**: Dataset configurations and metadata

#### Services (`ml/services/`)

- **domain_detector.py**: Auto-domain detection (interface only)
- **model_router.py**: Model routing logic (interface only)
- **postprocessor.py**: Output postprocessing (interface only)

#### Runtime (`ml/runtime/`)

- **loader.py**: Lazy model loading
- **predictor.py**: Inference execution

### Design Principles

- **Phase 0**: Interfaces only, no heavy computation
- **Lazy Loading**: Models loaded on-demand only
- **Domain-Driven**: Clear separation by detection domain
- **Production-Ready**: Error handling and logging built-in

### Detection Domains

- **Human**: Face detection, body recognition
- **Animal**: Species classification, behavior analysis
- **Plant**: Leaf identification, fruit classification
- **Medical**: MRI analysis, X-ray interpretation

### Versioning

Current version: **2.1.1-beta**

Follows semantic versioning with patch resets at 9:

- `2.1.1-beta` → `2.1.2-beta` (patch increment)
- `2.1.9-beta` → `2.2.0-beta` (minor increment)
- `2.9.9-beta` → `3.0.0-beta` (major increment)

### Next Phases

- **Phase 1**: Model loading and basic inference
- **Phase 2**: Domain detection implementation
- **Phase 3**: Full pipeline integration
- **Phase 4**: Performance optimization
- **Phase 5**: Production deployment

---

*This ML system is designed for scalability, maintainability, and production reliability.*