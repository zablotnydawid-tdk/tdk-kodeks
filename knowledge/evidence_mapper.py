from __future__ import annotations

from dataclasses import dataclass


HIGH_REVIEW_DOMAINS = {"REGULATORY", "SUBSIDY", "BILLING", "VPP_ALGORITHM"}


@dataclass(frozen=True)
class EvidenceAssessment:
    evidence_type: str
    confidence: float
    requires_human_review: bool
    risk_notes: tuple[str, ...]


def assess_evidence(claim: str, domain: str, base_confidence: float) -> EvidenceAssessment:
    lowered = claim.lower()
    notes: list[str] = []

    if any(token in lowered for token in ("faktura", "csv", "zdjecie", "zdjęcie", "pomiar", "zalacznik", "załącznik")):
        evidence_type = "CLIENT_PROVIDED_EVIDENCE"
        confidence = min(0.9, base_confidence + 0.1)
    elif domain in HIGH_REVIEW_DOMAINS:
        evidence_type = "NORMATIVE_OR_POLICY_CLAIM"
        confidence = min(base_confidence, 0.75)
        notes.append("normative claim requires operator/legal/regulatory review")
    elif any(token in lowered for token in ("powinien", "nalezy", "należy", "musi", "zaleca")):
        evidence_type = "RECOMMENDATION_CANDIDATE"
        confidence = min(base_confidence, 0.7)
        notes.append("recommendation candidate blocked until source trace is reviewed")
    else:
        evidence_type = "EXTRACTED_CLAIM"
        confidence = base_confidence

    requires_human_review = domain in HIGH_REVIEW_DOMAINS or evidence_type == "RECOMMENDATION_CANDIDATE"
    if "253v" in lowered:
        requires_human_review = True
        notes.append("253V diagnostic threshold must be checked against installation context")
    if "2026" in lowered and domain in {"REGULATORY", "SUBSIDY", "BILLING"}:
        requires_human_review = True
        notes.append("future-year regulatory/subsidy claim requires freshness validation")

    return EvidenceAssessment(
        evidence_type=evidence_type,
        confidence=round(confidence, 2),
        requires_human_review=requires_human_review,
        risk_notes=tuple(notes),
    )
