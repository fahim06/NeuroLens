"""
NeuroLens API Security Middleware

OWASP-compliant security middleware for FastAPI.
Includes security headers, CORS, input validation, and request sanitization.
"""
from __future__ import annotations

import re
import html
import hashlib
from typing import Any, Optional, Callable
from dataclasses import dataclass
from urllib.parse import urlparse
import json

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import HTTPException, status


# =============================================================================
# Security Headers
# =============================================================================

@dataclass
class SecurityHeadersConfig:
    """Security headers configuration."""
    
    # Content Security Policy
    csp_default_src: str = "'self'"
    csp_script_src: str = "'self'"
    csp_style_src: str = "'self' 'unsafe-inline'"
    csp_img_src: str = "'self' data: https:"
    csp_font_src: str = "'self'"
    csp_connect_src: str = "'self'"
    csp_frame_ancestors: str = "'none'"
    
    # Other headers
    x_content_type_options: str = "nosniff"
    x_frame_options: str = "DENY"
    x_xss_protection: str = "1; mode=block"
    referrer_policy: str = "strict-origin-when-cross-origin"
    permissions_policy: str = "camera=(), microphone=(), geolocation=()"
    
    # HSTS (HTTP Strict Transport Security)
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = False
    
    def get_csp_header(self) -> str:
        """Build Content-Security-Policy header value."""
        directives = [
            f"default-src {self.csp_default_src}",
            f"script-src {self.csp_script_src}",
            f"style-src {self.csp_style_src}",
            f"img-src {self.csp_img_src}",
            f"font-src {self.csp_font_src}",
            f"connect-src {self.csp_connect_src}",
            f"frame-ancestors {self.csp_frame_ancestors}",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        return "; ".join(directives)
    
    def get_hsts_header(self) -> str:
        """Build Strict-Transport-Security header value."""
        value = f"max-age={self.hsts_max_age}"
        if self.hsts_include_subdomains:
            value += "; includeSubDomains"
        if self.hsts_preload:
            value += "; preload"
        return value


DEFAULT_SECURITY_HEADERS = SecurityHeadersConfig()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    def __init__(self, app, config: SecurityHeadersConfig = None):
        super().__init__(app)
        self.config = config or DEFAULT_SECURITY_HEADERS
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = self.config.x_content_type_options
        response.headers["X-Frame-Options"] = self.config.x_frame_options
        response.headers["X-XSS-Protection"] = self.config.x_xss_protection
        response.headers["Referrer-Policy"] = self.config.referrer_policy
        response.headers["Permissions-Policy"] = self.config.permissions_policy
        response.headers["Content-Security-Policy"] = self.config.get_csp_header()
        
        # Add HSTS header for HTTPS requests
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = self.config.get_hsts_header()
        
        # Remove server header
        response.headers.pop("Server", None)
        
        return response


# =============================================================================
# CORS Configuration
# =============================================================================

@dataclass
class CORSConfig:
    """CORS configuration with security defaults."""
    
    allow_origins: list[str] = None  # Explicitly allowed origins
    allow_origin_regex: str = None  # Regex pattern for allowed origins
    allow_methods: list[str] = None
    allow_headers: list[str] = None
    expose_headers: list[str] = None
    allow_credentials: bool = False
    max_age: int = 600  # 10 minutes
    
    def __post_init__(self):
        if self.allow_origins is None:
            self.allow_origins = []
        if self.allow_methods is None:
            self.allow_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
        if self.allow_headers is None:
            self.allow_headers = [
                "Authorization", "Content-Type", "X-Request-ID",
                "X-API-Key", "Accept", "Accept-Language"
            ]
        if self.expose_headers is None:
            self.expose_headers = [
                "X-Request-ID", "X-RateLimit-Remaining",
                "X-RateLimit-Reset", "Retry-After"
            ]


def validate_origin(origin: str, config: CORSConfig) -> bool:
    """Validate if an origin is allowed."""
    if not origin:
        return False
    
    # Check explicit allow list
    if origin in config.allow_origins:
        return True
    
    # Check wildcard (only for development)
    if "*" in config.allow_origins:
        return True
    
    # Check regex pattern
    if config.allow_origin_regex:
        if re.match(config.allow_origin_regex, origin):
            return True
    
    return False


# =============================================================================
# Input Validation & Sanitization
# =============================================================================

class InputValidator:
    """Input validation utilities for security."""
    
    # Patterns for common injection attacks
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b)",
        r"(--|\#|\/\*|\*\/)",
        r"(\bOR\b\s+\d+\s*=\s*\d+)",
        r"(\bAND\b\s+\d+\s*=\s*\d+)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e",
        r"%252e%252e",
    ]
    
    @classmethod
    def check_sql_injection(cls, value: str) -> bool:
        """Check for potential SQL injection patterns."""
        if not value:
            return False
        
        value_upper = value.upper()
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def check_xss(cls, value: str) -> bool:
        """Check for potential XSS patterns."""
        if not value:
            return False
        
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def check_path_traversal(cls, value: str) -> bool:
        """Check for path traversal attempts."""
        if not value:
            return False
        
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        """Sanitize a string input."""
        if not value:
            return value
        
        # Truncate to max length
        value = value[:max_length]
        
        # HTML escape
        value = html.escape(value)
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        return value
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize a filename for safe storage."""
        if not filename:
            return "unnamed"
        
        # Remove path components
        filename = filename.replace("\\", "/").split("/")[-1]
        
        # Remove dangerous characters
        filename = re.sub(r'[^\w\-\.]', '_', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:250] + ('.' + ext if ext else '')
        
        return filename
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """Validate email format."""
        if not email:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email)) and len(email) <= 254
    
    @classmethod
    def validate_uuid(cls, value: str) -> bool:
        """Validate UUID format."""
        if not value:
            return False
        
        pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(pattern, value.lower()))
    
    @classmethod
    def validate_url(cls, url: str, allowed_schemes: list[str] = None) -> bool:
        """Validate URL format and scheme."""
        if not url:
            return False
        
        if allowed_schemes is None:
            allowed_schemes = ["http", "https"]
        
        try:
            parsed = urlparse(url)
            return (
                parsed.scheme in allowed_schemes and
                bool(parsed.netloc) and
                len(url) <= 2048
            )
        except Exception:
            return False


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate and sanitize incoming requests."""
    
    MAX_BODY_SIZE = 10 * 1024 * 1024  # 10 MB
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_BODY_SIZE:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "Request body too large"}
            )
        
        # Check for suspicious patterns in query parameters
        for key, value in request.query_params.items():
            if InputValidator.check_sql_injection(value):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid query parameter"}
                )
        
        # Check path for traversal
        if InputValidator.check_path_traversal(request.url.path):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid request path"}
            )
        
        return await call_next(request)


