# Full Project Inventory Before Live Ops

This document captures the current local project inventory before any LIVE CASE LOOP implementation.

Scope:

- primary repo: `C:\KODEKS`
- shallow external inventory: `C:\TDK`, `C:\ztsi-stability-gateway`, and nearby TDK / Witness / EXIM folders discovered at the root of `C:\`
- no refactor, no file move, no deletion, no new runtime behavior

Source references mentioned by the operator:

- `C:\Users\zablo\Desktop\ServicePlatform Projekt TDK&ProService\MASTER DOCUMENT PROTOCOL.pdf`
- `C:\Users\zablo\Desktop\ServicePlatform Projekt TDK&ProService\ZT&SI_CSK_DFRACTAL\ZT&SI_CSK_DFRACTAL.pdf`

The PDF files remain architecture sources. This inventory is a filesystem and repo-state map, not a full PDF extraction or kernel implementation.

## 1. Found Application Modules

### In `C:\KODEKS`

| Area | Path | Classification | Notes |
| --- | --- | --- | --- |
| KODEKS CLI process | `main.py`, `app/input`, `app/routing`, `app/engine`, `app/output`, `app/session` | Active local runtime | Text input, mask routing, process engine, report/session output. |
| KODEKS FastAPI/API/form layer | `app/api/server.py` | Active API and form gateway | Local/prod-oriented FastAPI app with forms, reports, admin order view, AnchorGrid endpoints, PDF generation, mail failure safety. |
| Order storage | `app/storage/order_store.py` | Active local storage | File-based order persistence under `data/orders`. |
| Supabase storage draft | `app/storage/supabase_order_store.py` | Partial / future | Migration draft only; raises `NotImplementedError`. |
| Final Axis | `app/final_axis` | Active isolated runtime prototype | Event schema, bus, reducer, monitors, projection, BCC/CPLDC-style boundaries, CyberPhysicalLink adapter, supervisor, logs, report. |
| DEMON legacy package | `app/drift_energy_monitor` | Existing preserved subsystem | Earlier DEMON_CORE package with metrics, rules, recovery, observability, reporting, supervisor. Do not refactor casually. |
| Drift Energy Monitor isolated observability | `app/monitoring/drift_energy_monitor.py` | Active isolated runtime observability | Diagnostic scoring/export only; no auto-remediation. |
| VMA runtime | `app/vma/runtime.py` | Active isolated continuity proof | Structure detection, topology mapping, anchors, recovery, continuity metrics. |
| VMA real session recorder | `app/vma/session_recorder.py` | Active manual runtime recorder | Manual transcript sessions, JSON/Markdown reports, no audio/cloud/UI. |
| AnchorGrid | `app/anchorgrid` | Active BESS / grid runtime | BESS advisory logic, schema, config, tests. |

### External Local Artifacts

| Area | Path | Classification | Notes |
| --- | --- | --- | --- |
| TDK backend | `C:\TDK\TDK_backend` | Active candidate gateway/API | FastAPI platform with auth, subscriptions, modules, GPT bridge, cases, demo case seed, AnchorGrid, usage limits, DB layer. |
| TDK frontend | `C:\TDK\TDK_front` | Active/demo operator UI | Vite React app. Currently routes immediately to `AnchorGridDashboard`. Uses `VITE_API_URL`, localStorage token/api-key patterns, AnchorGrid analysis and PDF export. |
| TDK platform Next | `C:\TDK\TDK_platform_next` | Future/product UI candidate | Next.js + Recharts platform shell with `NEXT_PUBLIC_API_URL`. Needs separate review before reuse. |
| ZT&SI Stability Gateway | `C:\ztsi-stability-gateway` | Strong reusable runtime proof / separate project | Gateway, coherence/drift/firewall/governance, lineage, memory, rollback, telemetry, dashboard, API, validation, tests. Keep separate until integration boundary is defined. |
| CodexIntrospect local | `C:\CodexIntrospect_Lokalny` | Local infra candidate | Package present; not inventoried deeply in this pass. |
| Witness / EXIM / other roots | `C:\WitnessAI`, `C:\WitnessAI_Dev`, `C:\EXIM_Witness`, `C:\WITNESS_SYSTEM`, `C:\BRAT_WITNESS_PHONE_MVP`, `C:\TAJNE\...` | External inventory candidates | Discovered as local project roots; do not touch without a dedicated operator-approved inventory pass. |

## 2. Found Operator Scripts

### Control Plane

- `scripts/control_plane.ps1`
- `scripts/generate_control_plane_snapshot.ps1`
- `scripts/validate_control_plane_snapshot.ps1`
- `scripts/show_control_plane.ps1`
- `scripts/show_control_plane_timeline.ps1`
- `scripts/diff_control_plane_snapshots.ps1`
- `scripts/control_plane_actions.ps1`

Status: active operator-driven observability. It generates, validates, archives, displays, diffs, and timelines local status snapshots. It does not run a daemon or auto-remediate.

### Final Axis / DEMON / VMA

- `scripts/run_final_axis.py`
- `scripts/run_drift_energy_monitor.py`
- `scripts/vma_continuity_benchmark.ps1`
- `scripts/vma_record_session.ps1`
- `scripts/vma_record_session.py`

Status: active proof/runtime commands. They are isolated and should remain separate from LIVE CASE LOOP until the entrypoint boundary is clear.

### Local Operator Stack / Local House

- `KODEKS_BRAT_START.bat`
- `KODEKS_LOCAL_CHAT.bat`
- `KODEKS_LOCAL_CHAT_SMART.bat`
- `TDK_LOCAL_HOUSE_START.bat`
- `TDK_LOCAL_HOUSE_STOP.bat`
- `scripts/start_local_house.ps1`
- `scripts/stop_local_house.ps1`
- `scripts/start_local_house_wsl.sh`
- `scripts/stop_local_house_wsl.sh`
- `scripts/local_house_status.py`
- `scripts/monitor_local_house.ps1`
- `scripts/backup_local_house.ps1`
- `scripts/recover_local_house.ps1`
- `scripts/local_operator_audit.py`
- `scripts/run_local_operator_audit.ps1`
- `scripts/kodeks_local_chat.py`
- `scripts/master_system_sync.ps1`

Status: active local operator tooling. Standard ports documented:

- `3000` Open WebUI
- `11434` Ollama
- `8001` KODEKS API
- `8010` TDK backend
- `5174` TDK frontend
- `6379` Redis
- `9092` Kafka
- `2181` Zookeeper

## 3. Found Dashboards / Demo UI

| UI | Path | Status | Reuse Potential |
| --- | --- | --- | --- |
| Retina Lite terminal | `scripts/show_control_plane.ps1` | Active | First read-only Control Plane UI. Strong fit for live ops observability. |
| Retina Timeline Lite | `scripts/show_control_plane_timeline.ps1` | Active | History review. Good fit for case timeline preview. |
| Control Plane UX blueprint | `docs/blueprints/tdk_control_plane_ux.md` | Documentation | Direction for future dashboard. |
| KODEKS HTML forms/admin | `app/api/server.py` | Active server-rendered UI | Existing intake/admin/report path. Good immediate entrypoint candidate. |
| PyInstaller GUI artifact | `gui.py`, `gui.spec`, `dist/gui.exe`, `build/gui/xref-gui.html` | Legacy/demo | Exists as local GUI artifact; classify as legacy until manually reviewed. |
| TDK Front React dashboard | `C:\TDK\TDK_front\src\App.jsx`, `AnchorGridDashboard.jsx` | Active/demo | Strongest existing web dashboard. Currently AnchorGrid-first. |
| TDK Platform Next | `C:\TDK\TDK_platform_next` | Future/demo | Possible product shell, not yet connected to KODEKS state. |
| ZT&SI Gateway UI | `C:\ztsi-stability-gateway\ui` | Separate demo UI | Runtime cockpit with mock snapshot/events. Good inspiration, not direct dependency yet. |

## 4. Found Gateways / Ingest / API / Web

### KODEKS API

Path: `app/api/server.py`

Found routes include:

- `GET /`
- `GET /anchorgrid`
- `POST /anchorgrid/analyze`
- `POST /anchorgrid/analyze-form`
- `POST /form-analyze`
- `GET /admin/orders`
- `GET /admin/generate/{order_id}`
- `GET /admin/retry-mail/{order_id}`
- `POST /analyze`
- `POST /analyze-paid`
- `GET /analyze-simple`

This is the closest in-repo gateway to a live case loop because it already has intake, report generation, order storage, admin review, email notification, and PDF outputs.

### TDK Backend

Path: `C:\TDK\TDK_backend`

Found routes/modules include:

- health: `/health`, `/api/v1/health`, `/zdrowie`
- auth: `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/me`
- subscriptions: `/subscriptions/activate`, `/subscriptions/subscription-check`
- modules: `/modules/`, `/modules/{module_id}`
- GPT bridge: `/gpt_bridge/open`
- cases: `/api/v1/cases`, `/api/v1/cases/{case_id}`, artifacts and download
- demo: `/api/v1/demo/seed-case`
- AnchorGrid: `/analyze`, `/api/v1/analyze`, `/analyze/pdf`, `/api/v1/analyze/pdf`

This is the strongest external candidate for the product/live ops gateway. It already has case management and a platform boundary.

### TDK Frontend

Path: `C:\TDK\TDK_front`

Found API client:

- default `VITE_API_URL`
- auth, subscriptions, modules, GPT bridge
- AnchorGrid `POST /api/v1/analyze`
- AnchorGrid PDF `POST /api/v1/analyze/pdf`

This is the strongest existing dashboard to reuse if LIVE CASE LOOP should be product-facing quickly.

### ZT&SI Stability Gateway

Path: `C:\ztsi-stability-gateway`

Found runtime areas:

- gateway: coherence, drift, firewall, governance, lineage, runtime, state
- intelligence: contradiction, recursive instability, semantic drift, scoring
- memory: graph, lineage graph, rollback, semantic memory, snapshots
- policy: engine, evaluator, registry, rules, severity
- stabilization: correction, normalization, projection, recovery
- telemetry: aggregation, events, health, metrics, store
- API/server and UI runtime dashboard
- validation/replay/evidence packs

This is highly relevant to LIVE CASE LOOP, but it should be integrated by adapter or copied as an explicit vendor/internal dependency only after a boundary decision.

## 5. Found Architecture Documents

### In `C:\KODEKS`

- `docs/control_plane_overview.md`
- `docs/final_axis_runtime.md`
- `docs/drift_energy_monitor.md`
- `docs/order-storage-migration.md`
- `docs/system-zablotny-online.md`
- `docs/blueprints/tdk_control_plane_ux.md`
- `docs/architecture/project_alignment_after_reset.md`
- `docs/architecture/ztsi_control_plane_alignment.md`
- `docs/architecture/vma_runtime_alignment.md`
- `docs/specs/vma_uscp_canonical_notes.md`
- `docs/reports/drift_energy_monitor.md`
- `docs/reports/first_real_continuity_win.md`
- `docs/reports/vma_runtime_mvp.md`
- `docs/reports/vma_real_user_validation.md`
- `docs/runbooks/*`
- `docs/local-audits/*`

### External Architecture Sources

- `C:\ztsi-stability-gateway\docs\*`
- `C:\ztsi-stability-gateway\observability\*`
- `C:\ztsi-stability-gateway\validation\*`
- operator-mentioned PDFs under Desktop ServicePlatform folders

## 6. Found Runtime State / Data Folders

### In `C:\KODEKS`

| Folder | Classification | Notes |
| --- | --- | --- |
| `state/control_plane_status.json` | Runtime state | Ignored by Git. Current Control Plane truth snapshot. |
| `state/history/*.json` | Runtime history memory | Ignored by Git. Snapshot archive. |
| `data/final_axis` | Runtime/sample outputs | JSONL runtime log, sample events, operational report. |
| `data/drift_energy_monitor` | Runtime/sample outputs | Runtime log, sample snapshots, operational report. |
| `data/vma` | Runtime continuity outputs | Continuity reports, state, sessions. Ignored by Git. |
| `data/orders` | Runtime business data | Local order/case intake records. Treat as local operational data. |
| `data/reports` | Runtime generated reports | PDF/TXT report outputs. Treat as local/generated data. |
| `data/sessions` | Runtime CLI sessions | Local KODEKS session records. |
| `data/operator` | Operator config/state | Local operator model/runtime JSON. |
| `data/logs` | Runtime logs | Mail failure and runtime logs. |
| `logs/local-house` | Runtime process logs | Local house process logs and PIDs. |
| `backups/` | Local backups | Should stay out of Git by default. |

### Schemas / Samples / Tests

- `schemas/control_plane_status.schema.json`
- `schemas/drift_energy_monitor.schema.yaml`
- `schemas/vma_runtime.schema.yaml`
- `sample_data/drift_energy_event.json`
- `sample_data/vma_turn_example.json`
- `sample_data/vma_continuity_session.json`
- `sample_data/vma_real_session_template.json`
- `tests/test_anchorgrid_engine.py`
- `tests/test_final_axis_runtime.py`
- `tests/test_drift_energy_monitor.py`
- `tests/test_vma_runtime.py`
- `tests/test_vma_continuity_win.py`
- `tests/test_vma_session_recorder.py`

These are code/test fixtures and can be reused for deterministic LIVE CASE LOOP proofing.

## 7. What Is Active

Active and usable now:

- KODEKS API / form / admin / report generation in `app/api/server.py`
- KODEKS CLI in `main.py`
- Control Plane snapshot, validation, Retina Lite, history, diff, timeline, actions
- Final Axis runtime prototype
- isolated Drift Energy Monitor observability module
- preserved DEMON_CORE package
- VMA runtime MVP and continuity benchmark
- VMA manual real-session recorder
- AnchorGrid BESS advisory engine
- Local Operator Stack scripts
- Master System Sync inventory
- TDK backend and TDK frontend as external local product stack

## 8. What Is Demo

Demo or proof-stage:

- ZT&SI Stability Gateway UI and runtime cockpit
- TDK Front AnchorGrid dashboard as product-facing demo
- TDK Platform Next shell
- PyInstaller GUI artifact under `dist/gui.exe`
- VMA continuity benchmark sample sessions
- Final Axis sample events and reports
- Drift Energy sample event/report
- AnchorGrid web dashboard in the external TDK frontend

These are useful, but should not all become entrypoints at once.

## 9. What Is Dead / Legacy / Needs Review

Potential legacy or review-needed artifacts:

- `gui.py`, `gui.spec`, `dist/gui.exe`, `build/gui/xref-gui.html`
- `Nowy dokument tekstowy.txt`
- old generated PDFs/TXT under `data/reports`
- old local sessions under `data/sessions`
- local backups under `backups/`
- broad external Witness/EXIM/TAJNE roots that were discovered but not inventoried deeply

Do not delete them in this phase. Mark them as inventory targets for a later cleanup pass.

## 10. What Can Be Reused For LIVE CASE LOOP

Best reuse candidates:

- KODEKS API intake/admin/report flow as the fastest in-repo case loop.
- TDK backend `cases` API as the strongest product-grade case memory base.
- TDK frontend AnchorGrid dashboard as the fastest existing visual entrypoint.
- Control Plane snapshot/status/history as live ops observability.
- DEMON / Drift Energy Monitor for drift, risk, economic loss, AI conflict, and state-machine panels.
- VMA runtime/session recorder for continuity UX and recovery after interruptions.
- Final Axis for traceable decisions, confinement, operator override support, and cyber-physical boundary rules.
- AnchorGrid for BESS/PV/EMS-adjacent advisory inside cases.
- `data/orders`, `data/reports`, `data/sessions`, `data/vma` as existing local memory patterns.
- `ztsi-stability-gateway` concepts for governance/firewall/lineage, but only through an explicit integration boundary.

## 11. What Must Stay Untouched

Leave untouched unless a specific integration task says otherwise:

- `app/drift_energy_monitor` legacy DEMON package
- `app/final_axis` runtime behavior
- `app/vma` runtime and session recorder logic
- Control Plane runtime contracts and exit-code behavior
- runtime data under `data/`, `state/`, `logs/`, and `backups/`
- external `C:\TDK` and `C:\ztsi-stability-gateway` sources
- PDF architecture sources
- generated customer/order/report data

The next LIVE CASE LOOP step should add adapters or documentation first, not mutate these foundations.

## 12. Recommended Integration

### Existing Gateway / Dashboard -> Live Ops

Use the existing gateway/dashboard before creating a new one:

1. For shortest repo-only proof, start from `app/api/server.py`.
2. For product-shaped proof, use `C:\TDK\TDK_backend` cases API and `C:\TDK\TDK_front`.
3. Keep `C:\ztsi-stability-gateway` separate as a governance/runtime reference until the live ops boundary is explicit.

Recommended first bridge:

- one operator command or route that creates a case,
- attaches an analysis/report artifact,
- records a local trace,
- shows read-only status through Control Plane.

### Control Plane -> Observability

Control Plane should remain the read-only truth layer:

- current component status,
- snapshot validation,
- history archive,
- timeline and diff,
- operator actions as preview/confirmed only.

LIVE CASE LOOP should emit status artifacts that Control Plane can read later. Control Plane should not become the case engine.

### VMA -> Continuity UX

Use VMA to preserve operational continuity:

- map case conversation structure,
- preserve current topic/objective/layer,
- detect interruptions/confusion,
- produce continuity summaries,
- support operator re-entry after drift.

VMA should not decide the case outcome.

### DEMON -> Drift / Risk

Use DEMON / Drift Energy Monitor for:

- coherence index,
- runtime entropy,
- energy loss factor,
- economic drift,
- AI conflict ratio,
- diagnostic events,
- risk level,
- state machine status.

DEMON should not trigger automatic remediation.

### Memory / State -> Case Memory

Use existing local memory patterns:

- `data/orders` for intake/order facts,
- `data/reports` for generated outputs,
- `data/sessions` for KODEKS traces,
- `data/vma/sessions` for continuity traces,
- `state/history` for system status history.

Longer term, the TDK backend cases API is the better structured case memory home.

## Shortest Path To One Operator Entrypoint

Recommended shortest path:

1. Keep `.\scripts\control_plane.ps1` as the system readiness command.
2. Keep `.\scripts\start_local_house.ps1` / `TDK_LOCAL_HOUSE_START.bat` as the local runtime launcher.
3. Choose exactly one case workspace:
   - repo-only: KODEKS FastAPI at `http://127.0.0.1:8001`
   - product stack: TDK frontend at `http://127.0.0.1:5174` backed by TDK backend at `http://127.0.0.1:8010`
4. Add one future `live_case_loop` proof that reads/writes only its own case artifact first.
5. Let Control Plane observe it after the proof is stable.

Do not create a third dashboard unless the existing frontend is rejected.

## Should LIVE CASE LOOP Use Existing Gateway / Dashboard?

Recommendation: yes, but in two steps.

First executable proof:

- isolated runtime proof inside `C:\KODEKS`, using sample/local case data;
- no UI, no external stack dependency;
- output JSON/Markdown case trace.

Second integration:

- connect the proof to `C:\TDK\TDK_backend` cases API or KODEKS API forms;
- display read-only status in TDK frontend or Control Plane Retina.

This reduces integration risk while preserving the existing gateway/dashboard investment.

## Isolated Runtime Proof vs Existing Gateway

Best decision:

- build the smallest isolated LIVE CASE LOOP proof first;
- immediately design it so it can attach to the existing TDK backend cases API;
- do not build a new UI in the proof phase.

Reason:

- the repo already has many stable runtime layers;
- the external product stack already has case/dashboard primitives;
- direct coupling too early could break working local house flows.

## Integration Risks

- Fragmentation risk: KODEKS API, TDK backend, TDK frontend, Next platform, and ZT&SI gateway can become competing entrypoints.
- Data boundary risk: runtime outputs under `data/` and `state/` include local operational history and should not be committed casually.
- Secret/config risk: `.env.example` files exist, but real secrets must stay outside Git. `SECRET_KEY`, `DATABASE_URL`, SMTP, API keys, and frontend API URLs need clear handling.
- Authority risk: Final Axis, DEMON, VMA, and ZT&SI gateway must remain observability/advisory until operator approval gates are explicit.
- Dashboard risk: building a new UI before choosing between KODEKS API HTML, TDK Front, and ZT&SI UI will increase chaos.
- External dependency risk: `C:\TDK` and `C:\ztsi-stability-gateway` are outside the repo; integration needs versioning or a documented boundary.
- Legacy risk: old GUI/build/report/session artifacts may confuse operators if treated as active product code.
- Live ingest risk: EMS/PV/BESS telemetry must be schema-validated and read-only before any control path exists.

## Direction Decision Before LIVE CASE LOOP

Use this rule:

```text
Models generate, Control Plane observes, operator decides.
```

For LIVE CASE LOOP:

- case runtime may generate analysis and reports;
- Control Plane may observe status and trace;
- DEMON may score drift/risk;
- VMA may preserve continuity;
- Final Axis may enforce trace/confinement doctrine;
- operator remains the authority.

