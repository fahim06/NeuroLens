"""
Retraining Triggers.

Automated triggers for initiating model retraining.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """Type of retraining trigger."""
    
    DATA_VERSION = "data_version"
    DRIFT_DETECTED = "drift_detected"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    PERFORMANCE_DEGRADATION = "performance_degradation"


class TriggerPriority(Enum):
    """Priority level for triggered retraining."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TriggerEvent:
    """Event representing a retraining trigger."""
    
    trigger_type: TriggerType
    priority: TriggerPriority
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    acknowledged: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trigger_type": self.trigger_type.value,
            "priority": self.priority.value,
            "reason": self.reason,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "acknowledged": self.acknowledged,
        }


class RetrainingTrigger(ABC):
    """Abstract base class for retraining triggers."""
    
    def __init__(
        self,
        name: str,
        priority: TriggerPriority = TriggerPriority.MEDIUM,
        enabled: bool = True,
    ):
        self.name = name
        self.priority = priority
        self.enabled = enabled
    
    @abstractmethod
    def check(self, context: dict[str, Any]) -> TriggerEvent | None:
        """Check if trigger condition is met."""
        pass


class DataVersionTrigger(RetrainingTrigger):
    """Trigger when a new dataset version is available."""
    
    def __init__(
        self,
        priority: TriggerPriority = TriggerPriority.MEDIUM,
    ):
        super().__init__("data_version", priority)
        self._last_known_hash: str | None = None
    
    def check(self, context: dict[str, Any]) -> TriggerEvent | None:
        """Check if dataset version has changed."""
        if not self.enabled:
            return None
        
        current_hash = context.get("data_hash")
        previous_hash = context.get("previous_data_hash") or self._last_known_hash
        
        if current_hash and previous_hash and current_hash != previous_hash:
            self._last_known_hash = current_hash
            return TriggerEvent(
                trigger_type=TriggerType.DATA_VERSION,
                priority=self.priority,
                reason="New dataset version detected",
                metadata={
                    "previous_hash": previous_hash[:16] + "...",
                    "current_hash": current_hash[:16] + "...",
                },
            )
        
        self._last_known_hash = current_hash
        return None


class DriftTrigger(RetrainingTrigger):
    """Trigger when data drift is detected."""
    
    def __init__(
        self,
        drift_threshold: float = 0.1,
        priority: TriggerPriority = TriggerPriority.HIGH,
    ):
        super().__init__("drift_detection", priority)
        self.drift_threshold = drift_threshold
    
    def check(self, context: dict[str, Any]) -> TriggerEvent | None:
        """Check if drift exceeds threshold."""
        if not self.enabled:
            return None
        
        drift_report = context.get("drift_report", {})
        drift_score = drift_report.get("overall_drift_score", 0.0)
        drifted_features = drift_report.get("drifted_features", [])
        
        if drift_score > self.drift_threshold:
            return TriggerEvent(
                trigger_type=TriggerType.DRIFT_DETECTED,
                priority=self.priority,
                reason=f"Data drift detected (score: {drift_score:.3f})",
                metadata={
                    "drift_score": drift_score,
                    "threshold": self.drift_threshold,
                    "drifted_features": drifted_features,
                },
            )
        
        return None


class ScheduledTrigger(RetrainingTrigger):
    """Trigger on a schedule (e.g., weekly)."""
    
    def __init__(
        self,
        interval_days: int = 7,
        priority: TriggerPriority = TriggerPriority.LOW,
    ):
        super().__init__("scheduled", priority)
        self.interval_days = interval_days
        self._last_trigger: datetime | None = None
    
    def check(self, context: dict[str, Any]) -> TriggerEvent | None:
        """Check if scheduled retraining is due."""
        if not self.enabled:
            return None
        
        now = datetime.now()
        
        # Get last training time from context or state
        last_training_str = context.get("last_training_time")
        if last_training_str:
            try:
                last_training = datetime.fromisoformat(last_training_str)
            except ValueError:
                last_training = self._last_trigger or now - timedelta(days=self.interval_days + 1)
        else:
            last_training = self._last_trigger or now - timedelta(days=self.interval_days + 1)
        
        days_since = (now - last_training).days
        
        if days_since >= self.interval_days:
            self._last_trigger = now
            return TriggerEvent(
                trigger_type=TriggerType.SCHEDULED,
                priority=self.priority,
                reason=f"Scheduled retraining ({days_since} days since last)",
                metadata={
                    "interval_days": self.interval_days,
                    "days_since_last": days_since,
                    "last_training": last_training.isoformat(),
                },
            )
        
        return None


class ManualTrigger(RetrainingTrigger):
    """Trigger for manual retraining requests."""
    
    def __init__(
        self,
        priority: TriggerPriority = TriggerPriority.HIGH,
    ):
        super().__init__("manual", priority)
    
    def check(self, context: dict[str, Any]) -> TriggerEvent | None:
        """Check for manual trigger request."""
        if not self.enabled:
            return None
        
        manual_trigger = context.get("manual_trigger", False)
        trigger_reason = context.get("trigger_reason", "Manual request")
        requester = context.get("requester", "unknown")
        
        if manual_trigger:
            return TriggerEvent(
                trigger_type=TriggerType.MANUAL,
                priority=self.priority,
                reason=trigger_reason,
                metadata={
                    "requester": requester,
                    "request_time": datetime.now().isoformat(),
                },
            )
        
        return None


