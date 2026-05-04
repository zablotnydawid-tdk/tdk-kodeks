from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer


FONT_NAME = "ArialUnicode"
FONT_PATH = r"C:\Windows\Fonts\arial.ttf"
DEFAULT_TITLE = "RAPORT ANALIZY ENERGII – TDK&ProService"
BRAND_LINE = "TDK&ProService – Diagnostyka OZE"


def generate_pdf(report_text: str, output_path: str) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    _register_fonts()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=56,
        rightMargin=56,
        topMargin=56,
        bottomMargin=56,
    )

    styles = _build_styles()
    story = []

    lines = report_text.splitlines()
    if _has_report_header(lines):
        title = _clean_header(lines[0])
        remaining_lines = lines[1:]
    else:
        title = DEFAULT_TITLE
        remaining_lines = lines

    story.append(Paragraph(escape(BRAND_LINE), styles["Brand"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(escape(title), styles["ReportTitle"]))
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=1, color="#666666"))
    story.append(Spacer(1, 18))

    for line in remaining_lines:
        stripped = line.strip()

        if not stripped:
            story.append(Spacer(1, 8))
        elif _is_section_heading(stripped):
            story.append(Spacer(1, 16))
            story.append(Paragraph(escape(stripped), styles["SectionHeading"]))
            story.append(Spacer(1, 8))
        else:
            story.append(Paragraph(escape(stripped), styles["BodyText"]))
            story.append(Spacer(1, 6))

    doc.build(story)
    return output_path


def _register_fonts() -> None:
    if FONT_NAME not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))


def _build_styles() -> dict:
    base_styles = getSampleStyleSheet()

    return {
        "Brand": ParagraphStyle(
            "Brand",
            parent=base_styles["Normal"],
            fontName=FONT_NAME,
            fontSize=10,
            leading=13,
            textColor="#555555",
            spaceAfter=4,
        ),
        "ReportTitle": ParagraphStyle(
            "ReportTitle",
            parent=base_styles["Title"],
            fontName=FONT_NAME,
            fontSize=20,
            leading=26,
            spaceAfter=10,
        ),
        "SectionHeading": ParagraphStyle(
            "SectionHeading",
            parent=base_styles["Heading2"],
            fontName=FONT_NAME,
            fontSize=13,
            leading=18,
            spaceBefore=12,
            spaceAfter=8,
        ),
        "BodyText": ParagraphStyle(
            "BodyText",
            parent=base_styles["Normal"],
            fontName=FONT_NAME,
            fontSize=10.5,
            leading=16,
            spaceAfter=2,
        ),
    }


def _has_report_header(lines: list[str]) -> bool:
    if not lines:
        return False

    first_line = lines[0].strip()
    return first_line.startswith("===") and first_line.endswith("===")


def _clean_header(header: str) -> str:
    return header.strip().strip("=").strip()


def _is_section_heading(line: str) -> bool:
    return bool(line[:1].isdigit() and "." in line[:4])
