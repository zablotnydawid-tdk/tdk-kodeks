from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from acpc_api.storage import db


ROOT = Path(__file__).resolve().parents[4]


class StorageService:
    def __init__(self, db_path: Path | None = None, reports_dir: Path | None = None):
        self.db_path = db_path
        self.reports_dir = Path(reports_dir or os.getenv("ACPC_REPORTS_DIR") or ROOT / "data" / "reports")
        with db.connect(db_path):
            pass

    def save_report(self, report: dict[str, Any], markdown: str) -> None:
        db.insert_report(report, markdown, self.db_path)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        report_id = report["report_id"]
        (self.reports_dir / f"{report_id}.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (self.reports_dir / f"{report_id}.md").write_text(markdown, encoding="utf-8")

    def list_reports(self) -> list[dict[str, Any]]:
        return db.list_reports(self.db_path)

    def get_report(self, report_id: str) -> dict[str, Any] | None:
        return db.get_report(report_id, self.db_path)

    def get_markdown(self, report_id: str) -> str | None:
        return db.get_markdown(report_id, self.db_path)
