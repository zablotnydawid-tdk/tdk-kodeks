from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


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

COLOR_BG = colors.HexColor("#050b10")
COLOR_PANEL = colors.HexColor("#0e1a24")
COLOR_PANEL_2 = colors.HexColor("#111f2b")
COLOR_CARD = colors.HexColor("#142837")
COLOR_LINE = colors.HexColor("#28495c")
COLOR_TEXT = colors.HexColor("#f4f8fb")
COLOR_MUTED = colors.HexColor("#9fb1bc")
COLOR_ACCENT = colors.HexColor("#49c7e8")
COLOR_ACCENT_2 = colors.HexColor("#7de3ff")
COLOR_GOLD = colors.HexColor("#d8b45f")
COLOR_OK = colors.HexColor("#55d69e")
COLOR_WARN = colors.HexColor("#f4c76b")
COLOR_DANGER = colors.HexColor("#ff6b7a")
COLOR_WHITE = colors.HexColor("#ffffff")


class ForecastTraceChart(Flowable):
    def __init__(self, forecast: dict, width: float = 165 * mm, height: float = 72 * mm):
        super().__init__()
        self.forecast = forecast or {}
        self.width = width
        self.height = height

    def wrap(self, avail_width, avail_height):
        return min(self.width, avail_width), self.height

    def draw(self):
        c = self.canv
        width = self.width
        height = self.height
        left = 13 * mm
        bottom = 11 * mm
        plot_w = width - left - 8 * mm
        plot_h = height - bottom - 9 * mm

        minutes = self.forecast.get("minutes") or []
        soc = self.forecast.get("soc") or []
        temperature = self.forecast.get("temperature") or []
        requested_u = self.forecast.get("requested_u") or []
        recommended_u = self.forecast.get("recommended_u") or []

        c.setFillColor(COLOR_PANEL)
        c.roundRect(0, 0, width, height, 7, stroke=0, fill=1)
        c.setStrokeColor(COLOR_LINE)
        c.setLineWidth(0.7)
        c.line(left, bottom, left + plot_w, bottom)
        c.line(left, bottom, left, bottom + plot_h)
        c.setFont(BASE_FONT, 7.5)
        c.setFillColor(COLOR_MUTED)
        c.drawString(left, height - 7 * mm, "Forecast trace")
        c.drawRightString(width - 8 * mm, height - 7 * mm, "SoC / temp / C-rate")

        if not minutes:
            c.setFillColor(COLOR_MUTED)
            c.drawString(left + 4 * mm, bottom + plot_h / 2, "Forecast unavailable")
            return

        max_minute = max(max(minutes), 1)

        def x_for(minute: float) -> float:
            return left + (minute / max_minute) * plot_w

        def points(values: list[float], min_v: float, max_v: float) -> list[tuple[float, float]]:
            span = max(max_v - min_v, 0.001)
            built = []
            for index, value in enumerate(values):
                if index >= len(minutes):
                    break
                x = x_for(float(minutes[index]))
                y = bottom + ((float(value) - min_v) / span) * plot_h
                built.append((x, y))
            return built

        def draw_line(values: list[float], min_v: float, max_v: float, color, dashed=False):
            pts = points(values, min_v, max_v)
            if len(pts) < 2:
                return
            c.setStrokeColor(color)
            c.setLineWidth(1.8)
            c.setDash(4, 3) if dashed else c.setDash()
            path = c.beginPath()
            path.moveTo(*pts[0])
            for point in pts[1:]:
                path.lineTo(*point)
            c.drawPath(path, stroke=1, fill=0)
            c.setDash()

        draw_line(temperature, min(min(temperature or [20]), 20), max(max(temperature or [55]), 55), COLOR_DANGER)
        draw_line(soc, 0, 1, COLOR_OK)
        c_max = max(max(requested_u or [0]), max(recommended_u or [0]), 1)
        draw_line(requested_u, 0, c_max, COLOR_ACCENT_2, dashed=True)
        draw_line(recommended_u, 0, c_max, COLOR_GOLD)

        c.setFont(BASE_FONT, 7)
        legend = [("temperature", COLOR_DANGER), ("SoC", COLOR_OK), ("requested C", COLOR_ACCENT_2), ("recommended C", COLOR_GOLD)]
        legend_x = left
        for label, color in legend:
            c.setFillColor(color)
            c.circle(legend_x, 5 * mm, 2.1, stroke=0, fill=1)
            c.setFillColor(COLOR_MUTED)
            c.drawString(legend_x + 3 * mm, 4 * mm, label)
            legend_x += 31 * mm


