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
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="TDK&ProService - Wstępna ocena systemu OZE",
        author="TDK&ProService",
    )

    styles = _build_styles()
    story = []

    sections = _parse_report_sections(report_text)
    report_meta = _build_report_meta(output)
    kpis = _extract_kpis(report_text)
    data_lines = _section_lines(sections, "DANE DO ANALIZY")[:4]
    warning = _extract_data_warning(report_text)
    assessment = _build_assessment_status(report_text, warning)

    story.extend(_build_hero(styles, report_meta))
    story.append(Spacer(1, 9))
    story.extend(_build_data_used_section(data_lines, styles))
    story.append(Spacer(1, 9))
    story.extend(_build_kpi_cards(kpis, styles))
    story.append(Spacer(1, 9))
    story.extend(_build_data_status_box(assessment, warning, styles))
    story.append(Spacer(1, 8))
    story.extend(_build_reading_note(styles))
    story.append(PageBreak())
    story.extend(_build_scope_page(styles))

    doc.build(story, onFirstPage=_page_footer, onLaterPages=_page_footer)

    return str(output)


def _build_styles() -> dict:
    return {
        "brand": ParagraphStyle(
            "brand",
            fontName=BOLD_FONT,
            fontSize=22,
            leading=25,
            textColor=COLOR_GOLD,
            alignment=TA_LEFT,
        ),
        "hero_title": ParagraphStyle(
            "hero_title",
            fontName=BOLD_FONT,
            fontSize=18,
            leading=22,
            textColor=COLOR_TEXT,
            alignment=TA_LEFT,
        ),
        "brand_subtitle": ParagraphStyle(
            "brand_subtitle",
            fontName=BASE_FONT,
            fontSize=10.5,
            leading=13,
            textColor=COLOR_TEXT,
            alignment=TA_LEFT,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            fontName=BASE_FONT,
            fontSize=9.5,
            leading=12.5,
            textColor=COLOR_MUTED,
            alignment=TA_LEFT,
        ),
        "eyebrow": ParagraphStyle(
            "eyebrow",
            fontName=BOLD_FONT,
            fontSize=12,
            leading=15,
            textColor=COLOR_TEXT,
            alignment=TA_LEFT,
        ),
        "meta": ParagraphStyle(
            "meta",
            fontName=BOLD_FONT,
            fontSize=6.8,
            leading=8.8,
            textColor=COLOR_MUTED,
            alignment=TA_LEFT,
        ),
        "section_title": ParagraphStyle(
            "section_title",
            fontName=BOLD_FONT,
            fontSize=11.5,
            leading=14,
            textColor=COLOR_GOLD,
            alignment=TA_LEFT,
        ),
        "section_title_light": ParagraphStyle(
            "section_title_light",
            fontName=BOLD_FONT,
            fontSize=11,
            leading=13,
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
            fontSize=9,
            leading=12.5,
            textColor=COLOR_TEXT,
            alignment=TA_LEFT,
        ),
        "body_bold": ParagraphStyle(
            "body_bold",
            fontName=BOLD_FONT,
            fontSize=9,
            leading=12.5,
            textColor=COLOR_GOLD,
            alignment=TA_LEFT,
        ),
        "kpi_label": ParagraphStyle(
            "kpi_label",
            fontName=BOLD_FONT,
            fontSize=7.8,
            leading=9.8,
            textColor=COLOR_MUTED,
            alignment=TA_LEFT,
        ),
        "kpi_value": ParagraphStyle(
            "kpi_value",
            fontName=BOLD_FONT,
            fontSize=17,
            leading=20,
            textColor=COLOR_TEXT,
            alignment=TA_LEFT,
        ),
        "small": ParagraphStyle(
            "small",
            fontName=BASE_FONT,
            fontSize=8,
            leading=10.5,
            textColor=COLOR_MUTED,
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
            fontSize=9.5,
            leading=12.5,
            textColor=COLOR_TEXT,
            alignment=TA_LEFT,
        ),
    }


