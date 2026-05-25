from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from knowledge.decision_mapper import build_decision_map
from knowledge.document_ingestor import ingest_document
from knowledge.drift_energy import build_document_drift_energy
from knowledge.human_review_queue import build_human_review_queue
from knowledge.report_generator import generate_operator_report
from knowledge.risk_mapper import build_risk_map


@dataclass(frozen=True)
class KnowledgeOSResult:
    source_file: str
    parser_warnings: list[str]
    report_context: dict[str, Any]
    risk_map: dict[str, Any]
    drift_energy: dict[str, Any]
    decision_map: dict[str, Any]
    human_review_queue: list[dict[str, Any]]
    operator_report_markdown: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "parser_warnings": self.parser_warnings,
            "report_context": self.report_context,
            "risk_map": self.risk_map,
            "drift_energy": self.drift_energy,
            "decision_map": self.decision_map,
            "human_review_queue": self.human_review_queue,
            "operator_report_markdown": self.operator_report_markdown,
        }


def run_knowledge_os(document_path: str | Path, max_chars: int = 900) -> KnowledgeOSResult:
    ingestion = ingest_document(document_path, max_chars=max_chars)
    report_context = ingestion.report_context.as_dict()
    risk_map = build_risk_map(report_context)
    drift_energy = build_document_drift_energy(float(risk_map["risk_score"]))
    decision_map = build_decision_map(report_context, risk_map)
    review_queue = build_human_review_queue(report_context, decision_map)
    result = KnowledgeOSResult(
        source_file=ingestion.source_file,
        parser_warnings=ingestion.parser_warnings,
        report_context=report_context,
        risk_map=risk_map,
        drift_energy=drift_energy,
        decision_map=decision_map,
        human_review_queue=review_queue,
        operator_report_markdown="",
    )
    report = generate_operator_report(result.as_dict())
    return KnowledgeOSResult(
        source_file=result.source_file,
        parser_warnings=result.parser_warnings,
        report_context=result.report_context,
        risk_map=result.risk_map,
        drift_energy=result.drift_energy,
        decision_map=result.decision_map,
        human_review_queue=result.human_review_queue,
        operator_report_markdown=report,
    )


def write_knowledge_os_result(result: KnowledgeOSResult, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.as_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
