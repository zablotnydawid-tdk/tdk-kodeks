from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class MonitorState(str, Enum):
    STABLE = "stable"
    OBSERVATION = "observation"
    DEGRADED = "degraded"
    UNSTABLE = "unstable"
    CRITICAL = "critical"
    ISOLATED = "isolated"
    RECOVERY = "recovery"


@dataclass(frozen=True)
class DiagnosticEvent:
    rule_id: str
    risk_level: RiskLevel
    evidence: dict[str, Any]
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["risk_level"] = self.risk_level.value
        return payload


@dataclass(frozen=True)
class DriftEnergyAnalysis:
    generated_at: str
    state_before: str
    state_after: str
    risk_level: str
    metrics: dict[str, float]
    metric_risks: dict[str, str]
    diagnostic_events: list[dict[str, Any]]
    compatibility: dict[str, bool]
    operator_action: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DriftEnergyMonitor:
    """DRIFT_ENERGY_MONITOR.SYS isolated observability runtime.

    The monitor computes diagnostic facts only. It does not remediate,
    schedule work, mutate external systems, or make autonomous operator
    decisions.
    """

    compatibility = {
        "final_axis_observability": True,
        "rollback_support": True,
        "degraded_mode_supported": True,
    }

    def __init__(self, initial_state: MonitorState = MonitorState.STABLE) -> None:
        self.state = initial_state

    def analyze(self, event: dict[str, Any]) -> DriftEnergyAnalysis:
        metrics = calculate_metrics(event)
        metric_risks = classify_metrics(metrics)
        diagnostic_events = evaluate_diagnostic_rules(event)
        risk_level = aggregate_risk(metric_risks, diagnostic_events)

        before = self.state
        after = transition_state(before, metrics, event)
        self.state = after

        return DriftEnergyAnalysis(
            generated_at=datetime.now(timezone.utc).isoformat(),
            state_before=before.value,
            state_after=after.value,
            risk_level=risk_level.value,
            metrics=metrics,
            metric_risks={key: value.value for key, value in metric_risks.items()},
            diagnostic_events=[item.to_dict() for item in diagnostic_events],
            compatibility=dict(self.compatibility),
            operator_action="none; diagnostic export only",
        )

    def export_json(self, analysis: DriftEnergyAnalysis) -> str:
        return json.dumps(analysis.to_dict(), indent=2, sort_keys=True)

    def export_markdown(self, analysis: DriftEnergyAnalysis) -> str:
        events = analysis.diagnostic_events
        event_lines = "\n".join(
            f"- {event['rule_id']}: {event['risk_level']} - {event['recommendation']}"
            for event in events
        )
        if not event_lines:
            event_lines = "- none"

        metric_lines = "\n".join(
            f"- {name}: {value} ({analysis.metric_risks[name]})"
            for name, value in analysis.metrics.items()
        )

        compatibility_lines = "\n".join(
            f"- {name}: {str(enabled).lower()}"
            for name, enabled in analysis.compatibility.items()
        )

        return (
            "# DRIFT_ENERGY_MONITOR.SYS Report\n\n"
            f"Generated: {analysis.generated_at}\n\n"
            "## Runtime State\n\n"
            f"- before: {analysis.state_before}\n"
            f"- after: {analysis.state_after}\n"
            f"- risk_level: {analysis.risk_level}\n"
            f"- operator_action: {analysis.operator_action}\n\n"
            "## Metrics\n\n"
            f"{metric_lines}\n\n"
            "## Diagnostic Events\n\n"
            f"{event_lines}\n\n"
            "## FINAL_AXIS Compatibility\n\n"
            f"{compatibility_lines}\n"
        )


def calculate_metrics(event: dict[str, Any]) -> dict[str, float]:
    runtime = event.get("runtime", {})
    ai_layer = event.get("ai_layer", {})
    economics = event.get("economics", {})

    coherence_index = _percent(
        ai_layer.get("stable_decisions", 0),
        ai_layer.get("total_decisions", 0),
    )
    runtime_entropy = _ratio(
        runtime.get("unexpected_events", 0),
        runtime.get("total_events", 0),
    )
    energy_loss_factor = (
        economics.get("expected_yield", 0.0) - economics.get("real_yield", 0.0)
    )
    economic_drift = (
        economics.get("actual_cost", 0.0) - economics.get("expected_cost", 0.0)
    )
    ai_conflict_ratio = _ratio(
        ai_layer.get("contradiction_events", 0),
        ai_layer.get("total_predictions", 0),
    )

    return {
        "coherence_index": round(coherence_index, 4),
        "runtime_entropy": round(runtime_entropy, 4),
        "energy_loss_factor": round(energy_loss_factor, 4),
        "economic_drift": round(economic_drift, 4),
        "ai_conflict_ratio": round(ai_conflict_ratio, 4),
    }


