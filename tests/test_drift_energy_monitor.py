from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.drift_energy_monitor.observability import load_jsonl
from app.drift_energy_monitor.reporting import build_markdown_report
from app.drift_energy_monitor.sample_data import drift_snapshot, stable_snapshot
from app.drift_energy_monitor.schemas import MonitorState
from app.drift_energy_monitor.supervisor import DriftEnergyMonitor


class DriftEnergyMonitorTests(unittest.TestCase):
    def test_stable_snapshot_stays_stable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            monitor = DriftEnergyMonitor(Path(tmp_dir) / "monitor.jsonl")

            analysis = monitor.observe(stable_snapshot())

            self.assertEqual(analysis["state_after"], MonitorState.STABLE.value)
            self.assertEqual(analysis["findings"], [])

    def test_drift_snapshot_triggers_critical_supervision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "monitor.jsonl"
            monitor = DriftEnergyMonitor(log_path)

            analysis = monitor.observe(drift_snapshot())

            self.assertEqual(analysis["state_after"], MonitorState.CRITICAL.value)
            rule_ids = {finding["rule_id"] for finding in analysis["findings"]}
            self.assertIn("PHASE_IMBALANCE_CRITICAL", rule_ids)
            self.assertIn("AI_RECURSIVE_DECISION_LOOP", rule_ids)
            self.assertIn("EMS_GRID_CHARGE_CONFLICT", rule_ids)
            self.assertIn("HIDDEN_ECONOMIC_LOSS", rule_ids)
            self.assertIn("operator_review", analysis["recovery_plan"]["manual_actions"])
            self.assertIn(
                "switch_to_safe_mode", analysis["recovery_plan"]["automatic_actions"]
            )

            records = load_jsonl(log_path)
            self.assertTrue(any(record["record_type"] == "snapshot" for record in records))
            self.assertTrue(any(record["record_type"] == "analysis" for record in records))

    def test_markdown_report_exports_witness_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "monitor.jsonl"
            report_path = Path(tmp_dir) / "report.md"
            monitor = DriftEnergyMonitor(log_path)
            monitor.observe(drift_snapshot())

            report = build_markdown_report(log_path, report_path)

            self.assertTrue(report_path.exists())
            self.assertIn("DRIFT_ENERGY_MONITOR Operational Report", report)
            self.assertIn("Witness Evidence", report)


if __name__ == "__main__":
    unittest.main()
