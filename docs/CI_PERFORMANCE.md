# ⚡ NeuroLens CI Performance Policy

This document defines CI performance standards and optimization strategies for NeuroLens.

---

## 🎯 Goals

- Reduce CI runtime
- Reduce redundant work
- Fail fast on errors
- Keep CI readable and maintainable
- Ensure Apple Silicon compatibility awareness

---

## 🧠 CI Optimization Principles

1. **One workflow, multiple jobs** — Single `ci.yml` file
2. **Parallelize by responsibility** — Backend / ML / Frontend / Tests
3. **Cache aggressively, invalidate carefully** — Conda & Node caching
4. **Fail early, test deeply later** — Syntax checks on dev, full tests on release
5. **Never rebuild what didn't change** — Path-based filtering

---

## 🧩 Job Responsibilities

| Job | Purpose | Runs When | Failure Impact |
|-----|---------|-----------|----------------|
| `changes` | Detect file changes | Always | N/A |
| `backend` | API syntax + imports | `backend/**` changed | Blocks merge |
| `ml` | ML code validation | `ml/**` changed | Blocks merge |
| `frontend` | UI build sanity | `frontend/**` changed | Blocks merge |
| `tests` | Test suite | `tests/**` or code changed | Blocks merge |
| `ci-status` | Aggregate status | Always | Required check |

---

## ⚡ File-Change Detection

Jobs only run if relevant files changed:

```yaml
# Uses dorny/paths-filter@v3
filters: |
  backend:
    - 'backend/**'
    - 'envs/neurolens-api.yml'
  ml:
    - 'ml/**'
    - 'envs/neurolens-ml.yml'
  frontend:
    - 'frontend/**'
  tests:
    - 'tests/**'
    - 'backend/**'
    - 'ml/**'
```

---

## 🗃️ Caching Strategy

### Conda Cache

- **Path:** `~/conda_pkgs_dir`
- **Key:** `conda-{env}-{os}-{hash(envs/*.yml)}`
- **Benefit:** ~60% faster environment setup

### Node Cache

- **Path:** `frontend/node_modules`
- **Key:** `node-{os}-{hash(package-lock.json)}`
- **Benefit:** ~80% faster npm install

---

## 🧪 Test Depth Strategy

### On `dev` branch (fast feedback)

- ✅ Syntax checks (`compileall`)
- ✅ Import validation
- ✅ Build checks
- ✅ Fast test suite (`-x --tb=short`)

### On production release (thorough)

- ✅ Full test suite
- ✅ Integration tests
- ✅ Load tests
- ✅ Security scans

---

## ⏱️ Performance Targets

| Job | Target Time |
|-----|-------------|
| Changes | < 10s |
| Backend | < 2 min |
| ML | < 3 min |
| Frontend | < 2 min |
| Tests | < 3 min |
| **Total** | **< 6 min** |

---

## 🔄 Concurrency Control

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

- Cancels in-progress runs when new commits are pushed
- Saves CI minutes on rapid iteration
- Prevents queue buildup

---

## 🚫 CI Anti-Patterns (Forbidden)

| Anti-Pattern | Why It's Bad |
|--------------|--------------|
| Multiple workflows doing same thing | Wastes resources |
| Installing full ML deps on frontend job | Slow, unnecessary |
| Running training in CI | Too slow, expensive |
| Hardcoding secrets | Security risk |
| CI-only logic divergence | Hard to debug locally |
| Not caching dependencies | Slow builds |
| Running all tests on every push | Wastes time |

---

## 🖥️ Apple Silicon Notes

For local development on Apple Silicon:

- CI runs on `ubuntu-latest` (x86_64)
- Some packages may behave differently
- Test locally with Rosetta if needed
- ML models should be architecture-agnostic

---

## 📊 Monitoring CI Performance

Track these metrics:

- Average CI duration
- Cache hit rate
- Job skip rate
- Failure rate by job

---

## ✅ Compliance Checklist

- [x] Single workflow file (`ci.yml`)
- [x] Path-based job filtering
- [x] Dependency caching enabled
- [x] Concurrency control enabled
- [x] Fast-fail testing (`-x`)
- [x] CI status aggregation job

---

*Last updated: February 2, 2026*
*Version: 1.0.0*
