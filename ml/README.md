# ML Core Architecture

NeuroLens v3.0 Machine Learning Module

## Overview

This module contains the core ML architecture for NeuroLens. It follows framework-agnostic design principles with strict
separation between training and inference.

## Directory Structure

```
ml/
├── core/
│   ├── interfaces/      # Abstract contracts for all ML components
│   ├── schemas/         # I/O schemas and validation
│   ├── registry/        # Model registry and versioning
│   └── utils/           # Reproducibility and helper utilities
├── pipelines/           # Training and inference pipelines
├── models/              # Model implementations
├── datasets/            # Dataset handling and versioning
└── experiments/         # Experiment tracking
```

## Architecture Principles

1. **Framework Agnostic**: Interfaces are framework-independent
2. **Training ≠ Inference**: Strict separation of concerns
3. **Deterministic Pipelines**: Reproducible data transformations
4. **Explicit I/O Schemas**: Clear input/output contracts
5. **Pluggable Models**: Easy to swap model architectures

## Pipeline Flow

### Training Pipeline

```
Raw Data → Validation → Preprocess → Train → Evaluate → Register
```

### Inference Pipeline

```
Input → Preprocess (frozen) → Predict → Postprocess
```

## Usage

```python
from ml.core.interfaces import BaseModel, BasePreprocessor
from ml.core.registry import ModelRegistry
from ml.pipelines import InferencePipeline
```

## Reproducibility

- Fixed random seeds via `ml.core.utils.reproducibility`
- Hash-based dataset versioning
- Config snapshot per training run
