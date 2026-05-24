from __future__ import annotations

from .schemas import EventDomain, EventSeverity, EventType, SystemEvent


class DriftConfinementMonitor:
    def __init__(self, drift_threshold: float = 0.35) -> None:
        self.drift_threshold = drift_threshold

    def inspect(self, event: SystemEvent) -> SystemEvent | None:
        drift_score = float(event.payload.get("drift_score", 0.0))
        semantic_delta = float(event.payload.get("semantic_delta", 0.0))
        if drift_score < self.drift_threshold and semantic_delta < self.drift_threshold:
            return None
        return SystemEvent(
            event_type=EventType.CONFINEMENT_TRIGGERED,
            domain=event.domain,
            severity=EventSeverity.CRITICAL,
            source="drift_confinement_monitor",
            payload={
                "trigger_event_id": event.event_id,
                "drift_score": drift_score,
                "semantic_delta": semantic_delta,
                "confinement": "hold_and_require_operator_review",
            },
            trace_id=event.trace_id,
            operator_override_supported=True,
            explanation=(
                "Runtime drift exceeded threshold; autonomous action is confined "
                "until an operator reviews the trace."
            ),
        )


class SemanticIsometryChecker:
    def __init__(self, minimum_score: float = 0.82) -> None:
        self.minimum_score = minimum_score

    def score(self, event: SystemEvent) -> float:
        declared = event.payload.get("semantic_isometry")
        if declared is not None:
            return float(declared)
        intent = str(event.payload.get("intent", ""))
        effect = str(event.payload.get("expected_effect", ""))
        if not intent or not effect:
            return 1.0
        intent_terms = set(intent.lower().split())
        effect_terms = set(effect.lower().split())
        if not intent_terms:
            return 1.0
        return len(intent_terms & effect_terms) / len(intent_terms | effect_terms)

    def inspect(self, event: SystemEvent) -> SystemEvent | None:
        score = self.score(event)
        if score >= self.minimum_score:
            return None
        return SystemEvent(
            event_type=EventType.DRIFT_DETECTED,
            domain=EventDomain.AI_GOVERNANCE,
            severity=EventSeverity.CRITICAL,
            source="semantic_isometry_checker",
            payload={
                "trigger_event_id": event.event_id,
                "semantic_isometry": score,
                "minimum_score": self.minimum_score,
                "semantic_delta": round(1.0 - score, 4),
            },
            trace_id=event.trace_id,
            operator_override_supported=True,
            explanation=(
                "Requested meaning and projected effect are not isometric enough "
                "for autonomous execution."
            ),
        )
