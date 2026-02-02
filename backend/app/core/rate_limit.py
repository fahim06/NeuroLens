"""
NeuroLens Rate Limiting Module

Token bucket and sliding window rate limiting for API protection.
Prevents abuse and ensures fair resource usage.
"""
from __future__ import annotations

import time
import hashlib
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional
from enum import Enum
import threading


class RateLimitScope(str, Enum):
    """Rate limit scope."""
    GLOBAL = "global"  # Applies to all requests
    IP = "ip"  # Per IP address
    USER = "user"  # Per authenticated user
    API_KEY = "api_key"  # Per API key
    ENDPOINT = "endpoint"  # Per endpoint


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests: int  # Number of requests allowed
    window_seconds: int  # Time window in seconds
    scope: RateLimitScope = RateLimitScope.IP
    
    @property
    def key_prefix(self) -> str:
        return f"ratelimit:{self.scope.value}"


# Pre-defined rate limit tiers
class RateLimits:
    """Standard rate limit configurations."""
    
    # Authentication endpoints (stricter)
    AUTH_LOGIN = RateLimitConfig(requests=5, window_seconds=60, scope=RateLimitScope.IP)
    AUTH_REGISTER = RateLimitConfig(requests=3, window_seconds=60, scope=RateLimitScope.IP)
    PASSWORD_RESET = RateLimitConfig(requests=3, window_seconds=300, scope=RateLimitScope.IP)
    
    # API endpoints (standard)
    API_STANDARD = RateLimitConfig(requests=100, window_seconds=60, scope=RateLimitScope.USER)
    API_STRICT = RateLimitConfig(requests=20, window_seconds=60, scope=RateLimitScope.USER)
    
    # Inference endpoints (resource-intensive)
    INFERENCE_SINGLE = RateLimitConfig(requests=30, window_seconds=60, scope=RateLimitScope.USER)
    INFERENCE_BATCH = RateLimitConfig(requests=5, window_seconds=60, scope=RateLimitScope.USER)
    
    # Admin endpoints
    ADMIN = RateLimitConfig(requests=50, window_seconds=60, scope=RateLimitScope.USER)
    
    # Anonymous/unauthenticated
    ANONYMOUS = RateLimitConfig(requests=20, window_seconds=60, scope=RateLimitScope.IP)


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    allowed: bool
    remaining: int
    reset_at: float  # Unix timestamp
    retry_after: Optional[int] = None  # Seconds until reset
    
    def to_headers(self) -> dict[str, str]:
        """Convert to HTTP headers."""
        headers = {
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(int(self.reset_at)),
        }
        if not self.allowed and self.retry_after:
            headers["Retry-After"] = str(self.retry_after)
        return headers


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter.
    
    Uses an in-memory store (replace with Redis for production).
    """
    
    def __init__(self):
        self._windows: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def _make_key(self, config: RateLimitConfig, identifier: str) -> str:
        """Create a unique key for rate limiting."""
        return f"{config.key_prefix}:{identifier}"
    
    def check(
        self,
        config: RateLimitConfig,
        identifier: str,
    ) -> RateLimitResult:
        """
        Check if request is allowed under rate limit.
        
        Args:
            config: Rate limit configuration
            identifier: Unique identifier (IP, user ID, etc.)
        
        Returns:
            RateLimitResult with allowed status and metadata
        """
        key = self._make_key(config, identifier)
        now = time.time()
        window_start = now - config.window_seconds
        
        with self._lock:
            # Clean old entries
            self._windows[key] = [
                ts for ts in self._windows[key]
                if ts > window_start
            ]
            
            current_count = len(self._windows[key])
            remaining = max(0, config.requests - current_count)
            reset_at = now + config.window_seconds
            
            if current_count >= config.requests:
                # Rate limited
                oldest = min(self._windows[key]) if self._windows[key] else now
                retry_after = int(oldest + config.window_seconds - now) + 1
                
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_at=reset_at,
                    retry_after=retry_after,
                )
            
            # Allow request and record timestamp
            self._windows[key].append(now)
            
            return RateLimitResult(
                allowed=True,
                remaining=remaining - 1,
                reset_at=reset_at,
            )
    
    def reset(self, config: RateLimitConfig, identifier: str) -> None:
        """Reset rate limit for an identifier."""
        key = self._make_key(config, identifier)
        with self._lock:
            self._windows.pop(key, None)


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter for smoother rate limiting.
    
    Allows bursts up to bucket capacity while maintaining average rate.
    """
    
    def __init__(self):
        self._buckets: dict[str, tuple[float, float]] = {}  # key -> (tokens, last_update)
        self._lock = threading.Lock()
    
    def check(
        self,
        identifier: str,
        capacity: int = 100,
        refill_rate: float = 10.0,  # Tokens per second
        tokens_needed: int = 1,
    ) -> RateLimitResult:
        """
        Check if request is allowed under token bucket limit.
        
        Args:
            identifier: Unique identifier
            capacity: Maximum bucket capacity
            refill_rate: Tokens added per second
            tokens_needed: Tokens required for this request
        
        Returns:
            RateLimitResult
        """
        now = time.time()
        
        with self._lock:
            if identifier in self._buckets:
                tokens, last_update = self._buckets[identifier]
                # Refill tokens based on elapsed time
                elapsed = now - last_update
                tokens = min(capacity, tokens + elapsed * refill_rate)
            else:
                tokens = capacity
            
            if tokens >= tokens_needed:
                # Allow request
                tokens -= tokens_needed
                self._buckets[identifier] = (tokens, now)
                
                return RateLimitResult(
                    allowed=True,
                    remaining=int(tokens),
                    reset_at=now + (capacity - tokens) / refill_rate,
                )
            else:
                # Not enough tokens
                wait_time = (tokens_needed - tokens) / refill_rate
                self._buckets[identifier] = (tokens, now)
                
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_at=now + wait_time,
                    retry_after=int(wait_time) + 1,
                )


