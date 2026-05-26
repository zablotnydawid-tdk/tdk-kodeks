# Local Machine Start Flow

## Purpose

This document defines one local machine start review for the existing ACPC / EXIM / TDK stack.

The goal is not to build new layers. The goal is to observe, verify, and recommend a safe local startup order for what already exists on the operator machine.

## Mode

```text
OBSERVE
VERIFY
RECOMMEND
```

No automatic orchestration is performed.

The start review does not:

- start every service,
- install dependencies,
- auto-fix missing runtime data,
- deploy cloud services,
- create Docker/Kubernetes orchestration,
- add auth,
- add payment automation.

## Operator Command

```powershell
.\scripts\start_exim_machine.ps1
```

Optional roots:

```powershell
.\scripts\start_exim_machine.ps1 `
  -Root C:\KODEKS `
  -TdkRoot C:\TDK `
  -EximRoot C:\EXIM
```

## Systems Checked

The script checks:

- KODEKS runtime,
- ACPC API foundation,
- existing dashboards and demo UI,
- existing form/admin/report flow through KODEKS and TDK paths,
- `TDK_front`,
- `TDK_backend`,
- `TDK_platform_next`,
- Control Plane,
- EXIM Operator Entrypoint,
- Live Case Loop,
- Operator Review Layer,
- ACPC diagnostics,
- local scripts and runbooks,
- Windows startup/run flow.

## Checks

The machine review verifies:

1. Python availability.
2. Node and NPM availability.
3. Git repository state.
4. Control Plane snapshot presence.
5. SQLite/API state for ACPC Web MVP.
6. Existing frontend/dashboard manifests.
7. Available local ports.
8. Runtimes that are present and likely runnable.
9. Missing dependencies or unknowns.
10. Recommended operator startup sequence.

## SAFE MODE

The script uses SAFE MODE rules:

- show `UNKNOWN` instead of guessing,
- do not auto-install,
- do not auto-fix,
- do not auto-start large runtime groups,
- keep operator in control.

If a required file, snapshot, command, or database is missing, the output remains a recommendation, not a repair action.

## Recommended Startup Sequence

Default sequence:

```text
1. Review git status.
2. Refresh Control Plane snapshot.
3. Open EXIM Operator Entrypoint.
4. Start ACPC API only if the demo needs backend diagnostics.
5. Verify ACPC API health.
6. Run Live Case Loop demo if a case proof is needed.
7. Run Operator Review demo to close the case.
8. Start one frontend only after backend/API target is known.
9. Keep TDK_backend separate until dependencies and ports are confirmed.
```

## Expected Operator View

After running the script, the operator should see:

- what already exists,
- what is currently running,
- what can be started now,
- what is ready for demo,
- what remains `UNKNOWN`,
- which ports are occupied,
- which startup order is safest.

## Integration Boundary

This flow is a local machine start review only.

It does not replace:

- Control Plane,
- EXIM Operator Entrypoint,
- ACPC API,
- Live Case Loop,
- Operator Review Layer,
- TDK frontend/backend runbooks.

It is the one operator-facing checklist before choosing what to launch.