class PerformanceDegradationTrigger(RetrainingTrigger):
    """Trigger when model performance degrades."""
    
    def __init__(
        self,
        baseline_metrics: dict[str, float],
        degradation_threshold: float = 0.10,
        priority: TriggerPriority = TriggerPriority.CRITICAL,
    ):
        super().__init__("performance_degradation", priority)
        self.baseline_metrics = baseline_metrics
        self.degradation_threshold = degradation_threshold
    
    def check(self, context: dict[str, Any]) -> TriggerEvent | None:
        """Check if performance has degraded significantly."""
        if not self.enabled:
            return None
        
        current_metrics = context.get("current_metrics", {})
        
        degradations = []
        for metric, baseline in self.baseline_metrics.items():
            current = current_metrics.get(metric)
            if current is None:
                continue
            
            degradation = (baseline - current) / baseline
            if degradation > self.degradation_threshold:
                degradations.append({
                    "metric": metric,
                    "baseline": baseline,
                    "current": current,
                    "degradation": f"{degradation * 100:.1f}%",
                })
        
        if degradations:
            return TriggerEvent(
                trigger_type=TriggerType.PERFORMANCE_DEGRADATION,
                priority=self.priority,
                reason=f"Performance degradation detected in {len(degradations)} metrics",
                metadata={
                    "degradations": degradations,
                    "threshold": f"{self.degradation_threshold * 100}%",
                },
            )
        
        return None


@dataclass
class TriggerManager:
    """Manager for retraining triggers."""
    
    triggers: list[RetrainingTrigger] = field(default_factory=list)
    event_log: list[TriggerEvent] = field(default_factory=list)
    callbacks: list[Callable[[TriggerEvent], None]] = field(default_factory=list)
    max_log_size: int = 1000
    
    def add_trigger(self, trigger: RetrainingTrigger) -> "TriggerManager":
        """Add a trigger to the manager."""
        self.triggers.append(trigger)
        return self
    
    def add_callback(self, callback: Callable[[TriggerEvent], None]) -> "TriggerManager":
        """Add a callback to be invoked when triggers fire."""
        self.callbacks.append(callback)
        return self
    
    def check_all(self, context: dict[str, Any]) -> list[TriggerEvent]:
        """Check all triggers and return fired events."""
        fired_events = []
        
        for trigger in self.triggers:
            try:
                event = trigger.check(context)
                if event:
                    fired_events.append(event)
                    self._log_event(event)
                    self._invoke_callbacks(event)
                    
            except Exception as e:
                logger.error(f"Trigger {trigger.name} failed: {e}")
        
        # Sort by priority (critical first)
        priority_order = {
            TriggerPriority.CRITICAL: 0,
            TriggerPriority.HIGH: 1,
            TriggerPriority.MEDIUM: 2,
            TriggerPriority.LOW: 3,
        }
        fired_events.sort(key=lambda e: priority_order[e.priority])
        
        return fired_events
    
    def _log_event(self, event: TriggerEvent) -> None:
        """Log a trigger event."""
        self.event_log.append(event)
        
        # Trim log if too large
        if len(self.event_log) > self.max_log_size:
            self.event_log = self.event_log[-self.max_log_size:]
    
    def _invoke_callbacks(self, event: TriggerEvent) -> None:
        """Invoke registered callbacks."""
        for callback in self.callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Callback failed: {e}")
    
    def get_pending_events(self) -> list[TriggerEvent]:
        """Get unacknowledged events."""
        return [e for e in self.event_log if not e.acknowledged]
    
    def acknowledge_event(self, timestamp: str) -> bool:
        """Acknowledge an event by timestamp."""
        for event in self.event_log:
            if event.timestamp == timestamp:
                event.acknowledged = True
                return True
        return False
    
    def save_log(self, path: Path | str) -> None:
        """Save event log to file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            json.dump(
                [e.to_dict() for e in self.event_log],
                f,
                indent=2,
            )
    
    def load_log(self, path: Path | str) -> None:
        """Load event log from file."""
        path = Path(path)
        if not path.exists():
            return
        
        with open(path) as f:
            events_data = json.load(f)
        
        self.event_log = [
            TriggerEvent(
                trigger_type=TriggerType(e["trigger_type"]),
                priority=TriggerPriority(e["priority"]),
                reason=e["reason"],
                metadata=e.get("metadata", {}),
                timestamp=e["timestamp"],
                acknowledged=e.get("acknowledged", False),
            )
            for e in events_data
        ]


def create_default_trigger_manager() -> TriggerManager:
    """Create the default trigger manager with standard triggers."""
    return TriggerManager(
        triggers=[
            DataVersionTrigger(),
            DriftTrigger(drift_threshold=0.1),
            ScheduledTrigger(interval_days=7),
            ManualTrigger(),
            PerformanceDegradationTrigger(
                baseline_metrics={
                    "accuracy": 0.90,
                    "f1_score": 0.88,
                },
                degradation_threshold=0.10,
            ),
        ]
    )
