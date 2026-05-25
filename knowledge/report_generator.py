from __future__ import annotations

from typing import Any


def generate_operator_report(knowledge_os_result: dict[str, Any]) -> str:
    report_context = knowledge_os_result["report_context"]
    risk_map = knowledge_os_result["risk_map"]
    drift_energy = knowledge_os_result.get("drift_energy", {})
    decision_map = knowledge_os_result["decision_map"]
    review_queue = knowledge_os_result["human_review_queue"]

    lines = [
        "# EXIM Knowledge OS Report",
        "",
        "## Source",
        f"- source_file: `{knowledge_os_result['source_file']}`",
        f"- parser_warnings: {len(knowledge_os_result.get('parser_warnings', []))}",
        "",
        "## Decision",
        f"- decision: {decision_map['decision']}",
        f"- validation_level: {decision_map['validation_level']}",
        f"- safe_state: {decision_map['safe_state']}",
        f"- ready_for_client_recommendation: {report_context['ready_for_client_recommendation']}",
        "",
        "## Risk",
        f"- risk_score: {risk_map['risk_score']}",
        f"- classification: {risk_map['classification']}",
        f"- blocked_count: {risk_map['blocked_count']}",
        "",
        "## Drift Energy",
        f"- safe_state: {drift_energy.get('payload', {}).get('safe_state', 'UNKNOWN')}",
        f"- normalized_score: {drift_energy.get('payload', {}).get('normalized_score', 'UNKNOWN')}",
        f"- classification: {drift_energy.get('trace', {}).get('classification', 'UNKNOWN')}",
        "",
        "## Evidence Map",
    ]
    for item in report_context.get("evidence_map", []):
        lines.append(
            "- {chunk_id} | {domain} | {evidence_type} | confidence={confidence} | validation={validation_status}".format(
                **item
            )
        )

    lines.extend(["", "## Human Review Queue"])
    if review_queue:
        for item in review_queue:
            lines.append(f"- {item['chunk_id']}: {item['reason']}")
    else:
        lines.append("- empty")

    lines.extend(
        [
            "",
            "## Output Gate",
            "No recommendation without trace. No trace without source. No source without classification. No output without validation level.",
        ]
    )
    return "\n".join(lines)
