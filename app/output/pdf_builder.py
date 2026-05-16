from pathlib import Path
import re
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Flowable,
    Image,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
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
LOGO_PATH = Path("app") / "output" / "assets" / "logo.png"

COLOR_BG = colors.HexColor("#050608")
COLOR_PANEL = colors.HexColor("#0d1016")
COLOR_PANEL_2 = colors.HexColor("#111722")
COLOR_GOLD = colors.HexColor("#d4a84f")
COLOR_GOLD_DARK = colors.HexColor("#7a5a1d")
COLOR_PURPLE = colors.HexColor("#8b3dff")
COLOR_PURPLE_DARK = colors.HexColor("#3b1b73")
COLOR_TEXT = colors.HexColor("#f4f6fb")
COLOR_MUTED = colors.HexColor("#aeb7c5")
COLOR_BORDER = colors.HexColor("#2b3240")


def generate_pdf(report_text: str, output_path: str) -> str:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="TDK&ProService - Raport analizy energii",
        author="TDK&ProService",
    )

    styles = _build_styles()
    story = []

    sections = _parse_report_sections(report_text)
    report_meta = _build_report_meta(output)
    kpis = _extract_kpis(report_text)
    status = _extract_report_status(report_text, kpis)

    story.extend(_build_hero(styles, report_meta, status))
    story.append(Spacer(1, 12))
    story.extend(_build_kpi_cards(kpis, styles))
    story.append(Spacer(1, 10))
    story.extend(_build_status_panel(status, styles))
    story.append(PageBreak())

    for title, lines in sections:
        story.extend(_build_section(title, lines, styles))
        story.append(Spacer(1, 11))

    story.extend(_build_diagnostics_panel(styles))
    story.append(Spacer(1, 8))
    story.extend(_build_footer_cta(styles))

    doc.build(story, onFirstPage=_page_footer, onLaterPages=_page_footer)

    return str(output)


def _build_styles() -> dict:
    return {
        "brand": ParagraphStyle(
            "brand",
            fontName=BOLD_FONT,
            fontSize=24,
            leading=29,
            textColor=COLOR_GOLD,
            alignment=TA_LEFT,
        ),
        "hero_title": ParagraphStyle(
            "hero_title",
            fontName=BOLD_FONT,
            fontSize=26,
            leading=31,
            textColor=COLOR_TEXT,
            alignment=TA_LEFT,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            fontName=BASE_FONT,
            fontSize=10.5,
            leading=15,
            textColor=COLOR_MUTED,
            alignment=TA_LEFT,
        ),
        "eyebrow": ParagraphStyle(
            "eyebrow",
            fontName=BOLD_FONT,
            fontSize=8.5,
            leading=11,
            textColor=COLOR_PURPLE,
            alignment=TA_LEFT,
        ),
        "meta": ParagraphStyle(
            "meta",
            fontName=BASE_FONT,
            fontSize=8.5,
            leading=11,
            textColor=COLOR_MUTED,
            alignment=TA_LEFT,
        ),
        "section_title": ParagraphStyle(
            "section_title",
            fontName=BOLD_FONT,
            fontSize=13,
            leading=16,
            textColor=COLOR_GOLD,
            alignment=TA_LEFT,
        ),
        "section_title_light": ParagraphStyle(
            "section_title_light",
            fontName=BOLD_FONT,
            fontSize=13,
            leading=16,
            textColor=COLOR_GOLD,
            alignment=TA_LEFT,
        ),
        "section_index": ParagraphStyle(
            "section_index",
            fontName=BOLD_FONT,
            fontSize=7.6,
            leading=10,
            textColor=COLOR_PURPLE,
            alignment=TA_LEFT,
        ),
        "body": ParagraphStyle(
            "body",
            fontName=BASE_FONT,
            fontSize=9.5,
            leading=14.5,
            textColor=COLOR_TEXT,
            alignment=TA_LEFT,
        ),
        "body_bold": ParagraphStyle(
            "body_bold",
            fontName=BOLD_FONT,
            fontSize=9.5,
            leading=14,
            textColor=COLOR_GOLD,
            alignment=TA_LEFT,
        ),
        "kpi_label": ParagraphStyle(
            "kpi_label",
            fontName=BASE_FONT,
            fontSize=8.2,
            leading=10.5,
            textColor=COLOR_MUTED,
            alignment=TA_LEFT,
        ),
        "kpi_value": ParagraphStyle(
            "kpi_value",
            fontName=BOLD_FONT,
            fontSize=16,
            leading=20,
            textColor=COLOR_TEXT,
            alignment=TA_LEFT,
        ),
        "status": ParagraphStyle(
            "status",
            fontName=BOLD_FONT,
            fontSize=10,
            leading=13,
            textColor=COLOR_TEXT,
            alignment=TA_CENTER,
        ),
        "cta": ParagraphStyle(
            "cta",
            fontName=BOLD_FONT,
            fontSize=11,
            leading=15,
            textColor=COLOR_TEXT,
            alignment=TA_LEFT,
        ),
    }


