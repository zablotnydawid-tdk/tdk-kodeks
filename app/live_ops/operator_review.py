from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TERMINAL_DECISIONS = {"APPROVED", "REJECTED", "SAFE_TO_MONITOR"}
KNOWN_DECISIONS = TERMINAL_DECISIONS | {
    "FIELD_VISIT_REQUIRED",
    "THERMAL_INSPECTION_REQUIRED",
    "ESCALATED",
    "UNKNOWN",
}


@dataclass(frozen=True)
class DecisionTraceEntry:
    step: str
    status: str
    summary: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OperatorReviewResult:
    review_id: str
    case_id: str
    generated_at: str
    operator_id: str
    safe_mode: str
    final_decision: str
    case_closed: bool
    review_closed: bool
    operator_acceptance_state: str
    autonomous_action: bool
    action_flags: dict[str, bool]
    operator_notes: str
    decision_trace: list[dict[str, Any]]
    final_governance_summary: dict[str, Any]
    report_generation: dict[str, Any]
    source_context: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def process_review(payload: dict[str, Any]) -> OperatorReviewResult:
    live_case = _read_live_case(payload)
    review = dict(payload.get("operator_review", payload))
    action_flags = _action_flags(review)
    generated_at = _now()

    missing = _missing_inputs(live_case, review)
    safe_mode = "PASSIVE"
    if missing:
        safe_mode = "SAFE_MODE_MISSING_DATA"

    case_id = _nested_get(live_case, ("case_id",), "UNKNOWN")
    operator_id = str(review.get("operator_id") or _nested_get(live_case, ("intake", "operator_id"), "UNKNOWN"))
    operator_notes = str(review.get("operator_notes") or "UNKNOWN")
    final_decision = _resolve_final_decision(review, action_flags, missing)
    case_closed = final_decision in TERMINAL_DECISIONS and not missing
    review_closed = not missing and final_decision != "UNKNOWN"
    acceptance_state = _acceptance_state(final_decision, case_closed, missing)
    decision_trace = _build_decision_trace(
        live_case=live_case,
        review=review,
        action_flags=action_flags,
        final_decision=final_decision,
        case_closed=case_closed,
        missing=missing,
    )

    source_context = {
        "live_case_present": bool(live_case),
        "case_id": case_id,
        "priority": _nested_get(live_case, ("priority", "level"), "UNKNOWN"),
        "classification": _nested_get(live_case, ("classification", "primary_type"), "UNKNOWN"),
        "evidence_gaps": _nested_get(live_case, ("diagnostic_summary", "evidence_gaps"), []),
        "diagnostic_findings_count": len(_nested_get(live_case, ("diagnostic_summary", "findings"), [])),
        "recommendation_owner": _nested_get(live_case, ("recommendation", "decision_owner"), "UNKNOWN"),
    }

    governance = {
        "operator_decides": True,
        "autonomous_action": False,
        "control_plane_observes": True,
        "local_first": True,
        "cloud_runtime": False,
        "saas_runtime": False,
        "ui_required": False,
        "safe_mode": safe_mode,
        "missing_data": missing,
        "decision_trace_preserved": True,
        "continuity_compatible": True,
        "recovery_hint": _recovery_hint(missing),
    }

    report_generation = {
        "json_report": "generated_by_cli_when_output_path_is_provided",
        "markdown_report": "generated_by_cli_when_markdown_path_is_provided",
        "read_only_by_default": True,
        "explicit_export_required": True,
    }

    return OperatorReviewResult(
        review_id=str(review.get("review_id") or f"{case_id}:operator-review"),
        case_id=case_id,
        generated_at=generated_at,
        operator_id=operator_id,
        safe_mode=safe_mode,
        final_decision=final_decision,
        case_closed=case_closed,
        review_closed=review_closed,
        operator_acceptance_state=acceptance_state,
        autonomous_action=False,
        action_flags=action_flags,
        operator_notes=operator_notes,
        decision_trace=[entry.to_dict() for entry in decision_trace],
        final_governance_summary=governance,
        report_generation=report_generation,
        source_context=source_context,
    )


def export_json(result: OperatorReviewResult) -> str:
    return json.dumps(result.to_dict(), indent=2, sort_keys=True)


