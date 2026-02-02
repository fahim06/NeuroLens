"""
NeuroLens Security Tests

Comprehensive tests for security modules.
"""
import pytest
import time
import hashlib
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

# Import modules to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'app'))

from core.security_hardened import (
    SecurityConfig,
    hash_password_secure,
    verify_password_secure,
    validate_password_strength,
    create_access_token_secure,
    create_refresh_token_secure,
    verify_token_secure,
    revoke_token,
    TokenBlacklist,
    generate_api_key_secure,
    sanitize_for_log,
    mask_email,
    mask_ip,
)
from core.audit import (
    AuditEventType,
    AuditSeverity,
    AuditEvent,
    AuditLogger,
    log_auth_success,
    log_auth_failure,
    log_permission_denied,
)
from core.rate_limit import (
    RateLimitScope,
    SlidingWindowRateLimiter,
    TokenBucketRateLimiter,
    LoginAttemptTracker,
    RateLimits,
)
from core.api_security import (
    InputValidator,
    SecurityHeadersConfig,
    CORSConfig,
    SafeErrorHandler,
)
from core.secrets import (
    SecretsManager,
    SecretType,
    EnvironmentValidator,
    SecretsScanner,
    generate_secret_key,
    generate_api_key,
)
from core.data_protection import (
    DataEncryptor,
    PIIDetector,
    PIIType,
    SecureFileHandler,
    hash_data,
)


# =============================================================================
# Password Hashing Tests
# =============================================================================