def _build_hero(styles: dict, report_meta: dict, status: dict) -> list:
    hero_rows = [
        [_build_logo_block(styles), Paragraph("TDK&amp;ProService<br/><font color='#f4f6fb'>WITNESS AI | ZT&amp;SI</font>", styles["brand"])],
        ["", Paragraph("PREMIUM TECHNICAL AUDIT REPORT", styles["eyebrow"])],
        [
            "",
            Paragraph(
                "Analiza faktur, kosztów energii i pracy instalacji PV",
                styles["hero_title"],
            )
        ],
        [
            "",
            Paragraph(
                "Wstępny raport techniczny na podstawie danych klienta. "
                "Układ dashboardowy pokazuje kluczowe KPI, poziom efektywności i obszary wymagające weryfikacji.",
                styles["subtitle"],
            )
        ],
        [
            "",
            _build_meta_table(report_meta, status, styles)
        ],
    ]

    table = Table(hero_rows, colWidths=[34 * mm, 144 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_PANEL),
                ("BOX", (0, 0), (-1, -1), 1.0, COLOR_GOLD_DARK),
                ("LINEBELOW", (0, 0), (-1, 0), 1.2, COLOR_PURPLE),
                ("SPAN", (0, 0), (0, 4)),
                ("LEFTPADDING", (0, 0), (-1, -1), 15),
                ("RIGHTPADDING", (0, 0), (-1, -1), 15),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (0, 0), 17),
                ("BOTTOMPADDING", (0, 4), (0, 4), 17),
            ]
        )
    )

    return [table]


def _build_logo_block(styles: dict):
    if LOGO_PATH.exists():
        try:
            logo = Image(str(LOGO_PATH), width=27 * mm, height=27 * mm)
            return logo
        except Exception:
            pass

    return _LogoMark()


def _build_meta_table(report_meta: dict, status: dict, styles: dict) -> Table:
    status_chip = Table(
        [[Paragraph(status["report_label"], styles["status"])]],
        colWidths=[48 * mm],
    )
    status_chip.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(status["color"])),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor(status["border"])),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    meta = Table(
        [
            [
                Paragraph(f"Numer raportu<br/><b>{report_meta['number']}</b>", styles["meta"]),
                Paragraph(f"Data<br/><b>{report_meta['date']}</b>", styles["meta"]),
                status_chip,
            ]
        ],
        colWidths=[62 * mm, 48 * mm, 52 * mm],
    )
    meta.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG),
                ("BOX", (0, 0), (-1, -1), 0.6, COLOR_BORDER),
                ("LINEBEFORE", (0, 0), (0, -1), 2.0, COLOR_GOLD),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return meta


def _build_kpi_cards(kpis: dict, styles: dict) -> list:
    title = Table(
        [[Paragraph("PODSUMOWANIE WYNIKÓW", styles["section_title_light"])]],
        colWidths=[174 * mm],
    )
    title.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG),
                ("LINEBELOW", (0, 0), (-1, -1), 0.7, COLOR_GOLD_DARK),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    cards = [
        _kpi_cell("Szacowany koszt bez PV", kpis["cost_without_pv"], "#0d1016", "#d4a84f", styles),
        _kpi_cell("Koszt po kompensacji PV", kpis["cost_after_pv"], "#0d1016", "#1f8f4d", styles),
        _kpi_cell("Szacowana różnica miesięczna", kpis["savings"], "#0d1016", "#8b3dff", styles),
    ]

    table = Table([cards], colWidths=[56.8 * mm, 56.8 * mm, 56.8 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return [title, Spacer(1, 5), table]


def _kpi_cell(label: str, value: str, background: str, accent: str, styles: dict) -> Table:
    cell = Table(
        [
            [Paragraph(label, styles["kpi_label"])],
            [Paragraph(value, styles["kpi_value"])],
            [_progress_bar(accent)],
        ],
        colWidths=[50.8 * mm],
    )
    cell.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(background)),
                ("BOX", (0, 0), (-1, -1), 0.7, COLOR_BORDER),
                ("LINEBEFORE", (0, 0), (0, -1), 4, colors.HexColor(accent)),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return cell


def _progress_bar(accent: str) -> Table:
    bar = Table([["", ""]], colWidths=[31 * mm, 13 * mm], rowHeights=[2.4 * mm])
    bar.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), colors.HexColor(accent)),
                ("BACKGROUND", (1, 0), (1, 0), COLOR_BORDER),
                ("BOX", (0, 0), (-1, -1), 0.0, COLOR_BG),
            ]
        )
    )
    return bar


