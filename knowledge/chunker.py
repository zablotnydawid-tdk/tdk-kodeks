from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from knowledge.domain_classifier import classify_domain
from knowledge.evidence_mapper import assess_evidence


@dataclass(frozen=True)
class KnowledgeTrace:
    source_file: str
    page: int
    domain: str
    claim: str
    evidence_type: str
    confidence: float
    requires_human_review: bool
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "page": self.page,
            "domain": self.domain,
            "claim": self.claim,
            "evidence_type": self.evidence_type,
            "confidence": self.confidence,
            "requires_human_review": self.requires_human_review,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    text: str
    trace: KnowledgeTrace

    def as_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "trace": self.trace.as_dict(),
        }


def chunk_text(
    text: str,
    source_file: str,
    page: int = 0,
    max_chars: int = 900,
) -> list[KnowledgeChunk]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []

    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", normalized) if part.strip()]
    chunks: list[str] = []
    current = ""
    for sentence in sentences or [normalized]:
        if current and len(current) + len(sentence) + 1 > max_chars:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)

    result: list[KnowledgeChunk] = []
    for index, claim in enumerate(chunks, start=1):
        classification = classify_domain(claim)
        evidence = assess_evidence(claim, classification.domain, classification.confidence)
        trace = KnowledgeTrace(
            source_file=source_file,
            page=page,
            domain=classification.domain,
            claim=claim,
            evidence_type=evidence.evidence_type,
            confidence=evidence.confidence,
            requires_human_review=evidence.requires_human_review,
            metadata={
                "matched_keywords": list(classification.matched_keywords),
                "risk_notes": list(evidence.risk_notes),
            },
        )
        result.append(
            KnowledgeChunk(
                chunk_id=f"{source_file}:p{page}:c{index}",
                text=claim,
                trace=trace,
            )
        )
    return result
