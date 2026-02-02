#!/usr/bin/env python3
"""Quick test script for security modules."""
import sys
import os

# Add backend to path for imports
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)
os.chdir(backend_path)

from app.core.security_hardened import hash_password_secure, verify_password_secure, validate_password_strength
from app.core.audit import AuditEvent, AuditEventType, AuditSeverity
from app.core.rate_limit import SlidingWindowRateLimiter
from app.core.api_security import InputValidator
from app.core.secrets import generate_secret_key, SecretsScanner
from app.core.data_protection import PIIDetector, DataEncryptor

def test_password_hashing():
    pwd = 'SecureP@ssw0rd123!'
    hashed = hash_password_secure(pwd)
    assert verify_password_secure(pwd, hashed), 'Password verification failed'
    assert not verify_password_secure('wrong', hashed), 'Wrong password should fail'
    print('✓ Password hashing works')

def test_password_validation():
    valid, errors = validate_password_strength('SecureP@ssw0rd123!')
    assert valid, f'Password validation failed: {errors}'
    
    invalid, errors = validate_password_strength('weak')
    assert not invalid, 'Weak password should fail'
    print('✓ Password validation works')

def test_rate_limiter():
    limiter = SlidingWindowRateLimiter()
    allowed, info = limiter.check('test_user', 10, 60)
    assert allowed, 'Rate limiter failed'
    print('✓ Rate limiter works')

def test_input_validation():
    assert InputValidator.check_sql_injection('SELECT * FROM users'), 'SQL injection not detected'
    assert not InputValidator.check_sql_injection('normal text'), 'False positive SQL injection'
    assert InputValidator.check_xss('<script>alert(1)</script>'), 'XSS not detected'
    print('✓ Input validation works')

def test_pii_detection():
    findings = PIIDetector.detect('email: test@example.com')
    assert len(findings) > 0, 'PII not detected'
    
    redacted = PIIDetector.redact('email: test@example.com')
    assert 'test@example.com' not in redacted
    print('✓ PII detection works')

def test_encryption():
    enc = DataEncryptor()
    encrypted = enc.encrypt_string('sensitive data')
    decrypted = enc.decrypt_string(encrypted)
    assert decrypted == 'sensitive data', 'Encryption/decryption failed'
    print('✓ Encryption works')

def test_secret_generation():
    key = generate_secret_key()
    assert len(key) >= 32, 'Secret key too short'
    print('✓ Secret generation works')

def test_audit_logging():
    event = AuditEvent(
        event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
        severity=AuditSeverity.INFO,
        actor_id='user_123',
        action='login'
    )
    assert event.id is not None, 'Audit event creation failed'
    print('✓ Audit logging works')

def test_secrets_scanner():
    findings = SecretsScanner.scan_content('api_key = sk_test_FAKE1234567890abcdefghi')
    assert len(findings) > 0, 'Secrets not detected'
    print('✓ Secrets scanner works')

if __name__ == '__main__':
    print('Running Phase 11 Security Module Tests')
    print('=' * 40)
    
    test_password_hashing()
    test_password_validation()
    test_rate_limiter()
    test_input_validation()
    test_pii_detection()
    test_encryption()
    test_secret_generation()
    test_audit_logging()
    test_secrets_scanner()
    
    print()
    print('=' * 40)
    print('✅ All security module tests passed!')
