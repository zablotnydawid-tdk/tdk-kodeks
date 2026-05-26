from __future__ import annotations

from typing import Any


def build_witness_markdown(report: dict[str, Any]) -> str:
    findings = "\n".join(
        f"- {item.get('severity', 'unknown')}: {item.get('diagnosis', 'unknown')}"
        for item in report.get("findings", [])
    ) or "- brak aktywnych ustalen"
    recommendations = "\n".join(
        f"- {item}" for item in report.get("recommendations", [])
    ) or "- kontynuuj monitoring"
    trace = "\n".join(
        f"- {item.get('step')}: {item.get('status')} - {item.get('summary')}"
        for item in report.get("decision_trace", [])
    )
    witness = report.get("witness_mode", {})
    return (
        "# ACPC PV Witness Report\n\n"
        f"Generated: {report['timestamp']}\n\n"
        "## Summary\n\n"
        f"{report['summary']}\n\n"
        "## Report State\n\n"
        f"- report_id: {report['report_id']}\n"
        f"- site_id: {report['site_id']}\n"
        f"- status: {report['status']}\n"
        f"- risk_level: {report['risk_level']}\n"
        f"- score: {report['score']}\n"
        f"- input_hash: {report['input_hash']}\n"
        f"- operator_review_required: {str(report['operator_review_required']).lower()}\n"
        f"- autonomous_action: {str(report['autonomous_action']).lower()}\n\n"
        "## Findings\n\n"
        f"{findings}\n\n"
        "## Recommendations\n\n"
        f"{recommendations}\n\n"
        "## Decision Trace\n\n"
        f"{trace}\n\n"
        "## Witness Mode\n\n"
        f"- enabled: {str(witness.get('enabled', True)).lower()}\n"
        f"- signature: {witness.get('signature', 'WitnessAI Serwis OZE')}\n"
        f"- intervention_logged: {str(witness.get('intervention_logged', True)).lower()}\n"
    )


def response_summary(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "report_id": report["report_id"],
        "summary": report["summary"],
        "status": report["status"],
        "risk_level": report["risk_level"],
    }
