# ACPC API Local Run

## Purpose

Run the local ACPC Web MVP API foundation on Windows.

This starts only the local FastAPI backend. It does not start cloud runtime, SaaS orchestration, auth automation, payment automation, or an enterprise frontend.

## Commands

```powershell
cd apps\api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Shortcut from repo root:

```bat
run_api.bat
```

## Health Check

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected posture:

```text
status: ok
local_first: true
cloud_runtime: false
autonomous_action: false
```

## PV Diagnostic JSON Example

```powershell
$payload = @{
  site_id = "PV-DEMO-001"
  system_kwp = 10.0
  inverter_brand = "Growatt"
  daily_yield_kwh = 32.0
  expected_yield_kwh = 41.0
  module_temperature_c = 72.0
  insulation_mohm = 1.2
  string_1_voltage = 720.0
  string_1_current = 8.4
  string_2_voltage = 690.0
  string_2_current = 5.6
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/diagnostics/pv `
  -ContentType "application/json" `
  -Body $payload
```

## Report History

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/reports
```

## Full Report

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/reports/<report_id>
```

## Markdown Export

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/reports/<report_id>/markdown
```

## Runtime Files

Local runtime data is written under:

```text
data\acpc.db
data\uploads\
data\reports\
```

These are local runtime outputs and are ignored by git.

## Test Command

From repo root:

```powershell
python -m compileall apps/api
pytest apps/api/tests
```

If `pytest` is unavailable in the operator shell, use the existing fallback runner:

```powershell
python scripts/run_tests.py apps/api/tests
```
