import hashlib, json
from dataclasses import dataclass, asdict
from typing import Dict, Any

def _canonical_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

@dataclass(frozen=True)
class PVSampleEvent:
    event_type: str
    timestamp: float
    site_id: str
    protocol: str
    source_id: str
    sequence: int
    lamport: int
    metrics: Dict[str, float]
    event_id: str = ""

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "timestamp": round(float(self.timestamp), 3),
            "site_id": self.site_id,
            "protocol": self.protocol,
            "source_id": self.source_id,
            "sequence": int(self.sequence),
            "lamport": int(self.lamport),
            "metrics": {k: float(v) for k, v in sorted(self.metrics.items())},
        }

    def with_event_id(self) -> "PVSampleEvent":
        digest = hashlib.sha256(_canonical_json(self.canonical_payload()).encode("utf-8")).hexdigest()
        return PVSampleEvent(self.event_type, self.timestamp, self.site_id, self.protocol,
                             self.source_id, self.sequence, self.lamport, self.metrics, digest)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["metrics"] = {k: float(v) for k, v in sorted(self.metrics.items())}
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def from_json(line: str) -> "PVSampleEvent":
        d = json.loads(line)
        return PVSampleEvent(d["event_type"], float(d["timestamp"]), d["site_id"], d["protocol"],
                             d["source_id"], int(d["sequence"]), int(d["lamport"]),
                             {k: float(v) for k, v in d["metrics"].items()}, d.get("event_id", ""))
