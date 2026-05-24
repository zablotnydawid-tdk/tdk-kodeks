# DRIFT_ENERGY_MONITOR

Runtime Drift and Energy Continuity Supervision Layer for TDK&ProService / WitnessAI / Final Axis.

## Identity

- name: `DRIFT_ENERGY_MONITOR`
- codename: `DEMON_CORE`
- version: `1.0.0`
- runtime mode: `continuous_observation`
- doctrine: `Operational Reality Is Noisy`

## Module Layout

- `app/drift_energy_monitor/schemas.py` - telemetry/runtime/AI/economic/environmental snapshots.
- `app/drift_energy_monitor/metrics.py` - coherence, entropy, energy loss, economic drift, AI conflict metrics.
- `app/drift_energy_monitor/state_machine.py` - stable, observation, degraded, unstable, critical, isolated, recovery transitions.
- `app/drift_energy_monitor/rules.py` - EMS grid charge conflict, COP drift, phase imbalance, recursive AI loop, hidden loss.
- `app/drift_energy_monitor/recovery.py` - automatic and manual recovery planning.
- `app/drift_energy_monitor/observability.py` - JSONL runtime log.
- `app/drift_energy_monitor/reporting.py` - Markdown operational report.
- `app/drift_energy_monitor/sample_data.py` - stable, drift, and recovery sample snapshots.
- `scripts/run_drift_energy_monitor.py` - executable local prototype.

## Drift Metrics

- `coherence_index`: stable decisions as a percentage of total decisions.
- `runtime_entropy`: unexpected events divided by total events.
- `energy_loss_factor`: expected yield minus real yield.
- `economic_drift`: actual cost minus expected cost, so positive values represent hidden loss.
- `ai_conflict_ratio`: contradictions divided by total predictions.

## Run

```bash
cd /mnt/c/KODEKS
.venv/bin/python scripts/run_drift_energy_monitor.py
```

Outputs:

- `data/drift_energy_monitor/runtime_log.jsonl`
- `data/drift_energy_monitor/operational_report.md`

## Test

```bash
cd /mnt/c/KODEKS
.venv/bin/python -m unittest discover -s tests -p test_drift_energy_monitor.py
```

## Final Axis Compatibility

- Observability: JSONL and Markdown exports.
- Explainability: every analysis includes metrics, findings, state transition, recovery plan, and witness evidence.
- Rollback support: recovery plan includes rollback and safe mode hooks.
- Continuity supervision: drift and hidden economic loss are treated as operational continuity risks.
- Degraded mode: state machine explicitly models degraded, unstable, critical, isolated, and recovery states.