def _styles() -> dict[str, ParagraphStyle]:
    return {
        "logo": ParagraphStyle("logo", fontName=BOLD_FONT, fontSize=30, leading=32, textColor=COLOR_WHITE, alignment=TA_LEFT),
        "cover_eyebrow": ParagraphStyle("cover_eyebrow", fontName=BOLD_FONT, fontSize=10, leading=13, textColor=COLOR_ACCENT_2, alignment=TA_LEFT),
        "cover_title": ParagraphStyle("cover_title", fontName=BOLD_FONT, fontSize=30, leading=35, textColor=COLOR_WHITE, alignment=TA_LEFT),
        "cover_subtitle": ParagraphStyle("cover_subtitle", fontName=BASE_FONT, fontSize=11, leading=16, textColor=COLOR_MUTED, alignment=TA_LEFT),
        "section": ParagraphStyle("section", fontName=BOLD_FONT, fontSize=13.5, leading=17, textColor=COLOR_ACCENT_2, alignment=TA_LEFT),
        "body": ParagraphStyle("body", fontName=BASE_FONT, fontSize=9.2, leading=13, textColor=COLOR_TEXT, alignment=TA_LEFT),
        "body_muted": ParagraphStyle("body_muted", fontName=BASE_FONT, fontSize=8.6, leading=12, textColor=COLOR_MUTED, alignment=TA_LEFT),
        "label": ParagraphStyle("label", fontName=BOLD_FONT, fontSize=7.4, leading=9.2, textColor=COLOR_MUTED, alignment=TA_LEFT),
        "value": ParagraphStyle("value", fontName=BOLD_FONT, fontSize=13.2, leading=16, textColor=COLOR_TEXT, alignment=TA_LEFT),
        "value_big": ParagraphStyle("value_big", fontName=BOLD_FONT, fontSize=22, leading=26, textColor=COLOR_TEXT, alignment=TA_LEFT),
        "center_muted": ParagraphStyle("center_muted", fontName=BASE_FONT, fontSize=8, leading=10.5, textColor=COLOR_MUTED, alignment=TA_CENTER),
    }


def _p(text: object, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape("" if text is None else str(text)), style)


def _state_color(state: str) -> colors.Color:
    normalized = state.upper().strip()
    if normalized == "STABLE":
        return COLOR_OK
    if normalized == "DAMPED":
        return COLOR_WARN
    if normalized == "LOCKED":
        return COLOR_DANGER
    return COLOR_MUTED


def _risk_level(state: str) -> str:
    normalized = state.upper().strip()
    if normalized == "STABLE":
        return "LOW"
    if normalized == "DAMPED":
        return "MEDIUM"
    if normalized == "LOCKED":
        return "HIGH"
    return "UNKNOWN"


def _status_label(state: str) -> str:
    normalized = state.upper().strip()
    if normalized == "STABLE":
        return "STABLE | monitor and continue"
    if normalized == "DAMPED":
        return "DAMPED | reduce and supervise"
    if normalized == "LOCKED":
        return "LOCKED | hold operation"
    return "UNKNOWN | human review required"


def _usage_text(usage: dict | None) -> str:
    if not usage:
        return "UNKNOWN"
    if usage.get("api_key_valid"):
        return "API key active"
    return f"{usage.get('usage_count', 'UNKNOWN')}/{usage.get('free_limit', 'UNKNOWN')} used | {usage.get('remaining', 'UNKNOWN')} remaining"


def _table(data: list[list[object]], col_widths: list[float], background=COLOR_PANEL, line=COLOR_LINE) -> Table:
    table = Table(data, colWidths=col_widths, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), background),
                ("BOX", (0, 0), (-1, -1), 0.7, line),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, line),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def _card(label: str, value: object, styles: dict[str, ParagraphStyle], tone: colors.Color | None = None) -> list[Paragraph]:
    value_style = ParagraphStyle("value_tone", parent=styles["value"], textColor=tone or COLOR_TEXT)
    return [_p(label.upper(), styles["label"]), _p(value, value_style)]


def _summary_text(result: dict) -> str:
    state = str(result.get("state", "UNKNOWN"))
    decision = result.get("decision", "UNKNOWN")
    if state.upper() == "LOCKED":
        prefix = "The requested BESS operation is not recommended under the provided operating conditions."
    elif state.upper() == "DAMPED":
        prefix = "The requested BESS operation requires limitation, supervision and controlled execution."
    elif state.upper() == "STABLE":
        prefix = "The requested BESS operation appears operationally acceptable within the advisory model."
    else:
        prefix = "The advisory state is unknown and requires human validation."
    return f"{prefix} {decision}"


