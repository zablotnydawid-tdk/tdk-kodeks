import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr

from app.engine.process_engine import run_process
from app.input.normalizer import normalize_input
from app.output.pdf_builder import generate_pdf
from app.output.report_builder import build_report
from app.routing.mask_router import choose_mask


app = FastAPI(title="KODEKS API")
app.mount("/reports", StaticFiles(directory="data/reports"), name="reports")


class AnalyzeRequest(BaseModel):
    text: str
    email: EmailStr


def run_analysis(text: str, email: str, base_url: str) -> dict:
    normalized = normalize_input(text)
    selected_mask, _route_reason = choose_mask(normalized)
    process_result = run_process(normalized, selected_mask)
    report_text = build_report(
        raw_input=text,
        selected_mask=selected_mask,
        process_result=process_result,
    )

    reports_dir = Path("data") / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    unique_id = uuid.uuid4().hex[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = reports_dir / f"raport_{timestamp}_{unique_id}.pdf"
    generate_pdf(report_text, str(pdf_path))
    pdf_filename = pdf_path.name

    return {
        "status": "ok",
        "pdf_url": f"{base_url}/reports/{pdf_filename}",
    }


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
    base_url = str(request_obj.base_url).rstrip("/")
    text = (
        f"Zużycie {consumption_kwh} kWh, "
        f"cena {price_per_kwh} zł, "
        f"PV {pv_power_kw} kWp, "
        f"produkcja PV {pv_monthly_production_kwh} kWh"
    )
    result = run_analysis(text, email, base_url)

    if result.get("status") != "ok":
        message = result.get("message", "Nieznany błąd")
        return f"""
        <!doctype html>
        <html lang="pl">
        <head>
            <meta charset="utf-8">
            <title>Błąd analizy</title>
        </head>
        <body>
            <h1>Nie udało się wygenerować raportu</h1>
            <p>{message}</p>
            <p><a href="/">Wróć do formularza</a></p>
        </body>
        </html>
        """

    pdf_url = result["pdf_url"]
    return f"""
    <!doctype html>
    <html lang="pl">
    <head>
        <meta charset="utf-8">
        <title>Raport gotowy</title>
    </head>
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
        return run_analysis(request.text, request.email, base_url)
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
        }


@app.get("/analyze-simple")
def analyze_simple(text: str, email: str, request_obj: Request) -> dict:
    try:
        base_url = str(request_obj.base_url).rstrip("/")
        decoded_text = unquote(text)
        return run_analysis(decoded_text, email, base_url)
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
        }
