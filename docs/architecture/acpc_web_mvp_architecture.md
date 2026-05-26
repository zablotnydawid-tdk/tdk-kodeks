# ACPC Web MVP Architecture

## Phase

`ACPC WEB MVP - PHASE 1: API FOUNDATION`

This is a local product demonstration, not final SaaS, enterprise cloud, or a multi-user platform.

## Flow

```text
form / JSON / CSV intake
-> FastAPI
-> ACPC PV diagnostics
-> witness report
-> SQLite persistence
-> report history
-> operator acceptance later
```

## Backend Scope

The API lives under:

```text
apps/api/
```

Core modules:

- `main.py` wires FastAPI routes.
- `acpc_api/routes/health.py` exposes API status.
- `acpc_api/routes/diagnostics.py` accepts PV diagnostic input.
- `acpc_api/routes/reports.py` exposes persisted report history and Markdown export.
- `acpc_api/services/pv_diagnostic_service.py` adapts API payloads to existing ACPC PV diagnostics.
- `acpc_api/services/report_service.py` builds the witness Markdown report.
- `acpc_api/services/storage_service.py` wraps SQLite persistence.
- `acpc_api/storage/db.py` owns the SQLite schema.
- `acpc_api/models/schemas.py` defines the pydantic contracts.

## Persistence

Runtime data is local:

```text
data/acpc.db
data/uploads/
data/reports/
```

These paths are ignored by git. The repository tracks code, tests, schemas, docs, and sample-safe material, not local runtime databases or generated reports.

## Witness Mode

Every persisted report includes:

- `report_id`
- `timestamp`
- `input_hash`
- `findings`
- `recommendations`
- `operator_review_required`
- `witness_mode.enabled = true`
- `witness_mode.signature = "WitnessAI Serwis OZE"`
- `witness_mode.intervention_logged = true`

## Governance Boundary

Operator remains the decision authority.

The API never performs autonomous remediation:

```text
autonomous_action = false
status = pending_review
```

The API does not:

- run cloud runtime,
- automate auth or payments,
- orchestrate SaaS,
- execute EMS/PV/BESS commands,
- close cases without operator acceptance.

## Status Model

Supported report statuses:

- `pending_review`
- `payment_confirmed`
- `approved`
- `closed`

Phase 1 creates diagnostic reports as `pending_review`.

## Next Boundary

The next phase can connect this API to an existing local form/admin/report flow or simple dashboard/history view. That should remain read-only first, with explicit operator acceptance before any case moves to `approved` or `closed`.
