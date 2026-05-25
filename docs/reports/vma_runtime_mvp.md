# VMA Runtime MVP

The VMA Runtime MVP is an isolated executable continuity proof.

Implemented module:

```text
app/vma/runtime.py
```

## Scope

The MVP supports:

- `detect_structure()`
- `map_topology()`
- `inject_anchors()`
- `estimate_cognitive_load()`
- `recover()`
- `process_turn()`

## Runtime State

The runtime state contains:

- `active`
- `mode`
- `current_topic`
- `current_layer`
- `parent_context`
- `active_objective`
- `known_hierarchy`
- `dependency_chain`
- `compression_level`
- `cognitive_load`
- `last_stable_anchor`
- `recovery_required`

## Safety Boundary

The MVP has no UI, dashboard, cloud, SaaS, scheduler, daemon, or autonomous remediation. It does not refactor or call existing runtime layers. It is only a local continuity proof.

## Continuity Proof

`process_turn()` returns:

- `voice_stable_output`
- updated runtime `state`
- detected `structure`
- mapped `topology`
- injected `anchors`
- continuity `telemetry`

The proof demonstrates that a voice-mode turn can be converted into stable continuity state and a replay-friendly topology without changing any external system.

