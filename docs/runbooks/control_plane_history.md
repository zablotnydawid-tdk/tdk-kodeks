# Control Plane Snapshot History

Control Plane keeps a local history of validated status snapshots. This is the time-based archive of the status truth layer for the operator-driven Control Plane.

## Purpose

The history records what the Control Plane believed at the moment a snapshot passed validation. It gives the operator a durable sequence of status facts without adding live monitoring, charts, or automated analysis.

## Location

Current snapshot:

```text
state\control_plane_status.json
```

Validated history snapshots:

```text
state\history\control_plane_status_YYYYMMDD_HHMMSS.json
```

The archive copy is created only after:

1. `scripts\generate_control_plane_snapshot.ps1` succeeds.
2. `scripts\validate_control_plane_snapshot.ps1` returns `status-ok`.

If validation fails, no history file is written and Retina Lite does not start.

## Read-Only Rule

History files are read-only evidence for operators and future UI layers. They should be treated as immutable local records of status at a point in time.

Do not edit old history files to fix current state. Generate a new snapshot instead.

## What This Is Not Yet

- Not trend analysis.
- Not snapshot diffing.
- Not charts.
- Not a monitoring database.
- Not a scheduler.
- Not evidence signing.

This is only the archive of validated status truth over time.
