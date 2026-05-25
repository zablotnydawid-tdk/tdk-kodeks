# TDK Control Plane

Single operator-driven command for the current Control Plane flow.

## One Command

```powershell
cd C:\KODEKS
.\scripts\control_plane.ps1
```

The command performs a deterministic four-step flow:

1. Generate `state\control_plane_status.json`.
2. Validate it against `schemas\control_plane_status.schema.json`.
3. Archive the validated snapshot into `state\history`.
4. Render Retina Lite in the terminal.

## Expected Flow

Successful run:

```text
TDK Control Plane operator flow
1/4 generate snapshot
2/4 validate snapshot
status-ok
3/4 archive snapshot
4/4 show Retina Lite
```

The terminal view then displays:

- AXIS
- DEMON
- GIT / ANCHOR
- OPERATOR STACK
- RETINA / UX
- ENVIRONMENT
- overall system state
- warning/error counts
- snapshot timestamp

Validated snapshots are archived as:

```text
state\history\control_plane_status_YYYYMMDD_HHMMSS.json
```

## Exit Codes

- `0` - success.
- `1` - validation failed; Retina Lite is not shown.
- `2` - missing dependency or execution failure.

## Exit Code Contract

`scripts\generate_control_plane_snapshot.ps1` always exits explicitly:

- `0` - snapshot was generated.
- `1` - controlled generation error.
- `2` - missing dependency, such as missing workspace root.

`scripts\control_plane.ps1` interprets only explicit script exit codes. Component-level `warning` statuses inside `state\control_plane_status.json` are displayed by Retina Lite but do not fail the command. The only validation gate is `scripts\validate_control_plane_snapshot.ps1`; if it returns non-zero, Retina Lite is not shown and Control Plane exits `1`.

## Recovery Basics

If generation fails:

```powershell
cd C:\KODEKS
.\scripts\generate_control_plane_snapshot.ps1
```

If validation fails:

```powershell
cd C:\KODEKS
.\scripts\validate_control_plane_snapshot.ps1
```

Read the printed errors, fix the snapshot or schema contract, then run:

```powershell
.\scripts\control_plane.ps1
```

If Retina Lite fails:

```powershell
cd C:\KODEKS
.\scripts\show_control_plane.ps1
```

## Operator Boundary

This command does not add auto-refresh, Windows services, scheduled tasks, deploy logic, recovery actions, or background monitoring. It is intentionally operator-driven: generate, validate, show, stop.
