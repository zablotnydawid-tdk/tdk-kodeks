# EXIM Operator Entrypoint Runbook

## Purpose

`EXIM_OPERATOR_ENTRYPOINT` gives the operator one terminal-first view of the local organism without starting cloud runtimes, SaaS dependencies, auth, payment, or a new dashboard.

It reuses existing KODEKS artifacts:

- Control Plane snapshot and history,
- Retina Lite / Timeline scripts,
- Operator Actions preview,
- DEMON / Drift Energy Monitor logs,
- VMA Runtime and VMA Continuity output,
- Live Case Loop result,
- existing form/admin/report flow as the surrounding local gateway.

Default behavior is read-only. Missing runtime data is reported as `UNKNOWN`, not inferred.

## Command

```powershell
cd C:\KODEKS
.\scripts\exim_operator_entrypoint.ps1
```

## What It Shows

- organism state from `state\control_plane_status.json`,
- latest Control Plane history snapshot from `state\history`,
- last Final Axis runtime state from `data\final_axis\runtime_log.jsonl`,
- latest VMA continuity state from `data\vma\vma_continuity_state.json`,
- latest DEMON drift/risk analysis from `data\drift_energy_monitor\runtime_log.jsonl`,
- active Live Case from `data\live_ops\live_case_result.json`,
- recommended next operator action,
- recovery hints for missing local data.

## Optional Local Launches

These are explicit operator actions. They are not run by default.

```powershell
.\scripts\exim_operator_entrypoint.ps1 -Launch timeline
.\scripts\exim_operator_entrypoint.ps1 -Launch operator_actions
.\scripts\exim_operator_entrypoint.ps1 -Launch live_case_demo
.\scripts\exim_operator_entrypoint.ps1 -Launch continuity_benchmark
```

`timeline` and `operator_actions` stay preview/read-only. `live_case_demo` and `continuity_benchmark` may refresh local proof output under `data\`.

## SAFE Mode

If required runtime files are missing, the entrypoint enters:

```text
SAFE_MODE_DEGRADED_READ_ONLY
```

In SAFE mode:

- values are shown as `UNKNOWN`,
- no autonomous action is recommended,
- recovery hints point to existing scripts,
- continuity is not reconstructed from narrative memory.

## Recovery Hints

Common recovery commands:

```powershell
.\scripts\generate_control_plane_snapshot.ps1
python .\scripts\run_final_axis.py
python .\scripts\run_drift_energy_monitor.py
.\scripts\live_case_demo.ps1
.\scripts\vma_continuity_benchmark.ps1
```

## Operator Rule

The entrypoint is an orientation layer. It observes and routes attention. It does not replace operator authority, issue EMS/PV/BESS commands, or mutate runtime state unless the operator explicitly launches an existing local proof script.
