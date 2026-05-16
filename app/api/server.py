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
from app.storage.order_store import FileSystemOrderStore, create_order_id


load_dotenv()

REPORTS_DIR = Path("data") / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

order_store = FileSystemOrderStore()

LEAD_NOTIFY_EMAIL = os.getenv(
    "LEAD_NOTIFY_EMAIL",
    "kontakt@tdkproservice.pl"
)

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
    "39,99 zł"
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


def _smtp_config() -> dict:
    return {
        "host": os.getenv("SMTP_HOST"),
        "port": int(os.getenv("SMTP_PORT", "465")),
        "user": os.getenv("SMTP_USER"),
        "password": os.getenv("SMTP_PASS"),
        "from_email": os.getenv("SMTP_FROM", "kontakt@tdkproservice.pl"),
    }


def _send_message(message: EmailMessage) -> None:
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

    context = ssl.create_default_context()

    if config["port"] == 465:
        with smtplib.SMTP_SSL(
            config["host"],
            config["port"],
            context=context,
            timeout=15,
        ) as smtp:
            smtp.login(config["user"], config["password"])
            smtp.send_message(message)
    else:
        with smtplib.SMTP(
            config["host"],
            config["port"],
            timeout=15,
        ) as smtp:
            smtp.starttls(context=context)
            smtp.login(config["user"], config["password"])
            smtp.send_message(message)


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

    _send_message(message)
    return True, "Mail z raportem został wysłany."


