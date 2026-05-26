
from __future__ import annotations
from typing import Iterable
from .models import PVEvent, PVInstallationState
from .reducer import reduce_event
from .reports import build_json_report, build_markdown_report


class PVDiagnosticEngine:
    """Deterministyczny engine diagnostyczny PV dla ACPC Energy Diagnostic MVP."""

    def __init__(self, site_id: str):
        self.state = PVInstallationState(site_id=site_id)

    def apply(self, event: PVEvent) -> PVInstallationState:
        if event.site_id != self.state.site_id:
            raise ValueError(f"event site_id={event.site_id} does not match engine site_id={self.state.site_id}")
        self.state = reduce_event(self.state, event)
        return self.state

    def replay(self, events: Iterable[PVEvent]) -> PVInstallationState:
        # deterministic ordering: lamport, timestamp, event_id/type
        for event in sorted(events, key=lambda e: (e.lamport, e.timestamp_ms, e.stable_id())):
            self.apply(event)
        return self.state

    def json_report(self):
        return build_json_report(self.state)

    def markdown_report(self) -> str:
        return build_markdown_report(self.state)
