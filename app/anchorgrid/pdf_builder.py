from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


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

COLOR_BG = colors.HexColor("#071014")
COLOR_PANEL = colors.HexColor("#10242d")
COLOR_LINE = colors.HexColor("#2c5260")
COLOR_TEXT = colors.HexColor("#f4f8fb")
COLOR_MUTED = colors.HexColor("#9fb1bc")
COLOR_ACCENT = colors.HexColor("#49c7e8")
COLOR_WARN = colors.HexColor("#f4c76b")
COLOR_DANGER = colors.HexColor("#ff9b9b")
COLOR_OK = colors.HexColor("#9be7c5")


def _styles() -> dict[str, ParagraphStyle]:
    return {
        "eyebrow": ParagraphStyle(
            "eyebrow",
            fontName=BOLD_FONT,
            fontSize=8,
            leading=10,
            textColor=COLOR_ACCENT,
            alignment=TA_LEFT,
        ),
        "title": ParagraphStyle(
            "title",
            fontName=BOLD_FONT,
            fontSize=22,
            leading=27,
            textColor=COLOR_TEXT,
            alignment=TA_LEFT,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            fontName=BASE_FONT,
            fontSize=9.5,
            leading=13,
            textColor=COLOR_MUTED,
            alignment=TA_LEFT,
        ),
        "section": ParagraphStyle(
            "section",
            fontName=BOLD_FONT,
            fontSize=12,
            leading=15,
            textColor=COLOR_ACCENT,
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
        "body_muted": ParagraphStyle(
            "body_muted",
            fontName=BASE_FONT,
            fontSize=8.5,
            leading=11.5,
            textColor=COLOR_MUTED,
            alignment=TA_LEFT,
        ),
        "kpi_label": ParagraphStyle(
            "kpi_label",
            fontName=BOLD_FONT,
            fontSize=7.5,
            leading=9.5,
            textColor=COLOR_MUTED,
            alignment=TA_LEFT,
        ),
        "kpi_value": ParagraphStyle(
            "kpi_value",
            fontName=BOLD_FONT,
            fontSize=12,
            leading=15,
            textColor=COLOR_TEXT,
            alignment=TA_LEFT,
        ),
    }


def _p(text: object, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape("" if text is None else str(text)), style)


def _kpi(label: str, value: object, styles: dict[str, ParagraphStyle]) -> list[Paragraph]:
    return [_p(label.upper(), styles["kpi_label"]), _p(value, styles["kpi_value"])]


def _table(data: list[list[object]], col_widths: list[float], background=COLOR_PANEL) -> Table:
    table = Table(data, colWidths=col_widths, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), background),
                ("BOX", (0, 0), (-1, -1), 0.7, COLOR_LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, COLOR_LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def _state_color(state: str) -> colors.Color:
    normalized = state.upper().strip()
    if normalized == "STABLE":
        return COLOR_OK
    if normalized == "DAMPED":
        return COLOR_WARN
    if normalized == "LOCKED":
        return COLOR_DANGER
    return COLOR_TEXT


def _usage_text(usage: dict | None) -> str:
    if not usage:
        return "UNKNOWN"
    if usage.get("api_key_valid"):
        return "API key active"
    free_limit = usage.get("free_limit", "UNKNOWN")
    usage_count = usage.get("usage_count", "UNKNOWN")
    remaining = usage.get("remaining", "UNKNOWN")
    return f"{usage_count}/{free_limit} used, {remaining} remaining"


def _format_warnings(warnings: list[str], styles: dict[str, ParagraphStyle]) -> list[Paragraph]:
    if not warnings:
        return [_p("No active warnings.", styles["body_muted"])]
    return [_p(f"- {warning}", styles["body"]) for warning in warnings]


def _forecast_table(result: dict, styles: dict[str, ParagraphStyle]) -> Table | None:
    forecast = result.get("forecast") or {}
    minutes = forecast.get("minutes") or []
    soc = forecast.get("soc") or []
    temperature = forecast.get("temperature") or []
    requested_u = forecast.get("requested_u") or []
    recommended_u = forecast.get("recommended_u") or []

    if not minutes:
        return None

    rows = [
        [
            _p("Minute", styles["kpi_label"]),
            _p("SoC", styles["kpi_label"]),
            _p("Temp C", styles["kpi_label"]),
            _p("Requested C-rate", styles["kpi_label"]),
            _p("Recommended C-rate", styles["kpi_label"]),
        ]
    ]
    for index, minute in enumerate(minutes):
        rows.append(
            [
                _p(minute, styles["body"]),
                _p(_safe_index(soc, index), styles["body"]),
                _p(_safe_index(temperature, index), styles["body"]),
                _p(_safe_index(requested_u, index), styles["body"]),
                _p(_safe_index(recommended_u, index), styles["body"]),
            ]
        )
    return _table(rows, [24 * mm, 25 * mm, 28 * mm, 42 * mm, 46 * mm])


def _safe_index(values: list, index: int) -> object:
    if index >= len(values):
        return "UNKNOWN"
    value = values[index]
    if isinstance(value, float):
        return round(value, 3)
    return value


def build_anchorgrid_pdf(
    result: dict,
    usage: dict | None,
    output_path: str,
    *,
    request_id: str | None = None,
) -> str:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    styles = _styles()

    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="TDK Energy Intelligence Platform - AnchorGrid BESS Advisory",
        author="TDK&ProService",
    )

    state_style = ParagraphStyle(
        "state",
        parent=styles["title"],
        textColor=_state_color(str(result.get("state", "UNKNOWN"))),
        fontSize=26,
        leading=31,
    )

    story = [
        _p("TDK ENERGY INTELLIGENCE PLATFORM", styles["eyebrow"]),
        _p("AnchorGrid BESS Advisory Report", styles["title"]),
        _p(
            "Decision-support report for battery energy storage operation. "
            "This document is advisory only. Final decisions remain with BMS/PCS/operator.",
            styles["subtitle"],
        ),
        Spacer(1, 8),
        _table(
            [
                [
                    _p("State", styles["kpi_label"]),
                    _p("Execution mode", styles["kpi_label"]),
                    _p("Request ID", styles["kpi_label"]),
                    _p("Generated", styles["kpi_label"]),
                ],
                [
                    Paragraph(escape(str(result.get("state", "UNKNOWN"))), state_style),
                    _p(result.get("execution_mode", "UNKNOWN"), styles["kpi_value"]),
                    _p(request_id or "UNKNOWN", styles["body"]),
                    _p(datetime.now().isoformat(timespec="seconds"), styles["body"]),
                ],
            ],
            [36 * mm, 42 * mm, 44 * mm, 43 * mm],
        ),
        Spacer(1, 10),
        _p("Operational KPIs", styles["section"]),
        _table(
            [
                [
                    _kpi("Safe C-rate", result.get("recommended_u_safe", "UNKNOWN"), styles),
                    _kpi("Safe C-rate value", result.get("recommended_u_safe_value", "UNKNOWN"), styles),
                    _kpi("Predicted max temp", f"{result.get('predicted_max_temp', 'UNKNOWN')} C", styles),
                ],
                [
                    _kpi("Tension index", result.get("tension", "UNKNOWN"), styles),
                    _kpi("Net value PLN", (result.get("economics") or {}).get("net_value_pln", "UNKNOWN"), styles),
                    _kpi("Forecast confidence", result.get("forecast_confidence", "UNKNOWN"), styles),
                ],
            ],
            [55 * mm, 55 * mm, 55 * mm],
        ),
        Spacer(1, 10),
        _p("Decision", styles["section"]),
        _table(
            [[_p(result.get("decision", "UNKNOWN"), styles["body"])]],
            [165 * mm],
            background=colors.HexColor("#0b1a22"),
        ),
        Spacer(1, 10),
        _p("Warnings", styles["section"]),
        _table([[_format_warnings(result.get("warnings", []), styles)]], [165 * mm]),
        Spacer(1, 10),
        _p("Access And Governance", styles["section"]),
        _table(
            [
                [_p("Usage", styles["kpi_label"]), _p(_usage_text(usage), styles["body"])],
                [_p("Operator approval required", styles["kpi_label"]), _p("true", styles["body"])],
                [_p("Autonomous action", styles["kpi_label"]), _p("false", styles["body"])],
                [_p("Public boundary", styles["kpi_label"]), _p("Sanitized advisory output only", styles["body"])],
            ],
            [55 * mm, 110 * mm],
        ),
        Spacer(1, 10),
        _p("Forecast Trace", styles["section"]),
    ]

    forecast = _forecast_table(result, styles)
    if forecast is None:
        story.append(_p("Forecast unavailable.", styles["body_muted"]))
    else:
        story.append(forecast)

    story.extend(
        [
            Spacer(1, 12),
            _p("Disclaimer", styles["section"]),
            _p(result.get("disclaimer", "Final decisions belong to BMS/PCS/operator."), styles["body_muted"]),
            Spacer(1, 8),
            _p("TDK&ProService | kontakt@tdkproservice.pl | platform.tdkproservice.pl", styles["body_muted"]),
        ]
    )

    doc.build(story)
    return str(output)
