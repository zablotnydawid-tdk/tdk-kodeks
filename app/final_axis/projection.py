from __future__ import annotations

from typing import Any

from .schemas import SystemEvent


class CPLDCProjectionLayer:
    """Constrained projection from event payload into an explainable runtime intent."""

    def project(self, event: SystemEvent) -> dict[str, Any]:
        projection = {
            "trace_id": event.trace_id,
            "domain": event.domain.value,
            "requested_action": event.payload.get("requested_action", "observe"),
            "intent": event.payload.get("intent", "maintain safe operation"),
            "limits": event.payload.get("limits", {}),
            "evidence": event.payload.get("evidence", {}),
        }
        projection["explanation"] = (
            f"CPLDC projected {projection['requested_action']} for "
            f"{projection['domain']} from trace {event.trace_id}."
        )
        return projection


class BCCBoundaryControlLayer:
    def evaluate(self, projection: dict[str, Any], critical: bool) -> dict[str, Any]:
        requested_action = projection["requested_action"]
        limits = projection.get("limits", {})
        if critical:
            boundary = "operator_gated"
            allowed_action = "hold"
            reason = "Critical event requires operator override support."
        elif limits.get("allow_autonomous", False):
            boundary = "bounded_autonomy"
            allowed_action = requested_action
            reason = "Action remains inside declared operational limits."
        else:
            boundary = "observe_only"
            allowed_action = "observe"
            reason = "No autonomous permission was declared in runtime trace."
        return {
            "boundary": boundary,
            "allowed_action": allowed_action,
            "reason": reason,
            "projection": projection,
        }
