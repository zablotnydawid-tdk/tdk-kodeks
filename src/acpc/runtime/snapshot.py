
from __future__ import annotations

from pathlib import Path
import json

from .model import Snapshot, VersionVector, canonical_json


class SnapshotStore:
    def __init__(self, dir_path: str | Path):
        self.dir = Path(dir_path)
        self.dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, partition_id: str) -> Path:
        safe = partition_id.replace("/", "_")
        return self.dir / f"{safe}.snapshot.json"

    def save(self, snap: Snapshot) -> Snapshot:
        snap = snap.with_hash()
        tmp = self.path_for(snap.partition_id).with_suffix(".tmp")
        final = self.path_for(snap.partition_id)
        tmp.write_text(canonical_json(snapshot_to_dict(snap)), encoding="utf-8")
        tmp.replace(final)
        return snap

    def load(self, partition_id: str) -> Snapshot | None:
        path = self.path_for(partition_id)
        if not path.exists():
            return None
        snap = snapshot_from_dict(json.loads(path.read_text(encoding="utf-8")))
        if snap.with_hash().content_hash != snap.content_hash:
            raise ValueError("snapshot hash mismatch")
        return snap


def snapshot_to_dict(s: Snapshot) -> dict:
    s = s.with_hash()
    return {
        "partition_id": s.partition_id,
        "state": s.state,
        "checkpoint": s.checkpoint.to_dict(),
        "last_lamport": s.last_lamport,
        "applied_event_ids": list(s.applied_event_ids),
        "content_hash": s.content_hash,
    }


def snapshot_from_dict(d: dict) -> Snapshot:
    return Snapshot(
        partition_id=d["partition_id"],
        state=d["state"],
        checkpoint=VersionVector(d["checkpoint"]),
        last_lamport=int(d["last_lamport"]),
        applied_event_ids=tuple(d.get("applied_event_ids", [])),
        content_hash=d.get("content_hash", ""),
    )
