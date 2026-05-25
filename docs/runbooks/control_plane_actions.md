# Control Plane Operator Actions

Operator actions are manual checks for TDK Control Plane. They are intentionally read-only or preview-only.

## Run All Actions

```powershell
cd C:\KODEKS
.\scripts\control_plane_actions.ps1
```

## Run One Action

```powershell
cd C:\KODEKS
.\scripts\control_plane_actions.ps1 -Action repo_sync_check
```

Available actions:

- `repo_sync_check`
- `workspace_clean_check`
- `python_env_check`
- `node_env_check`
- `history_cleanup_preview`
- `history_cleanup_confirmed`
- `control_plane_verify`

## Output Contract

Each action prints:

- `action`
- `result`
- `recommendation`
- `risk_level`

## Safety Boundary

Operator actions do not perform destructive changes. They do not delete files, reset Git, install dependencies, start background services, schedule tasks, or run self-healing.

`history_cleanup_preview` is a preview only. It counts history snapshots and reports size. The operator decides whether any manual cleanup should happen later.

`history_cleanup_confirmed` is the only safe-write action. It still runs as preview unless the operator passes `-Confirm`, and it only removes history snapshots older than the selected retention window.

## Operator Decision

The system can show facts and recommendations. The operator decides what to do next.
