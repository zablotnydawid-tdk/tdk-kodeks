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


def send_email_with_pdf(to_email: str, pdf_path: str) -> tuple[bool, str]:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_from = os.getenv("SMTP_FROM", "kontakt@tdkproservice.pl")

    missing_config = []

    if not smtp_host:
        missing_config.append("SMTP_HOST")
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
        "Jeśli zdecydują się Państwo na pełną diagnostykę techniczną, koszt tej analizy "
        "w wysokości 39,99 zł zostanie odliczony od ceny pełnej usługi.\n\n"
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

            <h1>TDK&ProService — KODEKS</h1>

            <div class="subtitle">
                Analiza faktur, kosztów energii, instalacji PV i autokonsumpcji.<br>
                Wygeneruj wstępny raport techniczny na podstawie danych rzeczywistych.
            </div>

            <div class="container">

                <div class="form-box">
                    <form method="post" action="/form-analyze">

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

                        <button type="submit">
                            Generuj raport PDF
                        </button>

                    </form>
                </div>

                <div class="side">

                    <div class="price-box">
                        <h2>Wstępna analiza KODEKS</h2>
                        <div class="price">39,99 zł</div>

                        <div class="note">
                            Raport PDF generowany jest automatycznie na podstawie podanych danych.
                            To pierwszy etap oceny kosztów energii, pracy PV i możliwych strat.
                        </div>

                        <div class="credit">
                            Jeśli po raporcie zdecydujesz się na pełną diagnostykę techniczną
                            TDK&ProService, kwota <strong>39,99 zł</strong> zostanie odliczona
                            od ceny pełnej usługi.
                        </div>

                        <div class="levels">
                            Pełna analiza może obejmować poziomy:<br>
                            <strong>Starter</strong> — dokumenty i konsultacja<br>
                            <strong>Standard</strong> — raport i rekomendacje<br>
                            <strong>Premium</strong> — raport ekspercki i strategia<br>
                            <strong>Ekspercki</strong> — materiał pod spór, operatora lub wykonawcę
                        </div>
                    </div>

                    <div class="example-box">
                        <div class="example-title">
                            Przykładowe dane do analizy
                        </div>

                        <pre>- Zużycie miesięczne: 323 kWh
- Cena energii: 1.23 zł/kWh
- Moc instalacji PV: 8 kWp
- Miesięczna produkcja PV: 6543 kWh</pre>
                    </div>

                </div>

            </div>

            <div class="footer">
                TDK&ProService • Diagnostyka OZE • Audyt rozliczeń energii • Dane. Fakty. Efekt.
            </div>

        </div>
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
        if pv_power_kw > 100:
            return """
            <!doctype html>
            <html lang="pl">
            <head>
                <meta charset="utf-8">
                <title>Błąd danych</title>
            </head>
            <body style="background:#0f1115;color:#f1f1f1;font-family:Arial,sans-serif;padding:40px;">
                <div style="max-width:760px;margin:60px auto;background:#171b22;border:1px solid #2b3240;border-radius:16px;padding:32px;">
                    <h1>Błąd danych</h1>
                    <p>Moc PV wygląda nieprawidłowo. Podaj wartość w kWp, np. 8 zamiast 8000.</p>
                    <p><a style="color:#4d95ff;" href="/">Wróć do formularza</a></p>
                </div>
            </body>
            </html>
            """

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
        <head>
            <meta charset="utf-8">
            <title>Błąd</title>
        </head>
        <body style="background:#0f1115;color:#f1f1f1;font-family:Arial,sans-serif;padding:40px;">
            <div style="max-width:760px;margin:60px auto;background:#171b22;border:1px solid #2b3240;border-radius:16px;padding:32px;">
                <h1>Nie udało się wygenerować raportu</h1>
                <p>{exc}</p>
                <p><a style="color:#4d95ff;" href="/">Wróć do formularza</a></p>
            </div>
        </body>
        </html>
        """

    return f"""
    <!doctype html>
    <html lang="pl">
    <head>
        <meta charset="utf-8">
        <title>TDK&ProService | Raport gotowy</title>

        <style>
            body {{
                margin: 0;
                padding: 40px;
                background: #0f1115;
                color: #f1f1f1;
                font-family: Arial, sans-serif;
            }}

            .wrapper {{
                max-width: 880px;
                margin: 60px auto;
            }}

            .card {{
                background: #171b22;
                border: 1px solid #2b3240;
                border-radius: 18px;
                padding: 36px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.35);
            }}

            h1 {{
                margin-top: 0;
                font-size: 34px;
            }}

            .subtitle {{
                color: #b0b7c3;
                line-height: 1.6;
                margin-bottom: 28px;
            }}

            .button {{
                display: inline-block;
                padding: 14px 22px;
                border-radius: 10px;
                background: #2f7cf6;
                color: white;
                font-weight: bold;
                text-decoration: none;
                margin-right: 12px;
                margin-bottom: 12px;
            }}

            .button:hover {{
                background: #4d95ff;
            }}

            .secondary {{
                background: transparent;
                border: 1px solid #394252;
                color: #d8dee9;
            }}

            .secondary:hover {{
                background: #202631;
            }}

            .contact {{
                margin-top: 28px;
                padding: 18px;
                border-left: 4px solid #2f7cf6;
                background: #10141a;
                color: #d8dee9;
                line-height: 1.6;
            }}

            .credit {{
                margin-top: 18px;
                padding: 18px;
                border-left: 4px solid #d4a84f;
                background: #15110a;
                color: #f4e3b0;
                line-height: 1.6;
            }}

            .footer {{
                margin-top: 32px;
                color: #7d8796;
                font-size: 14px;
            }}
        </style>
    </head>

    <body>
        <div class="wrapper">
            <div class="card">
                <h1>Raport gotowy</h1>

                <div class="subtitle">
                    Wstępna analiza energii została wygenerowana.
                    Możesz teraz pobrać raport PDF i sprawdzić wynik obliczeń.
                </div>

                <a class="button" href="{pdf_url}" target="_blank">
                    Pobierz raport PDF
                </a>

                <a class="button secondary" href="/">
                    Wykonaj kolejną płatną analizę
                </a>

                <div class="credit">
                    Ten raport jest pierwszym etapem diagnostyki.
                    Jeśli zdecydujesz się na pełną analizę techniczną TDK&ProService,
                    koszt tej analizy, <strong>39,99 zł</strong>, zostanie odliczony
                    od ceny pełnej usługi.
                </div>

                <div class="contact">
                    Jeśli chcesz pełny audyt techniczny instalacji PV, rozliczeń energii,
                    pracy pompy ciepła lub magazynu energii, skontaktuj się z TDK&ProService:<br>
                    <strong>kontakt@tdkproservice.pl</strong>
                </div>
            </div>

            <div class="footer">
                TDK&ProService • Diagnostyka OZE • Audyt rozliczeń energii • Dane. Fakty. Efekt.
            </div>
        </div>
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
        email_sent, email_info = send_email_with_pdf(
            request.email or "",
            result["pdf_path"],
        )

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