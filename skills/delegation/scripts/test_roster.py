"""Roster policy regressions. Stdlib only."""

from __future__ import annotations

import unittest
from pathlib import Path


POLICY = Path(__file__).resolve().parent.parent / "references" / "roster.yaml"


class RosterPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = POLICY.read_text(encoding="utf-8")

    def test_excludes_fable_and_fast_skus(self) -> None:
        for needle in (
            "claude-fable-5",
            "claude-mythos-5",
            "claude-opus-5-fast",
            "gpt-5.6-sol-fast",
            "gpt-5.6-cyber",
        ):
            self.assertIn(needle, self.text)

    def test_t0_pins_are_frontier_not_fable(self) -> None:
        t0 = self.text.split("T1:")[0]
        self.assertIn("claude-opus-5", t0)
        self.assertIn("grok-4.6", t0)
        self.assertIn("gpt-5.6-sol", t0)
        self.assertIn("kimi-k3", t0)
        pins = t0.split("pin_when_allowed:")[1].split("notes:")[0]
        self.assertNotIn("fable", pins.lower())

    def test_composer_not_t1_pin(self) -> None:
        t1 = self.text.split("T1:")[1].split("T2:")[0]
        self.assertNotIn("composer-2.5", t1)
        self.assertIn("gemini-3.7-flash", t1)
        self.assertIn("gpt-5.6-terra", t1)

    def test_refresh_markers_present(self) -> None:
        for needle in (
            "# refresh:never_pin",
            "# refresh:pins:T0",
            "# refresh:pins:T1",
            "# refresh:pins:T2",
        ):
            self.assertIn(needle, self.text)


if __name__ == "__main__":
    unittest.main()
