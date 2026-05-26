from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DB_PATH = ROOT / "data" / "acpc.db"


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = Path(db_path or os.getenv("ACPC_DB_PATH") or DEFAULT_DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            report_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            site_id TEXT NOT NULL,
            status TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            summary TEXT NOT NULL,
            input_hash TEXT NOT NULL,
            report_json TEXT NOT NULL,
            markdown TEXT NOT NULL
        )
        """
    )
    conn.commit()


def insert_report(report: dict[str, Any], markdown: str, db_path: Path | None = None) -> None:
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO reports (
                report_id, timestamp, site_id, status, risk_level, summary,
                input_hash, report_json, markdown
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report["report_id"],
                report["timestamp"],
                report["site_id"],
                report["status"],
                report["risk_level"],
                report["summary"],
                report["input_hash"],
                json.dumps(report, indent=2, sort_keys=True),
                markdown,
            ),
        )
        conn.commit()


def list_reports(db_path: Path | None = None) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT report_id, timestamp, site_id, status, risk_level, summary
            FROM reports
            ORDER BY timestamp DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_report(report_id: str, db_path: Path | None = None) -> dict[str, Any] | None:
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT report_json FROM reports WHERE report_id = ?",
            (report_id,),
        ).fetchone()
    if row is None:
        return None
    return json.loads(row["report_json"])


def get_markdown(report_id: str, db_path: Path | None = None) -> str | None:
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT markdown FROM reports WHERE report_id = ?",
            (report_id,),
        ).fetchone()
    if row is None:
        return None
    return str(row["markdown"])
