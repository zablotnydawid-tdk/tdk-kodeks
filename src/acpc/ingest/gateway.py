import time
from collections import defaultdict
from typing import Optional
from .cache import LocalEdgeCache
from .clock import LamportClock
from .events import PVSampleEvent
from .normalizers import normalize
from .wal import WriteAheadLog

class ACPCLiveIngestGateway:
    def __init__(self, wal_path: str = "wal_live.log", cache_size: int = 10000, clock: Optional[LamportClock] = None):
        self.wal = WriteAheadLog(wal_path)
        self.cache = LocalEdgeCache(cache_size)
        self.clock = clock or LamportClock()
        self._seq = defaultdict(int)

    def ingest(self, raw_data, protocol: str, site_id: str, source_id: Optional[str] = None,
               timestamp: Optional[float] = None, remote_lamport: Optional[int] = None) -> PVSampleEvent:
        protocol = protocol.upper()
        source = source_id or f"{site_id}:{protocol}"
        self._seq[source] += 1
        lamport = self.clock.tick() if remote_lamport is None else self.clock.update(remote_lamport)
        metrics = normalize(protocol, raw_data)
        event = PVSampleEvent("PV_SAMPLE_RECEIVED", float(timestamp if timestamp is not None else time.time()),
                              site_id, protocol, source, self._seq[source], lamport, metrics).with_event_id()
        if self.wal.append(event):
            self.cache.store(event)
        return event

    def snapshot(self):
        return self.cache.get_snapshot()