def _build_hero(styles: dict, report_meta: dict) -> list:
    hero_rows = [
        [Paragraph("TDK&amp;ProService", styles["brand"])],
        [Paragraph("WSTĘPNA OCENA KIERUNKOWA SYSTEMU OZE", styles["eyebrow"])],
        [
            Paragraph(
                "Screening techniczno-energetyczny na podstawie danych podanych przez użytkownika.<br/>"
                "Ten dokument pokazuje podstawowe przeliczenie kosztów energii i pracy instalacji PV na podstawie danych wpisanych w formularzu. "
                "Nie jest pełnym audytem technicznym ani opinią rzeczoznawczą.",
                styles["subtitle"],
            )
        ],
        [
            _build_meta_table(report_meta, styles)
        ],
    ]

    table = Table(hero_rows, colWidths=[174 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_PANEL),
                ("BOX", (0, 0), (-1, -1), 0.55, COLOR_BORDER),
                ("LINEABOVE", (0, 0), (-1, 0), 1.0, COLOR_GOLD_DARK),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (0, 0), 14),
                ("BOTTOMPADDING", (0, 3), (0, 3), 13),
            ]
        )
    )

    return [table]


def _build_scope_panel(styles: dict) -> list:
    scope_items = [
        "zużycie miesięczne",
        "cena energii",
        "moc instalacji PV",
        "miesięczna produkcja PV",
        "podstawowe porównanie kosztów",
    ]
    excluded_items = [
        "faktury i rozliczenia szczegółowe",
        "profil autokonsumpcji godzinowej",
        "dane z falownika",
        "historia pracy instalacji",
        "ustawienia pompy ciepła",
        "magazyn energii",
        "taryfy dynamiczne",
        "pomiary i oględziny instalacji",
    ]

    scope = [Paragraph("Zakres obecnej oceny", styles["section_title_light"])]
    scope.extend(Paragraph(f"• {item}", styles["body"]) for item in scope_items)

    excluded = [Paragraph("Czego ta analiza jeszcze nie obejmuje", styles["section_title_light"])]
    excluded.extend(Paragraph(f"• {item}", styles["body"]) for item in excluded_items)

    table = Table([[scope, excluded]], colWidths=[86 * mm, 86 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_PANEL),
                ("BOX", (0, 0), (-1, -1), 0.7, COLOR_BORDER),
                ("LINEABOVE", (0, 0), (-1, 0), 0.9, COLOR_GOLD_DARK),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
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


def _build_meta_table(report_meta: dict, styles: dict) -> Table:
    meta = Table(
        [
            [
                Paragraph(f"RAPORT&nbsp;&nbsp;{report_meta['number']}", styles["meta"]),
                Paragraph(f"DATA&nbsp;&nbsp;{report_meta['date']}", styles["meta"]),
                Paragraph("TYP&nbsp;&nbsp;SCREENING", styles["meta"]),
            ]
        ],
        colWidths=[78 * mm, 40 * mm, 42 * mm],
    )
    meta.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG),
                ("BOX", (0, 0), (-1, -1), 0.45, COLOR_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return meta


def _build_data_used_section(data_lines: list[str], styles: dict) -> list:
    return [_full_width_section("Dane użyte do oceny", data_lines, styles)]


def _build_kpi_cards(kpis: dict, styles: dict) -> list:
    title = Table(
        [[Paragraph("Podstawowe przeliczenie", styles["section_title_light"])]],
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
        _kpi_cell("BEZ PV", kpis["cost_without_pv"], "#0d1016", "#d4a84f", styles),
        _kpi_cell("PO UWZGLĘDNIENIU PV", kpis["cost_after_pv"], "#0d1016", "#1f8f4d", styles),
        _kpi_cell("RÓŻNICA", kpis["savings"], "#0d1016", "#8b3dff", styles),
    ]

    table = Table([cards], colWidths=[56.4 * mm, 56.4 * mm, 56.4 * mm], hAlign="LEFT")
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
            [Spacer(1, 2)],
            [Paragraph(value, styles["kpi_value"])],
        ],
        colWidths=[51 * mm],
    )
    cell.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(background)),
                ("BOX", (0, 0), (-1, -1), 0.55, COLOR_BORDER),
                ("LINEABOVE", (0, 0), (-1, 0), 1.0, colors.HexColor(accent)),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
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


