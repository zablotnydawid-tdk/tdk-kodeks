from __future__ import annotations

from .schemas import EventDomain, EventSeverity, EventType, SystemEvent


def pv_event() -> SystemEvent:
    return SystemEvent(
        event_type=EventType.TELEMETRY,
        domain=EventDomain.PV,
        severity=EventSeverity.WARNING,
        source="pv_inverter_01",
        payload={
            "requested_action": "observe",
            "intent": "stabilize pv output",
            "expected_effect": "stabilize pv output",
            "evidence": {"dc_voltage": 920, "frequency_hz": 49.91},
            "limits": {"allow_autonomous": False},
            "semantic_isometry": 0.94,
        },
        explanation="PV telemetry shows voltage variance but remains inside observation mode.",
    )


def ems_event() -> SystemEvent:
    return SystemEvent(
        event_type=EventType.COMMAND_REQUEST,
        domain=EventDomain.EMS,
        severity=EventSeverity.CRITICAL,
        source="ems_dispatch",
        payload={
            "requested_action": "shed_noncritical_load",
            "intent": "prevent feeder overload",
            "expected_effect": "reduce feeder load",
            "evidence": {"feeder_load_pct": 104, "battery_soc_pct": 37},
            "limits": {"allow_autonomous": True, "max_load_shed_kw": 120},
            "semantic_isometry": 0.88,
        },
        operator_override_supported=True,
        explanation="EMS requests a load-shed action; critical command is operator-gated.",
    )


def ai_governance_drift_event() -> SystemEvent:
    return SystemEvent(
        event_type=EventType.COMMAND_REQUEST,
        domain=EventDomain.AI_GOVERNANCE,
        severity=EventSeverity.WARNING,
        source="ai_policy_agent",
        payload={
            "requested_action": "auto_apply_policy_change",
            "intent": "maintain contractual compliance",
            "expected_effect": "increase dispatch aggression",
            "evidence": {"policy_version": "draft-17", "contract_clause": "BESS-CPLDC"},
            "limits": {"allow_autonomous": True},
            "semantic_isometry": 0.41,
            "drift_score": 0.62,
        },
        explanation="AI policy recommendation diverges from declared compliance intent.",
    )


def operator_override_event(trace_id: str) -> SystemEvent:
    return SystemEvent(
        event_type=EventType.OVERRIDE_APPLIED,
        domain=EventDomain.OPERATOR,
        severity=EventSeverity.INFO,
        source="operator_console",
        trace_id=trace_id,
        payload={
            "requested_action": "release_confinement",
            "intent": "operator reviewed trace and accepted bounded continuation",
            "expected_effect": "operator reviewed trace and accepted bounded continuation",
            "limits": {"allow_autonomous": False},
            "operator_id": "sample-operator",
        },
        operator_override_supported=True,
        explanation="Human operator reviewed JSON trace and applied override.",
    )


def sample_events() -> list[SystemEvent]:
    return [pv_event(), ems_event(), ai_governance_drift_event()]
