# NeuroLens — CI/CD Documentation

## Overview

NeuroLens uses GitHub Actions for Continuous Integration and Continuous Deployment with a branch-based workflow strategy.

## Workflow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CI/CD Pipeline                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   django-rebuild ──► Backend CI ──► Frontend CI ──► Deploy Beta     │
│        │                  │              │              │            │
│        ▼                  ▼              ▼              ▼            │
│   ┌─────────┐      ┌──────────┐   ┌──────────┐   ┌──────────┐       │
│   │  Code   │      │  Lint    │   │  Lint    │   │  Docker  │       │
│   │  Push   │  ──► │  Tests   │   │  Build   │   │  Build   │       │
│   │         │      │  Build   │   │  Check   │   │  Deploy  │       │
│   └─────────┘      └──────────┘   └──────────┘   └──────────┘       │
│                                                                      │
│   dev ──────────► Backend CI ──► Frontend CI ──► Security ──►       │
│        │              │              │              │                │
│        │              ▼              ▼              ▼                │
│        │         [Required]    [Required]    [Recommended]          │
│        │                                                             │
│        └──────────────────────────────────────► Deploy Staging      │
│                                                      │               │
│                                              ┌───────┴───────┐      │
│                                              │  Blue-Green   │      │
│                                              │  Deployment   │      │
│                                              └───────────────┘      │
│                                                                      │
│   main ─────────► Backend CI ──► Frontend CI ──► Security ──►       │
│        │              │              │              │                │
│        │              ▼              ▼              ▼                │
│        │         [Required]    [Required]    [Required]             │
│        │                                                             │
│        └──────────────────────────────────► Approval Gate ──►       │
│                                                   │                  │
│                                              ┌────┴────┐            │
│                                              │ Manual  │            │
│                                              │ Review  │            │
│                                              └────┬────┘            │
│                                                   │                  │
│                                              Deploy Production       │
│                                              (Blue-Green + Canary)   │
└─────────────────────────────────────────────────────────────────────┘
```

## Workflows

### CI Workflows

| Workflow | File | Purpose |
|----------|------|---------|
| Backend CI | `backend-ci.yml` | Django checks, linting, tests, build |
| Frontend CI | `frontend-ci.yml` | TypeScript check, linting, Vite build |
| Security Scan | `security-scan.yml` | Dependency audit, secret scan, CodeQL |

### CD Workflows

| Workflow | File | Trigger | Environment |
|----------|------|---------|-------------|
| Deploy Beta | `deploy-beta.yml` | Push to `django-rebuild` | beta |
| Deploy Staging | `deploy-staging.yml` | Push to `dev` | staging |
| Deploy Production | `deploy-production.yml` | Push to `main` | production |

## Branch Matrix

| Branch | CI Strictness | Deployment | Approval |
|--------|--------------|------------|----------|
| `django-rebuild` | Warnings allowed | Auto → Beta | None |
| `dev` | Must pass | Auto → Staging | CI gates |
| `main` | Must pass + Security | Manual → Production | 2 reviews |

## Environment Configuration

### Required Secrets

```yaml
# Kubernetes access
KUBE_CONFIG_BETA: base64-encoded kubeconfig
KUBE_CONFIG_STAGING: base64-encoded kubeconfig  
KUBE_CONFIG_PRODUCTION: base64-encoded kubeconfig

# URLs for health checks
BETA_URL: https://beta.neurolens.example.com
STAGING_URL: https://staging.neurolens.example.com
PRODUCTION_URL: https://neurolens.example.com
```

### GitHub Environments

Create these environments in Settings → Environments:

1. **beta**
   - No protection rules
   - Deploy from: `django-rebuild`

2. **staging**
   - Required reviewers: 0
   - Wait timer: 0
   - Deploy from: `dev`

3. **production-approval**
   - Required reviewers: 2
   - Wait timer: 5 minutes
   - Deploy from: `main`

4. **production**
   - Required reviewers: 0 (approval handled by production-approval)
   - Deploy from: `main`

## Deployment Strategy

### Blue-Green Deployment

```
┌─────────────────────────────────────────────────────────────┐
│                     Load Balancer                            │
│                          │                                   │
│              ┌───────────┴───────────┐                      │
│              ▼                       ▼                       │
│       ┌─────────────┐         ┌─────────────┐               │
│       │    BLUE     │         │   GREEN     │               │
│       │   (v1.0)    │         │   (v1.1)    │               │
│       │   Active    │         │   Standby   │               │
│       └─────────────┘         └─────────────┘               │
│                                                              │
│  1. Deploy new version to inactive slot (Green)             │
│  2. Run health checks on Green                              │
│  3. Switch traffic to Green (becomes Active)                │
│  4. Blue becomes Standby (ready for rollback)               │
└─────────────────────────────────────────────────────────────┘
```

### Canary Deployment (Production)

Production deployments use canary releases:
1. Deploy to inactive slot
2. Route 10% traffic to new version
3. Monitor for 1 minute
4. If healthy, route 100% traffic
5. If errors, automatic rollback

## CI Job Details

### Backend CI Jobs

```yaml
setup:        # Prepare environment
lint:         # ruff, black, isort
django-checks: # manage.py check, migrations
tests:        # pytest with Redis service
build:        # python -m build
```

### Frontend CI Jobs

```yaml
setup:        # npm ci with caching
lint:         # ESLint, Prettier
typecheck:    # tsc --noEmit
build:        # vite build
```

### Security Jobs

```yaml
dependency-scan:  # safety, pip-audit, npm audit
secret-scan:      # gitleaks
license-check:    # pip-licenses, license-checker
codeql:           # GitHub CodeQL for Python/JS
```

## Troubleshooting

### CI Failures

**Backend CI fails on lint:**
```bash
# Fix locally
ruff check . --fix
black .
isort .
```

**Frontend CI fails on typecheck:**
```bash
cd frontend
npx tsc --noEmit
# Fix type errors shown
```

### Deployment Failures

**Check deployment status:**
```bash
kubectl get deployments -n <environment>
kubectl get pods -n <environment>
kubectl logs -l app=neurolens-backend -n <environment>
```

**Manual rollback:**
```bash
kubectl rollout undo deployment/neurolens-backend -n <environment>
```

## Adding New Workflows

1. Create workflow file in `.github/workflows/`
2. Use consistent naming: `<type>-<purpose>.yml`
3. Include concurrency groups to prevent duplicate runs
4. Add status checks to branch protection
5. Document in this file

## Monitoring

- **GitHub Actions:** https://github.com/NeuroLens/NeuroLens/actions
- **Grafana Dashboard:** See [grafana.json](../infra/dashboards/grafana.json)
- **Alerts:** See [slo_rules.yml](../infra/alerts/slo_rules.yml)
