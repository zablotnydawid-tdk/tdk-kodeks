# EXIM Operator Flow

## Goal

Collapse the local operator experience from many separate proofs into one visible flow:

```text
START
-> Control Plane snapshot
-> last runtime state
-> active live cases
-> latest continuity state
-> latest drift/risk state
-> recommended operator action
-> optional local launch
```

The entrypoint does not create a new dashboard, runtime, microservice, model router, or orchestration cluster. It reads existing files and delegates optional actions to existing scripts.

## Existing Components Reused

| Layer | Existing Source | Role |
| --- | --- | --- |
| Control Plane | `state/control_plane_status.json`, `scripts/show_control_plane.ps1` | Organism state and component health |
| Retina Timeline Lite | `scripts/show_control_plane_timeline.ps1` | Snapshot history |
| Operator Actions | `scripts/control_plane_actions.ps1` | Preview next maintenance checks |
| Final Axis Runtime | `data/final_axis/runtime_log.jsonl` | Last runtime boundary/action state |
| DEMON / Drift Energy Monitor | `data/drift_energy_monitor/runtime_log.jsonl` | Latest drift/risk analysis |
| VMA Continuity | `data/vma/vma_continuity_state.json` | Continuity score, anchor, recovery status |
| Live Case Loop | `data/live_ops/live_case_result.json`, `scripts/live_case_demo.ps1` | Last active operator-gated case |
| Existing gateway/forms/admin/reports | `app/api/server.py`, storage/report modules | Local application boundary retained for later use |

## Runtime Posture

Default posture:

```text
local-first
terminal-first
read-only by default
observe-only
cloud runtime disabled
SaaS disabled
```

The entrypoint treats missing data as `UNKNOWN`. It does not infer a state from old conversation context.

## Recommendation Logic

Recommended action is deliberately conservative:

- missing required data -> recover missing runtime data first,
- Control Plane errors -> inspect errors and keep observe-only,
- critical DEMON state -> hold autonomous actions and review findings,
- critical live case -> review evidence and operator-gated next actions,
- continuity recovery required -> restore anchor before expansion,
- warnings/unknowns -> run Control Plane verification,
- stable state -> continue observe-only or launch timeline/benchmark for proof.

## SAFE Mode

`SAFE_MODE_DEGRADED_READ_ONLY` is activated when any required runtime artifact is missing:

- Control Plane snapshot,
- Final Axis runtime log,
- VMA continuity state,
- Live Case result,
- DEMON runtime log.

SAFE mode emits recovery hints and blocks any implied autonomous interpretation.

## Continuity-Aware Output

The entrypoint comments on continuity without simulating memory:

- high continuity and no recovery requirement -> anchor preserved,
- recovery required -> restore anchor before expanding scope,
- missing continuity file -> `UNKNOWN`; do not infer operator memory.

## Operator Feeling

The intended operator experience is:

```text
one living local system
```

not:

```text
twenty disconnected proofs
```
