# WitnessAI Final Axis Runtime

Local operational runtime prototype for WitnessAI / Final Axis.

## Folder Structure

- `app/final_axis/schemas.py` - `SystemEvent`, severity/domain/type enums, runtime decisions.
- `app/final_axis/event_bus.py` - append-only event bus with JSON runtime trace logging.
- `app/final_axis/state.py` - explainable `RuntimeState` snapshot.
- `app/final_axis/reducer.py` - deterministic state transitions.
- `app/final_axis/monitors.py` - drift confinement and semantic isometry checks.
- `app/final_axis/projection.py` - CPLDC projection and BCC boundary-control layers.
- `app/final_axis/cyber_physical.py` - trace-aware cyber-physical adapter stub.
- `app/final_axis/supervisor.py` - Final Axis supervisor orchestration.
- `app/final_axis/reporting.py` - Markdown operational report builder.
- `app/final_axis/sample_events.py` - PV, EMS, AI governance, and operator override samples.
- `scripts/run_final_axis.py` - executable local prototype.
- `tests/test_final_axis_runtime.py` - runtime behavior test suite.

## Run

```bash
cd /mnt/c/KODEKS
.venv/bin/python scripts/run_final_axis.py
```

Outputs:

- `data/final_axis/runtime_log.jsonl`
- `data/final_axis/operational_report.md`

## Test

```bash
cd /mnt/c/KODEKS
.venv/bin/python -m unittest discover -s tests -p test_final_axis_runtime.py
```

## Runtime Rules Covered

- Every event is appended to JSONL before processing.
- Every decision is logged with trace ID, event ID, action, and reason.
- Every state change stores before/after snapshots with an explanation.
- Drift or semantic non-isometry triggers confinement.
- Critical events are operator-gated and support override.
- Cyber-physical commands are not transmitted without a trace-aware decision.

## Next Integration Steps

1. Connect `CyberPhysicalLink` to real EMS/PV command gateways behind operator gating.
2. Replace sample semantic scoring with the production WitnessAI governance model.
3. Persist JSONL logs to the official audit store and mirror report artifacts into session records.
4. Add signed operator identity and role policy before live control integration.
