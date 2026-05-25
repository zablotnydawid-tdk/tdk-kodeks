from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_human_review_queue(report_context: dict[str, Any], decision_map: dict[str, Any]) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    validation_by_id = {
        item.get("chunk_id"): item for item in report_context.get("validation", [])
    }
    for item in report_context.get("blocked_recommendation_claims", []):
        chunk_id = item.get("chunk_id")
        validation = validation_by_id.get(chunk_id, {})
        queue.append(
            {
                "chunk_id": chunk_id,
                "claim": item.get("claim", ""),
                "reason": item.get("reason", ""),
                "validation_status": validation.get("validation_status", "HUMAN_REVIEW_REQUIRED"),
                "decision_context": decision_map.get("decision", "UNKNOWN"),
                "operator_action": "review_source_trace_before_client_output",
            }
        )
    return queue


def write_human_review_queue(queue: list[dict[str, Any]], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in queue:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
