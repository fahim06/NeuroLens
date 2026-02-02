# NeuroLens v3.0 — Developer Rules

> Guidelines for all developers and AI agents contributing to NeuroLens.

---

## 🛠️ Environment Setup

### Required Tools

| Tool       | Version / Notes                        |
|------------|----------------------------------------|
| conda      | Latest (Miniforge recommended for ARM) |
| Python     | Latest stable via conda (arm64)        |
| Git        | Latest                                 |
| TensorFlow | Metal-optimized for Apple Silicon      |

### Conda Environments

Developers must use the appropriate conda environment for their work:

| Environment     | Purpose                   |
|-----------------|---------------------------|
| `neurolens-dev` | General development       |
| `neurolens-ml`  | ML training and inference |
| `neurolens-api` | Backend API development   |

### Environment Activation

```bash
# Activate development environment
conda activate neurolens-dev

# Activate ML environment
conda activate neurolens-ml

# Activate API environment
conda activate neurolens-api
```

---

## 🌿 Git Workflow

### Branch Rules

1. **Never commit directly to `main`**
2. **Work on your assigned branch only**
3. **Keep branches up-to-date with upstream**
4. **Use meaningful commit messages**

### Commit Message Format

```text
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

**Types:**

- `feat` — New feature
- `fix` — Bug fix
- `docs` — Documentation
- `style` — Formatting, no code change
- `refactor` — Code restructuring
- `test` — Adding tests
- `chore` — Maintenance tasks

**Examples:**

```text
feat(api): add JWT authentication endpoint
fix(ml): resolve Metal GPU memory leak
docs(readme): update installation instructions
```

### Pull Request Rules

1. PRs must target the correct feature branch (not `main` directly for features)
2. PRs require at least one approval
3. All CI checks must pass
4. Squash commits when merging

---

## 📁 Code Organization

### Directory Structure

```text
NeuroLens/
├── src/                    # Source code
│   ├── api/                # FastAPI backend
│   ├── frontend/           # React frontend
│   ├── ml/                 # ML core, training, inference
│   ├── data/               # Data pipelines
│   └── utils/              # Shared utilities
├── tests/                  # Test suites
├── notebooks/              # Jupyter notebooks
├── assets/                 # Static assets, models
├── docs/                   # Documentation
├── config/                 # Configuration files
├── scripts/                # Automation scripts
└── envs/                   # Conda environment files
```

### Naming Conventions

| Element     | Convention       | Example           |
|-------------|------------------|-------------------|
| Files       | snake_case       | model_registry.py |
| Classes     | PascalCase       | ModelRegistry     |
| Functions   | snake_case       | get_model_by_id() |
| Constants   | UPPER_SNAKE_CASE | MAX_BATCH_SIZE    |
| Variables   | snake_case       | model_path        |
| Branches    | kebab-case       | backend-api       |
| Environment | kebab-case       | neurolens-dev     |

---

## 🧪 Testing Requirements

### Test Coverage

- All new code must include tests
- Minimum coverage: **80%**
- Critical paths: **100%**

### Test Types

| Type        | Location           | Command                   |
|-------------|--------------------|---------------------------|
| Unit        | tests/unit/        | pytest tests/unit/        |
| Integration | tests/integration/ | pytest tests/integration/ |
| E2E         | tests/e2e/         | pytest tests/e2e/         |

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_classifier.py
```

---

## 📝 Documentation Requirements

### Code Documentation

- All public functions must have docstrings
- Use Google-style docstrings
- Include type hints

**Example:**

```python
def classify_image(image_path: str, model_name: str = "default") -> dict:
    """Classify an image using the specified model.

    Args:
        image_path: Path to the image file.
        model_name: Name of the model to use for classification.

    Returns:
        Dictionary containing classification results with keys:
            - 'label': Predicted class label
            - 'confidence': Confidence score (0-1)

    Raises:
        FileNotFoundError: If image_path does not exist.
        ModelNotFoundError: If model_name is not registered.
    """
    ...
```

### README Requirements

Each module must have a `README.md` with:

- [ ] Purpose and overview
- [ ] Installation instructions
- [ ] Usage examples
- [ ] API reference (if applicable)
- [ ] Contributing guidelines

---

## 🔐 Security Rules

1. **Never commit secrets or credentials**
2. **Use environment variables for sensitive config**
3. **Keep dependencies updated**
4. **Report security issues privately**

### Secrets Management

```bash
# Use .env files (never commit these)
cp .env.example .env

# Load environment variables
source .env
```

### .gitignore Requirements

Ensure these are always ignored:

```text
.env
*.pem
*.key
secrets/
credentials/
```

---

## 🚀 Deployment Rules

1. **Only `main` branch deploys to production**
2. **All deployments require CI/CD pipeline success**
3. **Rollback plan must exist before deployment**
4. **Monitor after every deployment**

---

## ✅ Pre-Commit Checklist

Before committing:

- [ ] Code follows naming conventions
- [ ] All tests pass locally
- [ ] No linting errors
- [ ] Documentation updated
- [ ] No secrets in code
- [ ] Commit message follows format
- [ ] Branch is up-to-date with upstream

---

## 🤝 Collaboration Rules

1. **Communicate blockers early**
2. **Review PRs within 24 hours**
3. **Be constructive in code reviews**
4. **Document decisions in issues/PRs**
5. **Keep discussions focused and professional**
