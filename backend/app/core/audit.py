"""
NeuroLens Audit Logging Module

Tamper-resistant audit logging for security events and compliance.
Logs authentication, authorization, and data access events.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass, field, asdict
from collections import deque
import threading


class AuditEventType(str, Enum):
    """Audit event types."""
    
    # Authentication Events
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILURE = "auth.login.failure"
    AUTH_LOGOUT = "auth.logout"
    AUTH_TOKEN_REFRESH = "auth.token.refresh"
    AUTH_TOKEN_REVOKED = "auth.token.revoked"
    AUTH_PASSWORD_CHANGE = "auth.password.change"
    AUTH_PASSWORD_RESET_REQUEST = "auth.password.reset_request"
    AUTH_MFA_ENABLED = "auth.mfa.enabled"
    AUTH_MFA_DISABLED = "auth.mfa.disabled"
    
    # Authorization Events
    AUTHZ_PERMISSION_GRANTED = "authz.permission.granted"
    AUTHZ_PERMISSION_DENIED = "authz.permission.denied"
    AUTHZ_ROLE_ASSIGNED = "authz.role.assigned"
    AUTHZ_ROLE_REVOKED = "authz.role.revoked"
    
    # User Events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_LOCKED = "user.locked"
    USER_UNLOCKED = "user.unlocked"
    
    # Organization Events
    ORG_CREATED = "org.created"
    ORG_UPDATED = "org.updated"
    ORG_DELETED = "org.deleted"
    ORG_MEMBER_ADDED = "org.member.added"
    ORG_MEMBER_REMOVED = "org.member.removed"
    
    # Data Events
    DATASET_CREATED = "dataset.created"
    DATASET_ACCESSED = "dataset.accessed"
    DATASET_UPDATED = "dataset.updated"
    DATASET_DELETED = "dataset.deleted"
    
    # Model Events
    MODEL_CREATED = "model.created"
    MODEL_DEPLOYED = "model.deployed"
    MODEL_PROMOTED = "model.promoted"
    MODEL_RETIRED = "model.retired"
    
    # Inference Events
    INFERENCE_REQUEST = "inference.request"
    INFERENCE_BATCH = "inference.batch"
    
    # Admin Events
    ADMIN_CONFIG_CHANGE = "admin.config.change"
    ADMIN_SYSTEM_ACCESS = "admin.system.access"
    
    # Security Events
    SECURITY_SUSPICIOUS_ACTIVITY = "security.suspicious_activity"
    SECURITY_RATE_LIMIT_EXCEEDED = "security.rate_limit.exceeded"
    SECURITY_INVALID_TOKEN = "security.invalid_token"


class AuditSeverity(str, Enum):
    """Audit event severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Immutable audit event record."""
    
    id: str
    timestamp: datetime
    event_type: AuditEventType
    severity: AuditSeverity
    actor_id: Optional[str]  # User who performed the action
    actor_type: str  # "user", "system", "api_key"
    resource_type: Optional[str]  # e.g., "user", "dataset", "model"
    resource_id: Optional[str]
    action: str  # Human-readable action description
    outcome: str  # "success" or "failure"
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]
    trace_id: Optional[str]
    metadata: dict[str, Any] = field(default_factory=dict)
    org_id: Optional[str] = None
    previous_hash: Optional[str] = None  # For chain integrity
    event_hash: Optional[str] = None  # Hash of this event
    
    def __post_init__(self):
        if self.event_hash is None:
            self.event_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute hash for tamper detection."""
        data = {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "actor_id": self.actor_id,
            "resource_id": self.resource_id,
            "action": self.action,
            "outcome": self.outcome,
            "previous_hash": self.previous_hash,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "outcome": self.outcome,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "metadata": self.metadata,
            "org_id": self.org_id,
            "event_hash": self.event_hash,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class AuditLogger:
    """
    Centralized audit logger for security events.
    
    Features:
    - Tamper-resistant event chain
    - Async-safe event logging
    - Multiple output backends
    """
    
    def __init__(self, max_buffer_size: int = 10000):
        self._events: deque = deque(maxlen=max_buffer_size)
        self._last_hash: Optional[str] = None
        self._lock = threading.Lock()
        self._handlers: list = []
    
    def log(
        self,
        event_type: AuditEventType,
        action: str,
        outcome: str = "success",
        actor_id: Optional[str] = None,
        actor_type: str = "user",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        org_id: Optional[str] = None,
        metadata: dict[str, Any] = None,
    ) -> AuditEvent:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            action: Human-readable action description
            outcome: "success" or "failure"
            actor_id: ID of user/system performing action
            actor_type: Type of actor
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            severity: Event severity level
            ip_address: Client IP address
            user_agent: Client user agent
            request_id: Request correlation ID
            trace_id: Distributed trace ID
            org_id: Organization ID
            metadata: Additional event data
        
        Returns:
            Created AuditEvent
        """
        with self._lock:
            event = AuditEvent(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc),
                event_type=event_type,
                severity=severity,
                actor_id=actor_id,
                actor_type=actor_type,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                outcome=outcome,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                trace_id=trace_id,
                org_id=org_id,
                metadata=metadata or {},
                previous_hash=self._last_hash,
            )
            
            self._events.append(event)
            self._last_hash = event.event_hash
            
            # Dispatch to handlers
            for handler in self._handlers:
                try:
                    handler(event)
                except Exception:
                    pass  # Don't let handler errors affect logging
            
            return event
    
    def add_handler(self, handler) -> None:
        """Add an event handler."""
        self._handlers.append(handler)
    
    def get_events(
        self,
        event_type: AuditEventType = None,
        actor_id: str = None,
        resource_id: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """
        Query audit events with filters.
        """
        with self._lock:
            events = list(self._events)
        
        # Apply filters
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if actor_id:
            events = [e for e in events if e.actor_id == actor_id]
        if resource_id:
            events = [e for e in events if e.resource_id == resource_id]
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]
        
        # Sort by timestamp descending
        events.sort(key=lambda e: e.timestamp, reverse=True)
        
        return events[:limit]
    
    def verify_chain_integrity(self) -> tuple[bool, Optional[str]]:
        """
        Verify the integrity of the audit event chain.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        with self._lock:
            events = list(self._events)
        
        if not events:
            return True, None
        
        expected_prev_hash = None
        for event in events:
            if event.previous_hash != expected_prev_hash:
                return False, f"Chain broken at event {event.id}"
            
            computed_hash = event._compute_hash()
            if computed_hash != event.event_hash:
                return False, f"Hash mismatch at event {event.id}"
            
            expected_prev_hash = event.event_hash
        
        return True, None
    
    def export_events(self, format: str = "json") -> str:
        """Export all events in specified format."""
        with self._lock:
            events = [e.to_dict() for e in self._events]
        
        if format == "json":
            return json.dumps(events, indent=2)
        elif format == "ndjson":
            return "\n".join(json.dumps(e) for e in events)
        else:
            raise ValueError(f"Unsupported format: {format}")


# Global audit logger instance
audit_logger = AuditLogger()


# Convenience functions for common audit events

def log_auth_success(
    user_id: str,
    ip_address: str = None,
    user_agent: str = None,
    request_id: str = None,
) -> AuditEvent:
    """Log successful authentication."""
    return audit_logger.log(
        event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
        action="User logged in successfully",
        actor_id=user_id,
        resource_type="user",
        resource_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
    )


def log_auth_failure(
    identifier: str,
    reason: str,
    ip_address: str = None,
    user_agent: str = None,
    request_id: str = None,
) -> AuditEvent:
    """Log failed authentication attempt."""
    return audit_logger.log(
        event_type=AuditEventType.AUTH_LOGIN_FAILURE,
        action=f"Authentication failed: {reason}",
        outcome="failure",
        actor_id=identifier,
        actor_type="unknown",
        severity=AuditSeverity.WARNING,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
        metadata={"reason": reason},
    )


def log_permission_denied(
    user_id: str,
    permission: str,
    resource_type: str = None,
    resource_id: str = None,
    request_id: str = None,
) -> AuditEvent:
    """Log permission denied event."""
    return audit_logger.log(
        event_type=AuditEventType.AUTHZ_PERMISSION_DENIED,
        action=f"Permission denied: {permission}",
        outcome="failure",
        actor_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        severity=AuditSeverity.WARNING,
        request_id=request_id,
        metadata={"required_permission": permission},
    )


def log_data_access(
    user_id: str,
    resource_type: str,
    resource_id: str,
    action: str = "accessed",
    org_id: str = None,
    request_id: str = None,
) -> AuditEvent:
    """Log data access event."""
    return audit_logger.log(
        event_type=AuditEventType.DATASET_ACCESSED,
        action=f"{resource_type} {action}",
        actor_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        org_id=org_id,
        request_id=request_id,
    )


def log_admin_action(
    admin_id: str,
    action: str,
    target_type: str = None,
    target_id: str = None,
    metadata: dict = None,
    request_id: str = None,
) -> AuditEvent:
    """Log administrative action."""
    return audit_logger.log(
        event_type=AuditEventType.ADMIN_SYSTEM_ACCESS,
        action=action,
        actor_id=admin_id,
        resource_type=target_type,
        resource_id=target_id,
        severity=AuditSeverity.INFO,
        metadata=metadata or {},
        request_id=request_id,
    )


def log_security_event(
    event_type: AuditEventType,
    description: str,
    actor_id: str = None,
    ip_address: str = None,
    metadata: dict = None,
    request_id: str = None,
) -> AuditEvent:
    """Log security-related event."""
    return audit_logger.log(
        event_type=event_type,
        action=description,
        severity=AuditSeverity.WARNING,
        actor_id=actor_id,
        actor_type="system" if actor_id is None else "user",
        ip_address=ip_address,
        metadata=metadata or {},
        request_id=request_id,
    )
