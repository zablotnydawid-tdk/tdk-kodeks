from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .runtime import process_session, process_turn


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_session(session_id: str | None = None, notes: str = "") -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "session_id": session_id or f"vma-real-{uuid4().hex[:12]}",
        "started_at": utc_now(),
        "ended_at": None,
        "turns": [],
        "notes": notes,
        "first_real_user_continuity_win": False,
        "continuity_metrics": {},
    }


def append_turn(
    session: dict[str, Any],
    user_input: str,
    assistant_output: str,
    event_type: str = "turn",
    notes: str = "",
    visual_reentry_required: bool = False,
) -> dict[str, Any]:
    updated = deepcopy(session)
    previous_state = (
        updated["turns"][-1]["state_after"] if updated.get("turns") else None
    )
    runtime_turn = {
        "turn_id": f"turn-{len(updated.get('turns', [])) + 1:03d}",
        "event_type": event_type,
        "mode": "voice",
        "topic": updated.get("session_id", "real user session"),
        "layer": "real_user_session",
        "parent_context": "VMA real user session recorder",
        "objective": "preserve real user continuity",
        "text": f"{user_input}\n{assistant_output}".strip(),
        "visual_reentry_required": visual_reentry_required,
    }
    processed = process_turn(runtime_turn, previous_state)
    interruption_detected = event_type == "interruption"
    recovery_triggered = event_type == "recovery_attempt" or processed["state"].get(
        "recovery_required", False
    )

    updated.setdefault("turns", []).append(
        {
            "turn_id": runtime_turn["turn_id"],
            "event_type": event_type,
            "recorded_at": utc_now(),
            "user_input": user_input,
            "assistant_output": assistant_output,
            "detected_structure": processed["structure"],
            "topology_map": processed["topology"],
            "continuity_score": processed["state"].get("continuity_score", 1.0),
            "cognitive_load": processed["state"]["cognitive_load"],
            "recovery_required": processed["state"]["recovery_required"],
            "recovery_triggered": recovery_triggered,
            "visual_reentry_required": visual_reentry_required,
            "interruption_detected": interruption_detected,
            "notes": notes,
            "state_after": processed["state"],
        }
    )
    return updated


def finalize_session(session: dict[str, Any]) -> dict[str, Any]:
    updated = deepcopy(session)
    updated["ended_at"] = updated.get("ended_at") or utc_now()
    benchmark_session = _to_benchmark_session(updated)
    benchmark = process_session(benchmark_session)
    metrics = benchmark["continuity_report_json"]
    minimum_turns_met = len(updated.get("turns", [])) >= 5
    interruption_or_recovery = any(
        turn.get("interruption_detected") or turn.get("recovery_triggered")
        for turn in updated.get("turns", [])
    )
    recursive_stability = (
        "stable"
        if metrics["topology_retention_score"] >= 0.75
        and metrics["recovery_efficiency"] >= 0.60
        and metrics["visual_reentry_required"] is False
        else "unstable"
    )
    continuity_score = round(
        (
            metrics["topology_retention_score"]
            + metrics["recovery_efficiency"]
            + (1.0 if recursive_stability == "stable" else 0.0)
            + (0.0 if metrics["visual_reentry_required"] else 1.0)
        )
        / 4,
        4,
    )
    first_real_user_win = (
        continuity_score >= 0.75
        and metrics["topology_retention_score"] >= 0.75
        and metrics["recovery_efficiency"] >= 0.60
        and metrics["visual_reentry_required"] is False
        and minimum_turns_met
        and interruption_or_recovery
    )

    updated["first_real_user_continuity_win"] = first_real_user_win
    updated["continuity_metrics"] = {
        "continuity_score": continuity_score,
        "topology_retention_score": metrics["topology_retention_score"],
        "recovery_efficiency": metrics["recovery_efficiency"],
        "hierarchy_stability": metrics["hierarchy_stability"],
        "visual_reentry_required": metrics["visual_reentry_required"],
        "recursive_stability": recursive_stability,
        "minimum_turns_met": minimum_turns_met,
        "interruption_or_recovery_event": interruption_or_recovery,
    }
    return updated


def build_markdown_report(session: dict[str, Any]) -> str:
    metrics = session.get("continuity_metrics", {})
    status = (
        "ACHIEVED"
        if session.get("first_real_user_continuity_win")
        else "NOT_ACHIEVED"
    )
    return (
        "# VMA Real User Session Validation\n\n"
        f"- session_id: {session.get('session_id')}\n"
        f"- started_at: {session.get('started_at')}\n"
        f"- ended_at: {session.get('ended_at')}\n"
        f"- turns: {len(session.get('turns', []))}\n"
        f"- FIRST_REAL_USER_CONTINUITY_WIN: {status}\n\n"
        "## Metrics\n\n"
        f"- continuity_score: {metrics.get('continuity_score')}\n"
        f"- topology_retention_score: {metrics.get('topology_retention_score')}\n"
        f"- recovery_efficiency: {metrics.get('recovery_efficiency')}\n"
        f"- hierarchy_stability: {metrics.get('hierarchy_stability')}\n"
        f"- visual_reentry_required: {metrics.get('visual_reentry_required')}\n"
        f"- recursive_stability: {metrics.get('recursive_stability')}\n"
        f"- minimum_turns_met: {metrics.get('minimum_turns_met')}\n"
        f"- interruption_or_recovery_event: {metrics.get('interruption_or_recovery_event')}\n\n"
        "## Safety\n\n"
        "Manual transcript only. No microphone, audio recording, cloud runtime, dashboard, or sensitive data capture.\n"
    )


def save_session(session: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(session, indent=2, sort_keys=True), encoding="utf-8")


def load_session(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_report(session: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_markdown_report(session), encoding="utf-8")


def _to_benchmark_session(session: dict[str, Any]) -> dict[str, Any]:
    turns = session.get("turns", [])
    first_topology = turns[0].get("topology_map", {}) if turns else {}
    expected_hierarchy = [
        node["label"] for node in first_topology.get("nodes", [])
    ] or ["preserve real user continuity"]
    expected_dependency_chain = [
        f"{edge['from']}->{edge['to']}" for edge in first_topology.get("edges", [])
    ]
    return {
        "session_id": session.get("session_id", "real-user-session"),
        "duration_minutes": max(5, len(turns)),
        "expected_hierarchy": expected_hierarchy,
        "expected_dependency_chain": expected_dependency_chain,
        "turns": [
            {
                "turn_id": turn.get("turn_id"),
                "event_type": turn.get("event_type", "turn"),
                "mode": "voice",
                "topic": session.get("session_id", "real user session"),
                "layer": "real_user_session",
                "parent_context": "VMA real user session recorder",
                "objective": "preserve real user continuity",
                "text": f"{turn.get('user_input', '')}\n{turn.get('assistant_output', '')}".strip(),
                "visual_reentry_required": turn.get("visual_reentry_required", False),
            }
            for turn in turns
        ],
    }
