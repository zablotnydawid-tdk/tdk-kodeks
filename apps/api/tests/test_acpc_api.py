from __future__ import annotations

import os
import sys
import tempfile
import asyncio
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from acpc_api.routes.diagnostics import pv_diagnostic  # noqa: E402
from acpc_api.routes.health import health  # noqa: E402
from acpc_api.routes.reports import get_report, get_report_markdown, list_reports  # noqa: E402


def warning_payload() -> dict:
    return {
        "site_id": "PV-WARNING-001",
        "system_kwp": 10.0,
        "inverter_brand": "Growatt",
        "daily_yield_kwh": 32.0,
        "expected_yield_kwh": 41.0,
        "module_temperature_c": 45.0,
        "insulation_mohm": 6.5,
        "string_1_voltage": 720.0,
        "string_1_current": 8.4,
        "string_2_voltage": 710.0,
        "string_2_current": 8.1,
    }


def critical_payload() -> dict:
    payload = warning_payload()
    payload.update(
        {
            "site_id": "PV-CRITICAL-001",
            "insulation_mohm": 1.2,
            "module_temperature_c": 72.0,
            "string_2_current": 5.6,
        }
    )
    return payload


class FakeRequest:
    headers = {"content-type": "application/json"}

    def __init__(self, payload: dict):
        self.payload = payload

    async def json(self) -> dict:
        return self.payload


def temp_db() -> tempfile.TemporaryDirectory[str]:
    temp_dir = tempfile.TemporaryDirectory()
    os.environ["ACPC_DB_PATH"] = str(Path(temp_dir.name) / "acpc-test.db")
    os.environ["ACPC_REPORTS_DIR"] = str(Path(temp_dir.name) / "reports")
    return temp_dir


def run_diagnostic(payload: dict) -> dict:
    return asyncio.run(
        pv_diagnostic(
            request=FakeRequest(payload),
            file=None,
            payload_json=None,
        )
    )


def test_health_endpoint() -> None:
    temp_dir = temp_db()
    try:
        payload = health()
        assert payload["status"] == "ok"
        assert payload["local_first"] is True
        assert payload["autonomous_action"] is False
    finally:
        temp_dir.cleanup()
        os.environ.pop("ACPC_DB_PATH", None)
        os.environ.pop("ACPC_REPORTS_DIR", None)


def test_diagnostic_warning() -> None:
    temp_dir = temp_db()
    try:
        payload = run_diagnostic(warning_payload())
        assert payload["status"] == "pending_review"
        assert payload["risk_level"] == "warning"
        assert payload["report_id"]
    finally:
        temp_dir.cleanup()
        os.environ.pop("ACPC_DB_PATH", None)
        os.environ.pop("ACPC_REPORTS_DIR", None)


def test_pid_critical() -> None:
    temp_dir = temp_db()
    try:
        payload = run_diagnostic(critical_payload())
        assert payload["risk_level"] == "critical"
    finally:
        temp_dir.cleanup()
        os.environ.pop("ACPC_DB_PATH", None)
        os.environ.pop("ACPC_REPORTS_DIR", None)


def test_report_persistence() -> None:
    temp_dir = temp_db()
    try:
        created = run_diagnostic(critical_payload())
        report_id = created["report_id"]

        listing = list_reports()
        detail = get_report(report_id)

        assert any(item["report_id"] == report_id for item in listing["reports"])
        report = detail["report"]
        assert report["report_id"] == report_id
        assert report["operator_review_required"] is True
        assert report["autonomous_action"] is False
        assert report["witness_mode"]["signature"] == "WitnessAI Serwis OZE"
        assert (Path(os.environ["ACPC_REPORTS_DIR"]) / f"{report_id}.json").exists()
        assert (Path(os.environ["ACPC_REPORTS_DIR"]) / f"{report_id}.md").exists()
    finally:
        temp_dir.cleanup()
        os.environ.pop("ACPC_DB_PATH", None)
        os.environ.pop("ACPC_REPORTS_DIR", None)


def test_markdown_export() -> None:
    temp_dir = temp_db()
    try:
        created = run_diagnostic(critical_payload())
        report_id = created["report_id"]

        response = get_report_markdown(report_id)
        body = response.body.decode("utf-8")

        assert response.status_code == 200
        assert "ACPC PV Witness Report" in body
        assert "WitnessAI Serwis OZE" in body
    finally:
        temp_dir.cleanup()
        os.environ.pop("ACPC_DB_PATH", None)
        os.environ.pop("ACPC_REPORTS_DIR", None)
