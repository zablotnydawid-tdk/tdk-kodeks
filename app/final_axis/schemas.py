from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class EventSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class EventDomain(str, Enum):
    PV = "pv"
    EMS = "ems"
    AI_GOVERNANCE = "ai_governance"
    CYBER_PHYSICAL = "cyber_physical"
    OPERATOR = "operator"


class EventType(str, Enum):
    TELEMETRY = "telemetry"
    COMMAND_REQUEST = "command_request"
    DRIFT_DETECTED = "drift_detected"
    CONFINEMENT_TRIGGERED = "confinement_triggered"
    OVERRIDE_REQUESTED = "override_requested"
    OVERRIDE_APPLIED = "override_applied"
    STATE_CHANGED = "state_changed"
    DECISION = "decision"


@dataclass(frozen=True)
class SystemEvent:
    event_type: EventType
    domain: EventDomain
    severity: EventSeverity
    source: str
    payload: dict[str, Any]
    trace_id: str = field(default_factory=lambda: str(uuid4()))
    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    operator_override_supported: bool = False
    explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "trace_id": self.trace_id,
            "occurred_at": self.occurred_at,
            "event_type": self.event_type.value,
            "domain": self.domain.value,
            "severity": self.severity.value,
            "source": self.source,
            "payload": self.payload,
            "operator_override_supported": self.operator_override_supported,
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class RuntimeDecision:
    decision: str
    reason: str
    trace_id: str
    event_id: str
    action: str
    autonomous_action: bool = False
    operator_override_supported: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "reason": self.reason,
            "trace_id": self.trace_id,
            "event_id": self.event_id,
            "action": self.action,
            "autonomous_action": self.autonomous_action,
            "operator_override_supported": self.operator_override_supported,
        }