# Global rate limiter instances
sliding_window_limiter = SlidingWindowRateLimiter()
token_bucket_limiter = TokenBucketRateLimiter()


def check_rate_limit(
    config: RateLimitConfig,
    ip_address: str = None,
    user_id: str = None,
    api_key: str = None,
    endpoint: str = None,
) -> RateLimitResult:
    """
    Check rate limit based on configuration scope.
    
    Args:
        config: Rate limit configuration
        ip_address: Client IP address
        user_id: Authenticated user ID
        api_key: API key (if using API key auth)
        endpoint: Request endpoint path
    
    Returns:
        RateLimitResult
    """
    # Determine identifier based on scope
    if config.scope == RateLimitScope.USER and user_id:
        identifier = user_id
    elif config.scope == RateLimitScope.API_KEY and api_key:
        identifier = hashlib.sha256(api_key.encode()).hexdigest()[:16]
    elif config.scope == RateLimitScope.ENDPOINT and endpoint:
        identifier = f"{ip_address or 'unknown'}:{endpoint}"
    elif config.scope == RateLimitScope.IP and ip_address:
        identifier = ip_address
    else:
        identifier = ip_address or "global"
    
    return sliding_window_limiter.check(config, identifier)


class LoginAttemptTracker:
    """
    Track failed login attempts for account lockout.
    """
    
    def __init__(
        self,
        max_attempts: int = 5,
        lockout_duration: int = 900,  # 15 minutes
    ):
        self.max_attempts = max_attempts
        self.lockout_duration = lockout_duration
        self._attempts: dict[str, list[float]] = defaultdict(list)
        self._lockouts: dict[str, float] = {}
        self._lock = threading.Lock()
    
    def record_failure(self, identifier: str) -> tuple[bool, int]:
        """
        Record a failed login attempt.
        
        Args:
            identifier: User identifier (email, username, IP)
        
        Returns:
            Tuple of (is_locked_out, remaining_attempts)
        """
        now = time.time()
        
        with self._lock:
            # Check if currently locked out
            if identifier in self._lockouts:
                if now < self._lockouts[identifier]:
                    return True, 0
                else:
                    # Lockout expired
                    del self._lockouts[identifier]
            
            # Clean old attempts
            window_start = now - self.lockout_duration
            self._attempts[identifier] = [
                ts for ts in self._attempts[identifier]
                if ts > window_start
            ]
            
            # Record this attempt
            self._attempts[identifier].append(now)
            attempt_count = len(self._attempts[identifier])
            
            if attempt_count >= self.max_attempts:
                # Lock out the account
                self._lockouts[identifier] = now + self.lockout_duration
                return True, 0
            
            return False, self.max_attempts - attempt_count
    
    def clear_attempts(self, identifier: str) -> None:
        """Clear failed attempts after successful login."""
        with self._lock:
            self._attempts.pop(identifier, None)
            self._lockouts.pop(identifier, None)
    
    def is_locked_out(self, identifier: str) -> tuple[bool, int]:
        """
        Check if identifier is locked out.
        
        Returns:
            Tuple of (is_locked, seconds_remaining)
        """
        now = time.time()
        
        with self._lock:
            if identifier in self._lockouts:
                remaining = self._lockouts[identifier] - now
                if remaining > 0:
                    return True, int(remaining)
                else:
                    del self._lockouts[identifier]
            
            return False, 0


# Global login attempt tracker
login_tracker = LoginAttemptTracker()
