# Final Axis Runtime Prototype

WitnessAI / Final Axis local operational runtime.

## Execute

```bash
cd /mnt/c/KODEKS
.venv/bin/python scripts/run_final_axis.py
```

## Test

```bash
cd /mnt/c/KODEKS
.venv/bin/python -m unittest discover -s tests -p test_final_axis_runtime.py
```

## Guarantees In Prototype

- Events, decisions, state changes, and cyber-physical adapter outcomes are logged to JSONL.
- State changes include before/after snapshots and an explanation.
- Semantic drift or declared drift triggers confinement.
- Critical events are held behind operator override support.
- No cyber-physical transmission is attempted without a trace-bearing decision.

## Outputs

- Runtime log: `data/final_axis/runtime_log.jsonl`
- Operational report: `data/final_axis/operational_report.md`
- Sample event data: `data/final_axis/sample_events.json`