def _risk_items(result: dict) -> list[str]:
    warnings = result.get("warnings") or []
    items = list(warnings)
    predicted_temp = result.get("predicted_max_temp")
    tension = result.get("tension")
    safe_value = result.get("recommended_u_safe_value")
    if predicted_temp is not None and float(predicted_temp) >= 40:
        items.append("Thermal envelope is elevated for the requested dispatch profile.")
    if tension is not None and float(tension) >= 0.55:
        items.append("Operational tension index suggests constrained execution margin.")
    if safe_value is not None and float(safe_value) <= 0.3:
        items.append("Recommended safe C-rate is materially below requested dispatch intensity.")
    return items or ["No elevated risk markers detected in the advisory output."]


def _recommendations(result: dict) -> list[str]:
    state = str(result.get("state", "UNKNOWN")).upper()
    safe_rate = result.get("recommended_u_safe", "UNKNOWN")
    base = [
        f"Use recommended safe C-rate: {safe_rate}.",
        "Keep operator review active before any real BMS/PCS action.",
        "Preserve this report with the case record and input data trace.",
    ]
    if state == "LOCKED":
        return ["Hold the requested operation until conditions are revalidated."] + base
    if state == "DAMPED":
        return ["Proceed only with reduced dispatch and monitoring."] + base
    if state == "STABLE":
        return ["Continue with normal monitoring and periodic verification."] + base
    return ["Escalate to human validation before operational use."] + base


def _economics_rows(result: dict, styles: dict[str, ParagraphStyle]) -> list[list[object]]:
    economics = result.get("economics") or {}
    return [
        [_p("Metric", styles["label"]), _p("Value", styles["label"])],
        [_p("Revenue PLN", styles["body"]), _p(economics.get("revenue_pln", "UNKNOWN"), styles["body"])],
        [_p("Degradation cost PLN", styles["body"]), _p(economics.get("degradation_cost_pln", "UNKNOWN"), styles["body"])],
        [_p("Net value PLN", styles["body"]), _p(economics.get("net_value_pln", "UNKNOWN"), styles["body"])],
        [_p("Stress multiplier", styles["body"]), _p(economics.get("stress_multiplier", "UNKNOWN"), styles["body"])],
    ]


def _forecast_rows(result: dict, styles: dict[str, ParagraphStyle]) -> list[list[object]]:
    forecast = result.get("forecast") or {}
    minutes = forecast.get("minutes") or []
    soc = forecast.get("soc") or []
    temperature = forecast.get("temperature") or []
    requested_u = forecast.get("requested_u") or []
    recommended_u = forecast.get("recommended_u") or []
    rows = [[_p("Minute", styles["label"]), _p("SoC", styles["label"]), _p("Temp C", styles["label"]), _p("Requested", styles["label"]), _p("Recommended", styles["label"])]]
    for index, minute in enumerate(minutes):
        rows.append([_p(minute, styles["body"]), _p(_safe_index(soc, index), styles["body"]), _p(_safe_index(temperature, index), styles["body"]), _p(_safe_index(requested_u, index), styles["body"]), _p(_safe_index(recommended_u, index), styles["body"])])
    return rows


def _safe_index(values: list, index: int) -> object:
    if index >= len(values):
        return "UNKNOWN"
    value = values[index]
    if isinstance(value, float):
        return round(value, 3)
    return value


