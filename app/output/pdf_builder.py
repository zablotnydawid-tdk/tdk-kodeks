from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


FONT_CANDIDATES = [
    {
        "regular": r"C:\Windows\Fonts\arial.ttf",
        "bold": r"C:\Windows\Fonts\arialbd.ttf",
        "regular_name": "Arial",
        "bold_name": "Arial-Bold",
    },
    {
        "regular": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "regular_name": "DejaVuSans",
        "bold_name": "DejaVuSans-Bold",
    },
]


def _register_fonts() -> tuple[str, str]:
    for font in FONT_CANDIDATES:
        regular = Path(font["regular"])
        bold = Path(font["bold"])

        if regular.exists() and bold.exists():
            pdfmetrics.registerFont(TTFont(font["regular_name"], str(regular)))
            pdfmetrics.registerFont(TTFont(font["bold_name"], str(bold)))
            return font["regular_name"], font["bold_name"]

    return "Helvetica", "Helvetica-Bold"


BASE_FONT, BOLD_FONT = _register_fonts()


def generate_pdf(report_text: str, output_path: str) -> str:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=16 * mm,
        title="TDK&ProService - Raport analizy energii",
        author="TDK&ProService",
    )

    styles = _build_styles()
    story = []

    story.extend(_build_header(styles))
    story.append(Spacer(1, 10))

    sections = _parse_report_sections(report_text)

    for title, lines in sections:
        story.extend(_build_section(title, lines, styles))
        story.append(Spacer(1, 8))

    story.extend(_build_footer_cta(styles))

    doc.build(story, onFirstPage=_page_footer, onLaterPages=_page_footer)

    return str(output)


def _build_styles() -> dict:
    return {
        "brand": ParagraphStyle(
            "brand",
            fontName=BOLD_FONT,
            fontSize=20,
            leading=24,
            textColor=colors.white,
            alignment=TA_LEFT,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            fontName=BASE_FONT,
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#c8d0dc"),
            alignment=TA_LEFT,
        ),
        "section_title": ParagraphStyle(
            "section_title",
            fontName=BOLD_FONT,
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#ffffff"),
            alignment=TA_LEFT,
        ),
        "body": ParagraphStyle(
            "body",
            fontName=BASE_FONT,
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#20242b"),
            alignment=TA_LEFT,
        ),
        "body_bold": ParagraphStyle(
            "body_bold",
            fontName=BOLD_FONT,
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#111827"),
            alignment=TA_LEFT,
        ),
        "cta": ParagraphStyle(
            "cta",
            fontName=BOLD_FONT,
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#0f172a"),
            alignment=TA_LEFT,
        ),
    }


def _build_header(styles: dict) -> list:
    header_content = [
        [Paragraph("TDK&ProService - KODEKS ANALIZA", styles["brand"])],
        [
            Paragraph(
                "Analiza faktur, kosztów energii i pracy instalacji PV<br/>"
                "Wstępny raport techniczny na podstawie danych klienta.",
                styles["subtitle"],
            )
        ],
    ]

    table = Table(header_content, colWidths=[174 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0f1115")),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#2b3240")),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )

    return [table]


def _build_section(title: str, lines: list[str], styles: dict) -> list:
    elements = []

    title_table = Table(
        [[Paragraph(_escape(title), styles["section_title"])]],
        colWidths=[174 * mm],
    )

    title_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#171b22")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#2b3240")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    elements.append(title_table)

    body_rows = []
    for line in lines:
        clean = line.strip()
        if clean:
            body_rows.append([Paragraph(_escape(clean), styles["body"])])

    if body_rows:
        body_table = Table(body_rows, colWidths=[174 * mm])
        body_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d7dde7")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    (
                        "ROWBACKGROUNDS",
                        (0, 0),
                        (-1, -1),
                        [colors.HexColor("#ffffff"), colors.HexColor("#f4f7fb")],
                    ),
                ]
            )
        )

        elements.append(body_table)

    return elements


def _build_footer_cta(styles: dict) -> list:
    cta_text = (
        "Pełna diagnostyka techniczna pozwala sprawdzić, czy instalacja rzeczywiście "
        "pracuje optymalnie i czy nie generuje ukrytych strat."
    )

    cta_table = Table(
        [
            [Paragraph("Następny krok", styles["section_title"])],
            [Paragraph(cta_text, styles["cta"])],
            [Paragraph("kontakt@tdkproservice.pl", styles["body_bold"])],
        ],
        colWidths=[174 * mm],
    )

    cta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#171b22")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#eaf2ff")),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#2f7cf6")),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    return [Spacer(1, 6), cta_table]


def _parse_report_sections(report_text: str) -> list[tuple[str, list[str]]]:
    lines = [line.rstrip() for line in report_text.splitlines()]

    sections = []
    current_title = None
    current_lines = []

    for line in lines:
        clean = line.strip()

        if not clean:
            continue

        if clean.startswith("==="):
            continue

        if _is_section_title(clean):
            if current_title:
                sections.append((current_title, current_lines))

            current_title = clean
            current_lines = []
        else:
            if current_title is None:
                current_title = "Raport"
            current_lines.append(clean)

    if current_title:
        sections.append((current_title, current_lines))

    return sections


def _is_section_title(line: str) -> bool:
    return line.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7."))


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _page_footer(canvas, doc) -> None:
    canvas.saveState()

    canvas.setFont(BASE_FONT, 8)
    canvas.setFillColor(colors.HexColor("#7d8796"))

    footer = "TDK&ProService • Diagnostyka OZE • Audyt rozliczeń energii"
    page = f"Strona {doc.page}"

    canvas.drawString(18 * mm, 10 * mm, footer)
    canvas.drawRightString(192 * mm, 10 * mm, page)

    canvas.restoreState()