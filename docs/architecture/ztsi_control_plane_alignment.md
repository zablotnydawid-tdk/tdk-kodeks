# ZT&SI Control Plane Alignment Map

This document maps the ZT&SI / CSK / DFRACTAL runtime-kernel direction onto the current KODEKS / TDK Control Plane implementation. It is an architecture alignment note only. It does not implement the kernel.

Source context:

- Local PDF reference: `C:\Users\zablo\Desktop\ServicePlatform Projekt TDK&ProService\ZT&SI_CSK_DFRACTAL\ZT&SI_CSK_DFRACTAL.pdf`
- Current repo state: KODEKS runtime, Control Plane, Final Axis, DEMON / Drift Energy Monitor, Local Operator Stack, AnchorGrid, ProService workflow.

Note: the PDF was present locally, but this environment did not have a working PDF text extractor. The mapping below is therefore based on the named ZT&SI / CSK / DFRACTAL concepts plus the concrete modules currently present in KODEKS.

## 1. What Already Exists In KODEKS

The following kernel-adjacent layers already exist as code or operator tooling:

- Control Plane snapshot contract: `schemas/control_plane_status.schema.json`
- Snapshot generator, validator, Retina Lite view, history, diff, timeline, and operator action scripts in `scripts/`
- Final Axis runtime prototype in `app/final_axis`
- Drift Energy Monitor observability runtime in `app/monitoring/drift_energy_monitor.py`
- Earlier DEMON_CORE package in `app/drift_energy_monitor`
- AnchorGrid runtime structures in `app/anchorgrid`
- Process engine and energy case calculations in `app/engine`
- Local Operator Stack scripts and runbooks
- Master System Sync inventory script in `scripts/master_system_sync.ps1`
- Read-only status state and history memory under local `state/`, ignored by Git as runtime data

These pieces are enough to support an operator-visible runtime map without building a full autonomous kernel.

## 2. What Is Partially Implemented

The following concepts exist, but are not yet unified as one kernel:

- Drift Engine: implemented diagnostically through DEMON / Drift Energy Monitor, not yet a live ingest service.
- Observability Layer: implemented through snapshots, JSON exports, Markdown reports, Retina Lite, and runbooks.
- Snapshot Store: exists as local JSON state and history files, but not as a database or retention-managed service.
- Runtime State: exists as generated Control Plane status and module-specific analysis outputs.
- Operator Actions: manual read-only and confirmed safe-write actions exist, but no remediation chain exists.
- Governance Gate: validation and operator confirmation exist; policy enforcement is still procedural.
- Output Firewall: concept exists through read-only Retina and no-autonomous-action rules; no dedicated output firewall module exists yet.
- Rollback Support: represented in Final Axis and Drift Energy Monitor compatibility fields, but not wired to an operational rollback engine.
- Lineage / History: snapshot history, diff, timeline, Git history, and reports exist, but are not unified into one lineage model.

## 3. What Is Only Conceptual

The following remain architecture concepts for later phases:

- Full ZT&SI runtime kernel.
- CSK central semantic kernel.
- DFRACTAL execution fabric.
- Unified event lineage graph.
- Model governance router.
- Live multi-source ingest gateway.
- Output firewall with policy packs.
- Runtime rollback orchestration.
- Stability dashboard with live panels.
- Voice continuity runtime connected to Control Plane.

These should not be implemented until the current operator plane is inventoried and productized.

## 4. Control Plane Mapping

| ZT&SI / Kernel Area | Current TDK Control Plane Mapping | Current Status |
| --- | --- | --- |
| Drift Engine | `app/monitoring/drift_energy_monitor.py`, `app/drift_energy_monitor`, `docs/reports/drift_energy_monitor.md` | Diagnostic runtime exists |
| Observability Layer | `scripts/control_plane.ps1`, `scripts/show_control_plane.ps1`, Markdown reports, JSON status | Active read-only layer |
| Snapshot Store | `state/control_plane_status.json`, `state/history/*.json` | Local runtime memory, ignored by Git |
| Runtime State | `schemas/control_plane_status.schema.json`, generated snapshot fields | Contracted and validated |
| Operator Actions | `scripts/control_plane_actions.ps1` | Manual actions, preview by default |
| Governance Gate | snapshot validation, explicit `-Confirm`, no auto-remediation rule | Procedural gate exists |
| Output Firewall | Retina Lite read-only view, operator confirmation doctrine | Conceptual but enforced by process |
| Rollback Support | Final Axis compatibility, DEMON compatibility, Git history | Partial support |
| Lineage / History | snapshot archive, snapshot diff, timeline, Git commits, reports | Partial lineage |

## 5. What We Are Not Implementing Now

Do not implement these in this phase:

- Full ZT&SI / CSK / DFRACTAL kernel.
- Background daemons.
- Auto-remediation.
- Autonomous model decisions.
- Scheduler or Windows service.
- Live EMS/PV control.
- Automatic Git push, pull, reset, or deployment.
- Voice runtime integration.
- GUI dashboard implementation.
- New database layer for lineage.

The current work remains alignment and direction only.

## 6. Nearest MVP

The nearest MVP should be read-only and operator-driven:

1. Read-only Stability Dashboard
   - show current Control Plane status,
   - show component drift/risk,
   - show validation state,
   - do not mutate runtime.

2. Drift Timeline
   - read `state/history/`,
   - show status and drift changes over time,
   - no trend scoring yet.

3. Event Stream
   - read JSON/Markdown outputs from Final Axis and Drift Energy Monitor,
   - normalize display only,
   - no action execution.

4. Coherence / Drift Panels
   - show `coherence_index`, `runtime_entropy`, `energy_loss_factor`, `economic_drift`, `ai_conflict_ratio`,
   - show diagnostic events and state machine state,
   - keep recommendations separate from operator decisions.

## 7. Operating Principle

Models generate, Control Plane observes, operator decides.

That means:

- models may produce candidates, analyses, summaries, and reports;
- Control Plane reads, validates, displays, and preserves trace;
- the operator decides when a change is allowed.

