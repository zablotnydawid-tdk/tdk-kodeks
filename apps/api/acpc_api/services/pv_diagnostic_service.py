from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from acpc_api.models.schemas import PVDiagnosticInput, schema_dict
from src.acpc.energy.pv_diagnostics import PVDiagnosticEngine
from src.acpc.energy.pv_diagnostics.models import PVEvent, PVEventType


def run_pv_diagnostic(payload: PVDiagnosticInput) -> dict[str, Any]:
    input_payload = schema_dict(payload)
    event_payload = _to_acpc_sample(input_payload)
    event_id = _hash_payload(event_payload)

    engine = PVDiagnosticEngine(payload.site_id)
    engine.apply(
        PVEvent(
            PVEventType.PV_SAMPLE_RECEIVED,
            event_payload,
            payload.site_id,
            lamport=1,
            event_id=event_id,
        )
    )
    acpc_report = engine.json_report()

    findings = list(acpc_report.get("findings", []))
    recommendations = list(acpc_report.get("recommended_actions", []))
    risk_level = _risk_level(acpc_report)
    score = _score(findings, risk_level)
    report_id = f"acpc-pv-{uuid4().hex[:12]}"
    timestamp = datetime.now(timezone.utc).isoformat()
    summary = _summary(payload.site_id, risk_level, findings)

    return {
        "report_id": report_id,
        "timestamp": timestamp,
        "input_hash": _hash_payload(input_payload),
        "site_id": payload.site_id,
        "status": "pending_review",
        "findings": findings,
        "recommendations": recommendations,
        "summary": summary,
        "score": score,
        "risk_level": risk_level,
        "operator_review_required": True,
        "autonomous_action": False,
        "decision_trace": [
            {
                "step": "intake",
                "status": "validated",
                "summary": "PV diagnostic payload validated locally.",
            },
            {
                "step": "acpc_pv_diagnostics",
                "status": acpc_report.get("status", "unknown"),
                "summary": summary,
            },
            {
                "step": "governance",
                "status": "pending_operator_review",
                "summary": "Operator remains decision owner; autonomous action disabled.",
            },
        ],
        "witness_mode": {
            "enabled": True,
            "signature": "WitnessAI Serwis OZE",
            "intervention_logged": True,
        },
        "acpc_report": acpc_report,
        "input_payload": input_payload,
    }


def _to_acpc_sample(payload: dict[str, Any]) -> dict[str, Any]:
    string_1_power = payload["string_1_voltage"] * payload["string_1_current"]
    string_2_power = payload["string_2_voltage"] * payload["string_2_current"]
    return {
        "site_id": payload["site_id"],
        "system_kwp": payload["system_kwp"],
        "inverter": payload["inverter_brand"],
        "strings": [
            {
                "id": "S1",
                "voltage_v": payload["string_1_voltage"],
                "current_a": payload["string_1_current"],
                "power_w": round(string_1_power, 3),
            },
            {
                "id": "S2",
                "voltage_v": payload["string_2_voltage"],
                "current_a": payload["string_2_current"],
                "power_w": round(string_2_power, 3),
            },
        ],
        "daily_yield_kwh": payload["daily_yield_kwh"],
        "expected_yield_kwh": payload["expected_yield_kwh"],
        "module_temperature_c": payload["module_temperature_c"],
        "insulation_mohm": payload["insulation_mohm"],
        "witness_mode": True,
        "signature": "WitnessAI Serwis OZE",
    }


def _risk_level(acpc_report: dict[str, Any]) -> str:
    severities = [item.get("severity", "") for item in acpc_report.get("findings", [])]
    if "critical" in severities or acpc_report.get("status") == "critical":
        return "critical"
    if "warning" in severities or acpc_report.get("status") == "warning":
        return "warning"
    return "normal"


def _score(findings: list[dict[str, Any]], risk_level: str) -> float:
    base = {"normal": 0.15, "warning": 0.55, "critical": 0.9}[risk_level]
    return round(min(1.0, base + len(findings) * 0.03), 4)


def _summary(site_id: str, risk_level: str, findings: list[dict[str, Any]]) -> str:
    if not findings:
        return f"PV site {site_id} has no active ACPC findings; operator review still required."
    diagnoses = ", ".join(item.get("diagnosis", "unknown") for item in findings)
    return f"PV site {site_id} is {risk_level}; findings: {diagnoses}."


def _hash_payload(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