def send_lead_notification(
    client_email: str,
    consumption_kwh: float,
    price_per_kwh: float,
    pv_power_kw: float,
    pv_monthly_production_kwh: float,
    pdf_url: str,
) -> tuple[bool, str]:
    config = _smtp_config()

    message = EmailMessage()
    message["Subject"] = "Nowy lead KODEKS — TDK&ProService"
    message["From"] = config["from_email"]
    message["To"] = LEAD_NOTIFY_EMAIL

    message.set_content(
        "Nowy lead z formularza KODEKS.\n\n"
        f"Email klienta: {client_email}\n"
        f"Zużycie miesięczne: {consumption_kwh} kWh\n"
        f"Cena energii: {price_per_kwh} zł/kWh\n"
        f"Moc PV: {pv_power_kw} kWp\n"
        f"Miesięczna produkcja PV: {pv_monthly_production_kwh} kWh\n\n"
        f"Link do raportu PDF:\n{pdf_url}\n\n"
        "To jest potencjalny klient do dalszej diagnostyki technicznej.\n"
    )

    _send_message(message)
    return True, "Lead został wysłany na kontakt@tdkproservice.pl."


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
                Wypełnij formularz, opłać analizę i otrzymaj raport PDF po potwierdzeniu płatności.
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
                            Przejdź do płatności
                        </button>

                    </form>
                </div>

                <div class="side">

                    <div class="price-box">
                        <h2>Wstępna analiza KODEKS</h2>
                        <div class="price">39,99 zł</div>

                        <div class="note">
                            Raport PDF zostanie wygenerowany po potwierdzeniu płatności.
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
            "email": email,
            "consumption_kwh": consumption_kwh,
            "price_per_kwh": price_per_kwh,
            "pv_power_kw": pv_power_kw,
            "pv_monthly_production_kwh": pv_monthly_production_kwh,
            "amount": PAYMENT_AMOUNT,
            "pdf_url": None,
            "pdf_path": None,
            "base_url": base_url,
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
            )
        except Exception:
            pass

        return html_page(
            "TDK&ProService | Płatność",
            f"""
            <h1>Zgłoszenie przyjęte</h1>

            <p style="color:#b0b7c3;line-height:1.6;">
                Twoje zgłoszenie zostało zapisane. Raport PDF zostanie wygenerowany po potwierdzeniu płatności.
            </p>

            <div style="margin-top:24px;padding:22px;border-left:4px solid #2f7cf6;background:#10141a;color:#d8dee9;line-height:1.8;">
                <strong>Numer zgłoszenia:</strong><br>
                <span style="font-size:24px;color:#ffffff;">{order_id}</span><br><br>

                <strong>Kwota:</strong> {PAYMENT_AMOUNT}<br>
                <strong>Odbiorca:</strong> {PAYMENT_ACCOUNT_NAME}<br>
                <strong>Numer konta:</strong> {PAYMENT_BANK_ACCOUNT}<br>
                <strong>Tytuł przelewu:</strong> {order_id}
            </div>

            <div style="margin-top:22px;padding:18px;border-left:4px solid #d4a84f;background:#15110a;color:#f4e3b0;line-height:1.7;">
                Po zaksięgowaniu płatności raport zostanie wygenerowany i udostępniony dla tego konkretnego zgłoszenia.
                W razie pytań napisz: <strong>{PAYMENT_CONTACT_EMAIL}</strong>
            </div>

            <p style="margin-top:26px;">
                <a href="/" style="display:inline-block;padding:14px 22px;border-radius:10px;border:1px solid #394252;color:#d8dee9;font-weight:bold;text-decoration:none;">
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
            <td colspan="7" style="padding:14px;color:#b0b7c3;">Brak zgłoszeń.</td>
        </tr>
        """
    else:
        rows = ""
        for order in orders:
            order_id = order.get("order_id", "")
            status = order.get("status", "")
            email = order.get("email", "")
            created_at = order.get("created_at", "")
            amount = order.get("amount", PAYMENT_AMOUNT)
            pdf_url = order.get("pdf_url")
            if pdf_url:
                action = f"""
                <a href="{pdf_url}" target="_blank" style="color:#7ee787;font-weight:bold;">Pobierz PDF</a>
                """
            else:
                action = f"""
                <a href="/admin/generate/{order_id}?admin_key={admin_key}" style="display:inline-block;padding:9px 12px;border-radius:8px;background:#2f7cf6;color:white;font-weight:bold;text-decoration:none;">
                    GENERUJ
                </a>
                """

            rows += f"""
            <tr>
                <td style="padding:12px;border-top:1px solid #2b3240;">{created_at}</td>
                <td style="padding:12px;border-top:1px solid #2b3240;"><strong>{order_id}</strong></td>
                <td style="padding:12px;border-top:1px solid #2b3240;">{email}</td>
                <td style="padding:12px;border-top:1px solid #2b3240;">{amount}</td>
                <td style="padding:12px;border-top:1px solid #2b3240;">{status}</td>
                <td style="padding:12px;border-top:1px solid #2b3240;">{action}</td>
            </tr>
            """

    return html_page(
        "TDK&ProService | Admin zgłoszeń",
        f"""
        <h1>Panel zgłoszeń KODEKS</h1>
        <p style="color:#b0b7c3;line-height:1.6;">
            Po potwierdzeniu wpłaty w banku kliknij <strong>GENERUJ</strong>.
            System sam wygeneruje PDF dla konkretnego zgłoszenia.
        </p>

        <table style="width:100%;border-collapse:collapse;margin-top:24px;color:#d8dee9;">
            <thead>
                <tr style="text-align:left;color:#ffffff;">
                    <th style="padding:12px;">Data</th>
                    <th style="padding:12px;">Zgłoszenie</th>
                    <th style="padding:12px;">Email</th>
                    <th style="padding:12px;">Kwota</th>
                    <th style="padding:12px;">Status</th>
                    <th style="padding:12px;">Akcja</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
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
            return html_page(
                "Raport już istnieje",
                f"""
                <h1>Raport już był wygenerowany</h1>
                <p>Zgłoszenie: <strong>{order_id}</strong></p>
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
        except Exception as exc:
            email_info = f"PDF wygenerowany, ale mail nie wyszedł: {exc}"

        return html_page(
            "Raport wygenerowany",
            f"""
            <h1>Raport wygenerowany</h1>
            <p>Zgłoszenie: <strong>{order_id}</strong></p>
            <p style="color:#b0b7c3;">{email_info}</p>

            <p>
                <a href="{result['pdf_url']}" target="_blank" style="display:inline-block;padding:14px 22px;border-radius:10px;background:#2f7cf6;color:white;font-weight:bold;text-decoration:none;">
                    Pobierz PDF
                </a>

                <a href="/admin/orders?admin_key={admin_key}" style="display:inline-block;padding:14px 22px;border-radius:10px;border:1px solid #394252;color:#d8dee9;font-weight:bold;text-decoration:none;margin-left:10px;">
                    Wróć do panelu
                </a>
            </p>

            <div style="margin-top:22px;padding:18px;border-left:4px solid #2f7cf6;background:#10141a;color:#d8dee9;line-height:1.7;">
                Link dla klienta:<br>
                <strong>{result['pdf_url']}</strong>
            </div>
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
