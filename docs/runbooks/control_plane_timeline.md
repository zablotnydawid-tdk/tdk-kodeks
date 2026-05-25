# Control Plane Timeline

Retina Timeline Lite is a read-only terminal view over validated Control Plane snapshot history.

## Purpose

The timeline gives the operator a quick overview of historical Control Plane snapshots without opening each JSON file.

It shows:

- snapshot timestamp,
- filename,
- overall system state,
- warning count,
- error count,
- maximum `drift_level`.

## Run

```powershell
cd C:\KODEKS
.\scripts\show_control_plane_timeline.ps1
```

Default history folder:

```text
state\history
```

## Boundary

This is not trend analysis. It does not compute drift scores across time, generate charts, trigger alerts, or recommend actions.

The timeline does not change system state. It only reads validated history snapshots and prints a compact operator view.
