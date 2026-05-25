# TDK Control Plane Overview

TDK Control Plane is the operator-facing coordination layer for KODEKS / WitnessAI / EXIM / ProService. It gives the operator one place to generate a deterministic local status snapshot, validate that snapshot against the Control Plane contract, and render a read-only terminal view called Retina Lite.

It is not a live monitoring service, scheduler, deploy tool, or autonomous recovery system. The current Control Plane is intentionally operator-driven.

## Run

```powershell
cd C:\KODEKS
.\scripts\control_plane.ps1
```

## Flow

The main command runs three steps:

1. Generate status snapshot:
   `scripts\generate_control_plane_snapshot.ps1`

2. Validate snapshot against schema:
   `scripts\validate_control_plane_snapshot.ps1`

3. Show read-only Retina Lite terminal view:
   `scripts\show_control_plane.ps1`

If validation fails, Retina Lite does not start.

Exit codes:

- `0` - success.
- `1` - validation failed.
- `2` - missing dependency or execution failure.

## Files

Schema:

- `schemas/control_plane_status.schema.json`

State:

- `state/control_plane_status.json`

Scripts:

- `scripts/control_plane.ps1`
- `scripts/generate_control_plane_snapshot.ps1`
- `scripts/validate_control_plane_snapshot.ps1`
- `scripts/show_control_plane.ps1`

Runbooks:

- `docs/runbooks/control_plane.md`
- `docs/runbooks/control_plane_snapshot.md`

Blueprint:

- `docs/blueprints/tdk_control_plane_ux.md`

Related runtime layers:

- `app/final_axis`
- `app/drift_energy_monitor`
- `app/anchorgrid`
- `scripts/master_system_sync.ps1`
- `docs/runbooks/local-operator-flow.md`

## Current Scope

Control Plane currently reads and displays local status for:

- Final Axis runtime.
- DEMON_CORE / Drift Energy Monitor.
- AnchorGrid.
- Master System Sync.
- Local Operator Stack.
- ProService / TDK workflow.
- Retina dashboard blueprint.
- GitHub sync status.
- Windows environment markers.

## What It Does Not Do Yet

- No GUI dashboard.
- No auto-refresh.
- No Windows service.
- No scheduler.
- No automatic Git push, pull, deploy, or reset.
- No automatic recovery.
- No full disk scan unless the operator explicitly runs Master System Sync with `-FullDiskScan`.
- No external API calls.
- No autonomous EMS/PV/AI action.

## Operating Rule

The Control Plane is operator-driven. Retina Lite is read-only. The system may generate, validate, and display status, but it does not make automatic changes. Any future action layer must keep this boundary: observe first, validate second, show clearly, and require operator confirmation before changing runtime state.
