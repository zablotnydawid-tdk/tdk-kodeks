from __future__ import annotations

from pathlib import Path

from .logging import load_jsonl


def build_markdown_report(log_path: Path, report_path: Path) -> str:
    records = load_jsonl(log_path)
    decisions = [record for record in records if record["record_type"] == "decision"]
    events = [record for record in records if record["record_type"] == "event"]
    state_changes = [
        record for record in records if record["record_type"] == "state_change"
    ]
    confined = [
        record
        for record in events
        if record["event"]["event_type"] == "confinement_triggered"
    ]
    critical = [
        record
        for record in events
        if record["event"]["severity"] == "critical"
    ]
    lines = [
        "# WitnessAI Final Axis Operational Report",
        "",
        "## Runtime Summary",
        f"- Events processed: {len(events)}",
        f"- Decisions logged: {len(decisions)}",
        f"- State changes explained: {len(state_changes)}",
        f"- Drift confinement triggers: {len(confined)}",
        f"- Critical operator-gated events: {len(critical)}",
        "",
        "## Decision Trace",
    ]
    for record in decisions:
        decision = record["decision"]
        lines.append(
            f"- `{decision['trace_id']}` `{decision['decision']}` -> "
            f"`{decision['action']}`: {decision['reason']}"
        )
    lines.extend(["", "## Next Integration Steps", ""])
    lines.extend(
        [
            "1. Connect CyberPhysicalLink to real EMS/PV command gateways behind an operator-gated adapter.",
            "2. Replace sample semantic scoring with the production WitnessAI governance model.",
            "3. Persist JSONL logs to the official audit store and mirror report artifacts into case/session records.",
            "4. Add signed operator identity to override events before live control integration.",
        ]
    )
    report = "\n".join(lines) + "\n"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return report
