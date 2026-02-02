# 🔐 NeuroLens Release Governance Policy

This document defines the release governance rules for NeuroLens. These rules are **mandatory** and apply to all contributors.

---

## 🌳 Branch Model

```
main → production-only (locked)
dev  → pre-production, stabilized
```

### Rules

| Branch | Purpose | Direct Push | Force Push |
|--------|---------|-------------|------------|
| `main` | Production releases only | ❌ Forbidden | ❌ Forbidden |
| `dev`  | Integration & pre-release | ✅ Allowed | ⚠️ With caution |

---

## 🔐 Branch Protection Rules

### `main` Branch

- ✅ Require pull request before merging
- ✅ Require CI status checks to pass
- ✅ Require manual approval (1 reviewer minimum)
- ✅ Require conversation resolution
- ❌ No direct pushes
- ❌ No force pushes
- ❌ No deletions

### `dev` Branch

- ✅ Require CI status checks to pass
- ✅ Allow direct pushes for maintainers
- ⚠️ Force push allowed with justification

---

## 🏷️ Versioning Policy

### Dev Releases

- **Format:** `vX.Y.Z-dev.N`
- **Example:** `v3.0.0-dev.1`
- **Purpose:** Testing, review, validation
- **Created from:** `dev` branch

### Production Releases

- **Format:** `vX.Y.Z`
- **Example:** `v3.0.0`
- **Purpose:** Stable production deployment
- **Created from:** `main` branch only

---

## 🚦 Release Gates (MANDATORY)

Before **any** `dev → main` merge:

| Gate | Requirement |
|------|-------------|
| CI Green | All checks passing for 72 hours |
| Issues | No open P0/P1 issues |
| Security | Security scan clean |
| Performance | Performance baseline met |
| Approval | Manual approval by owner |

---

## 🔄 Release Flow

```
dev
 └── QA + soak period (72 hours)
     └── release PR to main
         └── review + approval
             └── merge to main
                 └── tag release
                     └── deploy
```

**No shortcuts. No exceptions.**

---

## 🧯 Rollback Policy

Rollback procedures:

1. **Tag Rollback:** Deploy previous git tag
2. **Model Rollback:** Restore previous model registry version
3. **Artifact Rollback:** Redeploy previous container image

### Rollback Requirements

- Rollback must be tested **before** release
- Rollback documentation must exist
- Rollback time target: < 15 minutes

---

## 📜 Release Documentation Requirements

Each release **must** include:

| Document | Required |
|----------|----------|
| Release Notes | ✅ Yes |
| Breaking Changes | ✅ Yes (if any) |
| Upgrade Notes | ✅ Yes |
| Rollback Instructions | ✅ Yes |
| Known Issues | ✅ Yes |

---

## 🚫 Forbidden Actions

The following actions are **strictly forbidden**:

- ❌ Direct push to `main`
- ❌ Force push to `main`
- ❌ Tagging releases from `dev`
- ❌ Skipping CI checks
- ❌ Merging without approval
- ❌ Deleting `main` or `dev` branches

---

## ✅ Compliance Checklist

Before any release, verify:

- [ ] CI has been green for 72 hours
- [ ] No open P0/P1 issues
- [ ] Security scan completed and clean
- [ ] Release notes written
- [ ] Rollback tested
- [ ] Owner approval obtained

---

## 📋 Release Authority

| Role | Authority |
|------|-----------|
| Owner | Approve production releases |
| Maintainer | Create dev releases |
| Contributor | Submit PRs only |

---

## 🔄 Policy Updates

This policy may only be updated via:

1. PR to `dev` with justification
2. Review period of 7 days
3. Owner approval
4. Merge to `main`

---

*Last updated: February 2, 2026*
*Version: 1.0.0*
