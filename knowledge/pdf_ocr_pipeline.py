from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ParsedPage:
    page: int
    text: str
    extraction_method: str
    requires_human_review: bool
    warnings: tuple[str, ...] = ()


def parse_pdf(path: str | Path) -> list[ParsedPage]:
    pdf_path = Path(path)
    warnings: list[str] = []

    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        warnings.append("pypdf unavailable; PDF text extraction not executed")
        return [
            ParsedPage(
                page=0,
                text="",
                extraction_method="unavailable",
                requires_human_review=True,
                warnings=tuple(warnings),
            )
        ]

    reader = PdfReader(str(pdf_path))
    pages: list[ParsedPage] = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        page_warnings: list[str] = []
        requires_review = False
        method = "pypdf_text"
        if not text.strip():
            method = "ocr_required"
            requires_review = True
            page_warnings.append("no embedded text found; OCR required")
        pages.append(
            ParsedPage(
                page=index,
                text=text,
                extraction_method=method,
                requires_human_review=requires_review,
                warnings=tuple(page_warnings),
            )
        )
    return pages


def parse_text_file(path: str | Path) -> list[ParsedPage]:
    text_path = Path(path)
    return [
        ParsedPage(
            page=0,
            text=text_path.read_text(encoding="utf-8"),
            extraction_method="text",
            requires_human_review=False,
        )
    ]