class TestPasswordHashing:
    """Tests for password hashing functionality."""
    
    def test_hash_password_produces_different_hashes(self):
        """Same password should produce different hashes (due to salt)."""
        password = "SecureP@ssw0rd123"
        hash1 = hash_password_secure(password)
        hash2 = hash_password_secure(password)
        assert hash1 != hash2
    
    def test_verify_password_correct(self):
        """Correct password should verify successfully."""
        password = "SecureP@ssw0rd123"
        hashed = hash_password_secure(password)
        assert verify_password_secure(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Incorrect password should fail verification."""
        password = "SecureP@ssw0rd123"
        wrong_password = "WrongPassword123!"
        hashed = hash_password_secure(password)
        assert verify_password_secure(wrong_password, hashed) is False
    
    def test_hash_contains_algorithm_info(self):
        """Hash should contain algorithm and iteration info."""
        password = "SecureP@ssw0rd123"
        hashed = hash_password_secure(password)
        assert "pbkdf2:sha256" in hashed
        assert "100000" in hashed


class TestPasswordValidation:
    """Tests for password strength validation."""
    
    def test_valid_strong_password(self):
        """Strong password should pass validation."""
        is_valid, errors = validate_password_strength("SecureP@ssw0rd123!")
        assert is_valid is True
        assert len(errors) == 0
    
    def test_password_too_short(self):
        """Short password should fail."""
        is_valid, errors = validate_password_strength("Short1!")
        assert is_valid is False
        assert any("12 characters" in e for e in errors)
    
    def test_password_no_uppercase(self):
        """Password without uppercase should fail."""
        is_valid, errors = validate_password_strength("lowercase1234567!")
        assert is_valid is False
        assert any("uppercase" in e for e in errors)
    
    def test_password_no_lowercase(self):
        """Password without lowercase should fail."""
        is_valid, errors = validate_password_strength("UPPERCASE1234567!")
        assert is_valid is False
        assert any("lowercase" in e for e in errors)
    
    def test_password_no_digit(self):
        """Password without digit should fail."""
        is_valid, errors = validate_password_strength("NoDigitsHere!@#$")
        assert is_valid is False
        assert any("digit" in e for e in errors)
    
    def test_password_no_special(self):
        """Password without special character should fail."""
        is_valid, errors = validate_password_strength("NoSpecialChars123")
        assert is_valid is False
        assert any("special" in e for e in errors)
    
    def test_common_password_rejected(self):
        """Common passwords should be rejected."""
        is_valid, errors = validate_password_strength("Password123!")
        assert is_valid is False
        assert any("common" in e for e in errors)


# =============================================================================
# JWT Token Tests
# =============================================================================

class TestJWTTokens:
    """Tests for JWT token creation and verification."""
    
    @patch.dict(os.environ, {"SECRET_KEY": "test-secret-key-at-least-32-characters"})
    def test_create_access_token(self):
        """Access token should be created successfully."""
        token = create_access_token_secure(
            user_id="user_123",
            role="user",
        )
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50
    
    @patch.dict(os.environ, {"SECRET_KEY": "test-secret-key-at-least-32-characters"})
    def test_verify_access_token(self):
        """Valid access token should verify correctly."""
        token = create_access_token_secure(
            user_id="user_123",
            role="admin",
        )
        payload = verify_token_secure(token, "access")
        assert payload is not None
        assert payload.user_id == "user_123"
        assert payload.role == "admin"
        assert payload.token_type == "access"
    
    @patch.dict(os.environ, {"SECRET_KEY": "test-secret-key-at-least-32-characters"})
    def test_refresh_token_different_type(self):
        """Refresh token should have different type."""
        token = create_refresh_token_secure(user_id="user_123")
        payload = verify_token_secure(token, "refresh")
        assert payload is not None
        assert payload.token_type == "refresh"
    
    @patch.dict(os.environ, {"SECRET_KEY": "test-secret-key-at-least-32-characters"})
    def test_wrong_token_type_rejected(self):
        """Access token should not verify as refresh token."""
        access_token = create_access_token_secure(user_id="user_123")
        payload = verify_token_secure(access_token, "refresh")
        assert payload is None
    
    @patch.dict(os.environ, {"SECRET_KEY": "test-secret-key-at-least-32-characters"})
    def test_token_revocation(self):
        """Revoked token should not verify."""
        token = create_access_token_secure(user_id="user_123")
        
        # Token should verify before revocation
        payload1 = verify_token_secure(token, "access")
        assert payload1 is not None
        
        # Revoke the token
        revoke_token(payload1.jti)
        
        # Token should not verify after revocation
        payload2 = verify_token_secure(token, "access")
        assert payload2 is None


class TestTokenBlacklist:
    """Tests for token blacklist functionality."""
    
    def test_add_to_blacklist(self):
        """Token should be addable to blacklist."""
        blacklist = TokenBlacklist()
        blacklist.add("token_123", ttl_seconds=3600)
        assert blacklist.is_blacklisted("token_123") is True
    
    def test_not_blacklisted(self):
        """Non-blacklisted token should return False."""
        blacklist = TokenBlacklist()
        assert blacklist.is_blacklisted("unknown_token") is False
    
    def test_cleanup_expired(self):
        """Expired entries should be cleaned up."""
        blacklist = TokenBlacklist()
        blacklist.add("token_123", ttl_seconds=0)  # Already expired
        time.sleep(0.1)
        blacklist.cleanup_expired()
        assert blacklist.is_blacklisted("token_123") is False


# =============================================================================
# Rate Limiting Tests
# =============================================================================

class TestSlidingWindowRateLimiter:
    """Tests for sliding window rate limiter."""
    
    def test_allows_within_limit(self):
        """Requests within limit should be allowed."""
        limiter = SlidingWindowRateLimiter()
        
        for _ in range(5):
            allowed, info = limiter.check("user_1", max_requests=10, window_seconds=60)
            assert allowed is True
    
    def test_blocks_over_limit(self):
        """Requests over limit should be blocked."""
        limiter = SlidingWindowRateLimiter()
        
        # Use up the limit
        for _ in range(10):
            limiter.check("user_1", max_requests=10, window_seconds=60)
        
        # Next request should be blocked
        allowed, info = limiter.check("user_1", max_requests=10, window_seconds=60)
        assert allowed is False
        assert info["remaining"] == 0
    
    def test_separate_keys(self):
        """Different keys should have separate limits."""
        limiter = SlidingWindowRateLimiter()
        
        # Use up limit for user_1
        for _ in range(10):
            limiter.check("user_1", max_requests=10, window_seconds=60)
        
        # user_2 should still be allowed
        allowed, info = limiter.check("user_2", max_requests=10, window_seconds=60)
        assert allowed is True


class TestTokenBucketRateLimiter:
    """Tests for token bucket rate limiter."""
    
    def test_allows_burst(self):
        """Burst of requests should be allowed."""
        limiter = TokenBucketRateLimiter()
        
        # Rapid burst
        allowed_count = 0
        for _ in range(10):
            allowed, _ = limiter.check("user_1", bucket_size=10, refill_rate=1)
            if allowed:
                allowed_count += 1
        
        assert allowed_count == 10
    
    def test_blocks_after_bucket_empty(self):
        """Requests after bucket is empty should be blocked."""
        limiter = TokenBucketRateLimiter()
        
        # Empty the bucket
        for _ in range(10):
            limiter.check("user_1", bucket_size=10, refill_rate=1)
        
        # Next request should be blocked
        allowed, info = limiter.check("user_1", bucket_size=10, refill_rate=1)
        assert allowed is False


class TestLoginAttemptTracker:
    """Tests for login attempt tracking."""
    
    def test_allows_normal_logins(self):
        """Normal login attempts should be allowed."""
        tracker = LoginAttemptTracker()
        
        for _ in range(3):
            allowed, info = tracker.check_attempt("user_1")
            assert allowed is True
    
    def test_lockout_after_max_attempts(self):
        """Account should be locked after max failed attempts."""
        tracker = LoginAttemptTracker()
        
        # Fail max attempts
        for _ in range(5):
            tracker.record_failure("user_1")
        
        # Should be locked out
        allowed, info = tracker.check_attempt("user_1")
        assert allowed is False
        assert info["locked"] is True
    
    def test_reset_on_success(self):
        """Successful login should reset attempt counter."""
        tracker = LoginAttemptTracker()
        
        # Some failed attempts
        for _ in range(3):
            tracker.record_failure("user_1")
        
        # Successful login
        tracker.record_success("user_1")
        
        # Should be allowed again with fresh counter
        allowed, info = tracker.check_attempt("user_1")
        assert allowed is True
        assert info["attempts"] == 0


# =============================================================================
# Input Validation Tests
# =============================================================================

class TestInputValidator:
    """Tests for input validation."""
    
    def test_detects_sql_injection(self):
        """SQL injection patterns should be detected."""
        assert InputValidator.check_sql_injection("SELECT * FROM users") is True
        assert InputValidator.check_sql_injection("1; DROP TABLE users") is True
        assert InputValidator.check_sql_injection("' OR '1'='1") is True
        assert InputValidator.check_sql_injection("normal text") is False
    
    def test_detects_xss(self):
        """XSS patterns should be detected."""
        assert InputValidator.check_xss("<script>alert('xss')</script>") is True
        assert InputValidator.check_xss("onclick=evil()") is True
        assert InputValidator.check_xss("javascript:alert(1)") is True
        assert InputValidator.check_xss("normal text") is False
    
    def test_detects_path_traversal(self):
        """Path traversal patterns should be detected."""
        assert InputValidator.check_path_traversal("../../../etc/passwd") is True
        assert InputValidator.check_path_traversal("..\\..\\windows") is True
        assert InputValidator.check_path_traversal("/normal/path") is False
    
    def test_sanitize_string(self):
        """String sanitization should work."""
        result = InputValidator.sanitize_string("  <script>Hello</script>  ")
        assert "<script>" not in result
        assert "Hello" in result
    
    def test_validate_email(self):
        """Email validation should work."""
        assert InputValidator.validate_email("user@example.com") is True
        assert InputValidator.validate_email("invalid-email") is False
        assert InputValidator.validate_email("user@") is False
    
    def test_validate_uuid(self):
        """UUID validation should work."""
        assert InputValidator.validate_uuid("550e8400-e29b-41d4-a716-446655440000") is True
        assert InputValidator.validate_uuid("not-a-uuid") is False


# =============================================================================
# Audit Logging Tests
# =============================================================================

class TestAuditLogging:
    """Tests for audit logging functionality."""
    
    def test_create_audit_event(self):
        """Audit event should be created correctly."""
        event = AuditEvent(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            severity=AuditSeverity.INFO,
            actor_id="user_123",
            action="login",
        )
        
        assert event.event_type == AuditEventType.AUTH_LOGIN_SUCCESS
        assert event.severity == AuditSeverity.INFO
        assert event.id is not None
    
    def test_audit_logger_logs_events(self):
        """Audit logger should store events."""
        logger = AuditLogger()
        
        event = AuditEvent(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            severity=AuditSeverity.INFO,
            actor_id="user_123",
            action="login",
        )
        
        logged = logger.log(event)
        assert logged is not None
        assert logged.hash is not None
    
    def test_audit_chain_integrity(self):
        """Audit chain should maintain integrity."""
        logger = AuditLogger()
        
        # Log multiple events
        for i in range(5):
            event = AuditEvent(
                event_type=AuditEventType.DATA_ACCESS,
                severity=AuditSeverity.INFO,
                actor_id=f"user_{i}",
                action="read",
            )
            logger.log(event)
        
        # Verify chain integrity
        assert logger.verify_chain_integrity() is True
    
    def test_convenience_log_functions(self):
        """Convenience logging functions should work."""
        event1 = log_auth_success("user_123", "192.168.1.1")
        assert event1.event_type == AuditEventType.AUTH_LOGIN_SUCCESS
        
        event2 = log_auth_failure("unknown", "192.168.1.1", "Invalid password")
        assert event2.event_type == AuditEventType.AUTH_LOGIN_FAILURE
        
        event3 = log_permission_denied("user_123", "ADMIN_ACCESS", "admin_panel")
        assert event3.event_type == AuditEventType.AUTHZ_PERMISSION_DENIED


# =============================================================================
# Secrets Management Tests
# =============================================================================

class TestSecretsManager:
    """Tests for secrets manager."""
    
    def test_set_and_get_secret(self):
        """Secret should be settable and gettable."""
        manager = SecretsManager()
        manager.set(
            "TEST_SECRET",
            "secret_value",
            SecretType.API_KEY,
        )
        
        assert manager.get("TEST_SECRET") == "secret_value"
    
    def test_delete_secret(self):
        """Secret should be deletable."""
        manager = SecretsManager()
        manager.set("TEST_SECRET", "value", SecretType.API_KEY)
        
        assert manager.delete("TEST_SECRET") is True
        assert manager.get("TEST_SECRET") is None
    
    def test_secrets_needing_rotation(self):
        """Should identify secrets needing rotation."""
        manager = SecretsManager()
        manager.set("OLD_SECRET", "value", SecretType.API_KEY)
        
        # Manually set old creation time
        manager._metadata["OLD_SECRET"].created_at = datetime.now(timezone.utc) - timedelta(days=100)
        
        needing_rotation = manager.get_secrets_needing_rotation(max_age_days=90)
        assert "OLD_SECRET" in needing_rotation


class TestSecretsScanner:
    """Tests for secrets scanning."""
    
    def test_detects_api_keys(self):
        """Should detect API key patterns."""
        content = "api_key = 'sk_test_FAKE1234567890abcdefghi'"
        findings = SecretsScanner.scan_content(content)
        assert len(findings) > 0
    
    def test_detects_aws_keys(self):
        """Should detect AWS access keys."""
        content = "aws_key = AKIAIOSFODNN7EXAMPLE"
        findings = SecretsScanner.scan_content(content)
        assert any("AWS" in f["type"] for f in findings)
    
    def test_detects_github_tokens(self):
        """Should detect GitHub tokens."""
        content = "token = ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        findings = SecretsScanner.scan_content(content)
        assert any("GitHub" in f["type"] for f in findings)


class TestEnvironmentValidator:
    """Tests for environment variable validation."""
    
    def test_check_secrets_in_code(self):
        """Should detect hardcoded secrets in code."""
        code = '''
        password = "hardcoded123"
        api_key = "secret_key_here"
        '''
        findings = EnvironmentValidator.check_for_secrets_in_code(code)
        assert len(findings) > 0


# =============================================================================
# Data Protection Tests
# =============================================================================

class TestDataEncryptor:
    """Tests for data encryption."""
    
    def test_encrypt_decrypt_bytes(self):
        """Should encrypt and decrypt bytes correctly."""
        encryptor = DataEncryptor()
        plaintext = b"Hello, World!"
        
        encrypted = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_encrypt_decrypt_string(self):
        """Should encrypt and decrypt strings correctly."""
        encryptor = DataEncryptor()
        plaintext = "Sensitive data here"
        
        encrypted = encryptor.encrypt_string(plaintext)
        decrypted = encryptor.decrypt_string(encrypted)
        
        assert decrypted == plaintext
    
    def test_different_ciphertexts(self):
        """Same plaintext should produce different ciphertexts."""
        encryptor = DataEncryptor()
        plaintext = b"Same data"
        
        encrypted1 = encryptor.encrypt(plaintext)
        encrypted2 = encryptor.encrypt(plaintext)
        
        assert encrypted1.ciphertext != encrypted2.ciphertext


class TestPIIDetector:
    """Tests for PII detection."""
    
    def test_detect_email(self):
        """Should detect email addresses."""
        text = "Contact me at user@example.com for more info"
        findings = PIIDetector.detect(text)
        
        assert any(f[0] == PIIType.EMAIL for f in findings)
    
    def test_detect_phone(self):
        """Should detect phone numbers."""
        text = "Call me at 555-123-4567"
        findings = PIIDetector.detect(text)
        
        assert any(f[0] == PIIType.PHONE for f in findings)
    
    def test_detect_ssn(self):
        """Should detect SSN patterns."""
        text = "SSN: 123-45-6789"
        findings = PIIDetector.detect(text)
        
        assert any(f[0] == PIIType.SSN for f in findings)
    
    def test_redact_pii(self):
        """Should redact all PII."""
        text = "Email: user@example.com, Phone: 555-123-4567"
        redacted = PIIDetector.redact(text)
        
        assert "user@example.com" not in redacted
        assert "555-123-4567" not in redacted
        assert "[REDACTED]" in redacted
    
    def test_mask_pii(self):
        """Should mask PII with partial info."""
        text = "Email: john@example.com"
        masked = PIIDetector.mask(text)
        
        assert "john@example.com" not in masked
        assert "@example.com" in masked  # Domain preserved


class TestSecureFileHandler:
    """Tests for secure file handling."""
    
    def test_validate_allowed_extension(self):
        """Should allow valid extensions."""
        is_valid, error = SecureFileHandler.validate_file(
            "test.png",
            b"fake image content",
            "image"
        )
        assert is_valid is True
    
    def test_reject_disallowed_extension(self):
        """Should reject disallowed extensions."""
        is_valid, error = SecureFileHandler.validate_file(
            "malicious.exe",
            b"fake content",
            "image"
        )
        assert is_valid is False
        assert "not allowed" in error
    
    def test_reject_oversized_file(self):
        """Should reject oversized files."""
        large_content = b"x" * (20 * 1024 * 1024)  # 20 MB
        is_valid, error = SecureFileHandler.validate_file(
            "large.png",
            large_content,
            "image"  # Max 10 MB
        )
        assert is_valid is False
        assert "exceeds" in error
    
    def test_sanitize_filename(self):
        """Should sanitize dangerous filenames."""
        dangerous_name = "../../../etc/passwd"
        sanitized = SecureFileHandler.sanitize_filename(dangerous_name)
        
        assert ".." not in sanitized
        assert "/" not in sanitized
    
    def test_signed_url_generation_and_verification(self):
        """Should generate and verify signed URLs."""
        url = SecureFileHandler.generate_signed_url(
            "/files/test.png",
            expires_in=3600,
            secret_key="test-secret",
        )
        
        is_valid, result = SecureFileHandler.verify_signed_url(
            url,
            secret_key="test-secret",
        )
        
        assert is_valid is True
        assert result == "/files/test.png"


# =============================================================================
# Utility Function Tests
# =============================================================================

class TestUtilityFunctions:
    """Tests for utility functions."""
    
    def test_sanitize_for_log(self):
        """Should sanitize sensitive data for logging."""
        data = {
            "username": "john",
            "password": "secret123",
            "token": "jwt_token_here",
        }
        sanitized = sanitize_for_log(data)
        
        assert sanitized["username"] == "john"
        assert sanitized["password"] == "[REDACTED]"
        assert sanitized["token"] == "[REDACTED]"
    
    def test_mask_email(self):
        """Should mask email addresses."""
        assert mask_email("john@example.com") == "j***n@example.com"
        assert mask_email("ab@test.com") == "**@test.com"
    
    def test_mask_ip(self):
        """Should mask IP addresses."""
        masked = mask_ip("192.168.1.100")
        assert "192.168" in masked
        assert "100" not in masked
    
    def test_hash_data(self):
        """Should hash data correctly."""
        result = hash_data(b"test data")
        assert len(result) == 64  # SHA256 hex
    
    def test_generate_secret_key(self):
        """Should generate unique secret keys."""
        key1 = generate_secret_key()
        key2 = generate_secret_key()
        
        assert key1 != key2
        assert len(key1) >= 32
    
    def test_generate_api_key(self):
        """Should generate API keys with prefix."""
        key = generate_api_key()
        assert key.startswith("nl_")


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
