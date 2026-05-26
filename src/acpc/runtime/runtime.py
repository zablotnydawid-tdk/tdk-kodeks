
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

from .model import Delta, Event, Snapshot, VersionVector
from .state import PartitionState
from .wal import WAL
from .snapshot import SnapshotStore


@dataclass
class NodeConfig:
    node_id: str
    data_dir: str
    partitions: tuple[str, ...] = ("default",)


class ACPCNode:
    """
    Node-local runtime.

    Responsibilities:
      - assign Lamport clock and origin sequence
      - append events to WAL before applying
      - apply idempotent deltas in deterministic order
      - buffer out-of-order events until gaps are filled
      - snapshot partition state with checkpoint vector
      - restore from snapshot + replay WAL suffix
    """
    def __init__(self, config: NodeConfig):
        self.config = config
        self.data_dir = Path(config.data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.wal = WAL(self.data_dir / "events.wal.jsonl")
        self.snapshots = SnapshotStore(self.data_dir / "snapshots")
        self.partitions: Dict[str, PartitionState] = {
            p: PartitionState(p) for p in config.partitions
        }
        self.local_seq = 0
        self.lamport = 0
        self.buffers: Dict[str, List[Event]] = {p: [] for p in config.partitions}

    def ensure_partition(self, partition_id: str) -> PartitionState:
        if partition_id not in self.partitions:
            snap = self.snapshots.load(partition_id)
            ps = PartitionState(partition_id, snap.state if snap else None)
            if snap:
                ps.vector = snap.checkpoint
                ps.last_lamport = snap.last_lamport
                ps.applied_event_ids = set(snap.applied_event_ids)
            self.partitions[partition_id] = ps
            self.buffers[partition_id] = []
        return self.partitions[partition_id]

    def emit(self, partition_id: str, delta: Delta) -> Event:
        ps = self.ensure_partition(partition_id)
        self.local_seq += 1
        self.lamport = max(self.lamport, ps.last_lamport) + 1
        event = Event(
            partition_id=partition_id,
            origin_node=self.config.node_id,
            origin_seq=self.local_seq,
            lamport=self.lamport,
            delta=delta,
            depends_on=ps.vector,
        ).with_id()
        self.wal.append(event)
        self.apply_event(event)
        return event

    def receive(self, event: Event) -> None:
        event = event.with_id()
        self.lamport = max(self.lamport, event.lamport) + 1
        self.wal.append(event)
        self.apply_event(event)

    def apply_event(self, event: Event) -> bool:
        ps = self.ensure_partition(event.partition_id)

        if event.event_id in ps.applied_event_ids or ps.is_stale(event):
            return False

        if ps.needs_buffering(event):
            self.buffers[event.partition_id].append(event)
            self.buffers[event.partition_id].sort(key=lambda e: e.ordering_key())
            return False

        applied = ps.apply(event)
        self._drain_buffer(event.partition_id)
        return applied

    def _drain_buffer(self, partition_id: str) -> None:
        ps = self.ensure_partition(partition_id)
        changed = True
        while changed:
            changed = False
            remaining = []
            for e in sorted(self.buffers.get(partition_id, []), key=lambda x: x.ordering_key()):
                if e.event_id in ps.applied_event_ids or ps.is_stale(e):
                    changed = True
                    continue
                if ps.can_apply(e):
                    ps.apply(e)
                    changed = True
                else:
                    remaining.append(e)
            self.buffers[partition_id] = remaining

    def snapshot(self, partition_id: str) -> Snapshot:
        ps = self.ensure_partition(partition_id)
        snap = Snapshot(
            partition_id=partition_id,
            state=ps.clone_data(),
            checkpoint=ps.vector,
            last_lamport=ps.last_lamport,
            applied_event_ids=tuple(sorted(ps.applied_event_ids)),
        )
        return self.snapshots.save(snap)

    def restore(self, partition_id: str) -> None:
        snap = self.snapshots.load(partition_id)
        if snap:
            ps = PartitionState(partition_id, snap.state)
            ps.vector = snap.checkpoint
            ps.last_lamport = snap.last_lamport
            ps.applied_event_ids = set(snap.applied_event_ids)
        else:
            ps = PartitionState(partition_id)
        self.partitions[partition_id] = ps
        self.buffers[partition_id] = []

        # Replay only events not covered by snapshot/applied index.
        for e in sorted(self.wal.read_all(), key=lambda x: x.ordering_key()):
            if e.partition_id == partition_id:
                self.apply_event(e)

    def state(self, partition_id: str) -> dict:
        return self.ensure_partition(partition_id).clone_data()

    def vector(self, partition_id: str) -> dict:
        return self.ensure_partition(partition_id).vector.to_dict()
