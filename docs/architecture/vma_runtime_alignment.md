# VMA-USCP Runtime Alignment Blueprint

This document aligns the VMA-USCP / Voice Mode Adapter direction with the current KODEKS runtime. It converts the architecture idea into the smallest executable runtime proof path, without implementing UI, cloud, SaaS, multimodal sync, or enterprise features.

Source context:

- Local PDF reference: `C:\Users\zablo\Desktop\ServicePlatform Projekt TDK&ProService\Vocal_Mode_adaptiv_ZT&SI\VOICE MODE ADAPTER_ZT&SI.pdf`
- Current KODEKS runtime: TDK Control Plane, DEMON / Drift Energy Monitor, FINAL_AXIS, Local Operator Stack, snapshot history, operator flow.

Extraction note: the PDF exists locally, but this environment does not provide `pdftotext`, `mutool`, `qpdf`, or installed Python PDF parsers. A low-level stream inspection did not expose usable document text because the PDF is rendered through Google Docs / Skia streams. This alignment is therefore based on the VMA-USCP concepts named by the operator plus concrete repo state, and should be refined if the PDF text is later exported to Markdown or text.

## 1. What VMA-USCP Already Has Indirectly In The Repo

The repo already contains several primitives that can support a voice continuity runtime:

- Control Plane status contract in `schemas/control_plane_status.schema.json`
- Runtime snapshot generation in `scripts/generate_control_plane_snapshot.ps1`
- Snapshot validation in `scripts/validate_control_plane_snapshot.ps1`
- Retina Lite terminal observability in `scripts/show_control_plane.ps1`
- Snapshot history in `state/history/*.json`
- Timeline and diff views in `scripts/show_control_plane_timeline.ps1` and `scripts/diff_control_plane_snapshots.ps1`
- Manual operator actions in `scripts/control_plane_actions.ps1`
- FINAL_AXIS runtime trace, event bus, reducer, logging, and reports in `app/final_axis`
- DEMON / Drift Energy Monitor scoring and state machine in `app/monitoring/drift_energy_monitor.py`
- Local Operator Flow and Local House scripts under `scripts/` and `docs/runbooks/`

These do not yet form VMA-USCP, but they already prove the key idea: runtime continuity can be represented as structured state, validated snapshots, replayable history, and operator-controlled actions.

## 2. What Exists Only Documentation-Wise

The following VMA-adjacent pieces are documentation or alignment only:

- `docs/architecture/project_alignment_after_reset.md`
- `docs/architecture/ztsi_control_plane_alignment.md`
- `docs/blueprints/tdk_control_plane_ux.md`
- Control Plane dashboard direction
- VMA-USCP continuity runtime concept
- Voice continuity as operator support
- Runtime topology mapping
- Anchor injection model
- Recovery mode for continuity sessions

No executable VMA runtime module exists yet.

## 3. Runtime Primitives Already Available

Existing primitives that can be reused without refactoring:

- JSON state files: local runtime facts can be stored deterministically.
- JSON schema style contracts: Control Plane already validates status shape.
- Markdown reports: current modules export operator-readable traces.
- History archive: snapshots are persisted locally over time.
- Diff and timeline: state changes can be inspected manually.
- Operator action model: preview by default, confirmed write only when explicitly safe.
- FINAL_AXIS trace model: event, decision, state change, confinement, override.
- DEMON scoring model: metrics, risk, diagnostic events, state machine.
- Local audit model: deterministic checks with PASS/FAIL style output.

The first VMA proof should reuse these primitives instead of creating a new platform.

## 4. Modules That Can Be Reused

| Existing Module | Reuse For VMA Runtime Proof |
| --- | --- |
| `scripts/control_plane.ps1` | top-level operator entrypoint pattern |
| `schemas/control_plane_status.schema.json` | status contract style |
| `state/history/` | continuity timeline storage pattern |
| `scripts/diff_control_plane_snapshots.ps1` | replay/diff pattern |
| `scripts/control_plane_actions.ps1` | manual action and preview/confirm doctrine |
| `app/final_axis` | trace, event, reducer, explainability model |
| `app/monitoring/drift_energy_monitor.py` | risk/state-machine/export pattern |
| `docs/runbooks/local-operator-flow.md` | operator handoff model |
| `scripts/master_system_sync.ps1` | topology/inventory precedent |

Reuse should be by pattern first, not direct coupling. The VMA runtime can start isolated and later expose read-only status to Control Plane.

## 5. Existing Telemetry / State / History Mechanisms

Current mechanisms:

- Current Control Plane state:
  - `state/control_plane_status.json`
- Control Plane history:
  - `state/history/control_plane_status_YYYYMMDD_HHMMSS.json`
- FINAL_AXIS runtime outputs:
  - JSONL runtime logs
  - Markdown operational report
- Drift Energy Monitor outputs:
  - JSON export
  - Markdown export
- Operator audits:
  - `docs/local-audits/`