def _build_data_status_box(assessment: dict, warning: str | None, styles: dict) -> list:
    if warning:
        detail = warning
    else:
        detail = "Dane wejściowe nie wykazują oczywistej niespójności na etapie formularza."

    rows = [
        [Paragraph(f"Status oceny: {assessment['label']}", styles["section_title_light"])],
        [Paragraph(detail, styles["body_bold"] if warning else styles["body"])],
        [
            Paragraph(
                "Wynik matematyczny został policzony, ale jego wiarygodność zależy od poprawności danych wejściowych.",
                styles["body"],
            )
        ],
    ]

    table = Table(rows, colWidths=[174 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_PANEL_2),
                ("BOX", (0, 0), (-1, -1), 0.7, COLOR_GOLD_DARK),
                ("LINEBEFORE", (0, 0), (0, -1), 3, COLOR_PURPLE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return [table]


def _build_reading_note(styles: dict) -> list:
    return [
        _full_width_section(
            "Jak czytać wynik",
            [
                "Wynik należy traktować jako orientacyjne porównanie kosztów, nie jako potwierdzenie rzeczywistej sprawności instalacji."
            ],
            styles,
        )
    ]


def _build_scope_page(styles: dict) -> list:
    excluded = [
        "faktur i rozliczeń szczegółowych",
        "profilu autokonsumpcji godzinowej",
        "eksportu i importu energii",
        "danych z falownika",
        "historii pracy instalacji",
        "pracy pompy ciepła",
        "magazynu energii",
        "taryf dynamicznych",
        "pomiarów i oględzin",
    ]

    to_check = [
        "autokonsumpcja",
        "taryfa i sposób rozliczania",
        "konfiguracja falownika",
        "sterowanie pompą ciepła lub magazynem",
        "rozbieżność między produkcją deklarowaną a realnym zużyciem",
        "wysokie koszty mimo instalacji PV",
    ]

    sections_flow = [
        _full_width_section("Czego ta ocena nie obejmuje", excluded, styles),
        Spacer(1, 7),
        _full_width_section("Co może wymagać sprawdzenia", to_check, styles),
        Spacer(1, 7),
        _full_width_section(
            "Następny krok",
            [
                "Jeżeli wynik budzi wątpliwości albo koszty energii nadal są wysokie mimo instalacji PV, kolejnym krokiem jest pełna diagnostyka TDK&ProService oparta na fakturach, danych z urządzeń i historii pracy systemu."
            ],
            styles,
        ),
        Spacer(1, 7),
        _full_width_section(
            "Odpowiedzialność i zakres",
            [
                "TDK&ProService nie wydaje końcowego wniosku technicznego na podstawie kilku danych z formularza.",
                "Ten dokument porządkuje pierwszy etap rozmowy i wskazuje, co warto sprawdzić dalej.",
            ],
            styles,
        ),
        Spacer(1, 7),
    ]

    contact = Table(
        [
            [Paragraph("Kontakt", styles["section_title_light"])],
            [
                Paragraph(
                    "TDK&amp;ProService • kontakt@tdkproservice.pl<br/>"
                    "Praktyka terenowa Dawida Zabłotnego w obszarze PV, pomp ciepła, magazynów energii i kosztów utraconej energii.",
                    styles["body"],
                )
            ],
        ],
        colWidths=[174 * mm],
    )
    contact.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_BG),
                ("BACKGROUND", (0, 1), (-1, -1), COLOR_PANEL_2),
                ("BOX", (0, 0), (-1, -1), 0.7, COLOR_BORDER),
                ("LINEBEFORE", (0, 0), (0, -1), 3, COLOR_PURPLE),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    return [*sections_flow, contact]


def _full_width_section(title: str, lines: list[str], styles: dict) -> Table:
    clean_lines = [line for line in lines if line.strip()]
    rows = [[Paragraph(_escape(title), styles["section_title"])]]
    rows.extend([[Paragraph(_format_bullet_line(line), styles["body"])] for line in clean_lines[:9]])

    card = Table(rows, colWidths=[174 * mm])
    card.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_BG),
                ("BACKGROUND", (0, 1), (-1, -1), COLOR_PANEL),
                ("BOX", (0, 0), (-1, -1), 0.7, COLOR_BORDER),
                ("LINEBEFORE", (0, 0), (0, -1), 3, COLOR_GOLD_DARK),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return card


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
        "Jeżeli wynik budzi wątpliwości albo koszty energii nadal są wysokie mimo instalacji PV, kolejnym krokiem powinna być pełna diagnostyka TDK&ProService.",
        "Pełna diagnostyka powinna opierać się na fakturach, danych z urządzeń i historii pracy systemu.",
        "Za analizą stoi TDK&ProService — praktyka terenowa Dawida Zabłotnego w obszarze fotowoltaiki, pomp ciepła, magazynów energii i kosztów utraconej energii.",
    ]
    rows = [[Paragraph("Zalecany następny krok", styles["section_title_light"])]]
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
            [Paragraph("Kolejny etap diagnostyki", styles["section_title_light"])],
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


