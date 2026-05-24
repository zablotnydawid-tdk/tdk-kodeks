from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuntimeState:
    mode: str = "observe"
    confined: bool = False
    drift_score: float = 0.0
    semantic_isometry: float = 1.0
    last_projection: dict[str, Any] = field(default_factory=dict)
    active_boundary: str = "normal"
    cyber_physical_status: str = "disconnected"
    pending_operator_overrides: list[str] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    explanations: list[str] = field(default_factory=list)
    event_count: int = 0

    def snapshot(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "confined": self.confined,
            "drift_score": self.drift_score,
            "semantic_isometry": self.semantic_isometry,
            "last_projection": self.last_projection,
            "active_boundary": self.active_boundary,
            "cyber_physical_status": self.cyber_physical_status,
            "pending_operator_overrides": list(self.pending_operator_overrides),
            "decisions": list(self.decisions),
            "explanations": list(self.explanations),
            "event_count": self.event_count,
        }
