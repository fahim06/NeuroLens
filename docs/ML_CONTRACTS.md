# ML System Contracts

## Overview

This document defines the explicit contracts between the API layer and ML subsystem.
These contracts enforce boundaries and ensure clean separation of concerns.

## Core Principles

1. **No UI logic in ML**: ML components are pure computation
2. **No API logic in ML**: No HTTP/routing knowledge
3. **No file-system coupling**: Use abstractions for I/O
4. **Explicit contracts**: Typed interfaces for all boundaries
5. **Deterministic pipelines**: Same input → same output

## Model Contract

All models must implement the `BaseModel` interface:

```python
class BaseModel(ABC):
    @property
    def name(self) -> str: ...
    
    @property
    def version(self) -> str: ...
    
    @property
    def input_shape(self) -> tuple[int, ...]: ...
    
    @property
    def output_classes(self) -> list[str]: ...
    
    def predict(self, images: NDArray) -> NDArray: ...
    
    def load(self, path: Path) -> None: ...
    
    def save(self, path: Path) -> None: ...
```

## Preprocessor Contract

```python
class Preprocessor(Protocol):
    def __call__(self, image: NDArray) -> NDArray: ...
```

## Trainer Contract

```python
class BaseTrainer(ABC):
    def train(
        self,
        train_data: Any,
        val_data: Any | None = None,
        config: dict | None = None,
    ) -> dict[str, float]: ...
    
    def evaluate(self, test_data: Any) -> dict[str, float]: ...
```

## Explainer Contract

```python
class BaseExplainer(ABC):
    def explain(
        self,
        model: BaseModel,
        image: NDArray,
        target_class: int | None = None,
    ) -> dict[str, Any]: ...
```

## Data Flow Contracts

### Inference Request

```python
@dataclass
class InferenceInput:
    image: bytes          # Raw image data
    model_id: str | None  # Optional model version
    options: dict         # Additional options
```

### Inference Response

```python
@dataclass
class InferenceOutput:
    predictions: list[Prediction]
    processing_time_ms: float
    model_id: str
    features: dict | None
    explainability: dict | None
```

### Training Configuration

```python
@dataclass
class TrainingConfig:
    dataset_id: str
    hyperparameters: HyperParameters
    validation_split: float
    experiment_name: str | None
```

## Versioning Contracts

### Model Versioning

- Format: `{major}.{minor}.{patch}` (semantic versioning)
- Example: `1.2.3`
- Major: Breaking changes in input/output
- Minor: New features, backward compatible
- Patch: Bug fixes only

### Dataset Versioning

- Format: `{hash}` (content hash)
- Example: `abc123def456`
- Any data change = new version

### Feature Schema Versioning

- Format: `v{number}`
- Example: `v1`, `v2`
- Schema changes require version bump

## Metrics Contract

Standard metrics returned by evaluation:

```python
class StandardMetrics(TypedDict):
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_roc: float | None
    confusion_matrix: list[list[int]]
```
