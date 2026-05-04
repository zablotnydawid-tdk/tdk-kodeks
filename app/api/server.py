import os
import smtplib
import ssl
import uuid
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Optional
from urllib.parse import unquote

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


from app.engine.process_engine import run_process
from app.input.normalizer import normalize_input
from app.output.pdf_builder import generate_pdf
from app.output.report_builder import build_report
from app.routing.mask_router import choose_mask


load_dotenv()

REPORTS_DIR = Path("data") / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="KODEKS API")
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")


class AnalyzeRequest(BaseModel):
    text: str
    email: str


class AnalyzePaidRequest(BaseModel):
    email: Optional[str] = None
    consumption_kwh: Optional[float] = None
    price_per_kwh: Optional[float] = None
    pv_power_kw: Optional[float] = None
    pv_monthly_production_kwh: Optional[float] = None


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
    pdf_filename = pdf_path.name

    return {
        "status": "ok",
        "pdf_url": f"{base_url}/reports/{pdf_filename}",
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

    if payload.pv_monthly_production_kwh is None:
        errors.append("pv_monthly_production_kwh jest wymagane")
    elif payload.pv_monthly_production_kwh < 0:
        errors.append("pv_monthly_production_kwh musi być większe lub równe 0")

    return errors


def send_email_with_pdf(to_email: str, pdf_path: str) -> tuple[bool, str]:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_from = os.getenv("SMTP_FROM", "kontakt@tdkproservice.pl")

    missing_config = []
    if not smtp_host:
        missing_config.append("SMTP_HOST")
    if not smtp_port:
        missing_config.append("SMTP_PORT")
    if not smtp_user:
        missing_config.append("SMTP_USER")
    if not smtp_pass:
        missing_config.append("SMTP_PASS")
    if not smtp_from:
        missing_config.append("SMTP_FROM")

    if missing_config:
        return False, "SMTP nie jest skonfigurowane: brakuje " + ", ".join(missing_config)

    path = Path(pdf_path)
    if not path.exists():
        raise RuntimeError(f"Nie znaleziono pliku PDF do wysyłki: {pdf_path}")

    message = EmailMessage()
    message["Subject"] = "Analiza kosztów energii — TDK&ProService"
    message["From"] = smtp_from
    message["To"] = to_email
    message.set_content(
        "Dzień dobry,\n\n"
        "w załączniku przesyłamy wstępną analizę kosztów energii przygotowaną przez TDK&ProService.\n\n"
        "Raport zawiera podstawowe obliczenia, interpretację wyniku oraz rekomendacje dalszych kroków.\n\n"
        "TDK&ProService\n"
        "kontakt@tdkproservice.pl\n"
    )

    message.add_attachment(
        path.read_bytes(),
        maintype="application",
        subtype="pdf",
        filename=path.name,
    )

    if smtp_port == 465:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as smtp:
            smtp.login(smtp_user, smtp_pass)
            smtp.send_message(message)
    else:
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as smtp:
            smtp.starttls(context=context)
            smtp.login(smtp_user, smtp_pass)
            smtp.send_message(message)

    return True, "Mail z raportem został wysłany."


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
    <!doctype html>
    <html lang="pl">
    <head>
        <meta charset="utf-8">
        <title>KODEKS - Analiza energii</title>
    </head>
    <body>
        <h1>KODEKS - Analiza energii</h1>
        <form method="post" action="/form-analyze">
            <label>Email</label><br>
            <input type="email" name="email" required><br><br>

            <label>Zużycie kWh miesięcznie</label><br>
            <input type="number" step="0.01" name="consumption_kwh" required><br><br>

            <label>Cena 1 kWh</label><br>
            <input type="number" step="0.01" name="price_per_kwh" required><br><br>

            <label>Moc PV</label><br>
            <input type="number" step="0.01" name="pv_power_kw" required><br><br>

            <label>Miesięczna produkcja PV</label><br>
            <input type="number" step="0.01" name="pv_monthly_production_kwh" required><br><br>

            <button type="submit">Generuj raport</button>
        </form>
    </body>
    </html>
    """


@app.post("/form-analyze", response_class=HTMLResponse)
def form_analyze(
    request_obj: Request,
    email: str = Form(...),
    consumption_kwh: float = Form(...),
    price_per_kwh: float = Form(...),
    pv_power_kw: float = Form(...),
    pv_monthly_production_kwh: float = Form(...),
) -> str:
    try:
        base_url = str(request_obj.base_url).rstrip("/")
        text = (
            f"Zużycie {consumption_kwh} kWh, "
            f"cena {price_per_kwh} zł, "
            f"PV {pv_power_kw} kWp, "
            f"produkcja PV {pv_monthly_production_kwh} kWh"
        )
        result = run_analysis(text, email, base_url)
        pdf_url = result["pdf_url"]
    except Exception as exc:
        return f"""
        <!doctype html>
        <html lang="pl">
        <head><meta charset="utf-8"><title>Błąd</title></head>
        <body>
            <h1>Nie udało się wygenerować raportu</h1>
            <p>{exc}</p>
            <p><a href="/">Wróć do formularza</a></p>
        </body>
        </html>
        """

    return f"""
    <!doctype html>
    <html lang="pl">
    <head><meta charset="utf-8"><title>Raport gotowy</title></head>
    <body>
        <h1>Raport gotowy</h1>
        <p><a href="{pdf_url}" target="_blank">Pobierz raport PDF</a></p>
        <p>Jeśli chcesz pełny audyt techniczny, skontaktuj się: kontakt@tdkproservice.pl</p>
        <p><a href="/">Wygeneruj kolejny raport</a></p>
    </body>
    </html>
    """


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

    try:
        email_sent, email_info = send_email_with_pdf(request.email or "", result["pdf_path"])
    except Exception as exc:
        return {
            "status": "ok",
            "pdf_url": result["pdf_url"],
            "email_sent": False,
            "email_info": f"Błąd wysyłki maila: {exc}",
        }

    return {
        "status": "ok",
        "pdf_url": result["pdf_url"],
        "email_sent": email_sent,
        "email_info": email_info,
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
