from __future__ import annotations

from typing import Any


def build_decision_map(report_context: dict[str, Any], risk_map: dict[str, Any]) -> dict[str, Any]:
    blocked = report_context.get("blocked_recommendation_claims", [])
    ready = bool(report_context.get("ready_for_client_recommendation"))
    safe_state = risk_map.get("safe_state", "PASSIVE")

    if blocked:
        decision = "HUMAN_VALIDATION_REQUIRED"
        allowed_outputs = ["operator_brief", "evidence_pack"]
        blocked_outputs = ["client_recommendation", "automated_remediation"]
    elif safe_state in {"LOCK", "STOP"}:
        decision = "SAFE_HOLD"
        allowed_outputs = ["operator_brief"]
        blocked_outputs = ["client_recommendation", "automated_remediation"]
    elif ready:
        decision = "REPORT_CONTEXT_READY"
        allowed_outputs = ["operator_brief", "client_report_draft"]
        blocked_outputs = ["automated_remediation"]
    else:
        decision = "INSUFFICIENT_CONTEXT"
        allowed_outputs = ["operator_brief"]
        blocked_outputs = ["client_recommendation", "automated_remediation"]

    return {
        "decision": decision,
        "validation_level": "human_required" if blocked else "trace_valid",
        "allowed_outputs": allowed_outputs,
        "blocked_outputs": blocked_outputs,
        "blocked_claim_count": len(blocked),
        "safe_state": safe_state,
    }
