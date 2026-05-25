# Project Alignment After Reset

This document captures the current project map after the Control Plane, DEMON / Drift Energy Monitor, ZT&SI / CSK / DFRACTAL, Live Energy Operations Platform, VMA-USCP, dashboard, domain, forms, API keys, and operational product discussions.

It is a pause-and-align artifact only. It does not add features, refactor modules, or change runtime behavior.

## 1. What Already Exists In The Repo

Current code and operator tooling:

- `app/final_axis`: Final Axis runtime prototype with event bus, reducer, monitors, projection, boundary control, cyber-physical adapter, supervisor, logging, and reporting.
- `app/monitoring/drift_energy_monitor.py`: isolated DRIFT_ENERGY_MONITOR.SYS observability module.
- `app/drift_energy_monitor`: earlier DEMON_CORE package, preserved as-is.
- `app/anchorgrid`: AnchorGrid / BESS-adjacent runtime structures and tests.
- `app/engine`: process engine, steps, and energy case calculations.
- `app/api`: local FastAPI server.
- `app/output`, `app/session`, `app/storage`: report, session, and order storage layers.
- `scripts/control_plane*.ps1`: Control Plane snapshot, validation, Retina Lite, timeline, diff, operator actions.
- `scripts/master_system_sync.ps1`: Windows workspace inventory map.
- `scripts/*local_house*`, `scripts/*operator*`: Local Operator Stack for audit, monitor, backup, start, stop, recovery.
- `schemas/control_plane_status.schema.json`: Control Plane status contract.
- `schemas/drift_energy_monitor.schema.yaml`: Drift Energy Monitor contract.
- `tests/`: Final Axis, AnchorGrid, and Drift Energy Monitor tests.

## 2. What Is Only Documentation

Documentation and architecture, not runtime execution:

- `docs/blueprints/tdk_control_plane_ux.md`
- `docs/control_plane_overview.md`
- `docs/architecture/ztsi_control_plane_alignment.md`
- `docs/architecture/project_alignment_after_reset.md`
- `docs/runbooks/*`
- `docs/reports/drift_energy_monitor.md`
- `docs/final_axis_runtime.md`
- `docs/drift_energy_monitor.md`
- `docs/system-zablotny-online.md`

These documents define direction, operating rules, runbooks, and product framing. They should not be confused with live services.

## 3. What Is Runtime

Runtime or runtime-adjacent pieces:

- Final Axis supervisor and JSON/Markdown outputs.
- Drift Energy Monitor analysis and export.
- Control Plane snapshot generation and validation.
- Retina Lite terminal view.
- Snapshot history, diff, and timeline.
- Local Operator Stack scripts.
- Master System Sync inventory generation.
- Local API server.
- Process engine and energy calculations.

Runtime state is local by default:

- `state/control_plane_status.json`
- `state/history/*.json`

These files are ignored by Git unless deliberately converted into sanitized fixtures.

## 4. What Is Demo UI / Dashboard

Current dashboard state is fragmented:

- Retina Lite exists as terminal UI.
- Control Plane UX blueprint exists as documentation.
- `build/gui/xref-gui.html` exists as build artifact, not product source.
- No committed production dashboard source was found in the current shallow repo inventory.
- A future operator portal should be read-only first and should use the existing Control Plane snapshot contract.

The dashboard direction is valid, but the product entrypoint is not yet unified.

## 5. What Is Product To Monetize

The strongest monetizable product direction is the Live Energy Operations Platform for TDK / ProService operations:

- operator portal,
- case intake,
- energy diagnostics,
- PV / EMS / heat pump operational analysis,
- drift and loss reporting,
- field workflow,
- evidence export,
- customer-ready reports,
- operator-controlled recommendations.

Control Plane is the internal operational spine. The market-facing product should be simpler: intake, analysis, report, field action, follow-up.

## 6. What Is Scattered And Needs Inventory

Inventory is needed for:

- existing dashboard demo files outside the current committed tree,
- domain and deployment configuration,
- form/API key locations,
- environment variables and secret handling,
- VMA-USCP / voice continuity prototypes,
- Live Energy Operations Platform materials,
- desktop shortcuts and Windows dashboard launchers,
- generated reports and historical local data,
- old prototypes under Desktop/Documents/Downloads.

This should be done with an operator-approved inventory pass, not by guessing.

## 7. Nearest Real Business Priority

The nearest business priority is to package one understandable offer:

TDK / ProService operator portal for energy operations.

Minimum business promise:

- accept or enter a case,
- calculate/diagnose energy situation,
- show drift/loss/risk clearly,
- produce a field-ready report,
- preserve evidence and operator trace.

This is closer to revenue than building a full kernel, full AI agent, or voice runtime.

## 8. Nearest Real Technical Priority

The nearest technical priority is inventory and consolidation:

- locate all dashboard and product-entry files,
- identify the real UI source,
- decide one local entrypoint,
- connect read-only status to Control Plane snapshot,
- keep write actions behind explicit operator confirmation.

The next technical move should reduce fragmentation before adding more runtime layers.

## 9. What Not To Build Now

Do not build now:

- full ZT&SI / CSK / DFRACTAL kernel,
- autonomous remediation,
- Windows service or daemon,
- scheduler,
- live EMS control,
- AI scoring over operator decisions,
- voice continuity runtime as the first product surface,
- complex database lineage,
- multiple dashboards,
- automatic deploy or Git automation.

These are valid later directions, but they would increase fragmentation now.

## 10. Proposed Order

1. Inventory existing files and dashboards
   - find product UI sources,
   - find domain/form/API materials,
   - map local prototypes.

2. Merge product into one entrypoint
   - one launcher,
   - one operator start path,
   - one read-only status source.

3. MVP operator portal
   - case intake,
   - energy diagnostics,
   - report export,
   - operator trace.

4. Read-only dashboard
   - Control Plane status,
   - Drift Energy metrics,
   - history/timeline,
   - no writes.

5. Live ingest gateway
   - telemetry/event input,
   - schema validation,
   - no autonomous control.

6. VMA-USCP runtime MVP
   - voice continuity as operator support,
   - not as control authority,
   - connected only after product entrypoint is stable.

## Operating Rule

Models generate, Control Plane observes, operator decides.

