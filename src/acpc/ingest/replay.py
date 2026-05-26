from dataclasses import dataclass, field
from typing import Dict
from .wal import WriteAheadLog

@dataclass
class SiteRuntimeState:
    site_id: str
    last_lamport: int = 0
    last_sequence_by_source: Dict[str, int] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    event_count: int = 0

def deterministic_order(events):
    return sorted(events, key=lambda e: (int(e.lamport), float(e.timestamp), e.site_id, e.source_id, int(e.sequence), e.event_id))

def apply_event(state_by_site, event):
    state = state_by_site.setdefault(event.site_id, SiteRuntimeState(event.site_id))
    last_seq = state.last_sequence_by_source.get(event.source_id, 0)
    if event.sequence <= last_seq:
        return
    state.metrics.update(event.metrics)
    state.last_lamport = max(state.last_lamport, event.lamport)
    state.last_sequence_by_source[event.source_id] = event.sequence
    state.event_count += 1

def replay_events(events):
    state_by_site, seen = {}, set()
    for event in deterministic_order(events):
        if event.event_id in seen:
            continue
        seen.add(event.event_id)
        apply_event(state_by_site, event)
    return state_by_site

def replay_wal(wal_path: str):
    wal = WriteAheadLog(wal_path)
    return replay_events(wal.read_all())
