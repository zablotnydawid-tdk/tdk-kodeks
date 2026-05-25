from __future__ import annotations

from dataclasses import dataclass

from knowledge.chunker import KnowledgeChunk


REVIEW_DOMAINS = {"REGULATORY", "SUBSIDY", "BILLING", "VPP_ALGORITHM"}


@dataclass(frozen=True)
class ValidationResult:
    chunk_id: str
    validation_status: str
    human_validation_required: bool
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "chunk_id": self.chunk_id,
            "validation_status": self.validation_status,
            "human_validation_required": self.human_validation_required,
            "reason": self.reason,
        }


def validate_chunk(chunk: KnowledgeChunk) -> ValidationResult:
    trace = chunk.trace
    claim = trace.claim.lower()

    if trace.domain in REVIEW_DOMAINS:
        return ValidationResult(
            chunk.chunk_id,
            "HUMAN_REVIEW_REQUIRED",
            True,
            f"{trace.domain} content requires source freshness and operator validation",
        )
    if "253v" in claim:
        return ValidationResult(
            chunk.chunk_id,
            "FIELD_VALIDATION_REQUIRED",
            True,
            "253V diagnostic content requires local measurement validation",
        )
    if trace.confidence < 0.55:
        return ValidationResult(
            chunk.chunk_id,
            "LOW_CONFIDENCE_REVIEW_REQUIRED",
            True,
            "domain confidence below reporting threshold",
        )
    return ValidationResult(chunk.chunk_id, "TRACE_VALID", False, "source trace and domain classification present")


def validate_chunks(chunks: list[KnowledgeChunk]) -> list[ValidationResult]:
    return [validate_chunk(chunk) for chunk in chunks]
