# Control Plane Snapshot

Quality gate for the future TDK Control Plane dashboard.

## 1. Generate Snapshot

```powershell
cd C:\KODEKS
.\scripts\generate_control_plane_snapshot.ps1
```

Default output:

```text
state\control_plane_status.json
```

The generator performs deterministic local checks only. It reads the repository, module paths, runtime markers, Git state, and Python/Node availability indicators. It does not start services and does not run live monitoring.

LIVE CASE LOOP is included as a read-only component named `live_case_loop`. The generator checks only for:

- `app/live_ops/live_case_loop.py`
- `scripts/live_case_demo.ps1`
- `sample_data/live_case_input.json`
- `docs/runbooks/live_case_demo.md`

It does not run `scripts/live_case_demo.ps1`, because that command writes runtime outputs. If the proof files are present, the component is `active`. If the latest `data/live_ops/live_case_result.json` is missing, the component stays active but reports `drift_level: low` and keeps the next action as `run scripts/live_case_demo.ps1 before field handoff`.

## 2. Validate Snapshot

```powershell
cd C:\KODEKS
.\scripts\validate_control_plane_snapshot.ps1
```

Expected success output:

```text
status-ok
```

If validation fails, the script prints one error per line and exits with a non-zero code.

## 3. Show Retina Lite

```powershell
cd C:\KODEKS
.\scripts\show_control_plane.ps1
```

This renders a read-only terminal view from `state\control_plane_status.json`.
It does not refresh live, does not launch a GUI, and does not execute actions.

Overall state treats planned components explicitly. If the only `unknown` component is `retina_dashboard`, and it is unknown because the full dashboard is only blueprinted as a read-only preview layer, Retina Lite still shows that component as `unknown` in the table but reports overall state as `active-with-planned-components`. This means there is no system problem; there is only a planned UI component that has not been implemented yet.

## 4. When To Use

Use this before building or running any Control Plane UI layer:

- after changing `schemas/control_plane_status.schema.json`,
- after changing `scripts/generate_control_plane_snapshot.ps1`,
- after changing `scripts/show_control_plane.ps1`,
- before wiring the dashboard to `state/control_plane_status.json`,
- before operator handoff,
- after adding a new runtime module that should appear in the status plane.

## 5. What The Validator Does Not Do

- It does not launch the dashboard.
- It does not monitor processes continuously.
- It does not contact GitHub or external APIs.
- It does not prove that every service is healthy.
- It does not execute recovery, backup, deploy, or full disk scan actions.
- It validates the local JSON contract shape, required components, enums, timestamps, and required status fields only.
