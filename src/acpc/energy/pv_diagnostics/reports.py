
from __future__ import annotations
from dataclasses import asdict
from typing import Dict, Any
from .models import PVInstallationState


def build_json_report(state: PVInstallationState) -> Dict[str, Any]:
    recommended = list(dict.fromkeys([f.recommendation for f in state.findings] + state.actions))
    return {
        "report_type": "PV_DIAGNOSTIC_REPORT",
        "site_id": state.site_id,
        "status": state.status.value,
        "main_findings": [f.diagnosis for f in state.findings],
        "findings": [asdict(f) for f in state.findings],
        "recommended_actions": recommended,
        "witness_mode": {
            "intervention_logged": "tak" if state.witness_log else "nie",
            "signature": "WitnessAI Serwis OZE",
            "location_required": "tak",
            "log": state.witness_log,
        },
        "consistency": {
            "lamport_clock": state.lamport_clock,
            "processed_events": len(state.processed_event_ids),
        },
    }


def build_markdown_report(state: PVInstallationState) -> str:
    report = build_json_report(state)
    lines = [
        "# Raport diagnostyczny PV",
        "",
        f"**Site:** {report['site_id']}",
        f"**Status:** {report['status']}",
        "",
        "## Główne ustalenia",
    ]
    for item in report["main_findings"] or ["brak aktywnych ustaleń"]:
        lines.append(f"- {item}")
    lines += ["", "## Rekomendowane działania"]
    for item in report["recommended_actions"] or ["kontynuuj monitoring"]:
        lines.append(f"- {item}")
    lines += ["", "## Tryb świadka", f"- intervention_logged: {report['witness_mode']['intervention_logged']}", f"- signature: {report['witness_mode']['signature']}"]
    return "\n".join(lines) + "\n"