def classify_metrics(metrics: dict[str, float]) -> dict[str, RiskLevel]:
    return {
        "coherence_index": _low_is_bad(
            metrics["coherence_index"], warning=85.0, critical=60.0
        ),
        "runtime_entropy": _high_is_bad(
            metrics["runtime_entropy"], warning=0.15, critical=0.35
        ),
        "energy_loss_factor": _high_is_bad(
            metrics["energy_loss_factor"], warning=8.0, critical=20.0
        ),
        "economic_drift": _high_is_bad(
            metrics["economic_drift"], warning=50.0, critical=300.0
        ),
        "ai_conflict_ratio": _high_is_bad(
            metrics["ai_conflict_ratio"], warning=0.10, critical=0.25
        ),
    }


def evaluate_diagnostic_rules(event: dict[str, Any]) -> list[DiagnosticEvent]:
    telemetry = event.get("telemetry", {})
    ai_layer = event.get("ai_layer", {})
    environmental = event.get("environmental", {})
    diagnostics = event.get("diagnostics", {})
    events: list[DiagnosticEvent] = []

    if (
        diagnostics.get("pv_surplus_active") is True
        and diagnostics.get("battery_charging_from_grid") is True
    ):
        events.append(
            DiagnosticEvent(
                rule_id="EMS_GRID_CHARGE_CONFLICT",
                risk_level=RiskLevel.HIGH,
                evidence={
                    "pv_surplus_active": True,
                    "battery_charging_from_grid": True,
                },
                recommendation="notify operator; inspect EMS charging policy",
            )
        )

    if (
        environmental.get("outside_temp_stable") is True
        and environmental.get("cop_drop_percent", 0.0) > 20.0
    ):
        events.append(
            DiagnosticEvent(
                rule_id="COP_RUNTIME_DRIFT",
                risk_level=RiskLevel.MEDIUM,
                evidence={
                    "outside_temp_stable": True,
                    "cop_drop_percent": environmental.get("cop_drop_percent", 0.0),
                },
                recommendation="compare heat pump flow temperature and efficiency",
            )
        )

    if telemetry.get("phase_difference", 0.0) > telemetry.get(
        "phase_difference_threshold", 0.0
    ):
        events.append(
            DiagnosticEvent(
                rule_id="PHASE_IMBALANCE_CRITICAL",
                risk_level=RiskLevel.CRITICAL,
                evidence={
                    "phase_difference": telemetry.get("phase_difference", 0.0),
                    "phase_difference_threshold": telemetry.get(
                        "phase_difference_threshold", 0.0
                    ),
                },
                recommendation="notify operator; enable manual safety review",
            )
        )

    if (
        ai_layer.get("repeated_decisions", 0) > 5
        and ai_layer.get("no_state_change") is True
    ):
        events.append(
            DiagnosticEvent(
                rule_id="AI_RECURSIVE_DECISION_LOOP",
                risk_level=RiskLevel.HIGH,
                evidence={
                    "repeated_decisions": ai_layer.get("repeated_decisions", 0),
                    "no_state_change": True,
                },
                recommendation="flag autonomous AI action path; request operator review",
            )
        )

    return events


def aggregate_risk(
    metric_risks: dict[str, RiskLevel], diagnostic_events: list[DiagnosticEvent]
) -> RiskLevel:
    ordered = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
    risks = list(metric_risks.values()) + [event.risk_level for event in diagnostic_events]
    return max(risks or [RiskLevel.LOW], key=ordered.index)


def transition_state(
    current: MonitorState, metrics: dict[str, float], event: dict[str, Any]
) -> MonitorState:
    runtime = event.get("runtime", {})

    if current == MonitorState.STABLE and metrics["runtime_entropy"] > 0.15:
        return MonitorState.OBSERVATION
    if current == MonitorState.OBSERVATION and metrics["coherence_index"] < 85.0:
        return MonitorState.DEGRADED
    if current == MonitorState.DEGRADED and metrics["energy_loss_factor"] > 20.0:
        return MonitorState.UNSTABLE
    if current == MonitorState.UNSTABLE and metrics["ai_conflict_ratio"] > 0.25:
        return MonitorState.CRITICAL
    if (
        current == MonitorState.CRITICAL
        and runtime.get("subsystem_failure_detected") is True
    ):
        return MonitorState.ISOLATED
    if current == MonitorState.ISOLATED and runtime.get("recovery_successful") is True:
        return MonitorState.RECOVERY
    if current == MonitorState.RECOVERY and metrics_normalized(metrics):
        return MonitorState.STABLE
    return current


def metrics_normalized(metrics: dict[str, float]) -> bool:
    return all(risk == RiskLevel.LOW for risk in classify_metrics(metrics).values())


def _ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _percent(numerator: float, denominator: float) -> float:
    return _ratio(numerator, denominator) * 100.0


def _high_is_bad(value: float, warning: float, critical: float) -> RiskLevel:
    high = warning + ((critical - warning) / 2)
    if value > critical:
        return RiskLevel.CRITICAL
    if value > high:
        return RiskLevel.HIGH
    if value > warning:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _low_is_bad(value: float, warning: float, critical: float) -> RiskLevel:
    high = critical + ((warning - critical) / 2)
    if value < critical:
        return RiskLevel.CRITICAL
    if value < high:
        return RiskLevel.HIGH
    if value < warning:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW
