import hashlib
import html
import json
import os
import smtplib
import ssl
import time
import uuid
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Optional
from urllib.parse import unquote
from urllib.request import Request as UrlRequest, urlopen
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
load_dotenv(r'C:\KODEKS\.env')
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.anchorgrid.engine import analyze_bess
from app.anchorgrid.premium_pdf_builder import build_anchorgrid_premium_pdf
from app.anchorgrid.schemas import BessInput
from app.engine.process_engine import run_process
from app.input.normalizer import normalize_input
from app.output.pdf_builder import generate_pdf
from app.output.report_builder import build_report
from app.routing.mask_router import choose_mask
from app.storage.order_store import FileSystemOrderStore, create_order_id


load_dotenv()

REPORTS_DIR = Path("data") / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
MAIL_LOG_PATH = Path("data") / "logs" / "mail_failures.log"
MAIL_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
ANCHORGRID_USAGE_PATH = Path("data") / "anchorgrid_usage.json"
ANCHORGRID_FREE_LIMIT = int(os.getenv("ANCHORGRID_FREE_LIMIT", "10"))
ANCHORGRID_API_KEYS = {
    key.strip()
    for key in os.getenv("ANCHORGRID_API_KEYS", "").split(",")
    if key.strip()
}
APP_ENV = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "public-intake")).lower()
DOCS_ENABLED = (
    os.getenv("ENABLE_PUBLIC_DOCS", "").lower() in {"1", "true", "yes"}
    or APP_ENV in {"local", "dev", "development", "test"}
)
ANCHORGRID_RATE_LIMIT_WINDOW_SEC = int(
    os.getenv("ANCHORGRID_RATE_LIMIT_WINDOW_SEC", "60")
)
ANCHORGRID_RATE_LIMIT_ANALYZE = int(os.getenv("ANCHORGRID_RATE_LIMIT_ANALYZE", "30"))
ANCHORGRID_RATE_LIMIT_PDF = int(os.getenv("ANCHORGRID_RATE_LIMIT_PDF", "10"))
_RATE_LIMIT_BUCKETS: dict[str, dict[str, float]] = {}
ASSISTANT_RATE_LIMIT = int(os.getenv("ASSISTANT_RATE_LIMIT", "20"))
ASSISTANT_MAX_MESSAGES = int(os.getenv("ASSISTANT_MAX_MESSAGES", "32"))
ASSISTANT_MAX_MESSAGE_CHARS = int(os.getenv("ASSISTANT_MAX_MESSAGE_CHARS", "1200"))
ASSISTANT_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ASSISTANT_ALLOWED_ORIGINS",
        "https://tdkproservice.pl,https://www.tdkproservice.pl,http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]

order_store = FileSystemOrderStore()
PL_TZ = ZoneInfo("Europe/Warsaw")

LEAD_NOTIFY_EMAIL = os.getenv(
    "LEAD_NOTIFY_EMAIL",
    "kontakt@tdkproservice.pl"
)

EMAIL_DELIVERY_CHANNEL = os.getenv("EMAIL_DELIVERY_CHANNEL", "smtp").strip().lower()
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
EMAIL_API_FROM = os.getenv("EMAIL_API_FROM", "TDK&ProService <kontakt@tdkproservice.pl>").strip()
EMAIL_REPLY_TO = os.getenv("EMAIL_REPLY_TO", "kontakt@tdkproservice.pl").strip()

# =========================
# ADMIN
# =========================

# Ustaw w Render → Environment
ADMIN_KEY = os.getenv(
    "ADMIN_KEY",
    "zmien-to-w-render"
)

# =========================
# PŁATNOŚĆ
# =========================

PAYMENT_AMOUNT = os.getenv(
    "PAYMENT_AMOUNT",
    "149,99 zł"
)

PAYMENT_ACCOUNT_NAME = os.getenv(
    "PAYMENT_ACCOUNT_NAME",
    "TDK&ProService Dawid Zabłotny"
)

# Konto bankowe
PAYMENT_BANK_ACCOUNT = os.getenv(
    "PAYMENT_BANK_ACCOUNT",
    "83102046490000700202108116"
)

# BLIK na telefon
PAYMENT_BLIK_PHONE = os.getenv(
    "PAYMENT_BLIK_PHONE",
    "723023152"
)

PAYMENT_CONTACT_EMAIL = os.getenv(
    "PAYMENT_CONTACT_EMAIL",
    "kontakt@tdkproservice.pl"
)
app = FastAPI(
    title="KODEKS API",
    docs_url="/docs" if DOCS_ENABLED else None,
    redoc_url="/redoc" if DOCS_ENABLED else None,
    openapi_url="/openapi.json" if DOCS_ENABLED else None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ASSISTANT_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault(
        "Strict-Transport-Security",
        "max-age=63072000; includeSubDomains; preload",
    )
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=(), payment=()",
    )
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; "
        "img-src 'self' data: https:; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "connect-src 'self' https://api.tdkproservice.pl https://platform.tdkproservice.pl; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'",
    )
    return response


@app.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "service": "KODEKS API",
        "runtime": "public-intake",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/v1/health")
def anchorgrid_platform_health() -> dict:
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "public-intake"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "api": "ready",
            "anchorgrid": "ready",
            "usage_guard": "ready",
            "control_plane": "private",
            "runtime_state": "private",
        },
    }


def format_pl_time(value: str | None) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    normalized = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized[:25])
    except ValueError:
        try:
            parsed = datetime.fromisoformat(normalized[:19])
        except ValueError:
            return raw
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    local_time = parsed.astimezone(PL_TZ)
    return (
        f'{local_time.strftime("%Y-%m-%d %H:%M")} '
        f'<span style="color:#7f8b99;font-size:12px;">czas lokalny PL</span>'
    )


class AnalyzeRequest(BaseModel):
    text: str
    email: str


class AnalyzePaidRequest(BaseModel):
    email: Optional[str] = None
    consumption_kwh: Optional[float] = None
    price_per_kwh: Optional[float] = None
    pv_power_kw: Optional[float] = None
    pv_monthly_production_kwh: Optional[float] = None



class AssistantMessage(BaseModel):
    role: str
    content: str


class AssistantIntakeRequest(BaseModel):
    name: str
    email: str
    phone: str
    city: Optional[str] = None
    category: str
    summary: str
    completeness: str
    conversation: list[AssistantMessage]
    collected_data: dict = {}
    safety_flags: list[str] = []
    missing_data: list[str] = []
    consent_contact: bool
    consent_data: bool
    source_page: str = "tdk_assistant_widget"


class AssistantIntakeResponse(BaseModel):
    case_id: str
    status: str
    public_label: str
    message: str
    next_action: str
    mail_status: str
    mail_error_type: Optional[str] = None
    public_status_url: str


class PublicCaseStatusResponse(BaseModel):
    case_id: str
    status: str
    public_label: str
    created_at: str
    updated_at: str
    message: str


class AnchorGridPlatformRequest(BaseModel):
    soc: float
    t_cell: float
    t_amb: float
    u_requested: float
    hvac: bool = False
    direction: str = "DISCHARGE"
    horizon: int = 15
    price: Optional[float] = None
    api_key: Optional[str] = None
    case_id: Optional[str] = None


def run_analysis(text: str, email: str, base_url: str) -> dict:
    normalized = normalize_input(text)
    selected_mask, _route_reason = choose_mask(normalized)
    process_result = run_process(normalized, selected_mask)

    report_text = build_report(
        raw_input=text,
        selected_mask=selected_mask,
        process_result=process_result,
    )

    unique_id = uuid.uuid4().hex[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = REPORTS_DIR / f"raport_{timestamp}_{unique_id}.pdf"

    generate_pdf(report_text, str(pdf_path))

    return {
        "status": "ok",
        "pdf_url": f"{base_url}/reports/{pdf_path.name}",
        "pdf_path": str(pdf_path),
    }


def build_paid_analysis_text(payload: AnalyzePaidRequest) -> str:
    return (
        f"Zużycie {payload.consumption_kwh} kWh, "
        f"cena {payload.price_per_kwh} zł, "
        f"PV {payload.pv_power_kw} kWp, "
        f"produkcja PV {payload.pv_monthly_production_kwh} kWh"
    )


def validate_paid_payload(payload: AnalyzePaidRequest) -> list[str]:
    errors = []

    if not payload.email:
        errors.append("email jest wymagany")

    if payload.consumption_kwh is None:
        errors.append("consumption_kwh jest wymagane")
    elif payload.consumption_kwh <= 0:
        errors.append("consumption_kwh musi być większe niż 0")

    if payload.price_per_kwh is None:
        errors.append("price_per_kwh jest wymagane")
    elif payload.price_per_kwh <= 0:
        errors.append("price_per_kwh musi być większe niż 0")

    if payload.pv_power_kw is None:
        errors.append("pv_power_kw jest wymagane")
    elif payload.pv_power_kw < 0:
        errors.append("pv_power_kw musi być większe lub równe 0")
    elif payload.pv_power_kw > 100:
        errors.append(
            "Moc PV wygląda nieprawidłowo. Podaj wartość w kWp, np. 8 zamiast 8000."
        )

    if payload.pv_monthly_production_kwh is None:
        errors.append("pv_monthly_production_kwh jest wymagane")
    elif payload.pv_monthly_production_kwh < 0:
        errors.append("pv_monthly_production_kwh musi być większe lub równe 0")

    return errors


def build_analysis_text_from_order(order: dict) -> str:
    return (
        f"Zużycie {order['consumption_kwh']} kWh, "
        f"cena {order['price_per_kwh']} zł, "
        f"PV {order['pv_power_kw']} kWp, "
        f"produkcja PV {order['pv_monthly_production_kwh']} kWh"
    )


def verify_admin_key(admin_key: str) -> bool:
    return admin_key == ADMIN_KEY and ADMIN_KEY != "zmien-to-w-render"


def html_page(title: str, body: str) -> str:
    return f"""
    <!doctype html>
    <html lang="pl">
    <head>
        <meta charset="utf-8">
        <title>{title}</title>
    </head>
    <body style="background:#0f1115;color:#f1f1f1;font-family:Arial,sans-serif;padding:40px;">
        <div style="max-width:980px;margin:40px auto;background:#171b22;border:1px solid #2b3240;border-radius:18px;padding:36px;">
            {body}
        </div>
    </body>
    </html>
    """


def log_mail_failure(recipient: str, exc: Exception) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    error_type = type(exc).__name__
    MAIL_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    MAIL_LOG_PATH.write_text(
        "",
        encoding="utf-8",
    ) if not MAIL_LOG_PATH.exists() else None
    with MAIL_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(
            f"{timestamp}\trecipient={recipient}\terror_type={error_type}\tmessage={str(exc)}\n"
        )


def update_order_mail_status(
    order_id: str,
    field_prefix: str,
    status: str,
    info: str,
    error: Exception | None = None,
) -> dict:
    order = order_store.get_order(order_id)
    now = datetime.now().isoformat(timespec="seconds")
    order[f"{field_prefix}_status"] = status
    order[f"{field_prefix}_info"] = info
    order[f"{field_prefix}_updated_at"] = now
    if error is not None:
        order[f"{field_prefix}_error_type"] = type(error).__name__
    else:
        order.pop(f"{field_prefix}_error_type", None)
    order_store.update_order(order_id, order)
    return order


def _smtp_config() -> dict:
    return {
        "host": os.getenv("SMTP_HOST"),
        "port": int(os.getenv("SMTP_PORT", "465")),
        "user": os.getenv("SMTP_USER"),
        "password": os.getenv("SMTP_PASS"),
        "from_email": os.getenv("SMTP_FROM", "kontakt@tdkproservice.pl"),
    }


def _message_text_content(message: EmailMessage) -> str:
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/plain" and not part.get_filename():
                return part.get_content()
        return ""
    return message.get_content()


def _send_message_via_resend(message: EmailMessage) -> None:
    if not RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY is not configured")
    if list(message.iter_attachments()):
        raise RuntimeError("Resend adapter does not handle attachments yet")

    payload = {
        "from": EMAIL_API_FROM,
        "to": [message["To"]],
        "reply_to": [EMAIL_REPLY_TO],
        "subject": message["Subject"],
        "text": _message_text_content(message),
    }
    request = UrlRequest(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            if response.status >= 300:
                raise RuntimeError(f"Resend API returned HTTP {response.status}")
    except HTTPError as exc:
        raise RuntimeError(f"Resend API returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError("Resend API request failed") from exc


def _send_message_smtp(message: EmailMessage) -> None:
    config = _smtp_config()

    missing = []
    if not config["host"]:
        missing.append("SMTP_HOST")
    if not config["user"]:
        missing.append("SMTP_USER")
    if not config["password"]:
        missing.append("SMTP_PASS")
    if not config["from_email"]:
        missing.append("SMTP_FROM")

    if missing:
        raise RuntimeError("SMTP nie jest skonfigurowane: brakuje " + ", ".join(missing))

    context = ssl._create_unverified_context()  # TDK LOCAL FIX: nazwa.pl self-signed chain

    fallback_hosts = []
    for host in [config["host"], "smtp.nazwa.pl"]:
        if host and host not in fallback_hosts:
            fallback_hosts.append(host)

    attempts = []
    if config["port"] == 465:
        attempts.extend([("ssl", 465), ("starttls", 587)])
    else:
        attempts.extend([("starttls", config["port"]), ("ssl", 465), ("starttls", 587)])

    last_error: Exception | None = None
    for host in fallback_hosts:
        for mode, port in attempts:
            try:
                if mode == "ssl":
                    with smtplib.SMTP_SSL(host, port, context=context, timeout=12) as smtp:
                        smtp.login(config["user"], config["password"])
                        smtp.send_message(message)
                        return
                with smtplib.SMTP(host, port, timeout=12) as smtp:
                    smtp.starttls(context=context)
                    smtp.login(config["user"], config["password"])
                    smtp.send_message(message)
                    return
            except TimeoutError as exc:
                last_error = exc
                continue

    if last_error:
        raise last_error
    raise RuntimeError("SMTP delivery failed")


def _send_message(message: EmailMessage) -> None:
    if EMAIL_DELIVERY_CHANNEL in {"resend", "https", "api"}:
        _send_message_via_resend(message)
        return
    if EMAIL_DELIVERY_CHANNEL == "auto" and RESEND_API_KEY:
        _send_message_via_resend(message)
        return
    _send_message_smtp(message)


def send_email_with_pdf(to_email: str, pdf_path: str) -> tuple[bool, str]:
    config = _smtp_config()

    path = Path(pdf_path)
    if not path.exists():
        raise RuntimeError(f"Nie znaleziono pliku PDF do wysyłki: {pdf_path}")

    message = EmailMessage()
    message["Subject"] = "Analiza kosztów energii — TDK&ProService"
    message["From"] = config["from_email"]
    message["To"] = to_email

    message.set_content(
        "Dzień dobry,\n\n"
        "w załączniku przesyłamy wstępną ocenę systemu OZE przygotowaną przez TDK&ProService.\n"
        "Dokument jest screeningiem techniczno-energetycznym opartym na danych wpisanych w formularzu.\n\n"
        "To nie jest pełny audyt techniczny ani opinia rzeczoznawcza.\n\n"
        "Jeśli zdecydują się Państwo na pełną diagnostykę techniczną, koszt tej analizy "
        "w wysokości 149,99 zł zostanie odliczony od ceny pełnej usługi.\n\n"
        "TDK&ProService\n"
        "kontakt@tdkproservice.pl\n"
    )

    message.add_attachment(
        path.read_bytes(),
        maintype="application",
        subtype="pdf",
        filename=path.name,
    )

    _send_message(message)
    return True, "Mail z raportem został wysłany."


def send_lead_notification(
    client_email: str,
    consumption_kwh: float,
    price_per_kwh: float,
    pv_power_kw: float,
    pv_monthly_production_kwh: float,
    pdf_url: str,
    client_name: str = "",
    client_phone: str = "",
    client_message: str = "",
) -> tuple[bool, str]:
    config = _smtp_config()

    message = EmailMessage()
    message["Subject"] = "Nowy lead KODEKS — TDK&ProService"
    message["From"] = config["from_email"]
    message["To"] = LEAD_NOTIFY_EMAIL
    message["Reply-To"] = EMAIL_REPLY_TO

    message.set_content(
        "Nowy lead z formularza KODEKS.\n\n"
        f"Imię: {client_name or 'brak'}\n"
        f"Email klienta: {client_email}\n"
        f"Telefon: {client_phone or 'brak'}\n"
        f"Opis problemu: {client_message or 'brak'}\n\n"
        f"Zużycie miesięczne: {consumption_kwh} kWh\n"
        f"Cena energii: {price_per_kwh} zł/kWh\n"
        f"Moc PV: {pv_power_kw} kWp\n"
        f"Miesięczna produkcja PV: {pv_monthly_production_kwh} kWh\n\n"
        f"Link do PDF / status zgłoszenia:\n{pdf_url}\n\n"
        "To jest zgłoszenie do wstępnej oceny i potencjalny klient do dalszej diagnostyki technicznej.\n"
    )

    _send_message(message)
    return True, "Lead został wysłany na kontakt@tdkproservice.pl."


def mail_status_badge(status: str | None) -> str:
    styles = {
        "MAIL_SENT": ("Mail wysłany", "#0f241b", "#245c3a", "#7ee787"),
        "MAIL_PENDING": ("Mail oczekuje", "#241d0f", "#7a5a1d", "#f4c76b"),
        "MAIL_NOT_CONFIRMED": ("Mail niepotwierdzony", "#2d1111", "#7a2b2b", "#ff9b9b"),
    }
    label, background, border, color = styles.get(
        status or "MAIL_PENDING",
        ("Mail oczekuje", "#241d0f", "#7a5a1d", "#f4c76b"),
    )
    return (
        f'<span style="display:inline-block;padding:8px 11px;border-radius:999px;'
        f'background:{background};border:1px solid {border};color:{color};'
        f'font-size:13px;font-weight:bold;white-space:nowrap;">{label}</span>'
    )


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
    <!doctype html>
    <html lang="pl">
    <head>
        <meta charset="utf-8">
        <title>TDK&ProService | KODEKS</title>

        <style>
            body {
                margin: 0;
                padding: 40px;
                background: #0f1115;
                color: #f1f1f1;
                font-family: Arial, sans-serif;
            }

            .wrapper {
                max-width: 1180px;
                margin: auto;
            }

            h1 {
                font-size: 38px;
                margin-bottom: 10px;
            }

            .subtitle {
                color: #b0b7c3;
                margin-bottom: 34px;
                line-height: 1.6;
            }

            .container {
                display: flex;
                gap: 30px;
                align-items: flex-start;
                flex-wrap: wrap;
            }

            .form-box,
            .example-box,
            .price-box {
                background: #171b22;
                border: 1px solid #2b3240;
                border-radius: 14px;
                padding: 28px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.35);
            }

            .form-box {
                flex: 1;
                min-width: 340px;
            }

            .side {
                width: 390px;
                display: flex;
                flex-direction: column;
                gap: 20px;
            }

            h2 {
                margin-top: 0;
                color: #ffffff;
            }

            label {
                display: block;
                margin-bottom: 6px;
                color: #d7dce5;
                font-weight: bold;
            }

            input {
                width: 100%;
                padding: 12px;
                margin-bottom: 22px;
                border-radius: 8px;
                border: 1px solid #394252;
                background: #10141a;
                color: white;
                box-sizing: border-box;
                font-size: 15px;
            }

            .helper {
                margin: -14px 0 22px;
                color: #9da7b3;
                line-height: 1.55;
                font-size: 13px;
            }

            input:focus {
                outline: none;
                border-color: #4da3ff;
                box-shadow: 0 0 0 3px rgba(77,163,255,0.15);
            }

            button {
                width: 100%;
                padding: 15px;
                border: none;
                border-radius: 10px;
                background: #2f7cf6;
                color: white;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                transition: 0.2s ease;
            }

            button:hover {
                background: #4d95ff;
            }

            .price {
                font-size: 34px;
                font-weight: bold;
                color: #ffffff;
                margin: 12px 0;
            }

            .note {
                color: #b0b7c3;
                line-height: 1.6;
                font-size: 14px;
            }

            .credit {
                margin-top: 16px;
                padding: 14px;
                border-left: 4px solid #2f7cf6;
                background: #10141a;
                color: #d8dee9;
                line-height: 1.6;
                font-size: 14px;
            }

            .example-title {
                margin-bottom: 18px;
                font-size: 20px;
                font-weight: bold;
            }

            pre {
                white-space: pre-wrap;
                line-height: 1.7;
                color: #d8dee9;
                margin: 0;
                font-size: 15px;
            }

            .levels {
                margin-top: 18px;
                color: #d8dee9;
                line-height: 1.6;
                font-size: 14px;
            }

            .levels strong {
                color: #ffffff;
            }

            .footer {
                margin-top: 50px;
                color: #7d8796;
                font-size: 14px;
            }

            .data-guide {
                margin-top: 22px;
                padding: 18px;
                border-radius: 12px;
                background: #10141a;
                border: 1px solid #2b3240;
                color: #d8dee9;
                line-height: 1.65;
                font-size: 14px;
            }

            .data-guide h3 {
                margin: 0 0 10px;
                color: #ffffff;
                font-size: 18px;
            }

            .data-guide ul {
                margin: 0;
                padding-left: 20px;
            }

            @media (max-width: 900px) {
                .container {
                    flex-direction: column;
                }

                .side {
                    width: 100%;
                }
            }
        </style>
    </head>

    <body>
        <div class="wrapper">

            <h1>Wstępna ocena systemu OZE</h1>

            <div class="subtitle">
                Wprowadź podstawowe dane o zużyciu energii i pracy instalacji PV. System przygotuje
                wstępną ocenę kierunkową, która pomaga sprawdzić, czy w układzie mogą występować
                koszty ukryte lub obszary wymagające dalszej diagnostyki.
            </div>

            <div class="container">

                <div class="form-box">
                    <form method="post" action="/form-analyze" id="kodeks-form">

                        <label>Email</label>
                        <input type="email" name="email" required>

                        <label>Zużycie kWh miesięcznie</label>
                        <input type="number" step="0.01" name="consumption_kwh" required>

                        <label>Cena 1 kWh</label>
                        <input type="number" step="0.01" name="price_per_kwh" required>

                        <label>Moc PV w kWp</label>
                        <input type="number" step="0.01" name="pv_power_kw" required>

                        <label>Miesięczna produkcja PV</label>
                        <input type="number" step="0.01" name="pv_monthly_production_kwh" required>
                        <div class="helper">
                            Podaj orientacyjną produkcję miesięczną instalacji PV w kWh.
                            Uwaga: wartości kilku tysięcy kWh miesięcznie są zwykle nietypowe
                            dla domowych instalacji i mogą oznaczać pomylenie danych rocznych
                            z miesięcznymi.
                        </div>

                        <div style="margin:18px 0;padding:16px;border-left:4px solid #d4a84f;background:#15110a;color:#f4e3b0;line-height:1.65;border-radius:12px;font-size:14px;">
                            To nie jest pełny audyt techniczny. Wynik opiera się na danych wpisanych
                            w formularzu i ma charakter wstępny. Pełna diagnostyka wymaga faktur,
                            danych z falownika, historii pracy instalacji oraz analizy sposobu
                            zużycia energii.
                        </div>

                        <button type="submit">
                            Rozpocznij wstępną ocenę
                        </button>

                    </form>

                    <div class="data-guide">
                        <h3>Jak przygotować dane?</h3>
                        <ul>
                            <li>Zużycie miesięczne znajdziesz na fakturze energii.</li>
                            <li>Produkcję PV sprawdzisz w aplikacji falownika.</li>
                            <li>Upewnij się, czy wpisujesz dane miesięczne, a nie roczne.</li>
                            <li>W przypadku przybliżonych danych wynik ma charakter orientacyjny.</li>
                        </ul>
                    </div>
                </div>

                <div class="side">

                    <div class="price-box">
                        <h2>Wstępna ocena KODEKS</h2>
                        <div class="price">149,99 zł</div>

                        <div class="note">
                            Otrzymujesz PDF z podstawowym przeliczeniem kosztów, interpretacją
                            kierunkową i listą możliwych obszarów do dalszej weryfikacji.
                        </div>

                        <div class="credit">
                            Jeśli po raporcie zdecydujesz się na pełną diagnostykę techniczną
                            TDK&ProService, kwota <strong>149,99 zł</strong> zostanie odliczona
                            od ceny pełnej usługi.
                        </div>

                        <div class="levels">
                            Za analizą stoi TDK&ProService — praktyka terenowa Dawida Zabłotnego
                            w obszarze fotowoltaiki, pomp ciepła, magazynów energii i kosztów
                            utraconej energii.
                        </div>
                    </div>

                    <div class="example-box">
                        <div class="example-title">
                            Przykładowe dane do analizy
                        </div>

                        <pre>- Zużycie miesięczne: 323 kWh
- Cena energii: 1.23 zł/kWh
- Moc instalacji PV: 8 kWp
- Miesięczna produkcja PV: 653 kWh</pre>
                    </div>

                </div>

            </div>

            <div class="footer">
                TDK&ProService • Screening techniczno-energetyczny • Pierwszy etap diagnostyki OZE
            </div>

        </div>
        <script>
            const form = document.getElementById("kodeks-form");

            form.addEventListener("submit", function(event) {
                const consumption = Number(form.elements["consumption_kwh"].value || 0);
                const pvPower = Number(form.elements["pv_power_kw"].value || 0);
                const pvProduction = Number(form.elements["pv_monthly_production_kwh"].value || 0);
                const warnings = [];

                if (pvPower > 0 && pvPower <= 15 && pvProduction > 2500) {
                    warnings.push(
                        "Wprowadzona miesięczna produkcja PV wygląda nietypowo dla tej mocy instalacji. Sprawdź, czy nie wpisano produkcji rocznej zamiast miesięcznej."
                    );
                }

                if (consumption > 5000) {
                    warnings.push(
                        "Wartość wygląda bardzo wysoko dla gospodarstwa domowego. Sprawdź poprawność danych."
                    );
                }

                if (warnings.length > 0) {
                    const message = warnings.join("\\n\\n") + "\\n\\nMożesz kontynuować, jeśli dane są poprawne. Kontynuować?";
                    if (!window.confirm(message)) {
                        event.preventDefault();
                    }
                }
            });
        </script>
    </body>
    </html>
    """


@app.get("/anchorgrid", response_class=HTMLResponse)
def anchorgrid_home() -> str:
    return """
    <!doctype html>
    <html lang="pl">
    <head>
        <meta charset="utf-8">
        <title>AnchorGrid AI System</title>
        <style>
            body {
                margin: 0;
                padding: 34px;
                background: #0d1117;
                color: #f0f6fc;
                font-family: Arial, sans-serif;
            }

            main {
                max-width: 1120px;
                margin: 0 auto;
            }

            h1 {
                margin: 0 0 8px;
                font-size: 34px;
            }

            .sub {
                color: #9da7b3;
                line-height: 1.6;
                margin-bottom: 26px;
            }

            .layout {
                display: grid;
                grid-template-columns: minmax(320px, 1fr) minmax(320px, 0.9fr);
                gap: 22px;
                align-items: start;
            }

            .panel {
                background: #151b23;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 22px;
            }

            label {
                display: block;
                margin: 0 0 6px;
                font-weight: bold;
                color: #d7dde5;
            }

            input,
            select {
                width: 100%;
                box-sizing: border-box;
                margin: 0 0 16px;
                padding: 11px;
                background: #0d1117;
                border: 1px solid #30363d;
                border-radius: 6px;
                color: #f0f6fc;
                font-size: 15px;
            }

            button {
                width: 100%;
                padding: 13px;
                border: 0;
                border-radius: 6px;
                background: #238636;
                color: white;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
            }

            pre {
                white-space: pre-wrap;
                line-height: 1.65;
                color: #c9d1d9;
                margin: 0;
            }

            .notice {
                margin-top: 18px;
                padding: 14px;
                border-left: 4px solid #d29922;
                background: #201a0f;
                color: #f2cc60;
                line-height: 1.55;
            }

            @media (max-width: 820px) {
                body {
                    padding: 18px;
                }

                .layout {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <main>
            <h1>AnchorGrid AI System</h1>
            <div class="sub">
                BESS Safety &amp; Dispatch Advisory Engine.<br>
                Developed by Dawid Zablotny • TDK&amp;ProService
            </div>

            <div class="layout">
                <section class="panel">
                    <form method="post" action="/anchorgrid/analyze-form">
                        <label>SoC %</label>
                        <input name="soc" type="number" step="0.01" value="78" required>

                        <label>Temperatura ogniw °C</label>
                        <input name="t_cell" type="number" step="0.1" value="39" required>

                        <label>Temperatura otoczenia °C</label>
                        <input name="t_amb" type="number" step="0.1" value="31" required>

                        <label>Planowany C-rate</label>
                        <input name="u" type="number" step="0.01" value="0.8" required>

                        <label>HVAC</label>
                        <select name="hvac">
                            <option value="true">tak</option>
                            <option value="false">nie</option>
                        </select>

                        <label>Kierunek</label>
                        <select name="direction">
                            <option value="DISCHARGE">rozladowanie</option>
                            <option value="CHARGE">ladowanie</option>
                        </select>

                        <label>Horyzont minut</label>
                        <input name="horizon_minutes" type="number" step="1" value="15" required>

                        <label>Cena energii opcjonalnie</label>
                        <input name="price" type="number" step="0.01">

                        <button type="submit">Analyze BESS</button>
                    </form>
                </section>

                <section class="panel">
                    <pre>ANCHORGRID RESULT

state: DAMPED
execution_mode: CANARY
operation: DISCHARGE
requested_u: 0.8C
recommended_u_safe: okolo 0.5C
thermal_margin: niski
predicted_max_temp: 41.0 °C
forecast_confidence: 0.85 (HIGH)
estimated_degradation_stress: MEDIUM
tension: 0.72
economics_net_value_pln: -1200.00
soc_projection_15m: 0.78 -> 0.58
warnings: temperatura podwyzszona, ograniczyc moc
decision: Operacja mozliwa tylko z redukcja C-rate i monitoringiem.</pre>

                    <div class="notice">
                        To nie jest prawdziwa decyzja bezpieczeństwa BMS. Finalne bezpieczeństwo
                        zawsze należy do BMS/PCS/operatora.
                    </div>
                </section>
            </div>
        </main>
    </body>
    </html>
    """


def anchorgrid_result_text(result: dict) -> str:
    warnings = ", ".join(result.get("warnings", [])) or "brak"
    return (
        "ANCHORGRID RESULT\n\n"
        f"state: {result['state']}\n"
        f"execution_mode: {result['execution_mode']}\n"
        f"operation: {result['operation']}\n"
        f"requested_u: {result['requested_u']}\n"
        f"recommended_u_safe: {result['recommended_u_safe']}\n"
        f"thermal_margin: {result['thermal_margin']}\n"
        f"predicted_max_temp: {result['predicted_max_temp']} °C\n"
        f"forecast_confidence: {result['forecast_confidence']}\n"
        f"estimated_degradation_stress: {result['estimated_degradation_stress']}\n"
        f"tension: {result['tension']}\n"
        f"economics_net_value_pln: {result['economics'].get('net_value_pln')}\n"
        f"soc_projection_15m: {result['soc_projection_15m']}\n"
        f"warnings: {warnings}\n"
        f"reasons: {', '.join(result.get('reasons', {}).keys()) or 'brak'}\n"
        f"decision: {result['decision']}\n\n"
        f"{result['disclaimer']}\n\n"
        "AnchorGrid AI System\n"
        "Developed by Dawid Zablotny\n"
        "TDK&ProService"
    )


def anchorgrid_status_badge(state: str) -> str:
    styles = {
        "STABLE": ("#0f241b", "#245c3a", "#7ee787"),
        "DAMPED": ("#241d0f", "#7a5a1d", "#f4c76b"),
        "LOCKED": ("#2d1111", "#7a2b2b", "#ff9b9b"),
    }
    background, border, color = styles.get(state, ("#10141a", "#394252", "#b0b7c3"))
    return (
        f'<span style="display:inline-block;padding:9px 13px;border-radius:999px;'
        f'background:{background};border:1px solid {border};color:{color};'
        f'font-size:13px;font-weight:bold;letter-spacing:0;">{state}</span>'
    )


def anchorgrid_temp_badge(temp: float) -> str:
    if temp < 35:
        background, border, color = "#0f241b", "#245c3a", "#7ee787"
    elif temp < 40:
        background, border, color = "#241d0f", "#7a5a1d", "#f4c76b"
    else:
        background, border, color = "#2d1111", "#7a2b2b", "#ff9b9b"
    return (
        f'<span style="display:inline-block;padding:9px 13px;border-radius:999px;'
        f'background:{background};border:1px solid {border};color:{color};'
        f'font-size:13px;font-weight:bold;">{temp:.1f} °C</span>'
    )


def anchorgrid_stress_badge(stress: str) -> str:
    styles = {
        "LOW": ("#0f241b", "#245c3a", "#7ee787"),
        "MEDIUM": ("#241d0f", "#7a5a1d", "#f4c76b"),
        "HIGH": ("#2d1111", "#7a2b2b", "#ff9b9b"),
    }
    background, border, color = styles.get(stress, ("#10141a", "#394252", "#b0b7c3"))
    tooltip = "szacowany wpływ operacji na zużycie ogniw"
    return (
        f'<span title="{tooltip}" style="display:inline-block;padding:9px 13px;border-radius:999px;'
        f'background:{background};border:1px solid {border};color:{color};'
        f'font-size:13px;font-weight:bold;cursor:help;">{stress}</span>'
    )


def anchorgrid_status_panel(result: dict) -> str:
    state = result["state"]
    state_badge = anchorgrid_status_badge(state)
    temp_badge = anchorgrid_temp_badge(float(result["predicted_max_temp"]))
    stress_badge = anchorgrid_stress_badge(result["estimated_degradation_stress"])
    confidence = result["forecast_confidence"]
    tension = result["tension"]
    net_value = result.get("economics", {}).get("net_value_pln", 0)
    decision = result["decision"]
    recommended = result["recommended_u_safe"]
    requested = result["requested_u"]
    return f"""
    <div style="margin:0 0 18px;padding:22px;border-radius:12px;background:#10141a;border:1px solid #2b3240;box-shadow:0 18px 48px rgba(0,0,0,0.26);">
        <div style="display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin-bottom:18px;">
            <div style="font-size:26px;font-weight:bold;color:#ffffff;margin-right:auto;">{state}</div>
            {state_badge}
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:18px;">
            <div style="padding:14px;border-radius:8px;background:#0d1117;border:1px solid #30363d;">
                <div style="color:#8b949e;font-size:12px;margin-bottom:8px;">requested_u</div>
                <div style="color:#ffffff;font-size:20px;font-weight:bold;">{requested}</div>
            </div>
            <div style="padding:14px;border-radius:8px;background:#0d1117;border:1px solid #30363d;">
                <div style="color:#8b949e;font-size:12px;margin-bottom:8px;">recommended_u_safe</div>
                <div style="color:#ffffff;font-size:20px;font-weight:bold;">{recommended}</div>
            </div>
            <div style="padding:14px;border-radius:8px;background:#0d1117;border:1px solid #30363d;">
                <div style="color:#8b949e;font-size:12px;margin-bottom:8px;">predicted_max_temp</div>
                {temp_badge}
            </div>
            <div style="padding:14px;border-radius:8px;background:#0d1117;border:1px solid #30363d;">
                <div style="color:#8b949e;font-size:12px;margin-bottom:8px;">forecast_confidence</div>
                <div style="color:#ffffff;font-size:20px;font-weight:bold;">{confidence}</div>
            </div>
            <div style="padding:14px;border-radius:8px;background:#0d1117;border:1px solid #30363d;">
                <div style="color:#8b949e;font-size:12px;margin-bottom:8px;">estimated_degradation_stress</div>
                {stress_badge}
            </div>
            <div style="padding:14px;border-radius:8px;background:#0d1117;border:1px solid #30363d;">
                <div style="color:#8b949e;font-size:12px;margin-bottom:8px;">tension</div>
                <div style="color:#ffffff;font-size:20px;font-weight:bold;">{tension}</div>
            </div>
            <div style="padding:14px;border-radius:8px;background:#0d1117;border:1px solid #30363d;">
                <div style="color:#8b949e;font-size:12px;margin-bottom:8px;">net_value_pln</div>
                <div style="color:#ffffff;font-size:20px;font-weight:bold;">{net_value}</div>
            </div>
        </div>
        <div style="padding:14px;border-left:4px solid #2f7cf6;background:#0d1117;border-radius:8px;color:#d8dee9;line-height:1.6;">
            {decision}
        </div>
    </div>
    """


def _scale_points(values: list[float], minutes: list[int], width: int, height: int, min_v: float, max_v: float) -> str:
    span_x = max(max(minutes), 1)
    span_y = max(max_v - min_v, 0.001)
    points = []
    for minute, value in zip(minutes, values):
        x = 44 + (minute / span_x) * (width - 70)
        y = 18 + (1 - ((value - min_v) / span_y)) * (height - 46)
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


def anchorgrid_forecast_chart(result: dict) -> str:
    forecast = result.get("forecast", {})
    minutes = forecast.get("minutes", [])
    soc = forecast.get("soc", [])
    temp = forecast.get("temperature", [])
    requested = forecast.get("requested_u", [])
    recommended = forecast.get("recommended_u", [])

    if not minutes or not soc or not temp:
        return ""

    width = 720
    height = 260
    soc_points = _scale_points(soc, minutes, width, height, 0, 1)
    temp_min = min(min(temp), 20)
    temp_max = max(max(temp), 55)
    temp_points = _scale_points(temp, minutes, width, height, temp_min, temp_max)
    c_max = max(max(requested or [0]), max(recommended or [0]), 1)
    requested_points = _scale_points(requested, minutes, width, height, 0, c_max)
    recommended_points = _scale_points(recommended, minutes, width, height, 0, c_max)

    return f"""
    <div style="margin-top:18px;padding:18px;border-radius:12px;background:#10141a;border:1px solid #2b3240;">
        <div style="font-size:18px;font-weight:bold;color:#ffffff;margin-bottom:12px;">15 min forecast</div>
        <svg viewBox="0 0 {width} {height}" width="100%" height="260" role="img" aria-label="AnchorGrid forecast chart">
            <rect x="0" y="0" width="{width}" height="{height}" fill="#0d1117" rx="8"></rect>
            <line x1="44" y1="214" x2="690" y2="214" stroke="#30363d"></line>
            <line x1="44" y1="18" x2="44" y2="214" stroke="#30363d"></line>
            <polyline points="{temp_points}" fill="none" stroke="#ff7b72" stroke-width="3"></polyline>
            <polyline points="{soc_points}" fill="none" stroke="#7ee787" stroke-width="3"></polyline>
            <polyline points="{requested_points}" fill="none" stroke="#79c0ff" stroke-width="3" stroke-dasharray="8 6"></polyline>
            <polyline points="{recommended_points}" fill="none" stroke="#f2cc60" stroke-width="3"></polyline>
            <text x="48" y="238" fill="#8b949e" font-size="12">0 min</text>
            <text x="638" y="238" fill="#8b949e" font-size="12">{minutes[-1]} min</text>
            <text x="58" y="34" fill="#ff7b72" font-size="13">temperature</text>
            <text x="170" y="34" fill="#7ee787" font-size="13">SoC</text>
            <text x="222" y="34" fill="#79c0ff" font-size="13">requested_u</text>
            <text x="330" y="34" fill="#f2cc60" font-size="13">recommended_u</text>
        </svg>
    </div>
    """


def anchorgrid_dump(result) -> dict:
    if hasattr(result, "model_dump"):
        return result.model_dump()
    return result.dict()


def _valid_anchorgrid_api_key(api_key: str | None) -> bool:
    key = (api_key or "").strip()
    return bool(key and key in ANCHORGRID_API_KEYS)


def _trusted_client_ip(request: Request) -> str:
    cloudflare_ip = request.headers.get("cf-connecting-ip", "").split(",")[0].strip()
    if cloudflare_ip:
        return cloudflare_ip
    if request.headers.get("x-forwarded-for"):
        return "unverified_proxy"
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _anchorgrid_client_id(request: Request) -> str:
    ip = _trusted_client_ip(request)
    user_agent = request.headers.get("user-agent", "unknown")
    raw = f"{ip or 'unknown'}|{user_agent}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"client_{digest}"


def enforce_anchorgrid_rate_limit(
    request: Request,
    scope: str,
    limit: int,
) -> None:
    if limit <= 0:
        return

    now = time.time()
    client_id = _anchorgrid_client_id(request)
    bucket_key = f"{scope}:{client_id}"
    bucket = _RATE_LIMIT_BUCKETS.get(bucket_key)

    if not bucket or now >= bucket["reset_at"]:
        _RATE_LIMIT_BUCKETS[bucket_key] = {
            "count": 1,
            "reset_at": now + ANCHORGRID_RATE_LIMIT_WINDOW_SEC,
        }
        return

    bucket["count"] += 1
    if bucket["count"] <= limit:
        return

    retry_after = max(1, int(bucket["reset_at"] - now))
    raise HTTPException(
        status_code=429,
        detail="Rate limit exceeded. Try again later.",
        headers={"Retry-After": str(retry_after)},
    )


def _read_anchorgrid_usage() -> dict:
    if not ANCHORGRID_USAGE_PATH.exists():
        return {}
    try:
        return json.loads(ANCHORGRID_USAGE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write_anchorgrid_usage(data: dict) -> None:
    ANCHORGRID_USAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    ANCHORGRID_USAGE_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def enforce_anchorgrid_usage(
    request: Request,
    api_key: str | None,
    *,
    increment: bool = True,
) -> dict:
    api_key_valid = _valid_anchorgrid_api_key(api_key)
    if api_key_valid:
        key_digest = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:10]
        return {
            "client_id": f"api_key_{key_digest}",
            "api_key_valid": True,
            "free_limit": None,
            "usage_count": 0,
            "remaining": ANCHORGRID_FREE_LIMIT,
        }

    client_id = _anchorgrid_client_id(request)
    usage_data = _read_anchorgrid_usage()
    current = int(usage_data.get(client_id, {}).get("usage_count", 0))

    if current >= ANCHORGRID_FREE_LIMIT:
        raise HTTPException(
            status_code=402,
            detail=(
                "Free AnchorGrid analysis limit exceeded. "
                "API key required. Contact kontakt@tdkproservice.pl."
            ),
        )

    usage_count = current + 1 if increment else current
    now = datetime.now(timezone.utc).isoformat()
    usage_data[client_id] = {
        "usage_count": usage_count,
        "first_seen_at": usage_data.get(client_id, {}).get("first_seen_at", now),
        "last_seen_at": now,
    }
    if increment:
        _write_anchorgrid_usage(usage_data)

    return {
        "client_id": client_id,
        "api_key_valid": False,
        "free_limit": ANCHORGRID_FREE_LIMIT,
        "usage_count": usage_count,
        "remaining": max(ANCHORGRID_FREE_LIMIT - usage_count, 0),
    }


def _anchorgrid_platform_input(data: AnchorGridPlatformRequest) -> BessInput:
    return BessInput(
        soc=data.soc,
        t_cell=data.t_cell,
        t_amb=data.t_amb,
        u=data.u_requested,
        hvac=data.hvac,
        direction=data.direction,
        horizon_minutes=data.horizon,
        price=data.price,
    )


def _anchorgrid_platform_response(
    result: dict,
    usage: dict | None,
    *,
    request_id: str | None = None,
) -> dict:
    return {
        "state": result["state"],
        "execution_mode": result["execution_mode"],
        "recommended_u_safe": result["recommended_u_safe"],
        "recommended_u_safe_value": result["recommended_u_safe_value"],
        "predicted_max_temp": result["predicted_max_temp"],
        "forecast_confidence": result["forecast_confidence"],
        "forecast_confidence_score": result["forecast_confidence_score"],
        "tension": result["tension"],
        "economics_net_value_pln": result.get("economics", {}).get("net_value_pln", 0.0),
        "warnings": result.get("warnings", []),
        "decision": result["decision"],
        "forecast": result.get("forecast", {}),
        "advisory_only": result["advisory_only"],
        "disclaimer": result["disclaimer"],
        "usage": usage,
        "request_id": request_id or uuid.uuid4().hex,
        "api_version": "v1",
    }


def _anchorgrid_platform_report_text(result: dict, usage: dict | None) -> str:
    usage_lines = []
    if usage:
        if usage["api_key_valid"]:
            usage_lines.append("Dostęp: klucz API aktywny")
        else:
            usage_lines.append(
                f"Darmowe analizy: {usage['usage_count']}/{usage['free_limit']}"
            )
            usage_lines.append(f"Pozostało: {usage['remaining']}")

    return (
        anchorgrid_result_text(result)
        + "\n\n"
        + "TDK Energy Intelligence Platform\n"
        + "Operator approval required: true\n"
        + "Autonomous action: false\n"
        + "\n".join(usage_lines)
    )


@app.post("/api/v1/analyze")
def anchorgrid_platform_analyze(
    data: AnchorGridPlatformRequest,
    request: Request,
) -> dict:
    enforce_anchorgrid_rate_limit(
        request,
        "anchorgrid_analyze",
        ANCHORGRID_RATE_LIMIT_ANALYZE,
    )
    usage = enforce_anchorgrid_usage(request, data.api_key)
    result = analyze_bess(_anchorgrid_platform_input(data))
    payload = anchorgrid_dump(result)
    return _anchorgrid_platform_response(payload, usage)


@app.post("/api/v1/analyze/pdf")
def anchorgrid_platform_analyze_pdf(
    data: AnchorGridPlatformRequest,
    request: Request,
) -> Response:
    enforce_anchorgrid_rate_limit(
        request,
        "anchorgrid_analyze_pdf",
        ANCHORGRID_RATE_LIMIT_PDF,
    )
    usage = enforce_anchorgrid_usage(request, data.api_key)
    result = analyze_bess(_anchorgrid_platform_input(data))
    payload = anchorgrid_dump(result)
    request_id = uuid.uuid4().hex

    unique_id = request_id[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = REPORTS_DIR / f"anchorgrid_{timestamp}_{unique_id}.pdf"
    build_anchorgrid_premium_pdf(
        payload,
        usage,
        str(pdf_path),
        request_id=request_id,
    )

    return Response(
        content=pdf_path.read_bytes(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{pdf_path.name}"'},
    )


@app.post("/anchorgrid/analyze")
def anchorgrid_analyze(data: BessInput) -> dict:
    result = analyze_bess(data)
    payload = anchorgrid_dump(result)
    payload["text_report"] = anchorgrid_result_text(payload)
    return payload


@app.post("/anchorgrid/analyze-form", response_class=HTMLResponse)
def anchorgrid_analyze_form(
    soc: float = Form(...),
    t_cell: float = Form(...),
    t_amb: float = Form(...),
    u: float = Form(...),
    hvac: bool = Form(False),
    direction: str = Form("DISCHARGE"),
    horizon_minutes: int = Form(15),
    price: Optional[float] = Form(None),
) -> str:
    result = analyze_bess(
        BessInput(
            soc=soc,
            t_cell=t_cell,
            t_amb=t_amb,
            u=u,
            hvac=hvac,
            direction=direction,
            horizon_minutes=horizon_minutes,
            price=price,
        )
    )
    result = anchorgrid_dump(result)
    report = anchorgrid_result_text(result)
    status_panel = anchorgrid_status_panel(result)
    chart = anchorgrid_forecast_chart(result)
    return html_page(
        "AnchorGrid AI System | Result",
        f"""
        <h1>AnchorGrid Result</h1>
        {status_panel}
        <pre style="white-space:pre-wrap;line-height:1.7;color:#d8dee9;background:#10141a;border:1px solid #2b3240;border-radius:12px;padding:18px;">{report}</pre>
        {chart}
        <p style="margin-top:22px;">
            <a href="/anchorgrid" style="display:inline-block;padding:13px 18px;border-radius:10px;background:#2f7cf6;color:white;font-weight:bold;text-decoration:none;">Nowa analiza</a>
        </p>
        """,
    )



def _clip_text(value: str, max_chars: int) -> str:
    text = (value or "").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _sanitize_assistant_messages(messages: list[AssistantMessage]) -> list[dict]:
    safe_messages = []
    for item in messages[:ASSISTANT_MAX_MESSAGES]:
        role = item.role if item.role in {"assistant", "client", "system"} else "client"
        safe_messages.append({
            "role": role,
            "content": _clip_text(item.content, ASSISTANT_MAX_MESSAGE_CHARS),
        })
    return safe_messages


def _assistant_public_label(status: str) -> tuple[str, str]:
    labels = {
        "waiting_for_operator_review": (
            "Zgłoszenie przyjęte",
            "Sprawa została przyjęta i czeka na weryfikację operatora TDK&ProService.",
        ),
        "reviewing": (
            "Weryfikacja operatora",
            "Operator analizuje dane i może poprosić o dodatkowe informacje.",
        ),
        "waiting_for_client": (
            "Czekamy na dane",
            "Do dalszej oceny potrzebne są dodatkowe dane od klienta.",
        ),
        "diagnostic_proposed": (
            "Propozycja diagnostyki",
            "Na podstawie zgłoszenia można przejść do dalszej diagnostyki po kontakcie z operatorem.",
        ),
        "closed": (
            "Zamknięte",
            "Sprawa została zamknięta. W razie pytań skontaktuj się z TDK&ProService.",
        ),
        "waiting_for_payment": (
            "Zgłoszenie przyjęte",
            "Zgłoszenie zostało zapisane i czeka na weryfikację operatora.",
        ),
    }
    return labels.get(status, ("Status sprawy", "Sprawa jest obsługiwana przez TDK&ProService."))


def _assistant_order_description(payload: AssistantIntakeRequest) -> str:
    lines = [
        "TDK&ProService assistant intake",
        f"Category: {payload.category}",
        f"Completeness: {payload.completeness}",
        f"City: {payload.city or 'not provided'}",
        f"Source page: {payload.source_page}",
        f"Consent contact: {'yes' if payload.consent_contact else 'no'}",
        f"Consent data: {'yes' if payload.consent_data else 'no'}",
        "",
        "Summary:",
        _clip_text(payload.summary, 1400),
        "",
        "Missing data:",
        ", ".join(payload.missing_data[:12]) or "none declared",
        "",
        "Safety flags:",
        ", ".join(payload.safety_flags[:12]) or "none",
        "",
        "Conversation:",
    ]
    for item in _sanitize_assistant_messages(payload.conversation):
        lines.append(f"[{item['role']}] {item['content']}")
    return _clip_text("\n".join(lines), 9000)


def _assistant_order_to_public_status(order: dict) -> PublicCaseStatusResponse:
    status = order.get("status", "waiting_for_operator_review")
    public_label, message = _assistant_public_label(status)
    created_at = order.get("created_at") or datetime.now(timezone.utc).isoformat()
    updated_at = order.get("updated_at") or order.get("lead_mail_updated_at") or created_at
    return PublicCaseStatusResponse(
        case_id=order.get("order_id", ""),
        status=status,
        public_label=public_label,
        created_at=created_at,
        updated_at=updated_at,
        message=message,
    )


@app.post("/api/v1/assistant/intake", response_model=AssistantIntakeResponse)
def assistant_intake(payload: AssistantIntakeRequest, request_obj: Request) -> AssistantIntakeResponse:
    enforce_anchorgrid_rate_limit(request_obj, "assistant_intake", ASSISTANT_RATE_LIMIT)

    if not payload.consent_contact or not payload.consent_data:
        raise HTTPException(status_code=400, detail="Zgoda na kontakt i przetwarzanie danych jest wymagana przed utworzeniem sprawy.")
    if len(payload.conversation) < 2:
        raise HTTPException(status_code=400, detail="Rozmowa jest zbyt krótka, aby utworzyć sprawę.")
    if len(payload.conversation) > ASSISTANT_MAX_MESSAGES:
        raise HTTPException(status_code=400, detail="Rozmowa przekroczyła limit długości. Skróć zgłoszenie i spróbuj ponownie.")

    order_id = create_order_id()
    now = datetime.now(timezone.utc).isoformat()
    conversation = _sanitize_assistant_messages(payload.conversation)
    description = _assistant_order_description(payload)

    numeric = payload.collected_data if isinstance(payload.collected_data, dict) else {}
    order = {
        "order_id": order_id,
        "case_id": order_id,
        "source": "tdk_assistant_widget",
        "status": "waiting_for_operator_review",
        "operator_stage": "NEW",
        "created_at": now,
        "updated_at": now,
        "name": payload.name.strip(),
        "email": payload.email.strip(),
        "phone": payload.phone.strip(),
        "city": (payload.city or "").strip(),
        "message": _clip_text(payload.summary, 1800),
        "description": description,
        "assistant_category": payload.category,
        "assistant_completeness": payload.completeness,
        "assistant_missing_data": payload.missing_data[:20],
        "assistant_safety_flags": payload.safety_flags[:20],
        "assistant_collected_data": numeric,
        "assistant_conversation": conversation,
        "consent_contact": payload.consent_contact,
        "consent_data": payload.consent_data,
        "amount": "operator review",
        "pdf_url": None,
        "pdf_path": None,
        "base_url": str(request_obj.base_url).rstrip("/"),
        "lead_mail_status": "MAIL_PENDING",
        "client_mail_status": "NOT_APPLICABLE",
        "consumption_kwh": float(numeric.get("monthly_consumption_kwh") or 0),
        "price_per_kwh": float(numeric.get("price_per_kwh") or 0),
        "pv_power_kw": float(numeric.get("pv_power_kwp") or 0),
        "pv_monthly_production_kwh": float(numeric.get("monthly_production_kwh") or 0),
    }
    order_store.create_order(order)

    mail_status = "MAIL_NOT_CONFIRMED"
    mail_error_type = None
    try:
        panel_hint = f"Zgłoszenie asystenta: {order_id}"
        send_lead_notification(
            client_email=order["email"],
            consumption_kwh=order["consumption_kwh"],
            price_per_kwh=order["price_per_kwh"],
            pv_power_kw=order["pv_power_kw"],
            pv_monthly_production_kwh=order["pv_monthly_production_kwh"],
            pdf_url=panel_hint,
            client_name=order["name"],
            client_phone=order["phone"],
            client_message=(
                f"Kategoria: {payload.category}\n"
                f"Kompletność: {payload.completeness}\n"
                f"Miasto: {payload.city or 'brak'}\n\n"
                f"Podsumowanie:\n{_clip_text(payload.summary, 1100)}\n\n"
                "Pełna rozmowa jest zapisana w panelu/operator store."
            ),
        )
        update_order_mail_status(order_id, "lead_mail", "MAIL_SENT", "Powiadomienie operatora zostało wysłane.")
        mail_status = "MAIL_SENT"
    except Exception as exc:
        mail_error_type = type(exc).__name__
        log_mail_failure(LEAD_NOTIFY_EMAIL, exc)
        update_order_mail_status(
            order_id,
            "lead_mail",
            "MAIL_NOT_CONFIRMED",
            "Powiadomienie e-mail nie zostało potwierdzone. Sprawa jest zapisana w panelu.",
            exc,
        )

    return AssistantIntakeResponse(
        case_id=order_id,
        status="waiting_for_operator_review",
        public_label="Zgłoszenie przyjęte",
        message="Sprawa została zapisana i czeka na weryfikację operatora TDK&ProService.",
        next_action="Zapisz numer sprawy i sprawdzaj status na /status. Operator może poprosić o dodatkowe dane.",
        mail_status=mail_status,
        mail_error_type=mail_error_type,
        public_status_url=f"https://tdkproservice.pl/status?case_id={order_id}",
    )


@app.get("/api/v1/cases/{case_id}/public-status", response_model=PublicCaseStatusResponse)
def public_case_status(case_id: str) -> PublicCaseStatusResponse:
    try:
        order = order_store.get_order(case_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Nie znaleziono sprawy")
    return _assistant_order_to_public_status(order)


@app.get("/admin/order/{order_id}", response_class=HTMLResponse)
def admin_order_detail(order_id: str, admin_key: str = "") -> str:
    if not verify_admin_key(admin_key):
        return html_page("Brak dostępu", "<h1>Brak dostępu</h1><p>Podaj poprawny admin_key.</p>")
    try:
        order = order_store.get_order(order_id)
    except Exception as exc:
        return html_page("Nie znaleziono zgłoszenia", f"<h1>Nie znaleziono zgłoszenia</h1><p>{html.escape(str(exc))}</p>")

    conversation_rows = ""
    for item in order.get("assistant_conversation", []):
        role = html.escape(str(item.get("role", "client")))
        content = html.escape(str(item.get("content", "")))
        conversation_rows += f"<div style='margin:10px 0;padding:12px;border-radius:10px;background:#0f1115;border:1px solid #2b3240;'><strong>{role}</strong><br><span style='white-space:pre-wrap;'>{content}</span></div>"

    fields = [
        ("Numer sprawy", order.get("order_id", "")),
        ("Źródło", order.get("source", "")),
        ("Status", order.get("status", "")),
        ("Etap operatora", order.get("operator_stage", "")),
        ("Kategoria", order.get("assistant_category", "")),
        ("Kompletność", order.get("assistant_completeness", "")),
        ("Imię/firma", order.get("name", "")),
        ("Email", order.get("email", "")),
        ("Telefon", order.get("phone", "")),
        ("Miasto", order.get("city", "")),
        ("Mail operatora", order.get("lead_mail_status", "")),
        ("Flagi bezpieczeństwa", ", ".join(order.get("assistant_safety_flags", []))),
        ("Brakujące dane", ", ".join(order.get("assistant_missing_data", []))),
    ]
    field_html = "".join(
        f"<tr><th style='text-align:left;padding:10px;border-top:1px solid #2b3240;color:#8fbcff;'>{html.escape(label)}</th><td style='padding:10px;border-top:1px solid #2b3240;'>{html.escape(str(value))}</td></tr>"
        for label, value in fields
    )
    summary = html.escape(str(order.get("message", "")))
    description = html.escape(str(order.get("description", "")))

    return html_page(
        f"Zgłoszenie {html.escape(order_id)}",
        f"""
        <h1>Zgłoszenie {html.escape(order_id)}</h1>
        <p><a style="color:#4d95ff;" href="/admin/orders?admin_key={html.escape(admin_key)}">Wróć do panelu</a></p>
        <table style="width:100%;border-collapse:collapse;color:#d8dee9;background:#10141a;border:1px solid #2b3240;border-radius:12px;overflow:hidden;">{field_html}</table>
        <h2>Podsumowanie asystenta</h2>
        <pre style="white-space:pre-wrap;background:#10141a;border:1px solid #2b3240;border-radius:12px;padding:16px;color:#d8dee9;">{summary}</pre>
        <h2>Opis techniczny / zapis sprawy</h2>
        <pre style="white-space:pre-wrap;background:#10141a;border:1px solid #2b3240;border-radius:12px;padding:16px;color:#d8dee9;">{description}</pre>
        <h2>Rozmowa</h2>
        {conversation_rows or '<p style="color:#b0b7c3;">Brak zapisu rozmowy.</p>'}
        """,
    )


def status_badge(status: str) -> str:
    styles = {
        "waiting_for_payment": ("Oczekuje na płatność", "#241d0f", "#7a5a1d", "#f4c76b"),
        "paid": ("Płatność potwierdzona", "#0f1d2d", "#2f7cf6", "#8fbcff"),
        "paid_generated": ("Raport wygenerowany", "#0f241b", "#245c3a", "#7ee787"),
    }
    label, background, border, color = styles.get(
        status,
        (status or "Nieznany status", "#10141a", "#394252", "#b0b7c3"),
    )
    return (
        f'<span style="display:inline-block;padding:8px 11px;border-radius:999px;'
        f'background:{background};border:1px solid {border};color:{color};'
        f'font-size:13px;font-weight:bold;white-space:nowrap;">{label}</span>'
    )


@app.post("/form-analyze", response_class=HTMLResponse)
def form_analyze(
    request_obj: Request,
    email: str = Form(...),
    consumption_kwh: float = Form(...),
    price_per_kwh: float = Form(...),
    pv_power_kw: float = Form(...),
    pv_monthly_production_kwh: float = Form(...),
    name: str = Form(""),
    phone: str = Form(""),
    message: str = Form(""),
) -> str:
    try:
        if pv_power_kw > 100:
            return html_page(
                "Błąd danych",
                """
                <h1>Błąd danych</h1>
                <p>Moc PV wygląda nieprawidłowo. Podaj wartość w kWp, np. 8 zamiast 8000.</p>
                <p><a style="color:#4d95ff;" href="/">Wróć do formularza</a></p>
                """,
            )

        base_url = str(request_obj.base_url).rstrip("/")
        order_id = create_order_id()

        order = {
            "order_id": order_id,
            "status": "waiting_for_payment",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "name": name,
            "email": email,
            "phone": phone,
            "message": message,
            "consumption_kwh": consumption_kwh,
            "price_per_kwh": price_per_kwh,
            "pv_power_kw": pv_power_kw,
            "pv_monthly_production_kwh": pv_monthly_production_kwh,
            "amount": PAYMENT_AMOUNT,
            "pdf_url": None,
            "pdf_path": None,
            "base_url": base_url,
            "lead_mail_status": "MAIL_PENDING",
            "client_mail_status": "MAIL_PENDING",
        }
        order_store.create_order(order)

        # SMTP jest tylko dodatkiem. Jeśli nie działa, zgłoszenie i tak jest zapisane.
        try:
            send_lead_notification(
                client_email=email,
                consumption_kwh=consumption_kwh,
                price_per_kwh=price_per_kwh,
                pv_power_kw=pv_power_kw,
                pv_monthly_production_kwh=pv_monthly_production_kwh,
                pdf_url=f"Zgłoszenie zapisane: {order_id}",
                client_name=name,
                client_phone=phone,
                client_message=message,
            )
            update_order_mail_status(
                order_id,
                "lead_mail",
                "MAIL_SENT",
                "Powiadomienie operatora zostało wysłane.",
            )
        except Exception as exc:
            log_mail_failure(LEAD_NOTIFY_EMAIL, exc)
            update_order_mail_status(
                order_id,
                "lead_mail",
                "MAIL_NOT_CONFIRMED",
                "Powiadomienie e-mail nie zostało potwierdzone. Zgłoszenie jest zapisane w panelu.",
                exc,
            )

        return html_page(
            "TDK&ProService | Płatność",
            f"""
            <h1>Zgłoszenie przyjęte</h1>

            <p style="color:#b0b7c3;line-height:1.6;">
                Twoje zgłoszenie zostało zapisane. Po potwierdzeniu płatności przygotujemy wstępny PDF dla tego zgłoszenia.
            </p>

            <p style="margin-top:12px;color:#d4a84f;line-height:1.6;">
                PDF nie jest pełnym audytem technicznym. To pierwszy etap oceny, oparty na danych wpisanych w formularzu.
            </p>

            <p style="margin-top:12px;color:#b0b7c3;line-height:1.6;">
                Zgłoszenie zostało zapisane. W przypadku problemów z dostarczeniem wiadomości operator może skontaktować się inną drogą.
            </p>

            <div style="display:grid;grid-template-columns:repeat(4,minmax(120px,1fr));gap:10px;margin-top:24px;">
                <div style="padding:12px;border-radius:12px;background:#0f241b;border:1px solid #245c3a;color:#7ee787;font-weight:bold;text-align:center;">1. Formularz ✓</div>
                <div style="padding:12px;border-radius:12px;background:#241d0f;border:1px solid #7a5a1d;color:#f4c76b;font-weight:bold;text-align:center;">2. Płatność ⏳</div>
                <div style="padding:12px;border-radius:12px;background:#10141a;border:1px solid #394252;color:#b0b7c3;font-weight:bold;text-align:center;">3. Weryfikacja</div>
                <div style="padding:12px;border-radius:12px;background:#10141a;border:1px solid #394252;color:#b0b7c3;font-weight:bold;text-align:center;">4. Raport PDF</div>
            </div>

            <div style="margin-top:24px;padding:22px;border-left:4px solid #2f7cf6;background:#10141a;color:#d8dee9;line-height:1.8;border-radius:12px;">
                <strong>Numer zgłoszenia:</strong><br>
                <span style="font-size:24px;color:#ffffff;">{order_id}</span><br><br>

                <strong>Kwota do zapłaty:</strong> {PAYMENT_AMOUNT}
            </div>

            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;margin-top:18px;">
                <div style="padding:22px;border-radius:14px;background:#10141a;border:1px solid #2b3240;color:#d8dee9;line-height:1.8;">
                    <div style="font-size:18px;font-weight:bold;color:#ffffff;margin-bottom:10px;">Przelew bankowy</div>
                    <strong>Odbiorca:</strong><br>
                    {PAYMENT_ACCOUNT_NAME}<br><br>
                    <strong>Numer konta:</strong><br>
                    <span style="font-size:18px;color:#ffffff;">{PAYMENT_BANK_ACCOUNT}</span><br><br>
                    <strong>Tytuł przelewu:</strong><br>
                    <span style="font-size:18px;color:#ffffff;">{order_id}</span>
                </div>

                <div style="padding:22px;border-radius:14px;background:#15110a;border:1px solid #7a5a1d;color:#f4e3b0;line-height:1.8;">
                    <div style="font-size:18px;font-weight:bold;color:#ffffff;margin-bottom:10px;">BLIK na telefon</div>
                    <strong>Numer BLIK:</strong><br>
                    <span style="font-size:26px;color:#ffffff;font-weight:bold;letter-spacing:1px;">723 023 152</span><br><br>
                    <strong>Tytuł:</strong><br>
                    <span style="font-size:18px;color:#ffffff;">{order_id}</span>
                </div>
            </div>

            <div style="margin-top:22px;padding:18px;border-left:4px solid #d4a84f;background:#15110a;color:#f4e3b0;line-height:1.7;border-radius:12px;">
                Wstępny PDF generowany jest po potwierdzeniu płatności dla konkretnego zgłoszenia.
                W razie pytań napisz: <strong>{PAYMENT_CONTACT_EMAIL}</strong>
            </div>

            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;margin-top:18px;">
                <div style="padding:22px;border-radius:16px;background:#10141a;border:1px solid #2b3240;color:#d8dee9;line-height:1.75;box-shadow:0 18px 48px rgba(0,0,0,0.28);">
                    <div style="font-size:18px;font-weight:bold;color:#ffffff;margin-bottom:10px;">Co obejmuje wstępna ocena</div>
                    <ul style="margin:0;padding-left:20px;color:#d8dee9;">
                        <li>podstawowe przeliczenie kosztów energii,</li>
                        <li>porównanie kosztu przed i po uwzględnieniu PV,</li>
                        <li>wskazanie możliwych obszarów strat,</li>
                        <li>informację, jakie dane są potrzebne do pełnej diagnostyki.</li>
                    </ul>
                </div>

                <div style="padding:22px;border-radius:16px;background:#10141a;border:1px solid #2b3240;color:#d8dee9;line-height:1.75;box-shadow:0 18px 48px rgba(0,0,0,0.28);">
                    <div style="font-size:18px;font-weight:bold;color:#ffffff;margin-bottom:10px;">Co przygotować do pełnej analizy</div>
                    <ul style="margin:0;padding-left:20px;color:#d8dee9;">
                        <li>ostatnia faktura,</li>
                        <li>dane z falownika,</li>
                        <li>taryfa,</li>
                        <li>zdjęcia instalacji,</li>
                        <li>informacje o pompie ciepła/magazynie.</li>
                    </ul>
                </div>
            </div>

            <p style="margin-top:18px;color:#8d96a6;font-size:13px;line-height:1.6;">
                Wstępna ocena opiera się na danych deklarowanych przez użytkownika.
            </p>

            <p style="margin-top:26px;">
                <a href="/" style="display:inline-block;padding:15px 24px;border-radius:12px;border:1px solid #394252;color:#d8dee9;font-weight:bold;text-decoration:none;box-shadow:0 12px 30px rgba(0,0,0,0.22);">
                    Wróć do formularza
                </a>
            </p>
            """,
        )

    except Exception as exc:
        return html_page(
            "Błąd",
            f"""
            <h1>Nie udało się zapisać zgłoszenia</h1>
            <p>{exc}</p>
            <p><a style="color:#4d95ff;" href="/">Wróć do formularza</a></p>
            """,
        )


@app.get("/admin/orders", response_class=HTMLResponse)
def admin_orders(admin_key: str = "") -> str:
    if not verify_admin_key(admin_key):
        return html_page(
            "Brak dostępu",
            """
            <h1>Brak dostępu</h1>
            <p>Podaj poprawny admin_key.</p>
            """,
        )

    orders = order_store.list_orders()

    if not orders:
        rows = """
        <tr>
            <td colspan="8" style="padding:14px;color:#b0b7c3;">Brak zgłoszeń.</td>
        </tr>
        """
    else:
        rows = ""
        for order in orders:
            order_id = order.get("order_id", "")
            status = order.get("status", "")
            status_html = status_badge(status)
            email = order.get("email", "")
            created_at = format_pl_time(order.get("created_at", ""))
            amount = order.get("amount", PAYMENT_AMOUNT)
            pdf_url = order.get("pdf_url")
            client_mail_status = order.get("client_mail_status", "MAIL_PENDING")
            mail_html = mail_status_badge(client_mail_status)
            retry_html = ""
            if pdf_url and client_mail_status != "MAIL_SENT":
                retry_html = f"""
                <a href="/admin/retry-mail/{order_id}?admin_key={admin_key}" style="display:inline-block;margin-top:8px;padding:9px 12px;border-radius:9px;background:#241d0f;border:1px solid #7a5a1d;color:#f4c76b;font-weight:bold;text-decoration:none;white-space:nowrap;">Ponów mail</a>
                """
            details_link = f"""
                <a href="/admin/order/{order_id}?admin_key={admin_key}" style="display:inline-block;margin-top:8px;padding:10px 14px;border-radius:10px;border:1px solid #394252;color:#d8dee9;font-weight:bold;text-decoration:none;white-space:nowrap;">Szczegóły</a>
                """
            if pdf_url:
                action = f"""
                <a href="{pdf_url}" target="_blank" style="display:inline-block;padding:11px 15px;border-radius:10px;background:#0f241b;border:1px solid #245c3a;color:#7ee787;font-weight:bold;text-decoration:none;white-space:nowrap;">Pobierz PDF</a>
                {retry_html}
                {details_link}
                """
            elif order.get("source") == "tdk_assistant_widget":
                action = details_link
            else:
                action = f"""
                <a href="/admin/generate/{order_id}?admin_key={admin_key}" style="display:inline-block;padding:12px 18px;border-radius:11px;background:#2f7cf6;color:white;font-weight:bold;text-decoration:none;box-shadow:0 12px 28px rgba(47,124,246,0.28);white-space:nowrap;">
                    GENERUJ
                </a>
                {details_link}
                """

            rows += f"""
            <tr style="background:#10141a;">
                <td style="padding:16px 14px;border-top:1px solid #2b3240;color:#b0b7c3;white-space:nowrap;">{created_at}</td>
                <td style="padding:16px 14px;border-top:1px solid #2b3240;"><strong style="color:#ffffff;">{order_id}</strong></td>
                <td style="padding:16px 14px;border-top:1px solid #2b3240;color:#d8dee9;">{email}</td>
                <td style="padding:16px 14px;border-top:1px solid #2b3240;color:#ffffff;font-weight:bold;white-space:nowrap;">{amount}</td>
                <td style="padding:16px 14px;border-top:1px solid #2b3240;">{status_html}</td>
                <td style="padding:16px 14px;border-top:1px solid #2b3240;">{mail_html}</td>
                <td style="padding:16px 14px;border-top:1px solid #2b3240;">{action}</td>
            </tr>
            """

    return html_page(
        "TDK&ProService | Admin zgłoszeń",
        f"""
        <h1>Panel zgłoszeń KODEKS</h1>
        <p style="color:#b0b7c3;line-height:1.6;">
            Po potwierdzeniu wpłaty w banku kliknij <strong>GENERUJ</strong>.
            System przygotuje PDF wstępnej oceny dla konkretnego zgłoszenia.
        </p>

        <div style="margin-top:24px;overflow-x:auto;border:1px solid #2b3240;border-radius:16px;background:#10141a;box-shadow:0 18px 48px rgba(0,0,0,0.28);">
            <table style="width:100%;min-width:900px;border-collapse:collapse;color:#d8dee9;">
                <thead>
                    <tr style="text-align:left;color:#ffffff;background:#151b24;">
                        <th style="padding:14px;">Data</th>
                        <th style="padding:14px;">Zgłoszenie</th>
                        <th style="padding:14px;">Email</th>
                        <th style="padding:14px;">Kwota</th>
                        <th style="padding:14px;">Status</th>
                        <th style="padding:14px;">Mail</th>
                        <th style="padding:14px;">Akcja</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
        """,
    )


@app.get("/admin/generate/{order_id}", response_class=HTMLResponse)
def admin_generate(order_id: str, request_obj: Request, admin_key: str = "") -> str:
    if not verify_admin_key(admin_key):
        return html_page(
            "Brak dostępu",
            """
            <h1>Brak dostępu</h1>
            <p>Podaj poprawny admin_key.</p>
            """,
        )

    try:
        order = order_store.get_order(order_id)

        if order.get("pdf_url"):
            pdf_url = order["pdf_url"]
            client_mail_status = order.get("client_mail_status", "MAIL_PENDING")
            mail_html = mail_status_badge(client_mail_status)
            retry_html = ""
            if client_mail_status != "MAIL_SENT":
                retry_html = f"""
                <a href="/admin/retry-mail/{order_id}?admin_key={admin_key}" style="display:inline-block;padding:14px 22px;border-radius:10px;background:#241d0f;border:1px solid #7a5a1d;color:#f4c76b;font-weight:bold;text-decoration:none;margin-left:10px;">
                    Ponów wysyłkę maila
                </a>
                """
            return html_page(
                "PDF już istnieje",
                f"""
                <h1>PDF wstępnej oceny już był wygenerowany</h1>
                <p>Zgłoszenie: <strong>{order_id}</strong></p>
                <p>Status maila: {mail_html}</p>
                <p>
                    <a href="{pdf_url}" target="_blank" style="display:inline-block;padding:14px 22px;border-radius:10px;background:#2f7cf6;color:white;font-weight:bold;text-decoration:none;">
                        Pobierz PDF
                    </a>
                    {retry_html}
                    <a href="/admin/orders?admin_key={admin_key}" style="display:inline-block;padding:14px 22px;border-radius:10px;border:1px solid #394252;color:#d8dee9;font-weight:bold;text-decoration:none;margin-left:10px;">
                        Wróć do panelu
                    </a>
                </p>
                """,
            )

        base_url = str(request_obj.base_url).rstrip("/")
        text = build_analysis_text_from_order(order)
        result = run_analysis(text, order.get("email", ""), base_url)

        order = order_store.mark_generated(
            order_id,
            result["pdf_url"],
            result.get("pdf_path"),
        )

        email_info = "Mail nie został wysłany."
        try:
            _, email_info = send_email_with_pdf(order.get("email", ""), result["pdf_path"])
            order = update_order_mail_status(
                order_id,
                "client_mail",
                "MAIL_SENT",
                email_info,
            )
        except Exception as exc:
            log_mail_failure(order.get("email", ""), exc)
            email_info = (
                "PDF został wygenerowany poprawnie. Mail nie został potwierdzony. "
                "Zgłoszenie zostało zapisane. W przypadku problemów z dostarczeniem wiadomości operator może skontaktować się inną drogą."
            )
            order = update_order_mail_status(
                order_id,
                "client_mail",
                "MAIL_NOT_CONFIRMED",
                email_info,
                exc,
            )

        return html_page(
            "PDF wygenerowany",
            f"""
            <div style="display:inline-block;padding:9px 14px;border-radius:999px;background:#0f241b;border:1px solid #245c3a;color:#7ee787;font-weight:bold;margin-bottom:16px;">
                Sukces ✓ PDF wstępnej oceny gotowy
            </div>

            <h1>PDF wstępnej oceny wygenerowany</h1>
            <p style="color:#b0b7c3;line-height:1.6;">Zgłoszenie: <strong style="color:#ffffff;">{order_id}</strong></p>
            <p style="color:#b0b7c3;line-height:1.6;">{email_info}</p>

            <p>
                <a href="{result['pdf_url']}" target="_blank" style="display:inline-block;padding:18px 30px;border-radius:12px;background:#1f8f4d;color:white;font-size:18px;font-weight:bold;text-decoration:none;box-shadow:0 10px 28px rgba(31,143,77,0.28);">
                    Pobierz PDF
                </a>

                <a href="/admin/orders?admin_key={admin_key}" style="display:inline-block;padding:14px 22px;border-radius:10px;border:1px solid #394252;color:#d8dee9;font-weight:bold;text-decoration:none;margin-left:10px;">
                    Wróć do panelu
                </a>
            </p>

            <div style="margin-top:24px;padding:22px;border-left:4px solid #1f8f4d;background:#101a14;border-radius:12px;color:#d8dee9;line-height:1.7;">
                <div style="font-size:18px;font-weight:bold;color:#ffffff;margin-bottom:10px;">Link dla klienta</div>
                <div style="word-break:break-all;color:#7ee787;font-weight:bold;">{result['pdf_url']}</div>
            </div>

            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;margin-top:18px;">
                <div style="padding:22px;border-radius:16px;background:#10141a;border:1px solid #2b3240;color:#d8dee9;line-height:1.75;box-shadow:0 18px 48px rgba(0,0,0,0.28);">
                    <div style="font-size:18px;font-weight:bold;color:#ffffff;margin-bottom:10px;">Co obejmuje wstępna ocena</div>
                    <ul style="margin:0;padding-left:20px;color:#d8dee9;">
                        <li>podstawowe przeliczenie kosztów energii,</li>
                        <li>porównanie kosztu przed i po uwzględnieniu PV,</li>
                        <li>wskazanie możliwych obszarów strat,</li>
                        <li>informację, jakie dane są potrzebne do pełnej diagnostyki.</li>
                    </ul>
                </div>

                <div style="padding:22px;border-radius:16px;background:#10141a;border:1px solid #2b3240;color:#d8dee9;line-height:1.75;box-shadow:0 18px 48px rgba(0,0,0,0.28);">
                    <div style="font-size:18px;font-weight:bold;color:#ffffff;margin-bottom:10px;">Co przygotować do pełnej analizy</div>
                    <ul style="margin:0;padding-left:20px;color:#d8dee9;">
                        <li>ostatnia faktura,</li>
                        <li>dane z falownika,</li>
                        <li>taryfa,</li>
                        <li>zdjęcia instalacji,</li>
                        <li>informacje o pompie ciepła/magazynie.</li>
                    </ul>
                </div>
            </div>

            <p style="margin-top:18px;color:#8d96a6;font-size:13px;line-height:1.6;">
                Wstępna ocena opiera się na danych deklarowanych przez użytkownika i nie zastępuje pełnego audytu technicznego.
            </p>
            """,
        )

    except Exception as exc:
        return html_page(
            "Błąd generowania",
            f"""
            <h1>Nie udało się wygenerować raportu</h1>
            <p>{exc}</p>
            <p><a style="color:#4d95ff;" href="/admin/orders?admin_key={admin_key}">Wróć do panelu</a></p>
            """,
        )


@app.get("/admin/retry-mail/{order_id}", response_class=HTMLResponse)
def admin_retry_mail(order_id: str, admin_key: str = "") -> str:
    if not verify_admin_key(admin_key):
        return html_page(
            "Brak dostępu",
            """
            <h1>Brak dostępu</h1>
            <p>Podaj poprawny admin_key.</p>
            """,
        )

    try:
        order = order_store.get_order(order_id)
        pdf_path = order.get("pdf_path")
        pdf_url = order.get("pdf_url")

        if not pdf_path or not Path(pdf_path).exists():
            return html_page(
                "Brak PDF",
                f"""
                <h1>Nie można ponowić wysyłki</h1>
                <p>Dla zgłoszenia <strong>{order_id}</strong> nie znaleziono lokalnego pliku PDF.</p>
                <p>Jeśli PDF nie został jeszcze wygenerowany, najpierw użyj przycisku <strong>GENERUJ</strong>.</p>
                <p><a style="color:#4d95ff;" href="/admin/orders?admin_key={admin_key}">Wróć do panelu</a></p>
                """,
            )

        try:
            _, email_info = send_email_with_pdf(order.get("email", ""), pdf_path)
            order = update_order_mail_status(
                order_id,
                "client_mail",
                "MAIL_SENT",
                email_info,
            )
            result_box = """
            <div style="display:inline-block;padding:9px 14px;border-radius:999px;background:#0f241b;border:1px solid #245c3a;color:#7ee787;font-weight:bold;margin-bottom:16px;">
                Mail wysłany
            </div>
            """
        except Exception as exc:
            log_mail_failure(order.get("email", ""), exc)
            email_info = (
                "Mail nadal nie został potwierdzony. PDF i zgłoszenie są zapisane. "
                "Operator może wysłać link ręcznie lub skontaktować się inną drogą."
            )
            order = update_order_mail_status(
                order_id,
                "client_mail",
                "MAIL_NOT_CONFIRMED",
                email_info,
                exc,
            )
            result_box = """
            <div style="display:inline-block;padding:9px 14px;border-radius:999px;background:#2d1111;border:1px solid #7a2b2b;color:#ff9b9b;font-weight:bold;margin-bottom:16px;">
                Mail niepotwierdzony
            </div>
            """

        return html_page(
            "Ponowna wysyłka maila",
            f"""
            {result_box}
            <h1>Ponowna próba wysyłki maila</h1>
            <p>Zgłoszenie: <strong>{order_id}</strong></p>
            <p>Status maila: {mail_status_badge(order.get("client_mail_status"))}</p>
            <p style="color:#b0b7c3;line-height:1.6;">{email_info}</p>
            <p style="color:#b0b7c3;line-height:1.6;">
                Zgłoszenie zostało zapisane. W przypadku problemów z dostarczeniem wiadomości operator może skontaktować się inną drogą.
            </p>
            <p>
                <a href="{pdf_url}" target="_blank" style="display:inline-block;padding:14px 22px;border-radius:10px;background:#2f7cf6;color:white;font-weight:bold;text-decoration:none;">
                    Pobierz PDF
                </a>
                <a href="/admin/orders?admin_key={admin_key}" style="display:inline-block;padding:14px 22px;border-radius:10px;border:1px solid #394252;color:#d8dee9;font-weight:bold;text-decoration:none;margin-left:10px;">
                    Wróć do panelu
                </a>
            </p>
            """,
        )

    except Exception as exc:
        return html_page(
            "Błąd wysyłki",
            f"""
            <h1>Nie udało się ponowić wysyłki maila</h1>
            <p>{exc}</p>
            <p><a style="color:#4d95ff;" href="/admin/orders?admin_key={admin_key}">Wróć do panelu</a></p>
            """,
        )


@app.post("/analyze")
def analyze(request: AnalyzeRequest, request_obj: Request) -> dict:
    try:
        base_url = str(request_obj.base_url).rstrip("/")
        result = run_analysis(request.text, request.email, base_url)

        return {
            "status": "ok",
            "pdf_url": result["pdf_url"],
        }

    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
        }


@app.post("/analyze-paid")
def analyze_paid(request: AnalyzePaidRequest, request_obj: Request) -> dict:
    validation_errors = validate_paid_payload(request)

    if validation_errors:
        return {
            "status": "error",
            "message": "; ".join(validation_errors),
        }

    try:
        base_url = str(request_obj.base_url).rstrip("/")
        text = build_paid_analysis_text(request)
        result = run_analysis(text, request.email or "", base_url)

    except Exception as exc:
        return {
            "status": "error",
            "message": f"Błąd analizy lub generowania PDF: {exc}",
        }

    email_sent = False
    email_info = "Nie wysłano maila do klienta."
    lead_sent = False
    lead_info = "Nie wysłano powiadomienia o leadzie."

    try:
        email_sent, email_info = send_email_with_pdf(
            request.email or "",
            result["pdf_path"],
        )
    except Exception as exc:
        email_info = f"Błąd wysyłki maila do klienta: {exc}"

    try:
        lead_sent, lead_info = send_lead_notification(
            client_email=request.email or "",
            consumption_kwh=request.consumption_kwh or 0,
            price_per_kwh=request.price_per_kwh or 0,
            pv_power_kw=request.pv_power_kw or 0,
            pv_monthly_production_kwh=request.pv_monthly_production_kwh or 0,
            pdf_url=result["pdf_url"],
        )
    except Exception as exc:
        lead_info = f"Błąd wysyłki leada: {exc}"

    return {
        "status": "ok",
        "pdf_url": result["pdf_url"],
        "email_sent": email_sent,
        "email_info": email_info,
        "lead_sent": lead_sent,
        "lead_info": lead_info,
    }


@app.get("/analyze-simple")
def analyze_simple(text: str, email: str, request_obj: Request) -> dict:
    try:
        base_url = str(request_obj.base_url).rstrip("/")
        decoded_text = unquote(text)
        result = run_analysis(decoded_text, email, base_url)

        return {
            "status": "ok",
            "pdf_url": result["pdf_url"],
        }

    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
        }
