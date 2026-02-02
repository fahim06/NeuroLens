"""
NeuroLens Data Protection Module

Data encryption, secure storage, and PII handling utilities.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import secrets
from datetime import datetime, timezone
from typing import Any, Optional
from dataclasses import dataclass
from enum import Enum


# =============================================================================
# Encryption Utilities
# =============================================================================

class EncryptionAlgorithm(str, Enum):
    """Supported encryption algorithms."""
    AES_256_GCM = "aes-256-gcm"
    CHACHA20_POLY1305 = "chacha20-poly1305"


@dataclass
class EncryptedData:
    """Container for encrypted data."""
    ciphertext: bytes
    nonce: bytes
    tag: bytes
    algorithm: EncryptionAlgorithm
    
    def to_base64(self) -> str:
        """Encode as base64 string for storage."""
        data = {
            "ct": base64.b64encode(self.ciphertext).decode(),
            "n": base64.b64encode(self.nonce).decode(),
            "t": base64.b64encode(self.tag).decode(),
            "a": self.algorithm.value,
        }
        import json
        return base64.b64encode(json.dumps(data).encode()).decode()
    
    @classmethod
    def from_base64(cls, encoded: str) -> EncryptedData:
        """Decode from base64 string."""
        import json
        data = json.loads(base64.b64decode(encoded).decode())
        return cls(
            ciphertext=base64.b64decode(data["ct"]),
            nonce=base64.b64decode(data["n"]),
            tag=base64.b64decode(data["t"]),
            algorithm=EncryptionAlgorithm(data["a"]),
        )


class DataEncryptor:
    """
    Symmetric encryption for data at rest.
    
    Uses AES-256-GCM for authenticated encryption.
    In production, keys should come from a KMS.
    """
    
    def __init__(self, key: bytes = None):
        """
        Initialize encryptor with encryption key.
        
        Args:
            key: 32-byte encryption key (uses env var if not provided)
        """
        if key is None:
            key_str = os.getenv("ENCRYPTION_KEY")
            if key_str:
                key = base64.b64decode(key_str)
            else:
                # Generate ephemeral key (for testing only)
                key = secrets.token_bytes(32)
        
        if len(key) != 32:
            raise ValueError("Encryption key must be 32 bytes")
        
        self.key = key
    
    def encrypt(self, plaintext: bytes) -> EncryptedData:
        """
        Encrypt data using AES-256-GCM.
        
        Args:
            plaintext: Data to encrypt
        
        Returns:
            EncryptedData container
        """
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            # Fallback for environments without cryptography
            return self._encrypt_fallback(plaintext)
        
        nonce = secrets.token_bytes(12)
        aesgcm = AESGCM(self.key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        
        # AES-GCM appends tag to ciphertext
        tag = ciphertext[-16:]
        ciphertext = ciphertext[:-16]
        
        return EncryptedData(
            ciphertext=ciphertext,
            nonce=nonce,
            tag=tag,
            algorithm=EncryptionAlgorithm.AES_256_GCM,
        )
    
    def decrypt(self, encrypted: EncryptedData) -> bytes:
        """
        Decrypt data.
        
        Args:
            encrypted: EncryptedData container
        
        Returns:
            Decrypted plaintext
        """
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            return self._decrypt_fallback(encrypted)
        
        aesgcm = AESGCM(self.key)
        ciphertext_with_tag = encrypted.ciphertext + encrypted.tag
        return aesgcm.decrypt(encrypted.nonce, ciphertext_with_tag, None)
    
    def _encrypt_fallback(self, plaintext: bytes) -> EncryptedData:
        """Fallback encryption using XOR (NOT SECURE - for testing only)."""
        nonce = secrets.token_bytes(12)
        # Simple XOR - NOT FOR PRODUCTION
        key_stream = hashlib.sha256(self.key + nonce).digest()
        ciphertext = bytes(p ^ k for p, k in zip(plaintext, key_stream * (len(plaintext) // 32 + 1)))
        tag = hashlib.sha256(ciphertext + self.key).digest()[:16]
        
        return EncryptedData(
            ciphertext=ciphertext,
            nonce=nonce,
            tag=tag,
            algorithm=EncryptionAlgorithm.AES_256_GCM,
        )
    
    def _decrypt_fallback(self, encrypted: EncryptedData) -> bytes:
        """Fallback decryption (NOT SECURE - for testing only)."""
        # Verify tag
        expected_tag = hashlib.sha256(encrypted.ciphertext + self.key).digest()[:16]
        if not hmac.compare_digest(encrypted.tag, expected_tag):
            raise ValueError("Decryption failed: invalid tag")
        
        key_stream = hashlib.sha256(self.key + encrypted.nonce).digest()
        plaintext = bytes(c ^ k for c, k in zip(encrypted.ciphertext, key_stream * (len(encrypted.ciphertext) // 32 + 1)))
        return plaintext
    
    def encrypt_string(self, plaintext: str) -> str:
        """Encrypt a string and return base64-encoded result."""
        encrypted = self.encrypt(plaintext.encode('utf-8'))
        return encrypted.to_base64()
    
    def decrypt_string(self, encrypted_b64: str) -> str:
        """Decrypt a base64-encoded encrypted string."""
        encrypted = EncryptedData.from_base64(encrypted_b64)
        return self.decrypt(encrypted).decode('utf-8')


# =============================================================================
# PII Detection and Handling
# =============================================================================

class PIIType(str, Enum):
    """Types of Personally Identifiable Information."""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    NAME = "name"
    ADDRESS = "address"
    DATE_OF_BIRTH = "date_of_birth"
    MEDICAL_RECORD = "medical_record"


class PIIDetector:
    """
    Detect and handle Personally Identifiable Information.
    """
    
    # PII detection patterns
    PATTERNS = {
        PIIType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        PIIType.PHONE: r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
        PIIType.SSN: r'\b\d{3}-\d{2}-\d{4}\b',
        PIIType.CREDIT_CARD: r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
        PIIType.IP_ADDRESS: r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    }
    
    @classmethod
    def detect(cls, text: str) -> list[tuple[PIIType, str, int]]:
        """
        Detect PII in text.
        
        Returns:
            List of (pii_type, matched_text, position) tuples
        """
        findings = []
        
        for pii_type, pattern in cls.PATTERNS.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                findings.append((pii_type, match.group(), match.start()))
        
        return findings
    
    @classmethod
    def redact(cls, text: str, replacement: str = "[REDACTED]") -> str:
        """
        Redact all PII from text.
        
        Args:
            text: Input text
            replacement: Replacement string
        
        Returns:
            Text with PII redacted
        """
        for pattern in cls.PATTERNS.values():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text
    
    @classmethod
    def mask(cls, text: str) -> str:
        """
        Mask PII in text (show partial info).
        """
        # Mask emails
        text = re.sub(
            cls.PATTERNS[PIIType.EMAIL],
            lambda m: cls._mask_email(m.group()),
            text,
            flags=re.IGNORECASE
        )
        
        # Mask phone numbers
        text = re.sub(
            cls.PATTERNS[PIIType.PHONE],
            lambda m: cls._mask_phone(m.group()),
            text
        )
        
        # Mask SSN
        text = re.sub(
            cls.PATTERNS[PIIType.SSN],
            "***-**-****",
            text
        )
        
        # Mask credit cards
        text = re.sub(
            cls.PATTERNS[PIIType.CREDIT_CARD],
            lambda m: cls._mask_credit_card(m.group()),
            text
        )
        
        return text
    
    @staticmethod
    def _mask_email(email: str) -> str:
        """Mask email address."""
        local, domain = email.split('@', 1)
        if len(local) <= 2:
            masked_local = '*' * len(local)
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        return f"{masked_local}@{domain}"
    
    @staticmethod
    def _mask_phone(phone: str) -> str:
        """Mask phone number."""
        digits = re.sub(r'\D', '', phone)
        if len(digits) >= 4:
            return '***-***-' + digits[-4:]
        return '***-***-****'
    
    @staticmethod
    def _mask_credit_card(card: str) -> str:
        """Mask credit card number."""
        digits = re.sub(r'\D', '', card)
        if len(digits) >= 4:
            return '**** **** **** ' + digits[-4:]
        return '**** **** **** ****'


# =============================================================================
# Secure File Handling
# =============================================================================

class SecureFileHandler:
    """
    Secure file upload and storage handling.
    """
    
    # Allowed file extensions by category
    ALLOWED_EXTENSIONS = {
        "image": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"},
        "document": {".pdf", ".doc", ".docx", ".txt", ".csv"},
        "medical": {".dcm", ".nii", ".nii.gz"},  # DICOM, NIfTI
        "model": {".h5", ".keras", ".onnx", ".pt", ".pth"},
    }
    
    # Maximum file sizes by category (in bytes)
    MAX_FILE_SIZES = {
        "image": 10 * 1024 * 1024,  # 10 MB
        "document": 50 * 1024 * 1024,  # 50 MB
        "medical": 500 * 1024 * 1024,  # 500 MB
        "model": 1024 * 1024 * 1024,  # 1 GB
    }
    
    # Dangerous file signatures (magic bytes)
    DANGEROUS_SIGNATURES = [
        b'MZ',  # Windows executable
        b'\x7fELF',  # Linux executable
        b'#!/',  # Shell script
        b'<?php',  # PHP
    ]
    
    @classmethod
    def validate_file(
        cls,
        filename: str,
        content: bytes,
        category: str,
    ) -> tuple[bool, Optional[str]]:
        """
        Validate an uploaded file.
        
        Args:
            filename: Original filename
            content: File content bytes
            category: File category (image, document, etc.)
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check extension
        ext = os.path.splitext(filename.lower())[1]
        allowed = cls.ALLOWED_EXTENSIONS.get(category, set())
        
        if ext not in allowed:
            return False, f"File extension '{ext}' not allowed for {category}"
        
        # Check file size
        max_size = cls.MAX_FILE_SIZES.get(category, 10 * 1024 * 1024)
        if len(content) > max_size:
            return False, f"File size exceeds maximum of {max_size // (1024*1024)} MB"
        
        # Check for dangerous file signatures
        for signature in cls.DANGEROUS_SIGNATURES:
            if content.startswith(signature):
                return False, "File content not allowed"
        
        return True, None
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove dangerous characters
        filename = re.sub(r'[^\w\-\.]', '_', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext
        
        # Add random suffix to prevent collisions
        name, ext = os.path.splitext(filename)
        random_suffix = secrets.token_hex(4)
        
        return f"{name}_{random_suffix}{ext}"
    
    @classmethod
    def generate_signed_url(
        cls,
        file_path: str,
        expires_in: int = 3600,
        secret_key: str = None,
    ) -> str:
        """
        Generate a signed URL for file access.
        
        Args:
            file_path: Path to file
            expires_in: Expiration time in seconds
            secret_key: Signing secret
        
        Returns:
            Signed URL
        """
        if secret_key is None:
            secret_key = os.getenv("SECRET_KEY", "default-key")
        
        expires_at = int(datetime.now(timezone.utc).timestamp()) + expires_in
        
        # Create signature
        message = f"{file_path}:{expires_at}"
        signature = hmac.new(
            secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()[:32]
        
        return f"{file_path}?expires={expires_at}&sig={signature}"
    
    @classmethod
    def verify_signed_url(
        cls,
        url: str,
        secret_key: str = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Verify a signed URL.
        
        Returns:
            Tuple of (is_valid, file_path or error_message)
        """
        if secret_key is None:
            secret_key = os.getenv("SECRET_KEY", "default-key")
        
        # Parse URL
        if '?' not in url:
            return False, "Invalid URL format"
        
        file_path, query = url.split('?', 1)
        
        # Parse query parameters
        params = {}
        for param in query.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                params[key] = value
        
        expires = params.get('expires')
        signature = params.get('sig')
        
        if not expires or not signature:
            return False, "Missing signature parameters"
        
        # Check expiration
        try:
            if int(expires) < datetime.now(timezone.utc).timestamp():
                return False, "URL expired"
        except ValueError:
            return False, "Invalid expiration"
        
        # Verify signature
        message = f"{file_path}:{expires}"
        expected_sig = hmac.new(
            secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()[:32]
        
        if not hmac.compare_digest(signature, expected_sig):
            return False, "Invalid signature"
        
        return True, file_path


# =============================================================================
# Data Hashing Utilities
# =============================================================================

def hash_data(data: bytes, algorithm: str = "sha256") -> str:
    """Hash data using specified algorithm."""
    hasher = hashlib.new(algorithm)
    hasher.update(data)
    return hasher.hexdigest()


def hash_for_deduplication(data: bytes) -> str:
    """Create a hash for data deduplication."""
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def create_data_fingerprint(data: dict[str, Any]) -> str:
    """Create a fingerprint for a data dictionary."""
    import json
    canonical = json.dumps(data, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()
