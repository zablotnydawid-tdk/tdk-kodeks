from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.final_axis.logging import load_jsonl
from app.final_axis.reporting import build_markdown_report
from app.final_axis.sample_events import (
    ai_governance_drift_event,
    ems_event,
    operator_override_event,
    pv_event,
)
from app.final_axis.supervisor import FinalAxisSupervisor


class FinalAxisRuntimeTests(unittest.TestCase):
    def test_every_decision_and_state_change_is_logged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "runtime.jsonl"
            supervisor = FinalAxisSupervisor(log_path)

            supervisor.ingest(pv_event())

            records = load_jsonl(log_path)
            self.assertTrue(
                any(record["record_type"] == "decision" for record in records)
            )
            state_changes = [
                record for record in records if record["record_type"] == "state_change"
            ]
            self.assertTrue(state_changes)
            self.assertTrue(state_changes[-1]["explanation"])

    def test_drift_event_triggers_confinement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "runtime.jsonl"
            supervisor = FinalAxisSupervisor(log_path)

            state = supervisor.ingest(ai_governance_drift_event())

            records = load_jsonl(log_path)
            self.assertTrue(state.confined)
            decisions = [
                record["decision"]
                for record in records
                if record["record_type"] == "decision"
            ]
            self.assertEqual(decisions[0]["action"], "hold")
            self.assertTrue(
                any(
                    record["record_type"] == "event"
                    and record["event"]["event_type"] == "confinement_triggered"
                    for record in records
                )
            )

    def test_critical_event_supports_operator_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "runtime.jsonl"
            supervisor = FinalAxisSupervisor(log_path)

            state = supervisor.ingest(ems_event())

            self.assertTrue(state.pending_operator_overrides)
            decisions = [
                record["decision"]
                for record in load_jsonl(log_path)
                if record["record_type"] == "decision"
            ]
            self.assertTrue(decisions[-1]["operator_override_supported"])
            self.assertEqual(decisions[-1]["action"], "hold")

    def test_operator_override_releases_confinement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "runtime.jsonl"
            supervisor = FinalAxisSupervisor(log_path)

            state = supervisor.ingest(ai_governance_drift_event())
            trace_id = state.pending_operator_overrides[0]
            state = supervisor.ingest(operator_override_event(trace_id))

            self.assertFalse(state.confined)
            self.assertNotIn(trace_id, state.pending_operator_overrides)

    def test_markdown_report_is_generated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "runtime.jsonl"
            report_path = Path(tmp_dir) / "report.md"
            supervisor = FinalAxisSupervisor(log_path)
            supervisor.ingest(pv_event())

            report = build_markdown_report(log_path, report_path)

            self.assertTrue(report_path.exists())
            self.assertIn("WitnessAI Final Axis Operational Report", report)
            self.assertIn("Next Integration Steps", report)


if __name__ == "__main__":
    unittest.main()
