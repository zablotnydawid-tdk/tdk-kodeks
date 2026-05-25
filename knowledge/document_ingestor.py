from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from knowledge.chunker import KnowledgeChunk, chunk_text
from knowledge.pdf_ocr_pipeline import ParsedPage, parse_pdf, parse_text_file
from knowledge.report_context_builder import ReportContext, build_report_context


SUPPORTED_TEXT_SUFFIXES = {".txt", ".md", ".json", ".csv"}


@dataclass(frozen=True)
class IngestionResult:
    source_file: str
    parser_warnings: list[str]
    chunks: list[KnowledgeChunk]
    report_context: ReportContext

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "parser_warnings": self.parser_warnings,
            "chunks": [chunk.as_dict() for chunk in self.chunks],
            "report_context": self.report_context.as_dict(),
        }


def _parse_document(path: Path) -> list[ParsedPage]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return parse_pdf(path)
    if suffix in SUPPORTED_TEXT_SUFFIXES:
        return parse_text_file(path)
    raise ValueError(f"unsupported document type: {suffix or 'no extension'}")


def ingest_document(path: str | Path, max_chars: int = 900) -> IngestionResult:
    document_path = Path(path)
    if not document_path.exists():
        raise FileNotFoundError(str(document_path))

    pages = _parse_document(document_path)
    parser_warnings: list[str] = []
    chunks: list[KnowledgeChunk] = []
    for page in pages:
        parser_warnings.extend(page.warnings)
        page_chunks = chunk_text(
            page.text,
            source_file=str(document_path),
            page=page.page,
            max_chars=max_chars,
        )
        if page.requires_human_review and not page_chunks:
            parser_warnings.append(f"page {page.page}: no extractable text; OCR/human review required")
        chunks.extend(page_chunks)

    report_context = build_report_context(chunks)
    return IngestionResult(
        source_file=str(document_path),
        parser_warnings=parser_warnings,
        chunks=chunks,
        report_context=report_context,
    )


def write_ingestion_result(result: IngestionResult, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.as_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
