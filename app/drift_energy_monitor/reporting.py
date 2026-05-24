from __future__ import annotations

from pathlib import Path

from .observability import load_jsonl


def build_markdown_report(log_path: Path, report_path: Path) -> str:
    records = load_jsonl(log_path)
    analyses = [record for record in records if record["record_type"] == "analysis"]
    lines = [
        "# DRIFT_ENERGY_MONITOR Operational Report",
        "",
        "## Runtime Identity",
        "- name: DRIFT_ENERGY_MONITOR",
        "- codename: DEMON_CORE",
        "- runtime_mode: continuous_observation",
        "- doctrine: Operational Reality Is Noisy",
        "",
        "## Analysis Trace",
    ]
    for record in analyses:
        lines.append(
            f"- `{record['snapshot_id']}` state `{record['state_before']}` -> "
            f"`{record['state_after']}`; findings: {len(record['findings'])}; "
            f"metrics: {record['metrics']}"
        )
    lines.extend(
        [
            "",
            "## Witness Evidence",
            "- timestamp",
            "- metric_snapshot",
            "- decision_trace",
            "- economic_delta",
            "- runtime_state",
            "",
            "## Recovery Readiness",
        ]
    )
    if analyses:
        latest = analyses[-1]["recovery_plan"]
        lines.append(f"- automatic_actions: {latest['automatic_actions']}")
        lines.append(f"- manual_actions: {latest['manual_actions']}")
    else:
        lines.append("- no analysis records")
    report = "\n".join(lines) + "\n"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return report
