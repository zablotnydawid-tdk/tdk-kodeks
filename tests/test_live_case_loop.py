from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.live_ops.live_case_loop import (  # noqa: E402
    classify_case,
    detect_priority,
    export_json,
    export_markdown,
    generate_diagnostic_summary,
    generate_recommendation,
    intake,
    memory_update,
    process_case,
    run_file,
)


def base_payload() -> dict:
    return {
        "case_id": "TEST-LIVE-001",
        "source": "unit_test",
        "operator_id": "test-operator",
        "title": "PV surplus and EMS battery issue",
        "description": "PV surplus exists but battery charges from grid. Customer reports high energy cost.",
        "customer_context": "Local operator diagnostic case.",
        "assets": ["invoice", "inverter_csv"],
        "measurements": {
            "pv_production_kwh": 1200,
            "battery_soc": 70,
            "economic_loss_pln": 350,
            "phase_imbalance_percent": 12,
            "tariff": "G12",
        },
        "reported_symptoms": [
            "battery charging from grid",
            "unexpected high bill",
        ],
        "requested_outcome": "operator summary",
    }


class LiveCaseLoopTests(unittest.TestCase):
    def test_intake_preserves_operator_trace(self) -> None:
        record = intake(base_payload())

        self.assertEqual(record["case_id"], "TEST-LIVE-001")
        self.assertEqual(record["operator_id"], "test-operator")
        self.assertTrue(record["signals"]["economic_language"])

    def test_classify_case_detects_pv_ems_economics(self) -> None:
        record = intake(base_payload())
        classification = classify_case(record)

        self.assertEqual(classification["primary_type"], "pv")
        self.assertIn("ems_bess", classification["categories"])
        self.assertIn("economics", classification["categories"])
        self.assertTrue(classification["operator_decision_required"])

    def test_detect_priority_high_from_economic_loss(self) -> None:
        record = intake(base_payload())
        classification = classify_case(record)

        priority = detect_priority(record, classification)

        self.assertEqual(priority["level"], "high")
        self.assertFalse(priority["autonomous_action_allowed"])
        self.assertTrue(priority["operator_override_supported"])

    def test_detect_priority_critical_from_phase_imbalance(self) -> None:
        payload = base_payload()
        payload["measurements"]["phase_imbalance_percent"] = 30
        record = intake(payload)
        classification = classify_case(record)

        priority = detect_priority(record, classification)

        self.assertEqual(priority["level"], "critical")

    def test_diagnostic_summary_lists_findings_and_gaps(self) -> None:
        payload = base_payload()
        del payload["measurements"]["tariff"]
        record = intake(payload)
        classification = classify_case(record)
        priority = detect_priority(record, classification)

        summary = generate_diagnostic_summary(record, classification, priority)

        self.assertTrue(summary["findings"])
        self.assertIn("tariff", summary["evidence_gaps"])
        self.assertEqual(summary["traceability"], "all findings derived from local input only")

    def test_recommendation_is_operator_gated(self) -> None:
        record = intake(base_payload())
        classification = classify_case(record)
        priority = detect_priority(record, classification)
        summary = generate_diagnostic_summary(record, classification, priority)

        recommendation = generate_recommendation(
            record, classification, priority, summary
        )

        self.assertEqual(recommendation["decision_owner"], "operator")
        self.assertIn("no autonomous remediation", recommendation["blocked_actions"])

    def test_memory_update_records_flow_steps(self) -> None:
        record = intake(base_payload())
        classification = classify_case(record)
        priority = detect_priority(record, classification)
        summary = generate_diagnostic_summary(record, classification, priority)
        recommendation = generate_recommendation(
            record, classification, priority, summary
        )

        memory = memory_update(record, classification, priority, summary, recommendation)

        self.assertEqual(len(memory["entries"]), 5)
        self.assertEqual(memory["entries"][0]["step"], "intake")

    def test_process_case_returns_full_executive_result(self) -> None:
        result = process_case(base_payload()).to_dict()

        self.assertEqual(result["case_id"], "TEST-LIVE-001")
        self.assertIn("executive_summary", result)
        self.assertTrue(result["governance"]["control_plane_observes"])
        self.assertFalse(result["governance"]["tdk_frontend_backend_integrated"])

    def test_json_and_markdown_exports(self) -> None:
        result = process_case(base_payload())

        payload = json.loads(export_json(result))
        markdown = export_markdown(result)

        self.assertEqual(payload["case_id"], "TEST-LIVE-001")
        self.assertIn("LIVE CASE LOOP Report", markdown)
        self.assertIn("Operator Recommendation", markdown)

    def test_run_file_writes_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "case.json"
            output_path = root / "result.json"
            markdown_path = root / "result.md"
            input_path.write_text(json.dumps(base_payload()), encoding="utf-8")

            result = run_file(input_path, output_path, markdown_path)

            self.assertEqual(result["case_id"], "TEST-LIVE-001")
            self.assertTrue(output_path.exists())
            self.assertTrue(markdown_path.exists())


if __name__ == "__main__":
    unittest.main()