# =============================================================================
# Error Handling (Safe Error Responses)
# =============================================================================

class SafeErrorHandler:
    """
    Safe error handling that doesn't leak sensitive information.
    """
    
    # Errors that are safe to show details for
    SAFE_STATUS_CODES = {400, 401, 403, 404, 405, 409, 422, 429}
    
    # Patterns to redact from error messages
    REDACT_PATTERNS = [
        r'password["\']?\s*[:=]\s*["\']?[^"\'\s]+',
        r'token["\']?\s*[:=]\s*["\']?[^"\'\s]+',
        r'secret["\']?\s*[:=]\s*["\']?[^"\'\s]+',
        r'api[_-]?key["\']?\s*[:=]\s*["\']?[^"\'\s]+',
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
    ]
    
    @classmethod
    def sanitize_error_message(cls, message: str) -> str:
        """Remove sensitive information from error messages."""
        if not message:
            return message
        
        for pattern in cls.REDACT_PATTERNS:
            message = re.sub(pattern, '[REDACTED]', message, flags=re.IGNORECASE)
        
        return message
    
    @classmethod
    def create_error_response(
        cls,
        status_code: int,
        message: str = None,
        request_id: str = None,
    ) -> dict[str, Any]:
        """Create a safe error response."""
        # Default messages for common status codes
        default_messages = {
            400: "Bad request",
            401: "Authentication required",
            403: "Access denied",
            404: "Resource not found",
            405: "Method not allowed",
            409: "Resource conflict",
            422: "Validation error",
            429: "Too many requests",
            500: "Internal server error",
            502: "Bad gateway",
            503: "Service unavailable",
        }
        
        response = {
            "error": True,
            "status_code": status_code,
        }
        
        if status_code in cls.SAFE_STATUS_CODES and message:
            response["message"] = cls.sanitize_error_message(message)
        else:
            response["message"] = default_messages.get(status_code, "An error occurred")
        
        if request_id:
            response["request_id"] = request_id
        
        return response


# =============================================================================
# Request ID Tracking
# =============================================================================

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to ensure every request has a unique ID."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = hashlib.sha256(
                f"{request.client.host}:{request.url.path}:{id(request)}".encode()
            ).hexdigest()[:16]
        
        # Store in request state
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


# =============================================================================
# Combined Security Middleware Setup
# =============================================================================

def setup_security_middleware(app, config: dict = None):
    """
    Set up all security middleware for a FastAPI app.
    
    Args:
        app: FastAPI application instance
        config: Optional configuration overrides
    """
    config = config or {}
    
    # Add middleware in order (first added = last executed)
    
    # Request ID (outermost)
    app.add_middleware(RequestIDMiddleware)
    
    # Request validation
    app.add_middleware(RequestValidationMiddleware)
    
    # Security headers
    headers_config = config.get("headers", DEFAULT_SECURITY_HEADERS)
    app.add_middleware(SecurityHeadersMiddleware, config=headers_config)
    
    return app
