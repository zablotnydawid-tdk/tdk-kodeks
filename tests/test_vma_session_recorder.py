from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.vma.session_recorder import (  # noqa: E402
    append_turn,
    build_markdown_report,
    create_session,
    finalize_session,
    load_session,
    save_report,
    save_session,
)


def build_real_session() -> dict:
    session = create_session("real-user-test", notes="manual transcript")
    turns = [
        ("turn", "VOICE MODE\n- Control Plane observes\n- VMA preserves continuity\n- Operator decides", "Stable anchor established."),
        ("turn", "Continue hierarchy\n- Control Plane observes\n- VMA preserves continuity\n- Operator decides", "Hierarchy retained."),
        ("interruption", "Interruption: phone call, pause.", "Holding last stable anchor."),
        ("recovery_attempt", "Return from interruption through Control Plane, VMA, Operator.", "Recovery path restored."),
        ("turn", "Continue\n- Control Plane observes\n- VMA preserves continuity\n- Operator decides", "Continuity proof remains stable."),
    ]
    for event_type, user_input, assistant_output in turns:
        session = append_turn(
            session,
            user_input=user_input,
            assistant_output=assistant_output,
            event_type=event_type,
        )
    return session


class VMASessionRecorderTests(unittest.TestCase):
    def test_records_turn_with_runtime_fields(self) -> None:
        session = create_session("recorder-test")
        session = append_turn(
            session,
            user_input="VOICE MODE\n- A\n- B\n- C",
            assistant_output="VOICE-STABLE",
        )
        turn = session["turns"][0]

        self.assertIn("detected_structure", turn)
        self.assertIn("topology_map", turn)
        self.assertIn("continuity_score", turn)
        self.assertIn("cognitive_load", turn)
        self.assertFalse(turn["visual_reentry_required"])

    def test_finalize_computes_first_real_user_win(self) -> None:
        session = finalize_session(build_real_session())

        self.assertTrue(session["first_real_user_continuity_win"])
        self.assertGreaterEqual(session["continuity_metrics"]["continuity_score"], 0.75)
        self.assertGreaterEqual(
            session["continuity_metrics"]["topology_retention_score"], 0.75
        )
        self.assertGreaterEqual(
            session["continuity_metrics"]["recovery_efficiency"], 0.60
        )
        self.assertFalse(session["continuity_metrics"]["visual_reentry_required"])

    def test_markdown_report_contains_status(self) -> None:
        session = finalize_session(build_real_session())
        report = build_markdown_report(session)

        self.assertIn("VMA Real User Session Validation", report)
        self.assertIn("FIRST_REAL_USER_CONTINUITY_WIN: ACHIEVED", report)

    def test_save_and_load_session_outputs(self) -> None:
        session = finalize_session(build_real_session())
        with tempfile.TemporaryDirectory() as tmp_dir:
            session_path = Path(tmp_dir) / "session.json"
            report_path = Path(tmp_dir) / "report.md"

            save_session(session, session_path)
            save_report(session, report_path)
            loaded = load_session(session_path)

            self.assertEqual(loaded["session_id"], "real-user-test")
            self.assertTrue(report_path.exists())


if __name__ == "__main__":
    unittest.main()

