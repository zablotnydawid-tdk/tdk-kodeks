import os
from pathlib import Path
from typing import Iterable, Set
from .events import PVSampleEvent

class WriteAheadLog:
    def __init__(self, filepath: str = "wal_live.log"):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self._seen: Set[str] = set()
        if self.filepath.exists():
            for event in self.read_all():
                if event.event_id:
                    self._seen.add(event.event_id)

    def append(self, event: PVSampleEvent) -> bool:
        if not event.event_id:
            event = event.with_event_id()
        if event.event_id in self._seen:
            return False
        with self.filepath.open("a", encoding="utf-8") as f:
            f.write(event.to_json() + "\n")
            f.flush()
            os.fsync(f.fileno())
        self._seen.add(event.event_id)
        return True

    def read_all(self) -> Iterable[PVSampleEvent]:
        if not self.filepath.exists():
            return []
        events = []
        with self.filepath.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    events.append(PVSampleEvent.from_json(line.strip()))
        return events
