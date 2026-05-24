from __future__ import annotations

from pathlib import Path

from .cyber_physical import CyberPhysicalLink
from .event_bus import EventBus
from .logging import JsonRuntimeLogger
from .monitors import DriftConfinementMonitor, SemanticIsometryChecker
from .projection import BCCBoundaryControlLayer, CPLDCProjectionLayer
from .reducer import Reducer
from .schemas import EventSeverity, EventType, RuntimeDecision, SystemEvent
from .state import RuntimeState


class FinalAxisSupervisor:
    def __init__(self, log_path: Path) -> None:
        self.logger = JsonRuntimeLogger(log_path)
        self.event_bus = EventBus(self.logger)
        self.state = RuntimeState()
        self.reducer = Reducer()
        self.drift_monitor = DriftConfinementMonitor()
        self.semantic_checker = SemanticIsometryChecker()
        self.cpldc = CPLDCProjectionLayer()
        self.bcc = BCCBoundaryControlLayer()
        self.link = CyberPhysicalLink()

    def ingest(self, event: SystemEvent) -> RuntimeState:
        self.event_bus.publish(event)
        self._process(event)
        semantic_drift = self.semantic_checker.inspect(event)
        if semantic_drift is not None:
            self.event_bus.publish(semantic_drift)
            self._process(semantic_drift)
            confinement = self.drift_monitor.inspect(semantic_drift)
            if confinement is not None:
                self.event_bus.publish(confinement)
                self._process(confinement)
        drift_confinement = self.drift_monitor.inspect(event)
        if drift_confinement is not None:
            self.event_bus.publish(drift_confinement)
            self._process(drift_confinement)
        return self.state

    def _process(self, event: SystemEvent) -> None:
        semantic_isometry = self.semantic_checker.score(event)
        projection = self.cpldc.project(event)
        drift_score = float(event.payload.get("drift_score", 0.0))
        requires_confinement = (
            event.severity == EventSeverity.CRITICAL
            or semantic_isometry < self.semantic_checker.minimum_score
            or drift_score >= self.drift_monitor.drift_threshold
            or (
                self.state.confined
                and event.event_type != EventType.OVERRIDE_APPLIED
            )
        )
        boundary = self.bcc.evaluate(projection, critical=requires_confinement)
        override_supported = requires_confinement or event.operator_override_supported
        action = boundary["allowed_action"]
        if requires_confinement and not override_supported:
            action = "hold"
        decision = RuntimeDecision(
            decision=f"{event.event_type.value}:{action}",
            reason=self._explain(event, boundary["reason"], projection["explanation"]),
            trace_id=event.trace_id,
            event_id=event.event_id,
            action=action,
            autonomous_action=action not in {"hold", "observe"},
            operator_override_supported=override_supported,
        )
        self.logger.append("decision", {"decision": decision.to_dict()})
        before = self.state.snapshot()
        self.state = self.reducer.reduce(
            self.state,
            event,
            decision,
            semantic_isometry,
            boundary["boundary"],
            projection,
        )
        after = self.state.snapshot()
        self.logger.append(
            "state_change",
            {
                "trace_id": event.trace_id,
                "event_id": event.event_id,
                "before": before,
                "after": after,
                "explanation": decision.reason,
            },
        )
        link_result = self.link.apply(decision)
        self.state.cyber_physical_status = link_result["status"]
        self.logger.append("cyber_physical_link", link_result)

    def _explain(
        self, event: SystemEvent, boundary_reason: str, projection_explanation: str
    ) -> str:
        event_explanation = event.explanation or "Event carried no additional note."
        return (
            f"{projection_explanation} {boundary_reason} "
            f"Event explanation: {event_explanation}"
        )
