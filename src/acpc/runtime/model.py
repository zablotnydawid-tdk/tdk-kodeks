
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple
import hashlib
import json
import time


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class VersionVector:
    """
    Per-origin causal vector.

    Example:
        {"node-a": 4, "node-b": 9}

    Means: state includes all events from node-a up to seq 4
    and all events from node-b up to seq 9.
    """
    clock: Mapping[str, int] = field(default_factory=dict)

    def get(self, node_id: str) -> int:
        return int(self.clock.get(node_id, 0))

    def increment(self, node_id: str) -> "VersionVector":
        c = dict(self.clock)
        c[node_id] = c.get(node_id, 0) + 1
        return VersionVector(c)

    def merge(self, other: "VersionVector") -> "VersionVector":
        keys = set(self.clock) | set(other.clock)
        return VersionVector({k: max(self.get(k), other.get(k)) for k in keys})

    def dominates(self, other: "VersionVector") -> bool:
        keys = set(self.clock) | set(other.clock)
        return all(self.get(k) >= other.get(k) for k in keys)

    def to_dict(self) -> Dict[str, int]:
        return dict(self.clock)


@dataclass(frozen=True)
class Delta:
    """
    Idempotent mutation to a partition-local graph/state.

    op:
      - set: value replaces path
      - delete: remove path
      - increment: numeric addition
      - append_unique: add item to list if not present
    """
    op: str
    path: Tuple[str, ...]
    value: Any = None

    def fingerprint(self) -> str:
        return stable_hash({"op": self.op, "path": self.path, "value": self.value})


@dataclass(frozen=True)
class Event:
    """
    Event = ordered, replayable delta envelope.

    origin_seq: strictly increasing sequence per origin node.
    lamport: logical clock assigned by sender.
    event_id: deterministic id from origin, seq, partition and delta hash.
    depends_on: vector visible to sender before this event.
    """
    partition_id: str
    origin_node: str
    origin_seq: int
    lamport: int
    delta: Delta
    depends_on: VersionVector
    timestamp_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    event_id: Optional[str] = None

    def with_id(self) -> "Event":
        if self.event_id:
            return self
        eid = stable_hash({
            "partition_id": self.partition_id,
            "origin_node": self.origin_node,
            "origin_seq": self.origin_seq,
            "lamport": self.lamport,
            "delta": self.delta.fingerprint(),
        })
        return Event(
            partition_id=self.partition_id,
            origin_node=self.origin_node,
            origin_seq=self.origin_seq,
            lamport=self.lamport,
            delta=self.delta,
            depends_on=self.depends_on,
            timestamp_ms=self.timestamp_ms,
            event_id=eid,
        )

    def ordering_key(self) -> Tuple[int, str, int, str]:
        """
        Deterministic total order.

        Causal order is checked separately with version vectors.
        Ties are resolved by origin_node, origin_seq, event_id.
        """
        e = self.with_id()
        return (e.lamport, e.origin_node, e.origin_seq, e.event_id or "")


@dataclass(frozen=True)
class Snapshot:
    partition_id: str
    state: Dict[str, Any]
    checkpoint: VersionVector
    last_lamport: int
    applied_event_ids: Tuple[str, ...]
    content_hash: str = ""

    def with_hash(self) -> "Snapshot":
        h = stable_hash({
            "partition_id": self.partition_id,
            "state": self.state,
            "checkpoint": self.checkpoint.to_dict(),
            "last_lamport": self.last_lamport,
            "applied_event_ids": sorted(self.applied_event_ids),
        })
        return Snapshot(
            partition_id=self.partition_id,
            state=self.state,
            checkpoint=self.checkpoint,
            last_lamport=self.last_lamport,
            applied_event_ids=self.applied_event_ids,
            content_hash=h,
        )
