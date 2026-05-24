from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.final_axis.reporting import build_markdown_report
from app.final_axis.sample_events import operator_override_event, sample_events
from app.final_axis.supervisor import FinalAxisSupervisor


LOG_PATH = ROOT / "data" / "final_axis" / "runtime_log.jsonl"
REPORT_PATH = ROOT / "data" / "final_axis" / "operational_report.md"


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()
    supervisor = FinalAxisSupervisor(LOG_PATH)
    for event in sample_events():
        supervisor.ingest(event)
    if supervisor.state.pending_operator_overrides:
        supervisor.ingest(operator_override_event(supervisor.state.pending_operator_overrides[0]))
    build_markdown_report(LOG_PATH, REPORT_PATH)
    print(f"Final Axis runtime log: {LOG_PATH}")
    print(f"Final Axis operational report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