def _draw_page(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(COLOR_BG)
    canvas.rect(0, 0, width, height, stroke=0, fill=1)
    canvas.setFillColor(colors.HexColor("#071a24"))
    canvas.circle(width - 18 * mm, height - 10 * mm, 58 * mm, stroke=0, fill=1)
    canvas.setStrokeColor(COLOR_LINE)
    canvas.setLineWidth(0.5)
    canvas.line(15 * mm, 13 * mm, width - 15 * mm, 13 * mm)
    canvas.setFont(BASE_FONT, 7.5)
    canvas.setFillColor(COLOR_MUTED)
    canvas.drawString(15 * mm, 8 * mm, "TDK Energy Intelligence Platform")
    canvas.drawRightString(width - 15 * mm, 8 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build_anchorgrid_premium_pdf(
    result: dict,
    usage: dict | None,
    output_path: str,
    *,
    request_id: str | None = None,
) -> str:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    styles = _styles()
    report_id = request_id or f"AGR-{datetime.now().strftime('%Y%m%d')}-{output.stem[-8:].upper()}"
    generated_at = datetime.now().isoformat(timespec="seconds")
    state = str(result.get("state", "UNKNOWN"))
    state_color = _state_color(state)

    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=17 * mm,
        title="TDK Energy Intelligence Platform - Executive AnchorGrid Report",
        author="TDK&ProService",
    )

    status_style = ParagraphStyle("status", parent=styles["value_big"], textColor=state_color)
    story = [
        Spacer(1, 16),
        _table(
            [[_p("TDK", styles["logo"]), _p("Energy Intelligence Platform", styles["cover_eyebrow"])]],
            [38 * mm, 98 * mm],
            background=colors.HexColor("#07141c"),
            line=colors.HexColor("#2e6b82"),
        ),
        Spacer(1, 32),
        _p("PREMIUM EXECUTIVE REPORT", styles["cover_eyebrow"]),
        _p("AnchorGrid BESS Advisory", styles["cover_title"]),
        _p("Executive decision-support report for battery energy storage dispatch, operational risk and economic impact.", styles["cover_subtitle"]),
        Spacer(1, 22),
        _table(
            [
                [_p("Report number", styles["label"]), _p(report_id, styles["body"])],
                [_p("Generated", styles["label"]), _p(generated_at, styles["body"])],
                [_p("Platform", styles["label"]), _p("TDK Energy Intelligence Platform", styles["body"])],
                [_p("Boundary", styles["label"]), _p("Advisory only | operator approval required | autonomous action false", styles["body"])],
            ],
            [42 * mm, 123 * mm],
            background=COLOR_PANEL,
        ),
        Spacer(1, 20),
        _table(
            [
                [_p("Executive status", styles["label"]), _p("Risk level", styles["label"]), _p("Access", styles["label"])],
                [Paragraph(escape(_status_label(state)), status_style), _p(_risk_level(state), styles["value_big"]), _p(_usage_text(usage), styles["value"])],
            ],
            [66 * mm, 38 * mm, 61 * mm],
            background=COLOR_CARD,
            line=state_color,
        ),
        Spacer(1, 18),
        _p("Executive Summary", styles["section"]),
        _table([[_p(_summary_text(result), styles["body"])]], [165 * mm], background=colors.HexColor("#0b1a22")),
        PageBreak(),
        _p("Executive Summary", styles["section"]),
        _table([[_p(_summary_text(result), styles["body"])]], [165 * mm], background=COLOR_PANEL),
        Spacer(1, 10),
        _p("KPI Dashboard", styles["section"]),
        _table(
            [
                [_card("State", state, styles, state_color), _card("Execution mode", result.get("execution_mode", "UNKNOWN"), styles), _card("Safe C-rate", result.get("recommended_u_safe", "UNKNOWN"), styles)],
                [_card("Predicted max temp", f"{result.get('predicted_max_temp', 'UNKNOWN')} C", styles, COLOR_WARN if float(result.get("predicted_max_temp", 0) or 0) >= 35 else COLOR_OK), _card("Tension index", result.get("tension", "UNKNOWN"), styles), _card("Forecast confidence", result.get("forecast_confidence", "UNKNOWN"), styles)],
            ],
            [55 * mm, 55 * mm, 55 * mm],
            background=COLOR_CARD,
        ),
        Spacer(1, 10),
        _p("Forecast Trace", styles["section"]),
        ForecastTraceChart(result.get("forecast") or {}),
        Spacer(1, 10),
        _table(_forecast_rows(result, styles), [25 * mm, 25 * mm, 30 * mm, 40 * mm, 45 * mm], background=COLOR_PANEL_2),
        Spacer(1, 10),
        _p("Risk Map", styles["section"]),
        _table([[_p(f"- {item}", styles["body"])] for item in _risk_items(result)], [165 * mm], background=COLOR_PANEL),
        Spacer(1, 10),
        _p("Recommendations", styles["section"]),
        _table([[_p(f"- {item}", styles["body"])] for item in _recommendations(result)], [165 * mm], background=colors.HexColor("#0b1a22")),
        Spacer(1, 10),
        _p("Economic View", styles["section"]),
        _table(_economics_rows(result, styles), [65 * mm, 100 * mm], background=COLOR_PANEL_2),
        Spacer(1, 10),
        _p("Governance Notes", styles["section"]),
        _table(
            [
                [_p("Operator approval required", styles["label"]), _p("true", styles["body"])],
                [_p("Autonomous action", styles["label"]), _p("false", styles["body"])],
                [_p("Public output", styles["label"]), _p("Sanitized advisory result only", styles["body"])],
                [_p("Final authority", styles["label"]), _p("BMS / PCS / human operator", styles["body"])],
            ],
            [55 * mm, 110 * mm],
            background=COLOR_PANEL,
        ),
        Spacer(1, 8),
        _p(result.get("disclaimer", "Final decisions belong to BMS/PCS/operator."), styles["body_muted"]),
        Spacer(1, 4),
        _p("TDK&ProService | kontakt@tdkproservice.pl | platform.tdkproservice.pl", styles["center_muted"]),
    ]

    doc.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
    return str(output)
