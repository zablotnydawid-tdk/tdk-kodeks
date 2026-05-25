from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from knowledge.chunker import KnowledgeChunk
from knowledge.regulatory_validator import validate_chunks
from knowledge.source_graph import build_source_graph


@dataclass(frozen=True)
class ReportContext:
    chunks: list[dict[str, Any]]
    source_graph: dict[str, Any]
    evidence_map: list[dict[str, Any]]
    validation: list[dict[str, Any]]
    blocked_recommendation_claims: list[dict[str, Any]]
    ready_for_client_recommendation: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "chunks": self.chunks,
            "source_graph": self.source_graph,
            "evidence_map": self.evidence_map,
            "validation": self.validation,
            "blocked_recommendation_claims": self.blocked_recommendation_claims,
            "ready_for_client_recommendation": self.ready_for_client_recommendation,
        }


def build_report_context(chunks: list[KnowledgeChunk]) -> ReportContext:
    graph = build_source_graph(chunks)
    validation = validate_chunks(chunks)
    validation_by_id = {item.chunk_id: item for item in validation}

    evidence_map: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for chunk in chunks:
        trace = chunk.trace
        validation_result = validation_by_id[chunk.chunk_id]
        evidence = {
            "chunk_id": chunk.chunk_id,
            "source_file": trace.source_file,
            "page": trace.page,
            "domain": trace.domain,
            "evidence_type": trace.evidence_type,
            "confidence": trace.confidence,
            "validation_status": validation_result.validation_status,
            "requires_human_review": validation_result.human_validation_required,
        }
        evidence_map.append(evidence)
        if validation_result.human_validation_required:
            blocked.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "claim": trace.claim,
                    "reason": validation_result.reason,
                }
            )

    return ReportContext(
        chunks=[chunk.as_dict() for chunk in chunks],
        source_graph=graph.as_dict(),
        evidence_map=evidence_map,
        validation=[item.as_dict() for item in validation],
        blocked_recommendation_claims=blocked,
        ready_for_client_recommendation=len(blocked) == 0,
    )