def export_markdown(result: OperatorReviewResult) -> str:
    payload = result.to_dict()
    trace = "\n".join(
        (
            f"- {item['step']}: {item['status']} - {item['summary']}"
        )
        for item in payload["decision_trace"]
    )
    missing = payload["final_governance_summary"].get("missing_data") or []
    missing_lines = "\n".join(f"- {item}" for item in missing) or "- none"
    flags = "\n".join(
        f"- {name}: {str(value).lower()}"
        for name, value in payload["action_flags"].items()
    )
    return (
        "# Operator Review Final Report\n\n"
        f"Generated: {payload['generated_at']}\n\n"
        "## Final Decision\n\n"
        f"- case_id: {payload['case_id']}\n"
        f"- operator_id: {payload['operator_id']}\n"
        f"- final_decision: {payload['final_decision']}\n"
        f"- operator_acceptance_state: {payload['operator_acceptance_state']}\n"
        f"- case_closed: {str(payload['case_closed']).lower()}\n"
        f"- autonomous_action: {str(payload['autonomous_action']).lower()}\n"
        f"- safe_mode: {payload['safe_mode']}\n\n"
        "## Operator Actions\n\n"
        f"{flags}\n\n"
        "## Operator Notes\n\n"
        f"{payload['operator_notes']}\n\n"
        "## Decision Trace\n\n"
        f"{trace}\n\n"
        "## Missing Data / Recovery\n\n"
        f"{missing_lines}\n\n"
        "## Governance Summary\n\n"
        "- Operator always decides\n"
        "- Control Plane observes\n"
        "- Autonomous action remains false\n"
        "- Local-first terminal review only\n"
        "- Decision trace preserved\n"
    )


def run_file(
    input_path: Path,
    output_path: Path | None = None,
    markdown_path: Path | None = None,
) -> dict[str, Any]:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    result = process_review(payload)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(export_json(result) + "\n", encoding="utf-8")
    if markdown_path is not None:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(export_markdown(result), encoding="utf-8")
    return result.to_dict()


def _read_live_case(payload: dict[str, Any]) -> dict[str, Any]:
    live_case = payload.get("live_case")
    if isinstance(live_case, dict):
        return live_case

    live_case_path = payload.get("live_case_path")
    if live_case_path:
        path = Path(str(live_case_path))
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return {}
            return data if isinstance(data, dict) else {}
    return {}


def _action_flags(review: dict[str, Any]) -> dict[str, bool]:
    return {
        "approve_recommendation": bool(review.get("approve_recommendation", False)),
        "reject_recommendation": bool(review.get("reject_recommendation", False)),
        "request_field_visit": bool(review.get("request_field_visit", False)),
        "request_thermal_inspection": bool(review.get("request_thermal_inspection", False)),
        "escalation_required": bool(review.get("escalation_required", False)),
        "safe_to_monitor": bool(review.get("safe_to_monitor", False)),
    }


