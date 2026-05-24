from __future__ import annotations

from .schemas import DiagnosticFinding, MonitorSnapshot, Severity


class DiagnosticRuleEngine:
    def evaluate(self, snapshot: MonitorSnapshot) -> list[DiagnosticFinding]:
        findings: list[DiagnosticFinding] = []
        telemetry = snapshot.telemetry
        economics = snapshot.economics
        ai = snapshot.ai_layer
        environmental = snapshot.environmental

        if telemetry.grid_export > 0 and telemetry.grid_import > 0 and telemetry.battery_soc < 95:
            findings.append(
                DiagnosticFinding(
                    rule_id="EMS_GRID_CHARGE_CONFLICT",
                    risk=Severity.WARNING,
                    actions=["stop_grid_charge", "log_conflict", "notify_operator"],
                    evidence={
                        "grid_import": telemetry.grid_import,
                        "grid_export": telemetry.grid_export,
                        "battery_soc": telemetry.battery_soc,
                    },
                    explanation=(
                        "PV surplus and grid import are both active while battery "
                        "still has charging headroom."
                    ),
                )
            )

        if environmental.outside_temp_stable and environmental.cop_drop > 20.0:
            findings.append(
                DiagnosticFinding(
                    rule_id="COP_RUNTIME_DRIFT",
                    risk=Severity.WARNING,
                    actions=[
                        "inspect_heat_pump",
                        "compare_flow_temperature",
                        "generate_efficiency_report",
                    ],
                    evidence={
                        "outside_temp_stable": environmental.outside_temp_stable,
                        "cop_drop": environmental.cop_drop,
                    },
                    explanation="COP dropped despite stable outside temperature.",
                )
            )

        phase_values = list(telemetry.phase_balance.values())
        if phase_values and max(phase_values) - min(phase_values) > 20.0:
            findings.append(
                DiagnosticFinding(
                    rule_id="PHASE_IMBALANCE_CRITICAL",
                    risk=Severity.CRITICAL,
                    actions=["isolate_loads", "notify_operator", "enable_safe_mode"],
                    evidence={"phase_balance": telemetry.phase_balance},
                    explanation="Phase difference exceeded critical threshold.",
                )
            )

        if ai.repeated_decisions > 5 and ai.no_state_change:
            findings.append(
                DiagnosticFinding(
                    rule_id="AI_RECURSIVE_DECISION_LOOP",
                    risk=Severity.CRITICAL,
                    actions=[
                        "freeze_ai_layer",
                        "rollback_last_decision",
                        "activate_manual_supervision",
                    ],
                    evidence={
                        "repeated_decisions": ai.repeated_decisions,
                        "no_state_change": ai.no_state_change,
                    },
                    explanation=(
                        "AI layer repeated decisions without producing a state change."
                    ),
                )
            )

        if economics.optimization_delta_pln < -50.0:
            findings.append(
                DiagnosticFinding(
                    rule_id="HIDDEN_ECONOMIC_LOSS",
                    risk=Severity.WARNING,
                    actions=[
                        "log_anomaly",
                        "compare_tariff_window",
                        "generate_witness_report",
                    ],
                    evidence={
                        "optimization_delta_pln": economics.optimization_delta_pln,
                        "tariff_window": economics.tariff_window,
                    },
                    explanation="Optimization delta indicates hidden economic loss.",
                )
            )
        return findings
