"""
NeuroLens Quotas Service

Quota management and rate limiting service.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class QuotaType(str, Enum):
    """Quota types."""
    API_CALLS = "api_calls"
    INFERENCE_REQUESTS = "inference_requests"
    STORAGE_MB = "storage_mb"
    DATASETS = "datasets"
    MODELS = "models"
    BATCH_SIZE = "batch_size"


@dataclass
class QuotaLimit:
    """Quota limit configuration."""
    limit: int
    period_seconds: int = 0  # 0 = no period (absolute limit)
    current: int = 0
    reset_at: Optional[datetime] = None


@dataclass
class QuotaUsage:
    """Current quota usage."""
    quota_type: QuotaType
    used: int
    limit: int
    remaining: int
    reset_at: Optional[datetime] = None
    
    @property
    def is_exceeded(self) -> bool:
        return self.used >= self.limit and self.limit != -1


# In-memory storage
_user_quotas: dict[str, dict[QuotaType, QuotaLimit]] = {}
_org_quotas: dict[str, dict[QuotaType, QuotaLimit]] = {}


# Default limits by plan
DEFAULT_LIMITS = {
    "free": {
        QuotaType.API_CALLS: QuotaLimit(limit=1000, period_seconds=86400),  # 1000/day
        QuotaType.INFERENCE_REQUESTS: QuotaLimit(limit=100, period_seconds=3600),  # 100/hour
        QuotaType.STORAGE_MB: QuotaLimit(limit=10240),  # 10 GB
        QuotaType.DATASETS: QuotaLimit(limit=10),
        QuotaType.MODELS: QuotaLimit(limit=5),
        QuotaType.BATCH_SIZE: QuotaLimit(limit=10),
    },
    "pro": {
        QuotaType.API_CALLS: QuotaLimit(limit=100000, period_seconds=86400),  # 100k/day
        QuotaType.INFERENCE_REQUESTS: QuotaLimit(limit=1000, period_seconds=3600),  # 1000/hour
        QuotaType.STORAGE_MB: QuotaLimit(limit=102400),  # 100 GB
        QuotaType.DATASETS: QuotaLimit(limit=100),
        QuotaType.MODELS: QuotaLimit(limit=25),
        QuotaType.BATCH_SIZE: QuotaLimit(limit=100),
    },
    "enterprise": {
        QuotaType.API_CALLS: QuotaLimit(limit=-1),  # Unlimited
        QuotaType.INFERENCE_REQUESTS: QuotaLimit(limit=-1),
        QuotaType.STORAGE_MB: QuotaLimit(limit=-1),
        QuotaType.DATASETS: QuotaLimit(limit=-1),
        QuotaType.MODELS: QuotaLimit(limit=-1),
        QuotaType.BATCH_SIZE: QuotaLimit(limit=1000),
    },
}


class QuotaExceededError(Exception):
    """Quota exceeded error."""
    def __init__(self, quota_type: QuotaType, usage: QuotaUsage):
        self.quota_type = quota_type
        self.usage = usage
        super().__init__(f"Quota exceeded for {quota_type.value}: {usage.used}/{usage.limit}")


class QuotasService:
    """Quotas management service."""
    
    @staticmethod
    def get_default_limits(plan: str) -> dict[QuotaType, QuotaLimit]:
        """Get default limits for a plan."""
        return DEFAULT_LIMITS.get(plan, DEFAULT_LIMITS["free"]).copy()
    
    @staticmethod
    async def initialize_org_quotas(org_id: str, plan: str = "free") -> None:
        """Initialize quotas for an organization."""
        _org_quotas[org_id] = QuotasService.get_default_limits(plan)
    
    @staticmethod
    async def initialize_user_quotas(user_id: str) -> None:
        """Initialize quotas for a user."""
        _user_quotas[user_id] = {
            QuotaType.API_CALLS: QuotaLimit(limit=1000, period_seconds=86400),
        }
    
    @staticmethod
    async def get_usage(
        org_id: Optional[str] = None,
        user_id: Optional[str] = None,
        quota_type: Optional[QuotaType] = None,
    ) -> dict[QuotaType, QuotaUsage]:
        """
        Get quota usage.
        
        Args:
            org_id: Organization ID
            user_id: User ID
            quota_type: Specific quota type (or all if None)
            
        Returns:
            Dictionary of quota usage by type
        """
        if org_id:
            quotas = _org_quotas.get(org_id, {})
        elif user_id:
            quotas = _user_quotas.get(user_id, {})
        else:
            return {}
        
        result = {}
        for qt, limit in quotas.items():
            if quota_type and qt != quota_type:
                continue
            
            # Check if period reset needed
            if limit.period_seconds > 0 and limit.reset_at:
                if datetime.now(timezone.utc) >= limit.reset_at:
                    limit.current = 0
                    limit.reset_at = None
            
            result[qt] = QuotaUsage(
                quota_type=qt,
                used=limit.current,
                limit=limit.limit,
                remaining=max(0, limit.limit - limit.current) if limit.limit != -1 else -1,
                reset_at=limit.reset_at,
            )
        
        return result
    
    @staticmethod
    async def check_quota(
        org_id: Optional[str] = None,
        user_id: Optional[str] = None,
        quota_type: QuotaType = QuotaType.API_CALLS,
        amount: int = 1,
    ) -> bool:
        """
        Check if quota is available.
        
        Args:
            org_id: Organization ID
            user_id: User ID
            quota_type: Type of quota to check
            amount: Amount to check
            
        Returns:
            True if quota available
        """
        if org_id:
            quotas = _org_quotas.get(org_id, {})
        elif user_id:
            quotas = _user_quotas.get(user_id, {})
        else:
            return True
        
        limit = quotas.get(quota_type)
        if not limit:
            return True
        
        if limit.limit == -1:  # Unlimited
            return True
        
        # Check if period reset needed
        if limit.period_seconds > 0 and limit.reset_at:
            if datetime.now(timezone.utc) >= limit.reset_at:
                limit.current = 0
                limit.reset_at = None
        
        return limit.current + amount <= limit.limit
    
    @staticmethod
    async def consume_quota(
        org_id: Optional[str] = None,
        user_id: Optional[str] = None,
        quota_type: QuotaType = QuotaType.API_CALLS,
        amount: int = 1,
    ) -> QuotaUsage:
        """
        Consume quota.
        
        Args:
            org_id: Organization ID
            user_id: User ID
            quota_type: Type of quota to consume
            amount: Amount to consume
            
        Returns:
            Updated quota usage
            
        Raises:
            QuotaExceededError: If quota exceeded
        """
        if org_id:
            if org_id not in _org_quotas:
                await QuotasService.initialize_org_quotas(org_id)
            quotas = _org_quotas[org_id]
        elif user_id:
            if user_id not in _user_quotas:
                await QuotasService.initialize_user_quotas(user_id)
            quotas = _user_quotas[user_id]
        else:
            return QuotaUsage(
                quota_type=quota_type,
                used=0,
                limit=-1,
                remaining=-1,
            )
        
        limit = quotas.get(quota_type)
        if not limit:
            return QuotaUsage(
                quota_type=quota_type,
                used=0,
                limit=-1,
                remaining=-1,
            )
        
        # Check if period reset needed
        if limit.period_seconds > 0:
            if limit.reset_at is None or datetime.now(timezone.utc) >= limit.reset_at:
                limit.current = 0
                from datetime import timedelta
                limit.reset_at = datetime.now(timezone.utc) + timedelta(seconds=limit.period_seconds)
        
        # Check limit
        if limit.limit != -1 and limit.current + amount > limit.limit:
            usage = QuotaUsage(
                quota_type=quota_type,
                used=limit.current,
                limit=limit.limit,
                remaining=0,
                reset_at=limit.reset_at,
            )
            raise QuotaExceededError(quota_type, usage)
        
        # Consume
        limit.current += amount
        
        return QuotaUsage(
            quota_type=quota_type,
            used=limit.current,
            limit=limit.limit,
            remaining=max(0, limit.limit - limit.current) if limit.limit != -1 else -1,
            reset_at=limit.reset_at,
        )
    
    @staticmethod
    async def reset_quota(
        org_id: Optional[str] = None,
        user_id: Optional[str] = None,
        quota_type: Optional[QuotaType] = None,
    ) -> None:
        """Reset quota usage."""
        if org_id:
            quotas = _org_quotas.get(org_id, {})
        elif user_id:
            quotas = _user_quotas.get(user_id, {})
        else:
            return
        
        for qt, limit in quotas.items():
            if quota_type is None or qt == quota_type:
                limit.current = 0
                limit.reset_at = None
    
    @staticmethod
    async def update_limit(
        org_id: Optional[str] = None,
        user_id: Optional[str] = None,
        quota_type: QuotaType = QuotaType.API_CALLS,
        new_limit: int = -1,
    ) -> None:
        """Update quota limit."""
        if org_id:
            if org_id not in _org_quotas:
                await QuotasService.initialize_org_quotas(org_id)
            quotas = _org_quotas[org_id]
        elif user_id:
            if user_id not in _user_quotas:
                await QuotasService.initialize_user_quotas(user_id)
            quotas = _user_quotas[user_id]
        else:
            return
        
        if quota_type in quotas:
            quotas[quota_type].limit = new_limit


# Singleton instance
quotas_service = QuotasService()
