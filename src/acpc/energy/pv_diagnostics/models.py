
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import hashlib, json, time


class PVEventType(str, Enum):
    PV_SAMPLE_RECEIVED = "PV_SAMPLE_RECEIVED"
    INVERTER_ALARM_RECEIVED = "INVERTER_ALARM_RECEIVED"
    THERMAL_SCAN_ATTACHED = "THERMAL_SCAN_ATTACHED"
    YIELD_DROP_DETECTED = "YIELD_DROP_DETECTED"
    PID_SUSPECTED = "PID_SUSPECTED"
    MPI_SUSPECTED = "MPI_SUSPECTED"
    DIAGNOSIS_CONFIRMED = "DIAGNOSIS_CONFIRMED"
    SERVICE_ACTION_RECOMMENDED = "SERVICE_ACTION_RECOMMENDED"


class PVState(str, Enum):
    IDLE = "idle"
    COLLECTING_DATA = "collecting_data"
    ANALYZING = "analyzing"
    WARNING = "warning"
    CRITICAL = "critical"
    RESOLVED = "resolved"


@dataclass(frozen=True)
class PVEvent:
    event_type: PVEventType
    payload: Dict[str, Any]
    site_id: str
    lamport: int = 0
    event_id: Optional[str] = None
    timestamp_ms: int = field(default_factory=lambda: int(time.time() * 1000))

    def stable_id(self) -> str:
        if self.event_id:
            return self.event_id
        raw = {
            "event_type": self.event_type.value,
            "payload": self.payload,
            "site_id": self.site_id,
            "lamport": self.lamport,
            "timestamp_ms": self.timestamp_ms,
        }
        return hashlib.sha256(json.dumps(raw, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


@dataclass
class Finding:
    id: str
    severity: str
    diagnosis: str
    recommendation: str
    evidence: Dict[str, Any]


@dataclass
class PVInstallationState:
    site_id: str
    status: PVState = PVState.IDLE
    processed_event_ids: set[str] = field(default_factory=set)
    lamport_clock: int = 0
    samples: List[Dict[str, Any]] = field(default_factory=list)
    inverter_alarms: List[Dict[str, Any]] = field(default_factory=list)
    thermal_scans: List[Dict[str, Any]] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    witness_log: List[Dict[str, Any]] = field(default_factory=list)

    def severity_rank(self) -> int:
        return {"idle": 0, "collecting_data": 1, "analyzing": 2, "warning": 3, "critical": 4, "resolved": 5}[self.status.value]
