# Phase 8 — MLOps & Automation
**NeuroLens v3.0 Platform Build**  
**Phase Type:** CI/CD, Model Ops, Automation  
**Git Branch:** `mlops`  
**Conda Environments:** `neurolens-dev` + `neurolens-ml`

This phase turns NeuroLens into a **self-maintaining ML system**. Focus is on CI/CD, automated validation, retraining triggers, and safe deployments.

---

# 🎯 Phase 8 Objectives

1. CI/CD for backend, frontend, and ML
2. Model CI (train → validate → register)
3. Automated retraining triggers
4. Model validation gates
5. Artifact management
6. Experiment lineage (code + data + model)
7. Canary / blue-green deployment readiness
8. Rollback strategy

---

# 🧪 Environment & Branch (MANDATORY)

```bash
conda activate neurolens-dev
git checkout -b mlops
# Use neurolens-ml for training jobs invoked by CI
```

---

# 🧰 Tooling Stack

- GitHub Actions
- Docker / Docker Compose
- MLflow (tracking + registry)
- DVC (data artifacts)
- pytest (validation)
- pre-commit (quality gates)

---

# 📁 MLOps Directory Structure

```
infra/
├── ci/
│   ├── backend.yml
│   ├── frontend.yml
│   └── ml.yml
├── docker/
│   ├── backend.Dockerfile
│   ├── inference.Dockerfile
│   └── training.Dockerfile
├── compose/
│   └── dev.yml
└── scripts/
    ├── train_and_validate.sh
    ├── register_model.sh
    └── rollback.sh
```

---

# 🔁 CI/CD Pipelines

## Code CI
Triggers:
- Pull requests
- Push to feature branches

Checks:
- Linting
- Type checks
- Unit tests
- Security scan

---

## Model CI

Flow:
```
Data Change / Schedule → Train → Evaluate → Validate → Register
```

Validation Gates:
- Accuracy threshold
- Calibration threshold
- No regression vs baseline
- Reproducibility check

---

# 🧠 Retraining Triggers

- New dataset version
- Drift detected (offline)
- Scheduled retraining
- Manual trigger

---

# 🧪 Model Validation

Automated checks:
- Metric thresholds
- Schema compatibility
- Inference sanity tests
- Latency budget

---

# 🚦 Deployment Strategy (Prep)

- Versioned models
- Canary releases
- Shadow traffic (future)
- Rollback on failure

---

# 🔐 Secrets & Credentials

- GitHub Secrets
- Environment-based injection
- No secrets in repo

---

# 📏 Coding Standards

- Scripts idempotent
- Clear logs
- Fail fast on errors

---

# ✅ Phase 8 Completion Criteria

- CI pipelines run successfully
- Model CI validates and registers models
- Retraining can be triggered
- Artifacts tracked
- Rollback script tested

---

# 🧠 Phase 8 AI Role

**Role:** MLOps Engineer Agent  
**Branch:** mlops  
**Conda Envs:** neurolens-dev (CI/control) + neurolens-ml (training)

---

# ▶️ Next Phase

After completion:

→ Phase 9: Product Layer
→ Branch: `product`
→ Conda Env: `neurolens-api`
→ Agent: Product Systems Agent

