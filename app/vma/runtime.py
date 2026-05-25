from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from typing import Any


VOICE_TRIGGERS = ("voice mode", "vma", "vma-uscp", "tryb glosowy", "tryb głosowy")
CONFUSION_TRIGGERS = (
    "confusion",
    "lost",
    "zgubilem",
    "zgubiłem",
    "zgubione",
    "nie wiem",
    "chaos",
    "reset context",
)


@dataclass
class VMARuntimeState:
    active: bool = False
    mode: str = "text"
    current_topic: str = "unknown"
    current_layer: str = "conversation"
    parent_context: str = "none"
    active_objective: str = "preserve continuity"
    known_hierarchy: list[str] = field(default_factory=list)
    dependency_chain: list[str] = field(default_factory=list)
    compression_level: str = "low"
    cognitive_load: float = 0.0
    continuity_score: float = 1.0
    topology_retention_score: float = 1.0
    recovery_efficiency: float = 1.0
    hierarchy_stability: float = 1.0
    visual_reentry_required: bool = False
    recursive_stability: str = "stable"
    last_stable_anchor: str = "none"
    recovery_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_state() -> dict[str, Any]:
    return VMARuntimeState().to_dict()


def detect_structure(turn: dict[str, Any]) -> dict[str, Any]:
    text = str(turn.get("text", ""))
    lower = text.lower()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    list_items = [
        _strip_marker(line)
        for line in lines
        if re.match(r"^(-|\*|\d+[\.\)]|[a-zA-Z][\.\)])\s+", line)
    ]
    flow_markers = ("->", "=>", " then ", " następnie ", " potem ", "flow", "pipeline")
    has_flow = any(marker in lower for marker in flow_markers) or len(list_items) >= 3
    confusion_signal = any(trigger in lower for trigger in CONFUSION_TRIGGERS)
    mode_hint = str(turn.get("mode", "")).lower()
    voice_mode = mode_hint == "voice" or any(trigger in lower for trigger in VOICE_TRIGGERS)

    topic = turn.get("topic") or _topic_from_text(text)
    layer = turn.get("layer") or _layer_from_text(lower)
    objective = turn.get("objective") or _objective_from_text(text)

    return {
        "voice_mode_detected": voice_mode,
        "has_list": bool(list_items),
        "has_flow": has_flow,
        "confusion_signal": confusion_signal,
        "items": list_items,
        "topic": topic,
        "layer": layer,
        "objective": objective,
        "parent_context": turn.get("parent_context", "operator-session"),
        "raw_text_length": len(text),
    }


def map_topology(structure: dict[str, Any]) -> dict[str, Any]:
    items = list(structure.get("items", []))
    if not items:
        items = [structure.get("objective", "preserve continuity")]

    nodes = [
        {
            "id": f"node_{index + 1}",
            "label": item,
            "layer": structure.get("layer", "conversation"),
        }
        for index, item in enumerate(items)
    ]
    edges = [
        {
            "from": nodes[index]["id"],
            "to": nodes[index + 1]["id"],
            "relation": "next",
        }
        for index in range(len(nodes) - 1)
    ]
    gaps = []
    if structure.get("confusion_signal"):
        gaps.append("operator_confusion_signal")
    if not structure.get("voice_mode_detected"):
        gaps.append("voice_mode_not_explicit")

    return {
        "nodes": nodes,
        "edges": edges,
        "gaps": gaps,
        "root": nodes[0]["id"] if nodes else "none",
        "topic": structure.get("topic", "unknown"),
        "layer": structure.get("layer", "conversation"),
    }


def inject_anchors(topology: dict[str, Any]) -> dict[str, Any]:
    nodes = list(topology.get("nodes", []))
    anchors = []
    if nodes:
        anchors.append(
            {
                "id": "anchor_root",
                "node_id": nodes[0]["id"],
                "kind": "root",
                "label": nodes[0]["label"],
            }
        )
    if len(nodes) > 1:
        anchors.append(
            {
                "id": "anchor_latest",
                "node_id": nodes[-1]["id"],
                "kind": "latest",
                "label": nodes[-1]["label"],
            }
        )
    if topology.get("topic") != "unknown":
        anchors.append(
            {
                "id": "anchor_topic",
                "node_id": topology.get("root", "none"),
                "kind": "topic",
                "label": topology["topic"],
            }
        )

    return {
        "anchors": anchors,
        "last_stable_anchor": anchors[-1]["id"] if anchors else "none",
        "missing_anchor_count": 0 if anchors else 1,
    }


