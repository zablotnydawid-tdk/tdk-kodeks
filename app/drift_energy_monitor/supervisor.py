from __future__ import annotations

from pathlib import Path

from .metrics import DriftMetricsEngine
from .observability import MonitorLogger
from .recovery import RecoveryEngine
from .rules import DiagnosticRuleEngine
from .schemas import MonitorSnapshot, MonitorState, Severity
from .state_machine import DriftEnergyStateMachine, metrics_normalized


class DriftEnergyMonitor:
    def __init__(self, log_path: Path) -> None:
        self.state = MonitorState.STABLE
        self.logger = MonitorLogger(log_path)
        self.metrics_engine = DriftMetricsEngine()
        self.state_machine = DriftEnergyStateMachine()
        self.rules = DiagnosticRuleEngine()
        self.recovery = RecoveryEngine()

    def observe(self, snapshot: MonitorSnapshot) -> dict:
        self.logger.append("snapshot", {"snapshot": snapshot.to_dict()})
        metrics = self.metrics_engine.calculate(snapshot)
        metric_severity = self.metrics_engine.classify(metrics)
        findings = self.rules.evaluate(snapshot)
        before = self.state
        candidate = self.state_machine.transition(
            before, metrics, snapshot, metrics_normalized(metrics)
        )
        direct = self.state_machine.state_for_metrics(metrics, snapshot)
        after = self._more_severe(candidate, direct)
        self.state = after
        recovery_plan = self.recovery.plan(after, findings)
        analysis = {
            "snapshot_id": snapshot.snapshot_id,
            "state_before": before.value,
            "state_after": after.value,
            "metrics": metrics,
            "metric_severity": {
                name: severity.value for name, severity in metric_severity.items()
            },
            "findings": [finding.to_dict() for finding in findings],
            "recovery_plan": recovery_plan,
            "explanation": self._explain(before, after, metrics, findings),
            "witness_evidence": {
                "timestamp": snapshot.captured_at,
                "metric_snapshot": metrics,
                "decision_trace": [finding.rule_id for finding in findings],
                "economic_delta": snapshot.economics.optimization_delta_pln,
                "runtime_state": after.value,
            },
        }
        self.logger.append("analysis", analysis)
        return analysis

    def _more_severe(
        self, first: MonitorState, second: MonitorState
    ) -> MonitorState:
        order = [
            MonitorState.STABLE,
            MonitorState.OBSERVATION,
            MonitorState.DEGRADED,
            MonitorState.UNSTABLE,
            MonitorState.CRITICAL,
            MonitorState.ISOLATED,
            MonitorState.RECOVERY,
        ]
        return first if order.index(first) >= order.index(second) else second

    def _explain(
        self,
        before: MonitorState,
        after: MonitorState,
        metrics: dict[str, float],
        findings: list,
    ) -> str:
        if before == after and not findings:
            return "Metrics stayed within continuity envelope."
        finding_ids = ", ".join(finding.rule_id for finding in findings) or "none"
        return (
            f"State changed from {before.value} to {after.value} from metrics "
            f"{metrics}; diagnostic findings: {finding_ids}."
        )
