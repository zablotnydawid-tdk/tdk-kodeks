from __future__ import annotations

from .schemas import DiagnosticFinding, MonitorState, Severity


class RecoveryEngine:
    automatic_actions = [
        "rollback_last_state",
        "isolate_faulty_module",
        "restart_service",
        "reduce_load",
        "switch_to_safe_mode",
    ]
    manual_actions = [
        "operator_review",
        "forensic_analysis",
        "runtime_export",
        "witness_report_generation",
    ]

    def plan(
        self, state: MonitorState, findings: list[DiagnosticFinding]
    ) -> dict[str, list[str]]:
        critical = any(finding.risk == Severity.CRITICAL for finding in findings)
        automatic: list[str] = []
        manual: list[str] = []
        if state in {MonitorState.UNSTABLE, MonitorState.CRITICAL, MonitorState.ISOLATED}:
            automatic.extend(["rollback_last_state", "switch_to_safe_mode"])
        if critical:
            automatic.extend(["isolate_faulty_module", "reduce_load"])
            manual.extend(["operator_review", "forensic_analysis"])
        if findings:
            manual.extend(["runtime_export", "witness_report_generation"])
        return {
            "automatic_actions": self._unique(automatic),
            "manual_actions": self._unique(manual),
        }

    def _unique(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            if value not in seen:
                result.append(value)
                seen.add(value)
        return result
