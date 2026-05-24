from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.drift_energy_monitor.reporting import build_markdown_report
from app.drift_energy_monitor.sample_data import sample_snapshots
from app.drift_energy_monitor.supervisor import DriftEnergyMonitor


LOG_PATH = ROOT / "data" / "drift_energy_monitor" / "runtime_log.jsonl"
REPORT_PATH = ROOT / "data" / "drift_energy_monitor" / "operational_report.md"


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()
    monitor = DriftEnergyMonitor(LOG_PATH)
    for snapshot in sample_snapshots():
        monitor.observe(snapshot)
    build_markdown_report(LOG_PATH, REPORT_PATH)
    print(f"Drift Energy Monitor log: {LOG_PATH}")
    print(f"Drift Energy Monitor report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