def _section_lines(sections: list[tuple[str, list[str]]], title_part: str) -> list[str]:
    title_part = title_part.lower()
    for title, lines in sections:
        if title_part in title.lower():
            return lines
    return []


def _extract_data_warning(report_text: str) -> str | None:
    lower = report_text.lower()
    if "wykryto dane wymagające dodatkowej weryfikacji" not in lower:
        return None
    if "produkcji rocznej zamiast miesięcznej" in lower or "produkcja pv wygląda nietypowo" in lower:
        return (
            "Dane wymagają weryfikacji. Podana produkcja PV wygląda nietypowo dla wskazanej mocy instalacji. "
            "Sprawdź, czy nie wpisano produkcji rocznej zamiast miesięcznej."
        )
    if "zużycie energii wygląda bardzo wysoko" in lower:
        return (
            "Dane wymagają weryfikacji. Podane miesięczne zużycie energii wygląda bardzo wysoko dla gospodarstwa domowego. "
            "Sprawdź, czy wartość nie pochodzi z innego okresu rozliczeniowego."
        )
    return (
        "Dane wymagają weryfikacji. Wynik może być obarczony większą niepewnością ze względu na możliwą niezgodność danych wejściowych."
    )


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


def _format_bullet_line(text: str) -> str:
    clean = _format_report_line(text)
    if clean.startswith("• "):
        return clean
    return f"• {clean}"


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


def _build_assessment_status(report_text: str, warning: str | None) -> dict:
    lower = report_text.lower()
    if warning:
        return {
            "label": "dane wymagają weryfikacji",
            "color": "#d4a84f",
            "border": "#8a641b",
        }
    if "oszczędność jest niewielka" in lower or "wymaga dokładniejszej weryfikacji" in lower:
        return {
            "label": "możliwe obszary do sprawdzenia",
            "color": "#d4a84f",
            "border": "#8a641b",
        }
    return {
        "label": "dane wejściowe wyglądają spójnie",
        "color": "#1f8f4d",
        "border": "#176b39",
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

    footer = "TDK&ProService | Diagnostyka OZE | Powered by ZT&SI Diagnostic Framework"
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
