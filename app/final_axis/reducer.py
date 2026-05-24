from __future__ import annotations

from .schemas import EventSeverity, EventType, RuntimeDecision, SystemEvent
from .state import RuntimeState


class Reducer:
    def reduce(
        self,
        state: RuntimeState,
        event: SystemEvent,
        decision: RuntimeDecision,
        semantic_isometry: float,
        boundary: str,
        projection: dict,
    ) -> RuntimeState:
        state.event_count += 1
        state.semantic_isometry = semantic_isometry
        state.last_projection = projection
        state.active_boundary = boundary
        state.decisions.append(decision.to_dict())
        state.explanations.append(decision.reason)

        if event.event_type in {EventType.DRIFT_DETECTED, EventType.CONFINEMENT_TRIGGERED}:
            state.confined = True
            state.mode = "confined"
            state.drift_score = max(
                state.drift_score,
                float(event.payload.get("drift_score", event.payload.get("semantic_delta", 0.0))),
            )

        if event.severity == EventSeverity.CRITICAL:
            if event.trace_id not in state.pending_operator_overrides:
                state.pending_operator_overrides.append(event.trace_id)

        if event.event_type == EventType.OVERRIDE_APPLIED:
            state.confined = False
            state.mode = "operator_override"
            state.pending_operator_overrides = [
                trace_id
                for trace_id in state.pending_operator_overrides
                if trace_id != event.trace_id
            ]

        return state
