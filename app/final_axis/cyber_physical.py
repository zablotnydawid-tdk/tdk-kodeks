from __future__ import annotations

from .schemas import RuntimeDecision


class CyberPhysicalLink:
    def __init__(self) -> None:
        self.transmitted: list[dict[str, str]] = []

    def apply(self, decision: RuntimeDecision) -> dict[str, str]:
        if decision.action in {"hold", "observe"}:
            status = "not_transmitted"
        else:
            status = "transmitted_with_trace"
        result = {
            "status": status,
            "action": decision.action,
            "trace_id": decision.trace_id,
            "reason": decision.reason,
        }
        self.transmitted.append(result)
        return result
