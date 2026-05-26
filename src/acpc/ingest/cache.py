from collections import deque
from .events import PVSampleEvent

class LocalEdgeCache:
    def __init__(self, max_size: int = 10000):
        self.cache = deque(maxlen=int(max_size))

    def store(self, event: PVSampleEvent) -> None:
        self.cache.append(event)

    def get_snapshot(self):
        return [e.to_dict() for e in self.cache]

    def __len__(self):
        return len(self.cache)
