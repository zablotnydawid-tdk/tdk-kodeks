from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, EmailStr

from app.engine.process_engine import run_process
from app.input.normalizer import normalize_input
from app.output.pdf_builder import generate_pdf
from app.output.report_builder import build_report
from app.routing.mask_router import choose_mask


app = FastAPI(title="KODEKS API")


class AnalyzeRequest(BaseModel):
    text: str
    email: EmailStr


@app.post("/analyze")
def analyze(request: AnalyzeRequest) -> dict:
    normalized = normalize_input(request.text)
    selected_mask, _route_reason = choose_mask(normalized)
    process_result = run_process(normalized, selected_mask)
    report_text = build_report(
        raw_input=request.text,
        selected_mask=selected_mask,
        process_result=process_result,
    )

    reports_dir = Path("data") / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = reports_dir / f"raport_{timestamp}.pdf"
    generated_path = generate_pdf(report_text, str(pdf_path))

    return {
        "status": "ok",
        "pdf_path": generated_path,
    }
