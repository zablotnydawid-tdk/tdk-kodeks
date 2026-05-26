
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, Tuple

from .model import Delta, Event, VersionVector


class ConflictPolicy:
    """
    Deterministic conflict policy.

    Default:
      1. causal stale events are ignored if the same origin seq already applied
      2. set/delete conflicts use deterministic last-writer-wins by event ordering key
      3. increment and append_unique are commutative/idempotent
      4. domain hooks can override for specific path prefixes
    """
    def resolve_set(self, old_meta, new_event: Event) -> bool:
        if old_meta is None:
            return True
        return new_event.ordering_key() >= old_meta


class PartitionState:
    def __init__(self, partition_id: str, initial: Dict[str, Any] | None = None):
        self.partition_id = partition_id
        self.data: Dict[str, Any] = deepcopy(initial or {})
        self.vector = VersionVector({})
        self.last_lamport = 0
        self.applied_event_ids: set[str] = set()
        self.path_meta: Dict[Tuple[str, ...], tuple] = {}
        self.conflicts: list[dict] = []
        self.policy = ConflictPolicy()

    def clone_data(self) -> Dict[str, Any]:
        return deepcopy(self.data)

    def can_apply(self, event: Event) -> bool:
        event = event.with_id()
        if event.event_id in self.applied_event_ids:
            return False
        # strict per-origin sequence continuity for deterministic replay
        expected = self.vector.get(event.origin_node) + 1
        return event.origin_seq == expected

    def needs_buffering(self, event: Event) -> bool:
        expected = self.vector.get(event.origin_node) + 1
        return event.origin_seq > expected

    def is_stale(self, event: Event) -> bool:
        return event.origin_seq <= self.vector.get(event.origin_node)

    def apply(self, event: Event) -> bool:
        event = event.with_id()
        if event.event_id in self.applied_event_ids:
            return False
        if self.is_stale(event):
            return False
        if self.needs_buffering(event):
            raise ValueError(f"event gap for {event.origin_node}: got {event.origin_seq}, expected {self.vector.get(event.origin_node)+1}")

        self._apply_delta(event)
        self.vector = self.vector.merge(VersionVector({event.origin_node: event.origin_seq}))
        self.last_lamport = max(self.last_lamport, event.lamport)
        self.applied_event_ids.add(event.event_id)
        return True

    def _apply_delta(self, event: Event) -> None:
        d = event.delta
        if not d.path:
            raise ValueError("delta path cannot be empty")

        parent = self.data
        for key in d.path[:-1]:
            if key not in parent or not isinstance(parent[key], dict):
                parent[key] = {}
            parent = parent[key]
        leaf = d.path[-1]

        if d.op == "set":
            old_meta = self.path_meta.get(d.path)
            if self.policy.resolve_set(old_meta, event):
                parent[leaf] = deepcopy(d.value)
                self.path_meta[d.path] = event.ordering_key()
            else:
                self.conflicts.append({"path": d.path, "winner": old_meta, "loser": event.ordering_key()})

        elif d.op == "delete":
            old_meta = self.path_meta.get(d.path)
            if self.policy.resolve_set(old_meta, event):
                parent.pop(leaf, None)
                self.path_meta[d.path] = event.ordering_key()
            else:
                self.conflicts.append({"path": d.path, "winner": old_meta, "loser": event.ordering_key()})

        elif d.op == "increment":
            current = parent.get(leaf, 0)
            if not isinstance(current, (int, float)):
                raise TypeError(f"cannot increment non-numeric path {d.path}")
            parent[leaf] = current + d.value

        elif d.op == "append_unique":
            current = parent.setdefault(leaf, [])
            if not isinstance(current, list):
                raise TypeError(f"cannot append_unique to non-list path {d.path}")
            if d.value not in current:
                current.append(deepcopy(d.value))

        else:
            raise ValueError(f"unknown delta op: {d.op}")
