# LIVE CASE LOOP Runtime Proof

This report describes the first isolated executable LIVE CASE LOOP proof.

The runtime is local, deterministic, and operator-gated. It does not implement UI, SaaS, cloud sync, autonomous action, or integration with `C:\TDK\TDK_backend` / `C:\TDK\TDK_front`.

## Flow

```text
INPUT
-> intake
-> classify_case
-> detect_priority
-> generate_diagnostic_summary
-> generate_recommendation
-> memory_update
-> executive_summary
```

## Runtime Files

- `app/live_ops/live_case_loop.py`
- `schemas/live_case.schema.yaml`
- `sample_data/live_case_input.json`
- `sample_data/live_case_result.json`
- `tests/test_live_case_loop.py`
- `scripts/live_case_demo.ps1`

## Governance Boundary

- Control Plane observes.
- DEMON calculates drift/risk later.
- VMA preserves continuity later.
- Operator decides.
- No autonomous remediation is performed.
- No EMS/PV/BESS command is executed.

## Output

The demo command can write:

- `data/live_ops/live_case_result.json`
- `data/live_ops/live_case_report.md`

These are runtime outputs and should be treated as local generated artifacts.

## Integration Direction

The next phase can expose this proof as a read-only status input for Control Plane or attach it to an existing case gateway. Do not connect it to frontend/backend production flows until the case memory boundary is approved.