def estimate_cognitive_load(
    structure: dict[str, Any], topology: dict[str, Any], anchors: dict[str, Any]
) -> float:
    node_count = len(topology.get("nodes", []))
    edge_count = len(topology.get("edges", []))
    gap_count = len(topology.get("gaps", []))
    missing_anchor_count = int(anchors.get("missing_anchor_count", 0))
    load = 0.12 + (node_count * 0.08) + (edge_count * 0.04)
    load += gap_count * 0.18
    load += missing_anchor_count * 0.22
    if structure.get("confusion_signal"):
        load += 0.3
    return round(min(load, 1.0), 4)


def recover(state: dict[str, Any], signal: str = "") -> dict[str, Any]:
    recovered = deepcopy(state)
    signal_lower = signal.lower()
    should_recover = bool(recovered.get("recovery_required")) or any(
        trigger in signal_lower for trigger in CONFUSION_TRIGGERS
    )
    if should_recover:
        recovered["mode"] = "recovery"
        recovered["recovery_required"] = True
        recovered["compression_level"] = "high"
        recovered["active_objective"] = "restore voice continuity from last stable anchor"
    return recovered


def process_turn(turn: dict[str, Any], state: dict[str, Any] | None = None) -> dict[str, Any]:
    previous = deepcopy(state) if state is not None else default_state()
    structure = detect_structure(turn)
    topology = map_topology(structure)
    anchors = inject_anchors(topology)
    cognitive_load = estimate_cognitive_load(structure, topology, anchors)
    recovery_required = structure["confusion_signal"] or cognitive_load >= 0.72

    updated = deepcopy(previous)
    updated.update(
        {
            "active": structure["voice_mode_detected"] or previous.get("active", False),
            "mode": "voice" if structure["voice_mode_detected"] else previous.get("mode", "text"),
            "current_topic": structure["topic"],
            "current_layer": structure["layer"],
            "parent_context": structure["parent_context"],
            "active_objective": structure["objective"],
            "known_hierarchy": [node["label"] for node in topology["nodes"]],
            "dependency_chain": [
                f"{edge['from']}->{edge['to']}" for edge in topology["edges"]
            ],
            "compression_level": _compression_level(cognitive_load),
            "cognitive_load": cognitive_load,
            "visual_reentry_required": bool(turn.get("visual_reentry_required", False)),
            "last_stable_anchor": anchors["last_stable_anchor"],
            "recovery_required": recovery_required,
        }
    )
    if recovery_required:
        updated = recover(updated, str(turn.get("text", "")))

    return {
        "voice_stable_output": _voice_stable_output(updated, topology, anchors),
        "state": updated,
        "structure": structure,
        "topology": topology,
        "anchors": anchors,
        "telemetry": {
            "node_count": len(topology["nodes"]),
            "edge_count": len(topology["edges"]),
            "anchor_count": len(anchors["anchors"]),
            "missing_anchor_count": anchors["missing_anchor_count"],
            "cognitive_load": cognitive_load,
            "recovery_required": updated["recovery_required"],
        },
    }


