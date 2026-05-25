from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.vma.runtime import (  # noqa: E402
    detect_continuity_break,
    evaluate_topology_retention,
    measure_recovery,
    process_session,
    process_turn,
)


def sample_session() -> dict:
    sample_path = ROOT / "sample_data" / "vma_continuity_session.json"
    return json.loads(sample_path.read_text(encoding="utf-8"))


def processed_turns(session: dict) -> list[dict]:
    state = None
    results = []
    for turn in session["turns"]:
        result = process_turn(turn, state)
        state = result["state"]
        results.append(result)
    return results


class VMAContinuityWinTests(unittest.TestCase):
    def test_detects_interruption_without_collapse(self) -> None:
        session = sample_session()
        turns = processed_turns(session)

        continuity_break = detect_continuity_break(session, turns)

        self.assertTrue(continuity_break["interruption_seen"])
        self.assertTrue(continuity_break["continuation_after_drift"])
        self.assertFalse(continuity_break["collapse_detected"])
        self.assertFalse(continuity_break["visual_reentry_required"])

    def test_evaluates_topology_retention(self) -> None:
        session = sample_session()
        turns = processed_turns(session)

        retention = evaluate_topology_retention(session, turns)

        self.assertGreaterEqual(retention["topology_retention_score"], 0.80)
        self.assertEqual(retention["hierarchy_stability"], 1.0)
        self.assertEqual(retention["dependency_direction_score"], 1.0)

    def test_measures_recovery_efficiency(self) -> None:
        session = sample_session()
        turns = processed_turns(session)
        continuity_break = detect_continuity_break(session, turns)

        recovery = measure_recovery(session, turns, continuity_break)

        self.assertGreaterEqual(recovery["recovery_efficiency"], 0.70)
        self.assertTrue(recovery["recovery_after_interruption"])
        self.assertTrue(recovery["continuation_after_recovery"])

    def test_first_real_continuity_win_is_achieved(self) -> None:
        report = process_session(sample_session())

        metrics = report["continuity_report_json"]
        state = report["continuity_state_update"]

        self.assertTrue(report["first_real_continuity_win"])
        self.assertGreaterEqual(metrics["topology_retention_score"], 0.80)
        self.assertGreaterEqual(metrics["recovery_efficiency"], 0.70)
        self.assertEqual(metrics["recursive_stability"], "stable")
        self.assertFalse(metrics["visual_reentry_required"])
        self.assertIn("FIRST_REAL_CONTINUITY_WIN", report["continuity_summary_markdown"])
        self.assertGreaterEqual(state["continuity_score"], 0.80)
        self.assertEqual(state["recursive_stability"], "stable")
        self.assertFalse(state["visual_reentry_required"])


if __name__ == "__main__":
    unittest.main()

