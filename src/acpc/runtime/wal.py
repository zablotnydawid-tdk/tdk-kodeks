
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List
import json

from .model import Delta, Event, VersionVector, canonical_json


class WAL:
    """
    Append-only JSONL write-ahead log.

    Each line is one event envelope. fsync is intentionally optional in MVP;
    production should fsync based on durability policy.
    """
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def append(self, event: Event) -> None:
        e = event.with_id()
        with self.path.open("a", encoding="utf-8") as f:
            f.write(canonical_json(event_to_dict(e)) + "\n")

    def read_all(self) -> List[Event]:
        events = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    events.append(event_from_dict(json.loads(line)))
        return events


def event_to_dict(e: Event) -> dict:
    e = e.with_id()
    return {
        "partition_id": e.partition_id,
        "origin_node": e.origin_node,
        "origin_seq": e.origin_seq,
        "lamport": e.lamport,
        "delta": {"op": e.delta.op, "path": list(e.delta.path), "value": e.delta.value},
        "depends_on": e.depends_on.to_dict(),
        "timestamp_ms": e.timestamp_ms,
        "event_id": e.event_id,
    }


def event_from_dict(d: dict) -> Event:
    return Event(
        partition_id=d["partition_id"],
        origin_node=d["origin_node"],
        origin_seq=int(d["origin_seq"]),
        lamport=int(d["lamport"]),
        delta=Delta(op=d["delta"]["op"], path=tuple(d["delta"]["path"]), value=d["delta"].get("value")),
        depends_on=VersionVector(d.get("depends_on", {})),
        timestamp_ms=int(d.get("timestamp_ms", 0)),
        event_id=d.get("event_id"),
    ).with_id()
