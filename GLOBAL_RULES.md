# NeuroLens v3.0 — Global Rules

> Canonical rules governing the entire NeuroLens platform build.

---

## 🖥️ Environment

| Setting         | Value                                |
|-----------------|--------------------------------------|
| Package Manager | **conda** (base environment manager) |
| Python Version  | Latest stable (conda arm64)          |
| Hardware        | Apple M2 Pro (Apple Silicon)         |
| ML Backend      | TensorFlow with Metal                |
| Architecture    | ARM64                                |

---

## 🌳 Repository Strategy

| Rule                 | Description                                    |
|----------------------|------------------------------------------------|
| **Monorepo**         | Single repository for all services and modules |
| **Branch-per-role**  | Each AI agent role works on a dedicated branch |
| **Branch-per-phase** | Each build phase maps to a specific branch     |
| **Protected `main`** | No direct commits; merge only after validation |

---

## 🌿 Branch Naming Convention

```text
main                     → stable production
dev                      → active development branch
3.0/platform-core        → base architecture
3.0/backend-api          → FastAPI backend
3.0/frontend-react       → React frontend
3.0/ml-core              → ML pipelines
3.0/ml-training          → training system
3.0/ml-inference         → inference system
3.0/mlops                → MLOps + automation
3.0/data-pipeline        → datasets + features
3.0/infra                → Docker/CI/CD
3.0/monitoring           → logging/metrics
3.0/research             → experiments
3.0/security             → auth/compliance
3.0/product              → SaaS/product layer
```

---

## 🔒 Branch Protection Rules

1. **`main` branch is production-only**
    - No direct commits allowed
    - Merge only from tested feature branches
    - Requires passing CI/CD checks

2. **Feature branches require review**
    - Each agent's branch must pass validation before merge
    - Automated tests must pass

3. **No force-push on protected branches**

4. **`dev` branch is the primary integration branch**
    - All feature branches should be based off `dev` during active development
    - No direct commits allowed to `dev`; use PRs
    - Requires CI checks to pass before merge into `dev`
    - PRs into `dev` require at least one approval
    - `dev` may be fast-forwarded to `main` only after full validation and release readiness

---

## 🧠 Control Model

| Principle              | Description                                     |
|------------------------|-------------------------------------------------|
| Agent Isolation        | Each agent works in isolation on its own branch |
| Branch Ownership       | Each agent owns its designated branch           |
| Merge-on-Test          | Only tested branches merge to `main`            |
| Production = Main      | `main` branch is the sole production source     |
| No Direct Main Commits | All changes go through feature branches         |

---

## 🎯 Execution Strategy

Phases execute **sequentially**:

```text
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7 → Phase 8 → Phase 9 → Phase 10 → Phase 11 → Phase 12
```

Each phase must complete before the next begins.

---

## 🧭 Philosophy

> This is not coding. This is **system engineering**.
> This is not ML experimentation. This is **AI platform construction**.
> This is not a project. This is a **technology product foundation**.

---

## ✅ Compliance Checklist

Before merging any branch:

- [ ] All tasks for the phase are complete
- [ ] All deliverables are produced
- [ ] CI/CD passes
- [ ] Code review approved
- [ ] Documentation updated
- [ ] No regressions introduced
