from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class MonitorState(str, Enum):
    STABLE = "stable"
    OBSERVATION = "observation"
    DEGRADED = "degraded"
    UNSTABLE = "unstable"
    CRITICAL = "critical"
    ISOLATED = "isolated"
    RECOVERY = "recovery"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    FORENSIC = "forensic"


class MonitorEventType(str, Enum):
    TELEMETRY_RECEIVED = "TELEMETRY_RECEIVED"
    RUNTIME_DRIFT_DETECTED = "RUNTIME_DRIFT_DETECTED"
    ECONOMIC_ANOMALY = "ECONOMIC_ANOMALY"
    AI_CONTRADICTION = "AI_CONTRADICTION"
    PHASE_IMBALANCE = "PHASE_IMBALANCE"
    ENERGY_WASTE_ALERT = "ENERGY_WASTE_ALERT"
    SYSTEM_RECOVERY_STARTED = "SYSTEM_RECOVERY_STARTED"
    SYSTEM_RECOVERY_COMPLETED = "SYSTEM_RECOVERY_COMPLETED"
    EMERGENCY_LOCK = "EMERGENCY_LOCK"


@dataclass(frozen=True)
class TelemetrySnapshot:
    inverter_power: float = 0.0
    grid_import: float = 0.0
    grid_export: float = 0.0
    battery_soc: float = 0.0
    phase_balance: dict[str, float] = field(default_factory=dict)
    voltage: float = 0.0
    current: float = 0.0
    temperature: float = 0.0


@dataclass(frozen=True)
class RuntimeSnapshot:
    event_latency: float = 0.0
    queue_depth: int = 0
    api_response_time: float = 0.0
    retry_cycles: int = 0
    watchdog_alerts: int = 0
    unexpected_events: int = 0
    total_events: int = 1
    subsystem_failure_detected: bool = False
    recovery_successful: bool = False


@dataclass(frozen=True)
class AiLayerSnapshot:
    stable_decisions: int = 1
    total_decisions: int = 1
    prediction_accuracy: float = 1.0
    recursive_loops: int = 0
    confidence_score: float = 1.0
    contradiction_events: int = 0
    total_predictions: int = 1
    repeated_decisions: int = 0
    no_state_change: bool = False


@dataclass(frozen=True)
class EconomicsSnapshot:
    tariff_window: str = "standard"
    energy_price: float = 0.0
    import_cost: float = 0.0
    export_value: float = 0.0
    optimization_delta_pln: float = 0.0
    expected_cost: float = 0.0
    actual_cost: float = 0.0
    expected_yield: float = 0.0
    real_yield: float = 0.0


@dataclass(frozen=True)
class EnvironmentalSnapshot:
    weather: str = "unknown"
    irradiance: float = 0.0
    humidity: float = 0.0
    ambient_temperature: float = 0.0
    outside_temp_stable: bool = False
    cop_drop: float = 0.0


@dataclass(frozen=True)
class MonitorSnapshot:
    telemetry: TelemetrySnapshot
    runtime: RuntimeSnapshot
    ai_layer: AiLayerSnapshot
    economics: EconomicsSnapshot
    environmental: EnvironmentalSnapshot
    snapshot_id: str = field(default_factory=lambda: str(uuid4()))
    captured_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "captured_at": self.captured_at,
            "telemetry": self.telemetry.__dict__,
            "runtime": self.runtime.__dict__,
            "ai_layer": self.ai_layer.__dict__,
            "economics": self.economics.__dict__,
            "environmental": self.environmental.__dict__,
        }


@dataclass(frozen=True)
class DiagnosticFinding:
    rule_id: str
    risk: Severity
    actions: list[str]
    evidence: dict[str, Any]
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "risk": self.risk.value,
            "actions": list(self.actions),
            "evidence": self.evidence,
            "explanation": self.explanation,
        }
