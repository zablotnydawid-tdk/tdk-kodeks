from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.live_ops.operator_review import (  # noqa: E402
    export_json,
    export_markdown,
    process_review,
    run_file,
)


def live_case() -> dict:
    return {
        "case_id": "TEST-REVIEW-001",
        "generated_at": "2026-05-26T00:00:00+00:00",
        "intake": {
            "case_id": "TEST-REVIEW-001",
            "operator_id": "test-operator",
            "source": "unit_test",
            "title": "PV diagnostics review case",
        },
        "classification": {
            "primary_type": "pv",
            "categories": ["pv", "ems_bess"],
            "operator_decision_required": True,
        },
        "priority": {
            "level": "high",
            "autonomous_action_allowed": False,
            "operator_override_supported": True,
        },
        "diagnostic_summary": {
            "summary": "pv case with high priority.",
            "findings": ["PV yield drop detected.", "EMS behavior requires review."],
            "evidence_gaps": [],
        },
        "recommendation": {
            "decision_owner": "operator",
            "operator_next_actions": ["operator reviews diagnostics"],
            "blocked_actions": ["no autonomous remediation"],
        },
    }


def review_payload(**overrides: object) -> dict:
    review = {
        "review_id": "TEST-REVIEW-001:operator-review",
        "operator_id": "test-operator",
        "approve_recommendation": True,
        "reject_recommendation": False,
        "request_field_visit": False,
        "request_thermal_inspection": False,
        "escalation_required": False,
        "safe_to_monitor": False,
        "operator_notes": "Operator accepts the recommendation for final report closure.",
        "final_decision": "APPROVED",
    }
    review.update(overrides)
    return {"live_case": live_case(), "operator_review": review}


def test_approve_flow_closes_case() -> None:
    result = process_review(review_payload()).to_dict()

    assert result["final_decision"] == "APPROVED"
    assert result["operator_acceptance_state"] == "OPERATOR_ACCEPTED"
    assert result["case_closed"] is True
    assert result["autonomous_action"] is False
    assert result["final_governance_summary"]["operator_decides"] is True


def test_reject_flow_closes_case_with_rejection() -> None:
    result = process_review(
        review_payload(
            approve_recommendation=False,
            reject_recommendation=True,
            final_decision="REJECTED",
            operator_notes="Operator rejects recommendation due to evidence mismatch.",
        )
    ).to_dict()

    assert result["final_decision"] == "REJECTED"
    assert result["operator_acceptance_state"] == "OPERATOR_REJECTED"
    assert result["case_closed"] is True


def test_escalation_flow_preserves_open_follow_up() -> None:
    result = process_review(
        review_payload(
            approve_recommendation=False,
            escalation_required=True,
            final_decision="ESCALATED",
            operator_notes="Operator escalates to senior review before closure.",
        )
    ).to_dict()

    assert result["final_decision"] == "ESCALATED"
    assert result["operator_acceptance_state"] == "OPERATOR_FOLLOW_UP_REQUIRED"
    assert result["case_closed"] is False
    assert result["review_closed"] is True


def test_missing_data_enters_safe_mode() -> None:
    result = process_review({"operator_review": {"operator_id": "test"}}).to_dict()

    assert result["safe_mode"] == "SAFE_MODE_MISSING_DATA"
    assert result["final_decision"] == "UNKNOWN"
    assert result["case_closed"] is False
    assert "live_case" in result["final_governance_summary"]["missing_data"]


def test_report_generation_exports_json_and_markdown(tmp_path: Path) -> None:
    input_path = tmp_path / "review_input.json"
    output_path = tmp_path / "operator_review_result.json"
    markdown_path = tmp_path / "operator_review_report.md"
    input_path.write_text(json.dumps(review_payload()), encoding="utf-8")

    result = run_file(input_path, output_path, markdown_path)

    assert result["final_decision"] == "APPROVED"
    assert output_path.exists()
    assert markdown_path.exists()
    assert "Operator Review Final Report" in markdown_path.read_text(encoding="utf-8")


def test_decision_trace_persistence() -> None:
    result = process_review(review_payload()).to_dict()
    exported = json.loads(export_json(process_review(review_payload())))
    markdown = export_markdown(process_review(review_payload()))

    assert len(result["decision_trace"]) == 5
    assert result["decision_trace"][0]["step"] == "live_ingest"
    assert exported["decision_trace"][-1]["step"] == "final_decision"
    assert "Decision Trace" in markdown
