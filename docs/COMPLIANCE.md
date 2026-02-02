# NeuroLens Security & Compliance Documentation

**Version:** 3.0.0  
**Last Updated:** 2024  
**Classification:** Internal / Confidential  

---

## Table of Contents

1. [Security Overview](#security-overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [API Security](#api-security)
4. [Data Protection](#data-protection)
5. [Secrets Management](#secrets-management)
6. [Audit Logging](#audit-logging)
7. [Incident Response](#incident-response)
8. [Compliance Frameworks](#compliance-frameworks)
9. [Security Checklist](#security-checklist)

---

## Security Overview

### Security Principles

NeuroLens follows **Defense in Depth** with multiple layers of security:

```
┌─────────────────────────────────────────────────────────────┐
│                    Network Layer                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Application Layer                        │    │
│  │  ┌─────────────────────────────────────────────┐    │    │
│  │  │            API Security Layer                 │    │    │
│  │  │  ┌───────────────────────────────────┐      │    │    │
│  │  │  │     Authentication Layer           │      │    │    │
│  │  │  │  ┌──────────────────────────┐    │      │    │    │
│  │  │  │  │    Data Protection       │    │      │    │    │
│  │  │  │  └──────────────────────────┘    │      │    │    │
│  │  │  └───────────────────────────────────┘      │    │    │
│  │  └─────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Core Security Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `security_hardened.py` | `backend/app/core/` | Password hashing, JWT, token management |
| `permissions.py` | `backend/app/core/` | RBAC, role-based access control |
| `api_security.py` | `backend/app/core/` | OWASP middleware, input validation |
| `rate_limit.py` | `backend/app/core/` | Rate limiting, abuse prevention |
| `audit.py` | `backend/app/core/` | Audit logging, compliance trail |
| `secrets.py` | `backend/app/core/` | Secrets management, scanning |
| `data_protection.py` | `backend/app/core/` | Encryption, PII handling |

---

## Authentication & Authorization

### Password Security

**Algorithm:** PBKDF2-SHA256 with 100,000 iterations

```python
# Password requirements enforced by validate_password_strength()
- Minimum length: 12 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit
- At least 1 special character
- Not in common password list
- No password reuse (last 5 passwords)
```

### JWT Token Security

| Token Type | TTL | Refresh | JTI | Revocable |
|------------|-----|---------|-----|-----------|
| Access Token | 15 minutes | No | Yes | Yes |
| Refresh Token | 7 days | Yes | Yes | Yes |

**Token Claims:**

```json
{
  "sub": "user_id",
  "exp": "expiration_timestamp",
  "iat": "issued_at_timestamp",
  "jti": "unique_token_id",
  "type": "access|refresh",
  "role": "user_role"
}
```

**Token Revocation:**
- Tokens can be revoked via JTI blacklist
- Revocation checked on every authenticated request
- Blacklist supports automatic expiration cleanup

### Multi-Factor Authentication (MFA)

Supported methods:
- TOTP (Time-based One-Time Password)
- Email OTP
- Recovery codes

### Session Management

- Sessions tied to device fingerprint
- Concurrent session limits configurable
- Session invalidation on password change
- Automatic logout after inactivity (30 minutes)

---

## API Security

### OWASP Top 10 Mitigations

| OWASP Category | Mitigation |
|----------------|------------|
| A01 Broken Access Control | RBAC, permission decorators, resource ownership checks |
| A02 Cryptographic Failures | AES-256-GCM encryption, TLS 1.3, secure key storage |
| A03 Injection | Input validation, parameterized queries, output encoding |
| A04 Insecure Design | Security requirements in design, threat modeling |
| A05 Security Misconfiguration | Secure defaults, hardened configurations |
| A06 Vulnerable Components | Dependency scanning, automatic updates |
| A07 Auth Failures | MFA, rate limiting, secure session management |
| A08 Software/Data Integrity | Signed deployments, integrity checks |
| A09 Logging Failures | Comprehensive audit logging, tamper detection |
| A10 SSRF | URL validation, network segmentation |

### Rate Limiting

```python
# Rate limit configurations
AUTH_LOGIN:        5 requests / 60 seconds (per IP)
AUTH_REGISTER:     3 requests / 60 seconds (per IP)
API_STANDARD:      100 requests / 60 seconds (per user)
INFERENCE_SINGLE:  10 requests / 60 seconds (per user)
INFERENCE_BATCH:   2 requests / 60 seconds (per user)
```

**Account Lockout:**
- 5 failed login attempts → 15 minute lockout
- Progressive lockout for repeated failures
- Unlock via email verification

### Security Headers

All API responses include:

```http
Content-Security-Policy: default-src 'self'; ...
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

### Input Validation

All inputs are validated for:
- SQL injection patterns
- XSS payloads
- Path traversal attempts
- Command injection
- Maximum length limits
- Content type verification

---

## Data Protection

### Encryption at Rest

| Data Type | Encryption | Key Management |
|-----------|------------|----------------|
| User passwords | PBKDF2-SHA256 (hashed) | N/A (one-way) |
| API keys | SHA256 (hashed) | N/A (one-way) |
| Medical images | AES-256-GCM | AWS KMS / HashiCorp Vault |
| User PII | AES-256-GCM | Application encryption key |
| Database | TDE (Transparent Data Encryption) | Database provider |

### Encryption in Transit

- TLS 1.3 required for all connections
- Certificate pinning for mobile clients
- Perfect Forward Secrecy (PFS) enabled
- Strong cipher suites only

### PII Handling

**PII Types Detected:**
- Email addresses
- Phone numbers
- SSN (Social Security Numbers)
- Credit card numbers
- IP addresses
- Names, addresses, dates of birth

**PII Operations:**
```python
# Detection
PIIDetector.detect(text) → [(type, value, position), ...]

# Redaction
PIIDetector.redact(text) → "[REDACTED]"

# Masking
PIIDetector.mask(text) → "j***e@example.com"
```

### Data Retention

| Data Type | Retention Period | Deletion Method |
|-----------|------------------|-----------------|
| Audit logs | 7 years | Secure archive → delete |
| User data | Account lifetime + 30 days | Hard delete |
| Medical images | Per regulation (HIPAA) | Secure deletion |
| Session data | 30 days | Automatic purge |
| Temp files | 24 hours | Automatic purge |

---

## Secrets Management

### Environment Variables

Required secrets (must be set):
```bash
SECRET_KEY          # JWT signing key (min 32 chars)
DATABASE_URL        # Database connection string
```

Optional secrets:
```bash
ENCRYPTION_KEY      # Data encryption key (base64, 32 bytes)
SENTRY_DSN          # Error tracking
REDIS_URL           # Cache/session store
AWS_ACCESS_KEY_ID   # Cloud storage
AWS_SECRET_ACCESS_KEY
```

### Secret Rotation

| Secret Type | Rotation Frequency | Procedure |
|-------------|-------------------|-----------|
| JWT Secret | 90 days | Blue-green deployment |
| API Keys | On demand | User-initiated |
| Database password | 90 days | Coordinated rotation |
| Encryption keys | Annually | Key versioning |

### Secrets Scanning

CI/CD pipelines include secrets scanning for:
- Hardcoded passwords
- API keys
- Private keys
- JWT tokens
- AWS credentials
- Generic secrets patterns

---

## Audit Logging

### Logged Events

**Authentication Events:**
- Login success/failure
- Logout
- Token refresh
- MFA events
- Password changes

**Authorization Events:**
- Permission granted/denied
- Role changes
- Resource access

**Data Events:**
- Create, read, update, delete operations
- Data exports
- Bulk operations

**Security Events:**
- Rate limiting triggered
- Suspicious activity
- Security configuration changes

### Audit Log Format

```json
{
  "id": "uuid",
  "timestamp": "2024-01-15T10:30:00Z",
  "event_type": "AUTH_LOGIN_SUCCESS",
  "severity": "INFO",
  "actor_id": "user_123",
  "actor_type": "user",
  "resource_type": "session",
  "resource_id": "session_456",
  "action": "create",
  "ip_address": "10.0.***.***",
  "user_agent": "Mozilla/5.0...",
  "details": {...},
  "hash": "sha256_hash",
  "previous_hash": "chain_link"
}
```

### Tamper Detection

Audit logs use hash chaining for tamper detection:
```python
hash = SHA256(previous_hash + event_data)
```

Integrity verification:
```python
audit_logger.verify_chain_integrity() → bool
```

---

## Incident Response

### Incident Severity Levels

| Level | Description | Response Time | Examples |
|-------|-------------|---------------|----------|
| P1 Critical | Active breach, data exposure | 15 minutes | Credential leak, unauthorized access |
| P2 High | Potential breach, vulnerability | 1 hour | Failed exploit, suspicious activity |
| P3 Medium | Security concern | 4 hours | Policy violation, misconfiguration |
| P4 Low | Minor issue | 24 hours | Failed logins, scan activity |

### Response Procedures

**1. Detection & Triage**
- Monitor alerts from observability stack
- Assess scope and severity
- Assign incident commander

**2. Containment**
- Isolate affected systems
- Revoke compromised credentials
- Block malicious IPs

**3. Eradication**
- Remove malicious access
- Patch vulnerabilities
- Rotate secrets

**4. Recovery**
- Restore from clean backups
- Verify system integrity
- Resume normal operations

**5. Lessons Learned**
- Post-incident review
- Update procedures
- Implement preventive measures

### Security Contacts

```
Security Team:     security@neurolens.ai
Incident Hotline:  +1-XXX-XXX-XXXX
Bug Bounty:        https://neurolens.ai/security/bounty
```

---

## Compliance Frameworks

### HIPAA (Health Insurance Portability and Accountability Act)

NeuroLens processes medical imaging data and maintains HIPAA compliance:

| Requirement | Implementation |
|-------------|----------------|
| Access Controls | RBAC, MFA, audit logging |
| Audit Trails | Comprehensive audit logging with retention |
| Data Encryption | AES-256 at rest, TLS 1.3 in transit |
| Integrity Controls | Hash verification, tamper detection |
| Emergency Access | Break-glass procedures documented |
| Disposal | Secure deletion procedures |

### SOC 2 Type II Alignment

| Trust Principle | Controls |
|-----------------|----------|
| Security | Access control, encryption, monitoring |
| Availability | HA deployment, disaster recovery |
| Processing Integrity | Input validation, data verification |
| Confidentiality | Encryption, access restrictions |
| Privacy | PII handling, consent management |

### GDPR Considerations

| Right | Implementation |
|-------|----------------|
| Access | Data export endpoint |
| Rectification | Profile update API |
| Erasure | Account deletion with data purge |
| Portability | Standardized export format |
| Restriction | Account suspension capability |

---

## Security Checklist

### Pre-Deployment

- [ ] All environment variables configured
- [ ] Secrets not in codebase (scanned)
- [ ] TLS certificates valid
- [ ] Security headers enabled
- [ ] Rate limiting configured
- [ ] CORS origins whitelisted
- [ ] Database connections encrypted
- [ ] Logging to secure destination

### Regular Reviews

- [ ] Dependency vulnerability scan (weekly)
- [ ] Access control review (monthly)
- [ ] Secret rotation (quarterly)
- [ ] Penetration testing (annually)
- [ ] Security training (annually)
- [ ] Incident response drill (annually)

### Code Review Security Checklist

- [ ] Input validation on all user inputs
- [ ] Output encoding for display
- [ ] Parameterized database queries
- [ ] Sensitive data not logged
- [ ] Error messages don't leak info
- [ ] Authentication required for protected routes
- [ ] Authorization checks for resources
- [ ] Rate limiting on sensitive endpoints

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.0.0 | 2024 | Phase 11 security hardening |
| 2.0.0 | 2024 | Initial security documentation |

---

*This document is maintained by the NeuroLens Security Team. For questions or updates, contact security@neurolens.ai.*