def _build_status_panel(status: dict, styles: dict) -> list:
    status_chip = Table([[Paragraph(status["efficiency_label"], styles["status"])]], colWidths=[46 * mm])
    status_chip.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(status["color"])),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor(status["border"])),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    table = Table(
        [
            [
                Paragraph("Poziom efektywności", styles["section_title_light"]),
                status_chip,
            ],
            [
                Paragraph(status["description"], styles["body"]),
                Paragraph(
                    "Raport ma charakter wstępnej analizy technicznej i nie stanowi pełnego audytu ani opinii rzeczoznawczej.",
                    styles["body"],
                ),
            ],
        ],
        colWidths=[118 * mm, 56 * mm],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_PANEL_2),
                ("BOX", (0, 0), (-1, -1), 0.7, COLOR_GOLD_DARK),
                ("LINEBEFORE", (0, 0), (0, -1), 3, COLOR_PURPLE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    return [table]


def _build_section(title: str, lines: list[str], styles: dict) -> list:
    elements = []
    section_no = title.split(".", 1)[0] if "." in title else ""
    clean_title = title.split(".", 1)[1].strip() if "." in title else title

    rows = [
        [
            Paragraph(f"SEKCJA {section_no}" if section_no else "SEKCJA", styles["section_index"]),
            Paragraph(_escape(clean_title), styles["section_title"]),
        ]
    ]

    for line in lines:
        clean = line.strip()
        if clean:
            rows.append(["", Paragraph(_format_report_line(clean), styles["body"])])

    card = Table(
        rows,
        colWidths=[28 * mm, 146 * mm],
    )

    card.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_PANEL),
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_BG),
                ("BOX", (0, 0), (-1, -1), 0.7, COLOR_BORDER),
                ("LINEBEFORE", (0, 0), (0, -1), 4, COLOR_PURPLE),
                ("LINEBELOW", (0, 0), (-1, 0), 0.7, COLOR_GOLD_DARK),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_PANEL, COLOR_PANEL_2]),
            ]
        )
    )

    elements.append(KeepTogether([card]))

    return elements


def _build_diagnostics_panel(styles: dict) -> list:
    items = [
        "ukryte straty",
        "błędy konfiguracji",
        "problemy autokonsumpcji",
        "błędne taryfy",
        "straty pracy instalacji PV",
        "niewłaściwe ustawienia urządzeń",
    ]
    rows = [[Paragraph("Pełna diagnostyka może wykryć", styles["section_title_light"])]]
    rows.extend([[Paragraph(f"• {item}", styles["body"])] for item in items])

    table = Table(rows, colWidths=[174 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_TEXT),
                ("BACKGROUND", (0, 1), (-1, -1), COLOR_PANEL),
                ("BOX", (0, 0), (-1, -1), 0.8, COLOR_GOLD_DARK),
                ("LINEBEFORE", (0, 0), (0, -1), 4, COLOR_GOLD),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return [table]


def _build_footer_cta(styles: dict) -> list:
    cta_text = (
        "Skontaktuj się z TDK&amp;ProService, jeśli chcesz sprawdzić rzeczywistą pracę "
        "instalacji na podstawie faktur, danych falownika i historii zużycia."
    )

    cta_table = Table(
        [
            [Paragraph("Final CTA premium", styles["section_title_light"])],
            [Paragraph(cta_text, styles["cta"])],
            [Paragraph("kontakt@tdkproservice.pl • TDK&amp;ProService", styles["body_bold"])],
        ],
        colWidths=[174 * mm],
    )

    cta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_TEXT),
                ("BACKGROUND", (0, 1), (-1, -1), COLOR_PANEL_2),
                ("BOX", (0, 0), (-1, -1), 0.8, COLOR_GOLD),
                ("LINEBEFORE", (0, 0), (0, -1), 4, COLOR_PURPLE),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
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
    return line.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8."))


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _format_report_line(text: str) -> str:
    clean = _escape(text)
    if clean.startswith("- "):
        return f"• {clean[2:]}"
    return clean


def _build_report_meta(output: Path) -> dict:
    stamp = datetime.now()
    report_id = output.stem.replace("raport_", "KODEKS-").upper()
    return {
        "number": report_id,
        "date": stamp.strftime("%Y-%m-%d %H:%M"),
    }


