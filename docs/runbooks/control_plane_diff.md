# Control Plane Snapshot Diff

Read-only terminal diff for two Control Plane status snapshots.

## Purpose

The diff helps an operator compare the current Control Plane status with the previous validated snapshot from `state\history`.

It shows:

- changed `status`,
- changed `drift_level`,
- changed `next_action`,
- new components,
- missing components.

## Run

```powershell
cd C:\KODEKS
.\scripts\diff_control_plane_snapshots.ps1
```

Default comparison:

- current: `state\control_plane_status.json`
- previous: latest different snapshot found in `state\history`

## Colors

- Green: improvement.
- Red: regression.
- Yellow: neutral change.

## Boundary

This is not trend analysis. It does not generate charts, AI scoring, recommendations, or automated recovery actions.

The diff does not change any state. It only reads snapshot files and prints an operator-friendly terminal comparison.