- Git lineage:
  - commits, branch state, origin sync status

VMA should use the same shape:

- current continuity state,
- append-only local history,
- replayable session records,
- Markdown operator report,
- no automatic external sync.

## 6. Connection Model

### Control Plane

VMA should appear first as a read-only future component:

- status: `unknown`, `active`, `warning`, or `error`
- drift/continuity level
- last continuity snapshot
- last replay result
- next operator action

No Control Plane execution action should be added until the runtime proof exists.

### DEMON

DEMON can provide diagnostic risk context:

- coherence pressure,
- runtime entropy,
- AI conflict ratio,
- recovery/degraded mode signal.

VMA should not let DEMON trigger autonomous recovery. It should only read DEMON outputs as continuity evidence.

### Replay / History

VMA continuity proof should be replayable from local files:

- read continuity session events,
- reconstruct topology,
- reapply anchors,
- compare state before/after,
- emit a replay report.

Replay must be deterministic and read-only.

### Operator Flow

VMA belongs after inventory and before recovery:

1. operator runs inventory,
2. VMA detects structure,
3. VMA maps topology,
4. VMA injects anchors into local continuity state,
5. operator reviews continuity telemetry,
6. operator decides whether recovery mode is needed.

## 7. Minimal Executable VMA Runtime MVP

The MVP should be a local CLI runtime with no UI:

- module:
  - `app/continuity/vma_runtime.py`
- schema:
  - `schemas/vma_continuity.schema.json`
- state:
  - `state/vma/continuity_state.json`
- history:
  - `state/vma/history/continuity_YYYYMMDD_HHMMSS.json`
- sample:
  - `sample_data/vma_continuity_session.json`
- CLI:
  - `scripts/run_vma_continuity.py`

Minimum functions:

```python
def detect_structure(input_event: dict) -> dict:
    """Detect available runtime structure without changing it."""

def map_topology(structure: dict) -> dict:
    """Map nodes, edges, anchors, and missing continuity links."""

def inject_anchors(topology: dict) -> dict:
    """Return proposed anchors in state form; do not mutate external systems."""

def build_continuity_state(topology: dict, anchors: dict) -> dict:
    """Create continuity_state.json payload."""

def emit_continuity_telemetry(state: dict) -> dict:
    """Return observable telemetry for Control Plane or report export."""

def enter_recovery_mode(state: dict) -> dict:
    """Mark recovery intent locally; no automatic remediation."""

def replay_session(session: dict) -> dict:
    """Reconstruct continuity state from recorded session events."""
```

## 8. What Not To Build Now

Do not build now:

- dashboard frontend,
- SaaS wrapper,
- cloud sync,
- multimodal synchronization,
- voice capture engine,
- speech-to-text pipeline,
- enterprise identity or tenant system,
- autonomous recovery,
- background daemon,
- scheduler,
- model-driven operator decisions,
- Control Plane write action for VMA.

The point is runtime continuity proof, not product completion.

## 9. Smallest Possible Continuity Proof

The smallest proof can be one command:

```powershell
cd C:\KODEKS
.\.venv\Scripts\python.exe scripts\run_vma_continuity.py --session sample_data\vma_continuity_session.json --replay
```

Expected proof output:

- detected structure count,
- topology nodes and edges,
- injected anchor proposals,
- continuity score,
- recovery mode recommendation,
- JSON state written locally,
- Markdown replay summary generated,
- no external changes.

Success means:

- the same input session produces the same continuity state,
- replay reconstructs the same topology,
- missing anchors are reported,
- operator can inspect the output before doing anything.

## 10. Runtime Implementation Order

1. Define schema
   - `schemas/vma_continuity.schema.json`
   - explicit fields for nodes, edges, anchors, gaps, telemetry, recovery mode.

2. Create sample session
   - small JSON with voice/session fragments represented as neutral events.

3. Implement isolated runtime module
   - `app/continuity/vma_runtime.py`
   - pure functions first.

4. Add CLI replay
   - `scripts/run_vma_continuity.py`
   - read input, write local state, print summary.

5. Add tests
   - deterministic structure detection,
   - topology mapping,
   - anchor injection,
   - replay equivalence,
   - recovery mode marking.

6. Add read-only Control Plane compatibility
   - only after proof passes,
   - status only,
   - no execution action.

## Runtime Skeleton Contract

First runtime skeleton should produce these files locally:

```text
state/vma/continuity_state.json
state/vma/history/continuity_YYYYMMDD_HHMMSS.json
docs/reports/vma_continuity_replay.md
```

It should expose these telemetry fields:

```text
continuity_state
structure_count
topology_node_count
topology_edge_count
anchor_count
missing_anchor_count
replay_status
recovery_mode
operator_action_required
```

## Operating Rule

Models generate, Control Plane observes, operator decides.

For VMA-USCP this means:

- VMA detects and maps continuity;
- VMA proposes anchors;
- Control Plane observes VMA state;
- operator decides whether recovery or integration proceeds.