def _extract_kpis(report_text: str) -> dict:
    return {
        "cost_without_pv": _extract_money(report_text, r"koszt bez pv:\s*([^\n]+)"),
        "cost_after_pv": _extract_money(report_text, r"koszt po kompensacji pv:\s*([^\n]+)"),
        "savings": _extract_money(report_text, r"różnica miesięczna:\s*([^\n]+)"),
    }


def _extract_money(text: str, pattern: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return "brak danych"
    value = match.group(1).strip().lstrip("- ").strip()
    return value or "brak danych"


def _extract_report_status(report_text: str, kpis: dict) -> dict:
    lower = report_text.lower()
    if "niska efektywność" in lower:
        return {
            "report_label": "WSTĘPNA ANALIZA",
            "efficiency_label": "niska efektywność",
            "color": "#b42318",
            "border": "#7a271a",
            "description": "Wstępny wynik wskazuje na istotne ryzyko strat lub niedopasowania konfiguracji.",
        }
    if "umiarkowana efektywność" in lower:
        return {
            "report_label": "WSTĘPNA ANALIZA",
            "efficiency_label": "umiarkowana efektywność",
            "color": "#d4a84f",
            "border": "#8a641b",
            "description": "System działa, ale może mieć rezerwę w autokonsumpcji, taryfie lub sterowaniu.",
        }
    if "wysoka efektywność" in lower:
        return {
            "report_label": "WSTĘPNA ANALIZA",
            "efficiency_label": "wysoka efektywność",
            "color": "#1f8f4d",
            "border": "#176b39",
            "description": "Wstępny wynik jest korzystny, jednak pełna diagnostyka może wykryć ukryte straty.",
        }

    if all(value != "brak danych" for value in kpis.values()):
        return {
            "report_label": "WSTĘPNA ANALIZA",
            "efficiency_label": "dane kompletne",
            "color": "#8b3dff",
            "border": "#3b1b73",
            "description": "Raport zawiera komplet głównych wskaźników kosztowych dla danych wejściowych.",
        }

    return {
        "report_label": "WSTĘPNA ANALIZA",
        "efficiency_label": "dane wstępne",
        "color": "#d4a84f",
        "border": "#8a641b",
        "description": "Część danych wymaga doprecyzowania przed pełnym audytem technicznym.",
    }


def _page_footer(canvas, doc) -> None:
    canvas.saveState()

    width, height = A4
    canvas.setFillColor(COLOR_BG)
    canvas.rect(0, 0, width, height, stroke=0, fill=1)

    canvas.setStrokeColor(COLOR_PURPLE_DARK)
    canvas.setLineWidth(0.35)
    for offset in range(0, 90, 18):
        canvas.line(118 * mm + offset, height - 12 * mm, width - 8 * mm, height - (44 + offset // 2) * mm)

    canvas.setStrokeColor(COLOR_GOLD_DARK)
    canvas.setLineWidth(0.4)
    canvas.line(18 * mm, 14 * mm, 192 * mm, 14 * mm)

    canvas.setFont(BASE_FONT, 8)
    canvas.setFillColor(COLOR_MUTED)

    footer = "TDK&ProService | Diagnostyka OZE | Audyt rozliczeń energii"
    page = f"Strona {doc.page}"

    canvas.drawString(18 * mm, 10 * mm, footer)
    canvas.drawRightString(192 * mm, 10 * mm, page)

    canvas.restoreState()


class _LogoMark(Flowable):
    def __init__(self) -> None:
        super().__init__()
        self.width = 27 * mm
        self.height = 27 * mm

    def draw(self) -> None:
        c = self.canv
        cx = self.width / 2
        cy = self.height / 2
        radius = 11 * mm

        c.saveState()
        c.setStrokeColor(COLOR_GOLD)
        c.setLineWidth(1.2)
        c.circle(cx, cy, radius, stroke=1, fill=0)

        c.setStrokeColor(COLOR_PURPLE)
        c.setLineWidth(2.0)
        c.arc(cx - 8 * mm, cy - 8 * mm, cx + 8 * mm, cy + 8 * mm, 205, 130)

        c.setFillColor(COLOR_PURPLE)
        c.circle(cx, cy, 4.1 * mm, stroke=0, fill=1)
        c.setFillColor(COLOR_BG)
        c.circle(cx, cy, 1.8 * mm, stroke=0, fill=1)

        c.setFillColor(COLOR_GOLD)
        c.setFont(BOLD_FONT, 6.5)
        c.drawCentredString(cx, cy - 10 * mm, "TDK")
        c.restoreState()
