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

## 3. When To Use

Use this before building or running any Control Plane UI layer:

- after changing `schemas/control_plane_status.schema.json`,
- after changing `scripts/generate_control_plane_snapshot.ps1`,
- before wiring the dashboard to `state/control_plane_status.json`,
- before operator handoff,
- after adding a new runtime module that should appear in the status plane.

## 4. What The Validator Does Not Do

- It does not launch the dashboard.
- It does not monitor processes continuously.
- It does not contact GitHub or external APIs.
- It does not prove that every service is healthy.
- It does not execute recovery, backup, deploy, or full disk scan actions.
- It validates the local JSON contract shape, required components, enums, timestamps, and required status fields only.
