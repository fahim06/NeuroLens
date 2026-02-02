# NeuroLens — Release Checklist

This document outlines the release process for NeuroLens deployments.

## 🌿 Branch Strategy

| Branch | Environment | Deployment | Approval |
|--------|-------------|------------|----------|
| `django-rebuild` | Beta | Automatic | None |
| `dev` | Staging | Automatic | CI Pass |
| `main` | Production | Manual | 2 Reviews + CI + Security |

---

## 📋 Pre-Release Checklist

### Code Quality
- [ ] All CI checks pass (Backend CI, Frontend CI)
- [ ] No critical security vulnerabilities
- [ ] Code review completed
- [ ] TypeScript compiles without errors
- [ ] Python linting passes (ruff, black, isort)

### Testing
- [ ] Unit tests pass with >80% coverage
- [ ] Integration tests pass
- [ ] E2E tests pass (if applicable)
- [ ] Manual QA on staging complete

### Documentation
- [ ] CHANGELOG.md updated
- [ ] API documentation current
- [ ] README updated if needed
- [ ] Migration notes documented

### Dependencies
- [ ] No known vulnerable dependencies
- [ ] Package versions locked
- [ ] License compliance verified

---

## 🚀 Deployment Process

### Beta (django-rebuild → beta)

1. **Merge to django-rebuild**
   ```bash
   git checkout django-rebuild
   git merge feature/my-feature
   git push origin django-rebuild
   ```

2. **Automatic Deployment**
   - CI runs automatically
   - Docker images built with `beta-` prefix
   - Deployed to beta environment

3. **Verify**
   - Check https://beta.neurolens.example.com
   - Review logs in Grafana

### Staging (dev → staging)

1. **Create PR to dev**
   ```bash
   git checkout dev
   git merge django-rebuild
   # or
   gh pr create --base dev --head django-rebuild
   ```

2. **Review Requirements**
   - 1 approving review
   - Backend CI Status ✅
   - Frontend CI Status ✅

3. **Merge and Deploy**
   - Merge PR
   - Automatic deployment triggers
   - Blue-Green deployment executed

4. **Verify Staging**
   - Check https://staging.neurolens.example.com
   - Run smoke tests
   - Verify migrations applied

### Production (main → production)

1. **Create PR to main**
   ```bash
   gh pr create --base main --head dev --title "Release v1.X.0"
   ```

2. **Review Requirements**
   - 2 approving reviews
   - Backend CI Status ✅
   - Frontend CI Status ✅
   - Security Status ✅
   - CodeQL Analysis ✅

3. **Manual Approval**
   - Approve in GitHub Actions
   - Verify deployment plan

4. **Deployment**
   - Blue-Green deployment
   - 10% canary traffic
   - Full traffic switch
   - Git tag created automatically

5. **Post-Deployment**
   - Verify production health
   - Monitor error rates
   - Update status page

---

## 🔙 Rollback Procedure

### Automatic Rollback (on failure)
The deployment workflow automatically keeps the previous version active if deployment fails.

### Manual Rollback

1. **Via GitHub Actions**
   - Go to Actions > Deploy Production
   - Click "Run workflow"
   - Check "Rollback to previous version"
   - Confirm

2. **Via kubectl**
   ```bash
   # Switch service to previous slot
   kubectl patch svc neurolens-active -n production \
     -p '{"spec":{"selector":{"slot":"blue"}}}'  # or "green"
   ```

3. **Via Rollback Script**
   ```bash
   ./infra/scripts/rollback.sh production
   ```

---

## 📊 Monitoring

### Health Checks
- `/api/health/` - Overall health
- `/api/health/db/` - Database connectivity
- `/api/health/redis/` - Redis connectivity

### Dashboards
- Grafana: https://grafana.neurolens.example.com
- Prometheus: https://prometheus.neurolens.example.com

### Alerts
- Slack: #neurolens-alerts
- PagerDuty: On-call rotation

---

## 🚫 Forbidden Actions

| Action | Reason |
|--------|--------|
| Direct push to `main` | Bypasses review and CI |
| Skip CI (`[skip ci]`) | Security risk |
| Force push to `main`/`dev` | History corruption |
| Hotfix without PR | Audit trail required |
| Deploy without tests | Quality gate bypass |

---

## 📝 Release Notes Template

```markdown
## v1.X.0 - YYYY-MM-DD

### 🎉 New Features
- Feature description (#PR)

### 🐛 Bug Fixes
- Bug fix description (#PR)

### 🔧 Improvements
- Improvement description (#PR)

### 🔒 Security
- Security fix description (#PR)

### 📦 Dependencies
- Updated package@version

### ⚠️ Breaking Changes
- Breaking change description

### 🔄 Migration Notes
- Required migration steps
```

---

## 🆘 Emergency Procedures

### Production Down
1. Check health endpoints
2. Review recent deployments
3. Rollback if recent deploy
4. Check infrastructure status
5. Escalate to on-call

### Security Incident
1. Rotate affected secrets
2. Block suspicious IPs
3. Review access logs
4. Notify security team
5. Document incident

---

## ✅ Release Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Dev Lead | | | |
| QA | | | |
| Security | | | |
| Product | | | |
