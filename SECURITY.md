# Security Policy

## Supported Versions

We are committed to ensuring the security of NeuroLens. Currently, we support the following versions:

| Version     | Supported          | Notes                      |
|-------------|--------------------|----------------------------|
| 2.0.21-beta | :white_check_mark: | Current Development (Beta) |
| 3.0.x       | :white_check_mark: | Next Stable Release        |
| 1.1.x       | :x:                | Deprecated                 |
| 1.0.x       | :x:                | No longer supported        |
| < 1.0       | :x:                | No longer supported        |

## Security Features (v3.0)

NeuroLens v3.0 includes comprehensive security hardening:

- **Authentication**: PBKDF2-SHA256 password hashing (100k iterations), JWT with JTI
- **Authorization**: Role-based access control (RBAC)
- **API Security**: Rate limiting, input validation, security headers
- **Audit Logging**: Tamper-resistant event chain
- **Data Protection**: AES-256-GCM encryption, PII detection
- **Container Security**: Docker hardening, non-root execution
- **Database Security**: PostgreSQL with encrypted connections

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please follow these steps to report it
responsibly.

### How to Report

Please do **not** report security vulnerabilities through public GitHub issues. Instead, please report them privately:

1. **Email:** Send a detailed description of the vulnerability to [fahim06@github.com](mailto:fahim06@github.com) (or
   the repository owner's contact email).
2. **Details:** Include as much information as possible:
    * Type of issue (e.g., buffer overflow, SQL injection, XSS).
    * Full paths of source file(s) related to the manifestation of the issue.
    * The location of the affected source code (tag/branch/commit or direct URL).
    * Any special configuration required to reproduce the issue.
    * Step-by-step instructions to reproduce the issue.
    * Proof-of-concept or exploit code (if available).
    * Impact of the issue, including how an attacker might exploit it.

### Response Timeline

* **Acknowledgment:** We will acknowledge receipt of your report within 48 hours.
* **Assessment:** We will assess the vulnerability and determine its impact within 1 week.
* **Resolution:** We aim to release a fix or mitigation within 2 weeks of assessment, depending on the complexity.

### Disclosure Policy

We request that you do not publicly disclose the vulnerability until we have had a chance to address it. We will notify
you when the fix is released and credit you for the discovery (if desired).

Thank you for helping keep NeuroLens secure!
