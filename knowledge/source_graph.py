from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from knowledge.chunker import KnowledgeChunk


@dataclass(frozen=True)
class SourceGraph:
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    risk_map: list[dict[str, Any]]
    dependency_map: list[dict[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "nodes": self.nodes,
            "edges": self.edges,
            "risk_map": self.risk_map,
            "dependency_map": self.dependency_map,
        }


def build_source_graph(chunks: list[KnowledgeChunk]) -> SourceGraph:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    risk_map: list[dict[str, Any]] = []
    dependency_map: list[dict[str, Any]] = []
    previous_by_domain: dict[str, str] = {}

    for chunk in chunks:
        trace = chunk.trace
        nodes.append(
            {
                "id": chunk.chunk_id,
                "source_file": trace.source_file,
                "page": trace.page,
                "domain": trace.domain,
                "confidence": trace.confidence,
                "requires_human_review": trace.requires_human_review,
            }
        )
        if trace.domain in previous_by_domain:
            edges.append(
                {
                    "from": previous_by_domain[trace.domain],
                    "to": chunk.chunk_id,
                    "relation": "same_domain_sequence",
                    "domain": trace.domain,
                }
            )
        previous_by_domain[trace.domain] = chunk.chunk_id

        if trace.requires_human_review or trace.confidence < 0.6:
            risk_map.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "risk": "human_review_required" if trace.requires_human_review else "low_confidence",
                    "domain": trace.domain,
                    "notes": trace.metadata.get("risk_notes", []),
                }
            )

        if trace.domain in {"REGULATORY", "SUBSIDY", "BILLING"}:
            dependency_map.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "depends_on": "freshness_validation",
                    "reason": "normative or financial policy content cannot become recommendation without review",
                }
            )
        if trace.domain == "TECHNICAL" and "253v" in trace.claim.lower():
            dependency_map.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "depends_on": "field_measurement_validation",
                    "reason": "253V diagnostic content needs site-specific measurement context",
                }
            )

    return SourceGraph(nodes=nodes, edges=edges, risk_map=risk_map, dependency_map=dependency_map)
