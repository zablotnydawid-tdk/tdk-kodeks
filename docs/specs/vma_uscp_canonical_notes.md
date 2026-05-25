# VMA-USCP Canonical Notes

This file is the repository-local canonical text source for VMA-USCP / Voice Mode Adapter alignment work.

Source PDF:

```text
C:\Users\zablo\Desktop\ServicePlatform Projekt TDK&ProService\Vocal_Mode_adaptiv_ZT&SI\VOICE MODE ADAPTER_ZT&SI.pdf
```

Repository note: the PDF is available locally, but the current execution environment cannot extract reliable text from it. These notes capture the canonical working sections needed by KODEKS so future runtime work has a stable text reference inside Git. If the PDF is later exported to Markdown/text, this file should be reconciled section by section.

## Executive Definition

VMA-USCP is a Voice Mode Adapter and continuity runtime concept for preserving operational coherence across voice-driven, model-assisted, and operator-driven sessions.

The adapter does not own final authority. Its role is to observe structure, detect continuity gaps, map conversational/runtime topology, propose anchors, emit continuity telemetry, and preserve replayable state for operator review.

Primary doctrine:

```text
models generate, Control Plane observes, operator decides
```

The VMA runtime proof should therefore be local, deterministic, replayable, and operator-controlled.

## Core Problem Domain

Voice and conversational workflows degrade when session context is fragmented across:

- model responses,
- operator intent,
- runtime state,
- task history,
- dashboard state,
- local files,
- telemetry,
- recovery handoffs,
- incomplete memory.

The core problem is continuity loss: the system may still produce language, but the operational thread can detach from prior structure, evidence, constraints, and operator decisions.

VMA-USCP addresses this by tracking:

- structure continuity,
- topology continuity,
- anchor continuity,
- replay continuity,
- recovery continuity,
- governance continuity.

## Core Adapter Layers

The adapter can be separated into minimal layers:

1. Structure Detection
   - detects current session fragments,
   - identifies available runtime objects,
   - marks missing or ambiguous structure.

2. Topology Mapping
   - maps nodes, edges, context groups, and dependencies,
   - separates operator intent from model output,
   - keeps runtime modules distinct.

3. Anchor Injection
   - proposes stable anchors for continuity,
   - does not mutate external systems automatically,
   - records anchors as local state.

4. Continuity Telemetry
   - emits deterministic counters and status fields,
   - exposes replay status,
   - can later be read by Control Plane.

5. Recovery Mode
   - marks continuity degradation,
   - prepares operator-visible recovery recommendations,
   - does not execute remediation by itself.

6. Replay Layer
   - reconstructs continuity state from recorded session events,
   - verifies deterministic recovery of topology,
   - produces a local report.

## Runtime State

Minimum runtime state should be a local JSON document:

```text
state/vma/continuity_state.json
```

Suggested fields:

```text
schema_version
generated_at
session_id
continuity_state
structure
topology
anchors
gaps
telemetry
recovery_mode
operator_action_required
source_events
```

Runtime state must be local by default and treated as generated state, not source code.

## Execution Pipeline

Minimum execution pipeline:

1. Load session input.
2. `detect_structure()`
3. `map_topology()`
4. `inject_anchors()`
5. `build_continuity_state()`
6. `emit_continuity_telemetry()`
7. Optionally `enter_recovery_mode()`
8. `replay_session()` for deterministic reconstruction.
9. Export JSON state and Markdown replay summary.

Every step should be deterministic for the same input.

## API/Middleware Contract

The first VMA proof should not expose a network API. Its middleware contract should be file and function based:

- input: session JSON,
- output: continuity state JSON,
- output: continuity telemetry dictionary,
- output: Markdown replay report,
- optional future read-only Control Plane status.

Minimal callable contract:

```python
detect_structure(input_event: dict) -> dict
map_topology(structure: dict) -> dict
inject_anchors(topology: dict) -> dict
build_continuity_state(topology: dict, anchors: dict) -> dict
emit_continuity_telemetry(state: dict) -> dict
enter_recovery_mode(state: dict) -> dict
replay_session(session: dict) -> dict
```

No function should call cloud services, start background jobs, alter Control Plane state, or execute operator decisions.

## Reference Implementation Skeleton

Proposed local files for the first executable proof:

```text
app/continuity/vma_runtime.py
schemas/vma_continuity.schema.json
sample_data/vma_continuity_session.json
scripts/run_vma_continuity.py
tests/test_vma_runtime.py
```

Generated local files:

```text
state/vma/continuity_state.json
state/vma/history/continuity_YYYYMMDD_HHMMSS.json
docs/reports/vma_continuity_replay.md
```

The skeleton should remain isolated. It may reuse patterns from Control Plane, FINAL_AXIS, and DEMON, but should not refactor or couple into those modules during the proof phase.

## Governance/Safety Rules

Safety rules:

- no autonomous operator decisions,
- no auto-remediation,
- no scheduler,
- no daemon,
- no cloud sync,
- no SaaS layer,
- no dashboard frontend in the proof phase,
- no multimodal synchronization,
- no enterprise identity layer,
- no mutation of existing runtime modules,
- no Control Plane execution action until VMA proof is deterministic and tested.

Allowed in proof phase:

- local JSON input,
- local JSON output,
- local Markdown report,
- local replay,
- read-only telemetry,
- operator-visible recommendations.

## Certification / Evaluation Metrics

Minimum evaluation metrics:

- `structure_count`
- `topology_node_count`
- `topology_edge_count`
- `anchor_count`
- `missing_anchor_count`
- `continuity_score`
- `replay_status`
- `recovery_mode`
- `operator_action_required`

Minimum pass criteria:

- same input produces same continuity state,
- replay reconstructs the same topology,
- missing anchors are reported,
- recovery mode is marked but does not execute remediation,
- JSON output is parseable,
- Markdown output is operator-readable,
- runtime remains local and isolated.

