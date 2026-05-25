from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.monitoring.drift_energy_monitor import (  # noqa: E402
    DriftEnergyMonitor,
    MonitorState,
    RiskLevel,
    calculate_metrics,
    classify_metrics,
    evaluate_diagnostic_rules,
    transition_state,
)


def base_event() -> dict:
    return {
        "telemetry": {
            "phase_difference": 5.0,
            "phase_difference_threshold": 30.0,
        },
        "runtime": {
            "unexpected_events": 1,
            "total_events": 100,
            "subsystem_failure_detected": False,
            "recovery_successful": False,
        },
        "ai_layer": {
            "stable_decisions": 100,
            "total_decisions": 100,
            "contradiction_events": 1,
            "total_predictions": 100,
            "repeated_decisions": 0,
            "no_state_change": False,
        },
        "economics": {
            "expected_yield": 100.0,
            "real_yield": 99.0,
            "expected_cost": 100.0,
            "actual_cost": 110.0,
        },
        "environmental": {
            "outside_temp_stable": False,
            "cop_drop_percent": 0.0,
        },
        "diagnostics": {
            "pv_surplus_active": False,
            "battery_charging_from_grid": False,
        },
    }


class DriftEnergyMonitorRuntimeTests(unittest.TestCase):
    def test_metric_calculation(self) -> None:
        event = base_event()
        event["ai_layer"]["stable_decisions"] = 80
        event["runtime"]["unexpected_events"] = 20
        event["economics"]["expected_yield"] = 120.0
        event["economics"]["real_yield"] = 100.0
        event["economics"]["expected_cost"] = 200.0
        event["economics"]["actual_cost"] = 260.0
        event["ai_layer"]["contradiction_events"] = 12

        metrics = calculate_metrics(event)

        self.assertEqual(metrics["coherence_index"], 80.0)
        self.assertEqual(metrics["runtime_entropy"], 0.2)
        self.assertEqual(metrics["energy_loss_factor"], 20.0)
        self.assertEqual(metrics["economic_drift"], 60.0)
        self.assertEqual(metrics["ai_conflict_ratio"], 0.12)

    def test_risk_levels_low_medium_high_critical(self) -> None:
        metrics = {
            "coherence_index": 100.0,
            "runtime_entropy": 0.01,
            "energy_loss_factor": 1.0,
            "economic_drift": 10.0,
            "ai_conflict_ratio": 0.01,
        }
        self.assertEqual(classify_metrics(metrics)["runtime_entropy"], RiskLevel.LOW)

        metrics["runtime_entropy"] = 0.16
        self.assertEqual(
            classify_metrics(metrics)["runtime_entropy"], RiskLevel.MEDIUM
        )

        metrics["runtime_entropy"] = 0.26
        self.assertEqual(classify_metrics(metrics)["runtime_entropy"], RiskLevel.HIGH)

        metrics["runtime_entropy"] = 0.36
        self.assertEqual(
            classify_metrics(metrics)["runtime_entropy"], RiskLevel.CRITICAL
        )

    def test_warning_threshold(self) -> None:
        metrics = {
            "coherence_index": 84.0,
            "runtime_entropy": 0.01,
            "energy_loss_factor": 1.0,
            "economic_drift": 10.0,
            "ai_conflict_ratio": 0.01,
        }

        self.assertEqual(classify_metrics(metrics)["coherence_index"], RiskLevel.MEDIUM)

    def test_critical_threshold(self) -> None:
        metrics = {
            "coherence_index": 59.0,
            "runtime_entropy": 0.36,
            "energy_loss_factor": 21.0,
            "economic_drift": 301.0,
            "ai_conflict_ratio": 0.26,
        }

        risks = classify_metrics(metrics)

        self.assertTrue(all(value == RiskLevel.CRITICAL for value in risks.values()))

    def test_ems_grid_charge_conflict_rule(self) -> None:
        event = base_event()
        event["diagnostics"]["pv_surplus_active"] = True
        event["diagnostics"]["battery_charging_from_grid"] = True

        findings = evaluate_diagnostic_rules(event)

        self.assertEqual(findings[0].rule_id, "EMS_GRID_CHARGE_CONFLICT")
        self.assertEqual(findings[0].risk_level, RiskLevel.HIGH)

    def test_cop_runtime_drift_rule(self) -> None:
        event = base_event()
        event["environmental"]["outside_temp_stable"] = True
        event["environmental"]["cop_drop_percent"] = 21.0

        findings = evaluate_diagnostic_rules(event)

        self.assertEqual(findings[0].rule_id, "COP_RUNTIME_DRIFT")
        self.assertEqual(findings[0].risk_level, RiskLevel.MEDIUM)

    def test_phase_imbalance_critical_rule(self) -> None:
        event = base_event()
        event["telemetry"]["phase_difference"] = 42.0
        event["telemetry"]["phase_difference_threshold"] = 30.0

        findings = evaluate_diagnostic_rules(event)

        self.assertEqual(findings[0].rule_id, "PHASE_IMBALANCE_CRITICAL")
        self.assertEqual(findings[0].risk_level, RiskLevel.CRITICAL)

    def test_ai_recursive_decision_loop_rule(self) -> None:
        event = base_event()
        event["ai_layer"]["repeated_decisions"] = 6
        event["ai_layer"]["no_state_change"] = True

        findings = evaluate_diagnostic_rules(event)

        self.assertEqual(findings[0].rule_id, "AI_RECURSIVE_DECISION_LOOP")
        self.assertEqual(findings[0].risk_level, RiskLevel.HIGH)

    def test_json_export(self) -> None:
        monitor = DriftEnergyMonitor()
        analysis = monitor.analyze(base_event())

        exported = monitor.export_json(analysis)
        payload = json.loads(exported)

        self.assertEqual(payload["risk_level"], "LOW")
        self.assertTrue(payload["compatibility"]["final_axis_observability"])
        self.assertEqual(payload["operator_action"], "none; diagnostic export only")

    def test_markdown_export(self) -> None:
        monitor = DriftEnergyMonitor()
        analysis = monitor.analyze(base_event())

        exported = monitor.export_markdown(analysis)

        self.assertIn("DRIFT_ENERGY_MONITOR.SYS Report", exported)
        self.assertIn("FINAL_AXIS Compatibility", exported)
        self.assertIn("operator_action: none; diagnostic export only", exported)

    def test_state_machine_transitions(self) -> None:
        event = base_event()
        event["runtime"]["unexpected_events"] = 16
        metrics = calculate_metrics(event)
        self.assertEqual(
            transition_state(MonitorState.STABLE, metrics, event),
            MonitorState.OBSERVATION,
        )

        event["ai_layer"]["stable_decisions"] = 84
        metrics = calculate_metrics(event)
        self.assertEqual(
            transition_state(MonitorState.OBSERVATION, metrics, event),
            MonitorState.DEGRADED,
        )

        event["economics"]["expected_yield"] = 130.0
        event["economics"]["real_yield"] = 100.0
        metrics = calculate_metrics(event)
        self.assertEqual(
            transition_state(MonitorState.DEGRADED, metrics, event),
            MonitorState.UNSTABLE,
        )

        event["ai_layer"]["contradiction_events"] = 26
        metrics = calculate_metrics(event)
        self.assertEqual(
            transition_state(MonitorState.UNSTABLE, metrics, event),
            MonitorState.CRITICAL,
        )

        event["runtime"]["subsystem_failure_detected"] = True
        self.assertEqual(
            transition_state(MonitorState.CRITICAL, metrics, event),
            MonitorState.ISOLATED,
        )

        event["runtime"]["recovery_successful"] = True
        self.assertEqual(
            transition_state(MonitorState.ISOLATED, metrics, event),
            MonitorState.RECOVERY,
        )

        normalized = base_event()
        normalized_metrics = calculate_metrics(normalized)
        self.assertEqual(
            transition_state(MonitorState.RECOVERY, normalized_metrics, normalized),
            MonitorState.STABLE,
        )


if __name__ == "__main__":
    unittest.main()
