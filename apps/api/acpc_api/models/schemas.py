from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


ReportStatus = Literal["pending_review", "payment_confirmed", "approved", "closed"]


class PVStringInput(BaseModel):
    voltage_v: float = Field(..., ge=0)
    current_a: float = Field(..., ge=0)


class PVDiagnosticInput(BaseModel):
    site_id: str = Field(..., min_length=1)
    system_kwp: float = Field(..., ge=0)
    inverter_brand: str = Field(..., min_length=1)
    daily_yield_kwh: float = Field(..., ge=0)
    expected_yield_kwh: float = Field(..., gt=0)
    module_temperature_c: float = Field(..., ge=-50)
    insulation_mohm: float = Field(..., ge=0)
    string_1_voltage: float = Field(..., ge=0)
    string_1_current: float = Field(..., ge=0)
    string_2_voltage: float = Field(..., ge=0)
    string_2_current: float = Field(..., ge=0)


class WitnessMode(BaseModel):
    enabled: bool = True
    signature: str = "WitnessAI Serwis OZE"
    intervention_logged: bool = True


class DiagnosticResponse(BaseModel):
    report_id: str
    summary: str
    status: ReportStatus
    risk_level: str


class ReportListItem(BaseModel):
    report_id: str
    timestamp: str
    site_id: str
    status: ReportStatus
    risk_level: str
    summary: str


class ReportEnvelope(BaseModel):
    report_id: str
    timestamp: str
    input_hash: str
    site_id: str
    status: ReportStatus
    findings: List[Dict[str, Any]]
    recommendations: List[str]
    summary: str
    score: float
    risk_level: str
    operator_review_required: bool
    autonomous_action: bool
    decision_trace: List[Dict[str, Any]]
    witness_mode: WitnessMode
    acpc_report: Dict[str, Any]
    input_payload: Dict[str, Any]


class ReportDetailResponse(BaseModel):
    report: ReportEnvelope


class ReportListResponse(BaseModel):
    reports: List[ReportListItem]


class HealthResponse(BaseModel):
    status: str
    service: str
    storage: str
    local_first: bool
    cloud_runtime: bool
    autonomous_action: bool


def schema_dict(model: BaseModel) -> dict[str, Any]:
    return model.dict()