def detect_continuity_break(
    session: dict[str, Any], processed_turns: list[dict[str, Any]]
) -> dict[str, Any]:
    interruption_seen = any(
        turn.get("event_type") == "interruption"
        for turn in session.get("turns", [])
    )
    confusion_seen = any(
        item["structure"].get("confusion_signal") for item in processed_turns
    )
    visual_reentry_required = any(
        bool(turn.get("visual_reentry_required", False))
        for turn in session.get("turns", [])
    )
    first_nodes = _node_labels(processed_turns[0]) if processed_turns else []
    final_nodes = _node_labels(processed_turns[-1]) if processed_turns else []
    collapse_detected = bool(first_nodes) and len(final_nodes) < max(1, len(first_nodes) // 2)
    continuation_after_drift = _has_event_after(session, "continuation", "interruption")

    return {
        "interruption_seen": interruption_seen,
        "confusion_seen": confusion_seen,
        "visual_reentry_required": visual_reentry_required,
        "collapse_detected": collapse_detected,
        "continuation_after_drift": continuation_after_drift,
        "continuity_break_detected": interruption_seen or confusion_seen or collapse_detected,
    }


def evaluate_topology_retention(
    session: dict[str, Any], processed_turns: list[dict[str, Any]]
) -> dict[str, float]:
    expected_hierarchy = list(session.get("expected_hierarchy", []))
    expected_dependency_chain = list(session.get("expected_dependency_chain", []))
    final_state = processed_turns[-1]["state"] if processed_turns else default_state()
    final_hierarchy = list(final_state.get("known_hierarchy", []))
    final_dependency_chain = list(final_state.get("dependency_chain", []))

    hierarchy_stability = _ordered_retention_score(expected_hierarchy, final_hierarchy)
    dependency_direction = _set_retention_score(
        expected_dependency_chain, final_dependency_chain
    )
    topology_retention_score = round(
        (hierarchy_stability + dependency_direction) / 2, 4
    )

    return {
        "topology_retention_score": topology_retention_score,
        "hierarchy_stability": hierarchy_stability,
        "dependency_direction_score": dependency_direction,
    }


def measure_recovery(
    session: dict[str, Any],
    processed_turns: list[dict[str, Any]],
    continuity_break: dict[str, Any],
) -> dict[str, Any]:
    turns = list(session.get("turns", []))
    interruption_index = _event_index(turns, "interruption")
    recovery_index = _event_index(turns, "recovery_attempt")
    continuation_index = _event_index(turns, "continuation")
    recovery_after_interruption = (
        interruption_index >= 0 and recovery_index > interruption_index
    )
    continuation_after_recovery = recovery_index >= 0 and continuation_index > recovery_index
    final_recovery_required = (
        processed_turns[-1]["state"].get("recovery_required", False)
        if processed_turns
        else True
    )

    score = 0.0
    if recovery_after_interruption:
        score += 0.45
    if continuation_after_recovery:
        score += 0.35
    if not final_recovery_required:
        score += 0.15
    if not continuity_break.get("visual_reentry_required", False):
        score += 0.05

    return {
        "recovery_efficiency": round(min(score, 1.0), 4),
        "recovery_after_interruption": recovery_after_interruption,
        "continuation_after_recovery": continuation_after_recovery,
        "final_recovery_required": final_recovery_required,
    }


def process_session(session: dict[str, Any]) -> dict[str, Any]:
    state = default_state()
    processed_turns = []
    for turn in session.get("turns", []):
        result = process_turn(turn, state)
        state = result["state"]
        processed_turns.append(result)

    continuity_break = detect_continuity_break(session, processed_turns)
    topology = evaluate_topology_retention(session, processed_turns)
    recovery = measure_recovery(session, processed_turns, continuity_break)

    visual_reentry_required = continuity_break["visual_reentry_required"]
    recursive_stability = (
        "stable"
        if topology["topology_retention_score"] >= 0.8
        and recovery["recovery_efficiency"] >= 0.7
        and not continuity_break["collapse_detected"]
        else "unstable"
    )
    continuity_score = round(
        (
            topology["topology_retention_score"]
            + recovery["recovery_efficiency"]
            + (1.0 if recursive_stability == "stable" else 0.0)
            + (0.0 if visual_reentry_required else 1.0)
        )
        / 4,
        4,
    )
    first_real_continuity_win = (
        topology["topology_retention_score"] >= 0.8
        and recovery["recovery_efficiency"] >= 0.7
        and recursive_stability == "stable"
        and visual_reentry_required is False
    )

    state.update(
        {
            "continuity_score": continuity_score,
            "topology_retention_score": topology["topology_retention_score"],
            "recovery_efficiency": recovery["recovery_efficiency"],
            "hierarchy_stability": topology["hierarchy_stability"],
            "visual_reentry_required": visual_reentry_required,
            "recursive_stability": recursive_stability,
            "recovery_required": not first_real_continuity_win,
        }
    )

    report = {
        "benchmark": "FIRST_REAL_CONTINUITY_WIN",
        "session_id": session.get("session_id", "unknown"),
        "minimum_duration_minutes": session.get("duration_minutes", 0),
        "first_real_continuity_win": first_real_continuity_win,
        "continuity_report_json": {
            "continuity_score": continuity_score,
            "topology_retention_score": topology["topology_retention_score"],
            "recovery_efficiency": recovery["recovery_efficiency"],
            "hierarchy_stability": topology["hierarchy_stability"],
            "dependency_direction_score": topology["dependency_direction_score"],
            "visual_reentry_required": visual_reentry_required,
            "recursive_stability": recursive_stability,
            "continuity_break": continuity_break,
            "recovery": recovery,
        },
        "continuity_summary_markdown": _continuity_summary_markdown(
            session, continuity_score, topology, recovery, visual_reentry_required, recursive_stability, first_real_continuity_win
        ),
        "continuity_state_update": state,
        "turn_count": len(processed_turns),
    }
    return report


def _strip_marker(line: str) -> str:
    return re.sub(r"^(-|\*|\d+[\.\)]|[a-zA-Z][\.\)])\s+", "", line).strip()


def _topic_from_text(text: str) -> str:
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if not first_line:
        return "unknown"
    cleaned = re.sub(r"^(voice mode|vma-uscp|vma)[:\s-]*", "", first_line, flags=re.I)
    return cleaned[:80] or "unknown"


def _layer_from_text(lower: str) -> str:
    if "control plane" in lower:
        return "control_plane"
    if "runtime" in lower:
        return "runtime"
    if "dashboard" in lower:
        return "dashboard"
    if "operator" in lower:
        return "operator_flow"
    return "conversation"


def _objective_from_text(text: str) -> str:
    for line in text.splitlines():
        if "cel:" in line.lower() or "objective:" in line.lower():
            return line.split(":", 1)[-1].strip() or "preserve continuity"
    return "preserve voice continuity"


def _compression_level(cognitive_load: float) -> str:
    if cognitive_load >= 0.72:
        return "high"
    if cognitive_load >= 0.42:
        return "medium"
    return "low"


def _voice_stable_output(
    state: dict[str, Any], topology: dict[str, Any], anchors: dict[str, Any]
) -> str:
    recovery = "yes" if state.get("recovery_required") else "no"
    return (
        "VOICE-STABLE: "
        f"topic={state['current_topic']}; "
        f"layer={state['current_layer']}; "
        f"nodes={len(topology.get('nodes', []))}; "
        f"anchors={len(anchors.get('anchors', []))}; "
        f"recovery_required={recovery}; "
        f"last_anchor={state['last_stable_anchor']}"
    )


def _node_labels(processed_turn: dict[str, Any]) -> list[str]:
    return [node["label"] for node in processed_turn.get("topology", {}).get("nodes", [])]


def _ordered_retention_score(expected: list[str], actual: list[str]) -> float:
    if not expected:
        return 1.0
    expected_norm = [_normalize_label(item) for item in expected]
    actual_norm = [_normalize_label(item) for item in actual]
    cursor = 0
    matches = 0
    for item in expected_norm:
        try:
            found = actual_norm.index(item, cursor)
        except ValueError:
            continue
        matches += 1
        cursor = found + 1
    return round(matches / len(expected_norm), 4)


def _set_retention_score(expected: list[str], actual: list[str]) -> float:
    if not expected:
        return 1.0
    expected_set = {_normalize_label(item) for item in expected}
    actual_set = {_normalize_label(item) for item in actual}
    return round(len(expected_set & actual_set) / len(expected_set), 4)


def _normalize_label(value: str) -> str:
    return re.sub(r"\s+", " ", str(value).strip().lower())


def _event_index(turns: list[dict[str, Any]], event_type: str) -> int:
    for index, turn in enumerate(turns):
        if turn.get("event_type") == event_type:
            return index
    return -1


def _has_event_after(
    session: dict[str, Any], target_event: str, after_event: str
) -> bool:
    turns = list(session.get("turns", []))
    after_index = _event_index(turns, after_event)
    target_index = _event_index(turns, target_event)
    return after_index >= 0 and target_index > after_index


def _continuity_summary_markdown(
    session: dict[str, Any],
    continuity_score: float,
    topology: dict[str, float],
    recovery: dict[str, Any],
    visual_reentry_required: bool,
    recursive_stability: str,
    first_real_continuity_win: bool,
) -> str:
    status = "ACHIEVED" if first_real_continuity_win else "NOT ACHIEVED"
    return (
        "# FIRST_REAL_CONTINUITY_WIN\n\n"
        f"- session_id: {session.get('session_id', 'unknown')}\n"
        f"- status: {status}\n"
        f"- continuity_score: {continuity_score}\n"
        f"- topology_retention_score: {topology['topology_retention_score']}\n"
        f"- recovery_efficiency: {recovery['recovery_efficiency']}\n"
        f"- hierarchy_stability: {topology['hierarchy_stability']}\n"
        f"- visual_reentry_required: {str(visual_reentry_required).lower()}\n"
        f"- recursive_stability: {recursive_stability}\n"
    )
