# NeuroLens v3.0 — CI Rules & CODEOWNERS

This document defines:

1. **CI/CD rules** for `dev` and `main`
2. **Branch enforcement policies**
3. **GitHub Actions pipeline logic**
4. **CODEOWNERS** mappings for governance

Designed to align with:

- Global Rules
- Developer Rules
- Branch Strategy
- Multi‑Agent Model

---

## Part I — CI Rules

### CI Philosophy

- `dev` = integration validation
- `main` = production certification
- No trust-based merges
- No manual bypass
- No human-only validation

Everything is **pipeline‑validated**.

---

## CI Scope Matrix

| Branch  | Purpose                | CI Level   |
|---------|------------------------|------------|
| `3.0/*` | Feature/agent branches | Basic CI   |
| `dev`   | Integration branch     | Full CI    |
| `main`  | Production             | Release CI |

---

## CI PIPELINES

### Pipeline A — Feature CI (3.0/* branches)

**Trigger:**

```yaml
on:
  pull_request:
    branches:
      - dev
```

**Stages:**

1. Lint
2. Type check
3. Unit tests
4. Static analysis
5. Security scan

**Rules:**

- Must pass before merge → `dev`
- No artifact deployment
- No container push

---

### Pipeline B — Dev CI (dev branch)

**Trigger:**

```yaml
on:
  push:
    branches:
      - dev
  pull_request:
    branches:
      - dev
```

**Stages:**

1. Lint
2. Type check
3. Unit tests
4. Integration tests
5. ML pipeline validation
6. API contract tests
7. Build containers
8. Dependency scan
9. SBOM generation

**Rules:**

- Must pass for any merge
- Artifacts built
- Containers built (not deployed)
- Model validation only (no prod deploy)

---

### Pipeline C — Main CI (main branch)

**Trigger:**

```yaml
on:
  push:
    branches:
      - main
```

**Stages:**

1. Full test suite
2. Regression tests
3. Integration tests
4. E2E tests
5. Security audit
6. Compliance scan
7. Model validation
8. Model signature verification
9. Container signing
10. Release packaging
11. Deployment staging
12. Production gate

**Rules:**

- Production deploy allowed
- Version tagging mandatory
- Rollback package generated
- Release artifact stored

---

## Branch Enforcement Rules

### dev branch

- ❌ No direct commits
- ✅ PR only
- ✅ CI mandatory
- ✅ 1 approval minimum
- ✅ All checks required
- ❌ Force push disabled

### main branch

- ❌ No direct commits
- ❌ No PR from feature branches
- ✅ Only PR from `dev`
- ✅ Full CI mandatory
- ✅ Release pipeline mandatory
- ✅ 2 approvals minimum
- ❌ Force push
- ❌ Admin bypass

---

## Merge Policy

```text
3.0/*  → dev  → main
```

Direct merges forbidden:

- 3.0/* → main ❌
- dev → 3.0/* ❌

---

## Deployment Gates

### dev

- Build only
- Test only
- Validate only
- No deployment

### main

- Deploy allowed
- Rollback mandatory
- Monitoring hook mandatory
- Audit log mandatory

---

## Part II — CODEOWNERS

> Path‑based governance + agent ownership

Create file: `.github/CODEOWNERS`

```text
# ===== Root Governance =====
*                           @platform-architect @release-manager

# ===== Core System =====
/config/                    @platform-architect
/envs/                      @environment-architect
/scripts/                   @mlops-engineer
/docs/                      @platform-architect

# ===== Backend =====
/src/api/                   @backend-engineer

# ===== Frontend =====
/src/frontend/              @frontend-architect

# ===== ML Core =====
/src/ml/core/               @ml-architect

# ===== Training =====
/src/ml/training/           @training-engineer

# ===== Inference =====
/src/ml/inference/          @inference-engineer

# ===== Data =====
/src/data/                  @data-engineer

# ===== MLOps =====
/mlops/                     @mlops-engineer

# ===== Monitoring =====
/monitoring/                @observability-engineer

# ===== Security =====
/security/                  @security-architect

# ===== Product =====
/product/                   @product-systems

# ===== CI/CD =====
/.github/workflows/         @mlops-engineer @release-manager

# ===== Infrastructure =====
/infra/                     @mlops-engineer

# ===== Research =====
/research/                  @research-lead

# ===== Release Control =====
/main/                      @release-manager
/dev/                       @platform-architect
```

---

## Ownership Enforcement Rules

### dev branch

- Required reviewers auto‑assigned via CODEOWNERS
- Domain owner approval mandatory
- CI must pass

### main branch

- Release Manager mandatory
- Platform Architect mandatory
- Security Architect mandatory
- Full pipeline pass mandatory

---

## Governance Model

| Layer   | Control         |
|---------|-----------------|
| Code    | CODEOWNERS      |
| Process | CI rules        |
| Trust   | Zero‑trust      |
| Deploy  | Pipeline only   |
| Release | Signed + tagged |

---

## Compliance Mode

This configuration enforces:

- Agent isolation
- Branch sovereignty
- Pipeline authority
- No human‑only trust
- No manual production changes
- Deterministic releases

---

## System Doctrine

**Branches are execution domains**  
**CI is law**  
**Pipelines are authority**  
**Main is sacred**  
**Dev is controlled chaos**  
**Agents are operators**  
**Humans are reviewers**
