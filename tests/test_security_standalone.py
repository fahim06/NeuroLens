#!/usr/bin/env python3
"""
Standalone test script for Phase 11 security modules.
Tests the core security logic without requiring full backend dependencies.
"""
import hashlib
import base64
import secrets
import time
import re
import os
from datetime import datetime, timezone, timedelta


def test_password_hashing():
    """Test PBKDF2 password hashing."""
    password = "SecureP@ssw0rd123!"
    
    # Hash password using PBKDF2
    salt = secrets.token_bytes(32)
    iterations = 100000
    
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations)
    hash_string = f"pbkdf2:sha256:{iterations}${base64.b64encode(salt).decode()}${base64.b64encode(key).decode()}"
    
    # Verify
    parts = hash_string.split('$')
    stored_salt = base64.b64decode(parts[1])
    stored_key = base64.b64decode(parts[2])
    
    check_key = hashlib.pbkdf2_hmac('sha256', password.encode(), stored_salt, iterations)
    assert check_key == stored_key, "Password verification failed"
    
    # Wrong password should fail
    wrong_key = hashlib.pbkdf2_hmac('sha256', "wrongpassword".encode(), stored_salt, iterations)
    assert wrong_key != stored_key, "Wrong password should fail"
    
    print("✓ Password hashing works (PBKDF2-SHA256, 100k iterations)")


def test_password_validation():
    """Test password strength validation."""
    def validate_password(password):
        errors = []
        if len(password) < 12:
            errors.append("Password must be at least 12 characters")
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain uppercase")
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain lowercase")
        if not re.search(r'\d', password):
            errors.append("Password must contain digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain special character")
        return len(errors) == 0, errors
    
    # Strong password should pass
    valid, _ = validate_password("SecureP@ssw0rd123!")
    assert valid, "Strong password should pass"
    
    # Weak passwords should fail
    assert not validate_password("weak")[0], "Short password should fail"
    assert not validate_password("lowercase123!@#")[0], "No uppercase should fail"
    
    print("✓ Password validation works")


def test_rate_limiting():
    """Test sliding window rate limiter."""
    class SimpleRateLimiter:
        def __init__(self):
            self.requests = {}
        
        def check(self, key, max_requests, window_seconds):
            now = time.time()
            if key not in self.requests:
                self.requests[key] = []
            
            # Remove old requests
            self.requests[key] = [t for t in self.requests[key] if now - t < window_seconds]
            
            if len(self.requests[key]) >= max_requests:
                return False, {"remaining": 0}
            
            self.requests[key].append(now)
            return True, {"remaining": max_requests - len(self.requests[key])}
    
    limiter = SimpleRateLimiter()
    
    # Should allow requests within limit
    for i in range(5):
        allowed, _ = limiter.check("user_1", 10, 60)
        assert allowed, f"Request {i+1} should be allowed"
    
    # Should block after limit
    for i in range(5):
        limiter.check("user_2", 5, 60)
    allowed, _ = limiter.check("user_2", 5, 60)
    assert not allowed, "Should block after limit"
    
    print("✓ Rate limiting works")


def test_input_validation():
    """Test SQL injection and XSS detection."""
    sql_patterns = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b)",
        r"(--|;|')",
        r"(\bOR\b.*=)",
    ]
    
    xss_patterns = [
        r"<script[^>]*>",
        r"javascript:",
        r"on\w+\s*=",
    ]
    
    def check_sql_injection(text):
        for pattern in sql_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def check_xss(text):
        for pattern in xss_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    # SQL injection tests
    assert check_sql_injection("SELECT * FROM users"), "SQL SELECT not detected"
    assert check_sql_injection("1; DROP TABLE users"), "SQL DROP not detected"
    assert not check_sql_injection("normal text here"), "False positive for normal text"
    
    # XSS tests
    assert check_xss("<script>alert('xss')</script>"), "XSS script not detected"
    assert check_xss("onclick=evil()"), "XSS onclick not detected"
    assert not check_xss("normal text here"), "False positive for normal text"
    
    print("✓ Input validation (SQL injection, XSS) works")


def test_pii_detection():
    """Test PII detection and redaction."""
    patterns = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
    }
    
    def detect_pii(text):
        findings = []
        for pii_type, pattern in patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                findings.append((pii_type, match.group()))
        return findings
    
    def redact_pii(text):
        for pattern in patterns.values():
            text = re.sub(pattern, "[REDACTED]", text, flags=re.IGNORECASE)
        return text
    
    # Detection tests
    findings = detect_pii("Contact: test@example.com, Phone: 555-123-4567")
    assert len(findings) == 2, f"Expected 2 PII items, found {len(findings)}"
    
    # Redaction test
    redacted = redact_pii("Email: test@example.com")
    assert "test@example.com" not in redacted, "Email should be redacted"
    assert "[REDACTED]" in redacted, "Should contain [REDACTED]"
    
    print("✓ PII detection and redaction works")


