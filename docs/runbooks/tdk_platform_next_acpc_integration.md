# TDK Platform Next ACPC Integration

## Purpose

This runbook describes the restricted public frontend integration between:

```text
C:\TDK\TDK_platform_next
```

and the local ACPC API foundation:

```text
C:\KODEKS\apps\api
```

This is a local integration step for the public `tdkproservice.pl` candidate. It does not deploy, change DNS, configure SSL, expose EXIM runtime, or publish Control Plane/DEMON/runtime state.

## Public Boundary

The public page exposes only:

- PV intake form,
- optional JSON/CSV upload,
- `pending_review` status,
- sanitized diagnostic summary,
- report ID,
- risk level,
- contact email: `kontakt@tdkproservice.pl`.

The public page does not expose:

- Control Plane,
- DEMON logs,
- VMA state,
- EXIM runtime state,
- Operator Review internals,
- raw decision trace,
- autonomous remediation,
- payment automation.

## Files

Frontend:

```text
C:\TDK\TDK_platform_next\app\pv-intake\page.tsx
C:\TDK\TDK_platform_next\lib\acpcApi.ts
C:\TDK\TDK_platform_next\.env.example
```

Runbook:

```text
C:\KODEKS\docs\runbooks\tdk_platform_next_acpc_integration.md
```

Repository boundary:

```text
C:\TDK\TDK_platform_next changes are outside the KODEKS repository.
KODEKS tracks this runbook only unless the operator explicitly imports frontend code later.
```

## Environment

Add to `C:\TDK\TDK_platform_next\.env.local`:

```text
NEXT_PUBLIC_ACPC_API_BASE=http://127.0.0.1:8000
```

The existing `NEXT_PUBLIC_API_URL` remains for the older AnchorGrid/TDK backend flow.

## Start ACPC API

From `C:\KODEKS`:

```bat
run_api.bat
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## Start Frontend

From `C:\TDK\TDK_platform_next`:

```powershell
npm run dev
```

Open:

```text
http://127.0.0.1:3000/pv-intake
```

If port `3000` is already occupied, choose a free local port according to the operator machine start review.

## Test Form

1. Start ACPC API.
2. Start TDK Platform Next.
3. Open `/pv-intake`.
4. Submit default PV values.
5. Confirm public output shows:
   - report ID,
   - `pending_review`,
   - risk level,
   - sanitized summary,
   - contact email.

## Test JSON Upload

Upload a JSON file matching:

```json
{
  "site_id": "PV-DEMO-001",
  "system_kwp": 10,
  "inverter_brand": "Growatt",
  "daily_yield_kwh": 32,
  "expected_yield_kwh": 41,
  "module_temperature_c": 72,
  "insulation_mohm": 1.2,
  "string_1_voltage": 720,
  "string_1_current": 8.4,
  "string_2_voltage": 690,
  "string_2_current": 5.6
}
```

## Test CSV Upload

Upload a CSV with a header row matching the ACPC API fields:

```csv
site_id,system_kwp,inverter_brand,daily_yield_kwh,expected_yield_kwh,module_temperature_c,insulation_mohm,string_1_voltage,string_1_current,string_2_voltage,string_2_current
PV-DEMO-001,10,Growatt,32,41,72,1.2,720,8.4,690,5.6
```

## Operator Rule

Public UI creates a diagnostic case only.

Final decision remains:

```text
pending_review -> operator review -> report/contact
```
