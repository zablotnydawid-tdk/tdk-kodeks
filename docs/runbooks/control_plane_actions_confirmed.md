# Control Plane Confirmed Operator Actions

Confirmed operator actions are manual actions that may write to local Control Plane state only after explicit operator confirmation.

## Default Mode

`control_plane_actions.ps1` runs in preview mode by default. Without `-Confirm`, no action is allowed to change files.

```powershell
cd C:\KODEKS
.\scripts\control_plane_actions.ps1 -Action history_cleanup_confirmed
```

This prints the selected files and reports that no files were deleted.

## Confirmed Cleanup

The only safe-write action currently available is:

- `history_cleanup_confirmed`

It deletes only Control Plane history snapshots from:

```text
state/history/
```

The action only targets files matching:

```text
control_plane_status_*.json
```

By default it selects snapshots older than 30 days.

```powershell
cd C:\KODEKS
.\scripts\control_plane_actions.ps1 -Action history_cleanup_confirmed -OlderThanDays 30 -Confirm
```

Before deletion, the script prints the full list of files selected for cleanup.

## Preview Override

`-Preview` keeps the run read-only even if `-Confirm` is also present.

```powershell
.\scripts\control_plane_actions.ps1 -Action history_cleanup_confirmed -OlderThanDays 30 -Preview -Confirm
```

## Safety Contract

- `-Confirm` works only for actions explicitly marked as safe-write.
- `-Action all -Confirm` does not authorize cleanup.
- No action performs auto-remediation.
- No scheduler, daemon, background service, self-healing, or AI decision layer is involved.
- The operator decides whether confirmed cleanup is appropriate.

