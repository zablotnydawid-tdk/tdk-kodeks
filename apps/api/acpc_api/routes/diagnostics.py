from __future__ import annotations

import csv
import json
from io import StringIO
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import ValidationError

from acpc_api.models.schemas import DiagnosticResponse, PVDiagnosticInput
from acpc_api.services.pv_diagnostic_service import run_pv_diagnostic
from acpc_api.services.report_service import build_witness_markdown, response_summary
from acpc_api.services.storage_service import StorageService


router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])


@router.post("/pv", response_model=DiagnosticResponse)
async def pv_diagnostic(
    request: Request,
    file: UploadFile | None = File(default=None),
    payload_json: str | None = Form(default=None),
    site_id: str | None = Form(default=None),
    system_kwp: float | None = Form(default=None),
    inverter_brand: str | None = Form(default=None),
    daily_yield_kwh: float | None = Form(default=None),
    expected_yield_kwh: float | None = Form(default=None),
    module_temperature_c: float | None = Form(default=None),
    insulation_mohm: float | None = Form(default=None),
    string_1_voltage: float | None = Form(default=None),
    string_1_current: float | None = Form(default=None),
    string_2_voltage: float | None = Form(default=None),
    string_2_current: float | None = Form(default=None),
) -> dict[str, Any]:
    raw = await _extract_payload(
        request=request,
        file=file,
        payload_json=payload_json,
        form_values={
            "site_id": site_id,
            "system_kwp": system_kwp,
            "inverter_brand": inverter_brand,
            "daily_yield_kwh": daily_yield_kwh,
            "expected_yield_kwh": expected_yield_kwh,
            "module_temperature_c": module_temperature_c,
            "insulation_mohm": insulation_mohm,
            "string_1_voltage": string_1_voltage,
            "string_1_current": string_1_current,
            "string_2_voltage": string_2_voltage,
            "string_2_current": string_2_current,
        },
    )

    try:
        payload = PVDiagnosticInput(**raw)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=json.loads(exc.json())) from exc

    report = run_pv_diagnostic(payload)
    markdown = build_witness_markdown(report)
    StorageService().save_report(report, markdown)
    return response_summary(report)


async def _extract_payload(
    request: Request,
    file: UploadFile | None,
    payload_json: str | None,
    form_values: dict[str, Any],
) -> dict[str, Any]:
    if file is not None:
        content = (await file.read()).decode("utf-8-sig")
        rows = list(csv.DictReader(StringIO(content)))
        if not rows:
            raise HTTPException(status_code=400, detail="CSV upload has no rows")
        return dict(rows[0])

    if payload_json:
        try:
            return json.loads(payload_json)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="payload_json is not valid JSON") from exc

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        return await request.json()

    clean_form = {key: value for key, value in form_values.items() if value is not None}
    if clean_form:
        return clean_form

    raise HTTPException(status_code=400, detail="Missing JSON, CSV, or form payload")