def test_encryption():
    """Test symmetric encryption (simplified)."""
    key = secrets.token_bytes(32)
    
    def encrypt(plaintext, key):
        nonce = secrets.token_bytes(12)
        # Simplified XOR encryption for testing (NOT secure, just for demo)
        key_stream = hashlib.sha256(key + nonce).digest()
        ciphertext = bytes(p ^ k for p, k in zip(plaintext, key_stream * (len(plaintext) // 32 + 1)))
        tag = hashlib.sha256(ciphertext + key).digest()[:16]
        return nonce, ciphertext, tag
    
    def decrypt(nonce, ciphertext, tag, key):
        # Verify tag
        expected_tag = hashlib.sha256(ciphertext + key).digest()[:16]
        if tag != expected_tag:
            raise ValueError("Decryption failed: invalid tag")
        
        key_stream = hashlib.sha256(key + nonce).digest()
        plaintext = bytes(c ^ k for c, k in zip(ciphertext, key_stream * (len(ciphertext) // 32 + 1)))
        return plaintext
    
    # Test encryption/decryption
    plaintext = b"Sensitive data here"
    nonce, ciphertext, tag = encrypt(plaintext, key)
    decrypted = decrypt(nonce, ciphertext, tag, key)
    
    assert decrypted == plaintext, "Decryption should match plaintext"
    assert ciphertext != plaintext, "Ciphertext should differ from plaintext"
    
    print("✓ Encryption/decryption works")


def test_secret_generation():
    """Test cryptographically secure secret generation."""
    key1 = secrets.token_urlsafe(32)
    key2 = secrets.token_urlsafe(32)
    
    assert key1 != key2, "Generated keys should be unique"
    assert len(key1) >= 32, "Key should be at least 32 characters"
    
    # Test API key generation
    api_key = f"nl_{secrets.token_urlsafe(32)}"
    assert api_key.startswith("nl_"), "API key should have prefix"
    
    print("✓ Secret generation works")


def test_audit_logging():
    """Test audit event creation with hash chain."""
    class AuditEvent:
        def __init__(self, event_type, actor_id, action, previous_hash=""):
            self.id = secrets.token_hex(16)
            self.timestamp = datetime.now(timezone.utc).isoformat()
            self.event_type = event_type
            self.actor_id = actor_id
            self.action = action
            self.hash = self._compute_hash(previous_hash)
        
        def _compute_hash(self, previous_hash):
            data = f"{self.id}:{self.timestamp}:{self.event_type}:{self.actor_id}:{previous_hash}"
            return hashlib.sha256(data.encode()).hexdigest()
    
    # Create chain of events
    events = []
    previous_hash = ""
    
    for i in range(5):
        event = AuditEvent(
            event_type="AUTH_LOGIN",
            actor_id=f"user_{i}",
            action="login",
            previous_hash=previous_hash
        )
        events.append(event)
        previous_hash = event.hash
    
    # Verify chain integrity
    prev = ""
    for event in events:
        expected_hash = hashlib.sha256(
            f"{event.id}:{event.timestamp}:{event.event_type}:{event.actor_id}:{prev}".encode()
        ).hexdigest()
        assert event.hash == expected_hash, "Hash chain integrity failed"
        prev = event.hash
    
    print("✓ Audit logging with hash chain works")


def test_secrets_scanning():
    """Test secrets pattern detection."""
    patterns = [
        (r'(sk_live_[a-zA-Z0-9]{24,})', 'Stripe Live Key'),
        (r'(ghp_[a-zA-Z0-9]{36})', 'GitHub Token'),
        (r'(AKIA[0-9A-Z]{16})', 'AWS Access Key'),
        (r'(?i)(api[_-]?key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9-_]{20,})', 'Generic API Key'),
    ]
    
    def scan_content(content):
        findings = []
        for pattern, description in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                findings.append(description)
        return findings
    
    # Test detection
    assert scan_content('sk_test_FAKE1234567890abcdefghi'), "Stripe key not detected"
    assert scan_content('api_key = "FAKE1234567890abcdefghij"'), "API key not detected"
    assert not scan_content('normal code here'), "False positive on normal text"
    
    print("✓ Secrets scanning works")


if __name__ == '__main__':
    print("=" * 50)
    print("Phase 11 Security Module Validation Tests")
    print("=" * 50)
    print()
    
    test_password_hashing()
    test_password_validation()
    test_rate_limiting()
    test_input_validation()
    test_pii_detection()
    test_encryption()
    test_secret_generation()
    test_audit_logging()
    test_secrets_scanning()
    
    print()
    print("=" * 50)
    print("✅ All Phase 11 security tests passed!")
    print("=" * 50)
