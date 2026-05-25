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