def _missing_inputs(live_case: dict[str, Any], review: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if not live_case:
        missing.append("live_case")
    if _nested_get(live_case, ("case_id",), "") == "":
        missing.append("live_case.case_id")
    if _nested_get(live_case, ("recommendation", "decision_owner"), "") != "operator":
        missing.append("live_case.recommendation.decision_owner")
    if not any(_action_flags(review).values()) and not review.get("final_decision"):
        missing.append("operator_review.action_or_final_decision")
    if not review.get("operator_notes"):
        missing.append("operator_review.operator_notes")
    return missing


def _resolve_final_decision(
    review: dict[str, Any],
    action_flags: dict[str, bool],
    missing: list[str],
) -> str:
    if missing:
        return "UNKNOWN"

    explicit = str(review.get("final_decision") or "").upper().strip()
    if explicit in KNOWN_DECISIONS:
        return explicit

    if action_flags["escalation_required"]:
        return "ESCALATED"
    if action_flags["request_thermal_inspection"]:
        return "THERMAL_INSPECTION_REQUIRED"
    if action_flags["request_field_visit"]:
        return "FIELD_VISIT_REQUIRED"
    if action_flags["reject_recommendation"]:
        return "REJECTED"
    if action_flags["approve_recommendation"]:
        return "APPROVED"
    if action_flags["safe_to_monitor"]:
        return "SAFE_TO_MONITOR"
    return "UNKNOWN"


def _acceptance_state(final_decision: str, case_closed: bool, missing: list[str]) -> str:
    if missing:
        return "SAFE_MODE_REVIEW_REQUIRED"
    if final_decision == "APPROVED":
        return "OPERATOR_ACCEPTED"
    if final_decision == "REJECTED":
        return "OPERATOR_REJECTED"
    if final_decision == "SAFE_TO_MONITOR":
        return "OPERATOR_MONITORING_ACCEPTED"
    if final_decision in {"ESCALATED", "FIELD_VISIT_REQUIRED", "THERMAL_INSPECTION_REQUIRED"}:
        return "OPERATOR_FOLLOW_UP_REQUIRED"
    if case_closed:
        return "OPERATOR_CLOSED"
    return "UNKNOWN"


def _build_decision_trace(
    live_case: dict[str, Any],
    review: dict[str, Any],
    action_flags: dict[str, bool],
    final_decision: str,
    case_closed: bool,
    missing: list[str],
) -> list[DecisionTraceEntry]:
    entries = [
        DecisionTraceEntry(
            step="live_ingest",
            status="PRESENT" if live_case else "UNKNOWN",
            summary=f"Live case loaded for {_nested_get(live_case, ('case_id',), 'UNKNOWN')}.",
            evidence={
                "source": _nested_get(live_case, ("intake", "source"), "UNKNOWN"),
                "generated_at": _nested_get(live_case, ("generated_at",), "UNKNOWN"),
            },
        ),
        DecisionTraceEntry(
            step="diagnostics",
            status=_nested_get(live_case, ("priority", "level"), "UNKNOWN"),
            summary=_nested_get(live_case, ("diagnostic_summary", "summary"), "UNKNOWN"),
            evidence={
                "findings_count": len(_nested_get(live_case, ("diagnostic_summary", "findings"), [])),
                "evidence_gaps": _nested_get(live_case, ("diagnostic_summary", "evidence_gaps"), []),
            },
        ),
        DecisionTraceEntry(
            step="governance",
            status="OPERATOR_GATED",
            summary="Autonomous action is disabled; Control Plane observes only.",
            evidence={
                "decision_owner": _nested_get(live_case, ("recommendation", "decision_owner"), "UNKNOWN"),
                "autonomous_action_allowed": _nested_get(live_case, ("priority", "autonomous_action_allowed"), "UNKNOWN"),
            },
        ),
        DecisionTraceEntry(
            step="operator_review",
            status="SAFE_MODE" if missing else "REVIEWED",
            summary=str(review.get("operator_notes") or "UNKNOWN"),
            evidence={"action_flags": action_flags, "missing_data": missing},
        ),
        DecisionTraceEntry(
            step="final_decision",
            status=final_decision,
            summary=f"Case closed: {str(case_closed).lower()}.",
            evidence={"case_closed": case_closed, "review_closed": not missing and final_decision != "UNKNOWN"},
        ),
    ]
    return entries


def _recovery_hint(missing: list[str]) -> str:
    if not missing:
        return "No recovery required; preserve report and continue operator-controlled workflow."
    if "live_case" in missing:
        return "Run scripts/live_case_demo.ps1 or pass a valid live_case object/path before final decision."
    return "Complete missing operator review fields; keep final decision UNKNOWN until trace is complete."


def _nested_get(payload: dict[str, Any], path: tuple[str, ...], default: Any) -> Any:
    value: Any = payload
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
    if value is None:
        return default
    return value


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local operator review layer")
    parser.add_argument("--input", required=True, help="Path to operator review input JSON")
    parser.add_argument("--output", default="", help="Optional final JSON report path")
    parser.add_argument("--markdown", default="", help="Optional final Markdown report path")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = run_file(
            Path(args.input),
            Path(args.output) if args.output else None,
            Path(args.markdown) if args.markdown else None,
        )
    except Exception as exc:
        print(f"operator-review-error: {type(exc).__name__}: {exc}")
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
