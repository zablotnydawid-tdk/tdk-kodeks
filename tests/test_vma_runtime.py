from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.vma.runtime import (  # noqa: E402
    default_state,
    detect_structure,
    estimate_cognitive_load,
    inject_anchors,
    map_topology,
    process_turn,
    recover,
)


def sample_turn() -> dict:
    sample_path = ROOT / "sample_data" / "vma_turn_example.json"
    return json.loads(sample_path.read_text(encoding="utf-8"))


class VMARuntimeTests(unittest.TestCase):
    def test_voice_mode_activation(self) -> None:
        structure = detect_structure(sample_turn())

        self.assertTrue(structure["voice_mode_detected"])

    def test_detects_list_and_flow(self) -> None:
        structure = detect_structure(sample_turn())

        self.assertTrue(structure["has_list"])
        self.assertTrue(structure["has_flow"])
        self.assertGreaterEqual(len(structure["items"]), 5)

    def test_maps_topology(self) -> None:
        topology = map_topology(detect_structure(sample_turn()))

        self.assertGreaterEqual(len(topology["nodes"]), 5)
        self.assertEqual(len(topology["edges"]), len(topology["nodes"]) - 1)
        self.assertEqual(topology["layer"], "runtime")

    def test_anchor_injection(self) -> None:
        topology = map_topology(detect_structure(sample_turn()))
        anchors = inject_anchors(topology)

        self.assertGreaterEqual(len(anchors["anchors"]), 2)
        self.assertNotEqual(anchors["last_stable_anchor"], "none")
        self.assertEqual(anchors["missing_anchor_count"], 0)

    def test_recovery_on_confusion_signal(self) -> None:
        state = default_state()
        recovered = recover(state, "confusion: zgubiłem kontekst")

        self.assertTrue(recovered["recovery_required"])
        self.assertEqual(recovered["mode"], "recovery")
        self.assertEqual(recovered["compression_level"], "high")

    def test_estimates_cognitive_load(self) -> None:
        structure = detect_structure(sample_turn())
        topology = map_topology(structure)
        anchors = inject_anchors(topology)

        load = estimate_cognitive_load(structure, topology, anchors)

        self.assertGreater(load, 0.0)
        self.assertLessEqual(load, 1.0)

    def test_process_turn_returns_voice_stable_output_and_updated_state(self) -> None:
        result = process_turn(sample_turn())

        self.assertIn("VOICE-STABLE", result["voice_stable_output"])
        self.assertTrue(result["state"]["active"])
        self.assertEqual(result["state"]["mode"], "voice")
        self.assertEqual(result["state"]["current_topic"], "VMA Runtime MVP")
        self.assertIn("known_hierarchy", result["state"])
        self.assertGreaterEqual(result["telemetry"]["anchor_count"], 2)


if __name__ == "__main__":
    unittest.main()

