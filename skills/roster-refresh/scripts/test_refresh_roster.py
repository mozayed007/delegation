"""Tests for roster-refresh parsers and pin cuts. Stdlib only. No network."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from refresh_roster import (
    apply_leaderboards,
    extract_pins,
    parse_anthropic_prices,
    parse_percent_near_name,
    parse_source,
    propose,
    replace_block,
)


ANTHROPIC = """
Claude Fable 5 Input $3 / MTok Output $50 / MTok
Claude Mythos 5 Input $5 / MTok Output $50 / MTok
Claude Opus 5 Input $5 / MTok Output $25 / MTok
Claude Sonnet 5 Input $1 / MTok Output $10 / MTok
Fast mode for Claude Opus 5 costs $50 / MTok.
"""

CURSORBENCH = """
Grok 4.6 scored 70.8%
Claude Opus 5 scored 70.0%
Composer 2.5 scored 56.1%
GPT-5.6 Luna scored 61.1%
"""

DEEPSWE = """
Claude Opus 5 73.6%
GPT-5.6 Terra 69.6%
GLM-5.2 43.8%
Gemini 3.1 Pro 11.7%
"""


class ParseTests(unittest.TestCase):
    def test_anthropic_output_is_max_mtok(self) -> None:
        prices: dict[str, float] = {}
        parse_anthropic_prices(ANTHROPIC, prices)
        self.assertEqual(prices["claude-fable-5"], 50.0)
        self.assertEqual(prices["claude-opus-5"], 25.0)
        self.assertEqual(prices["claude-opus-5-fast"], 50.0)

    def test_cursorbench_percent_near_name(self) -> None:
        scores: dict[str, dict[str, float]] = {}
        parse_percent_near_name(CURSORBENCH, "cursorbench", scores)
        self.assertEqual(scores["grok-4.6"]["cursorbench"], 70.8)
        self.assertEqual(scores["composer-2.5"]["cursorbench"], 56.1)


class ProposeTests(unittest.TestCase):
    def test_fable_never_pinned_even_with_high_score(self) -> None:
        proposal = propose(
            scores={"claude-fable-5": {"deepswe": 69.7, "cursorbench": 70.5}},
            prices={"claude-fable-5": 50.0, "gpt-5.6-sol": 30.0},
            old_pins={"T0": ["claude-opus-5"], "T1": [], "T2": ["mimo-v2.5-free"]},
            sub_ok={"gpt-5.6-sol"},
            max_out=25,
        )
        self.assertIn("claude-fable-5", proposal["never_pin"])
        self.assertNotIn("claude-fable-5", proposal["T0"])
        self.assertIn("gpt-5.6-sol", proposal["T0"])

    def test_composer_is_t2_not_t1(self) -> None:
        proposal = propose(
            scores={"composer-2.5": {"cursorbench": 56.1}, "gpt-5.6-terra": {"deepswe": 69.6}},
            prices={},
            old_pins={"T0": [], "T1": ["composer-2.5", "gpt-5.6-terra"], "T2": []},
            sub_ok={"gpt-5.6-sol"},
            max_out=25,
        )
        self.assertNotIn("composer-2.5", proposal["T1"])
        self.assertIn("composer-2.5", proposal["T2"])
        self.assertIn("gpt-5.6-terra", proposal["T1"])

    def test_glm_stays_t1_when_deepswe_is_weak(self) -> None:
        proposal = propose(
            scores={"glm-5.2": {"deepswe": 43.8}},
            prices={},
            old_pins={"T0": [], "T1": [], "T2": []},
            sub_ok=set(),
            max_out=25,
        )
        self.assertIn("glm-5.2", proposal["T1"])
        self.assertIn("glm-5.2", proposal["T2"])

    def test_merge_keeps_unobserved_zen_pins(self) -> None:
        proposal = propose(
            scores={"gpt-5.6-luna": {"deepswe": 67.2}},
            prices={},
            old_pins={"T0": [], "T1": [], "T2": ["big-pickle"]},
            sub_ok=set(),
            max_out=25,
        )
        self.assertIn("big-pickle", proposal["T2"])
        self.assertIn("mimo-v2.5-free", proposal["T2"])

    def test_price_26_is_not_never_pin(self) -> None:
        proposal = propose(
            scores={"claude-sonnet-5": {"deepswe": 53.8}},
            prices={"claude-sonnet-5": 26.0},
            old_pins={"T0": [], "T1": [], "T2": []},
            sub_ok=set(),
            max_out=25,
        )
        self.assertNotIn("claude-sonnet-5", proposal["never_pin"])
        self.assertIn("claude-sonnet-5", proposal["T1"])


class MarkerTests(unittest.TestCase):
    def test_replace_block_keeps_indent(self) -> None:
        text = "never_pin:\n  # refresh:never_pin\n  - old\n  # /refresh:never_pin\n"
        out = replace_block(text, "# refresh:never_pin", "# /refresh:never_pin", "  - new\n")
        self.assertIn("  - new\n  # /refresh:never_pin", out)

    def test_extract_pins(self) -> None:
        text = "    pin_when_allowed:\n      # refresh:pins:T0\n      - grok-4.6\n      # /refresh:pins:T0\n"
        self.assertEqual(extract_pins(text, "T0"), ["grok-4.6"])

    def test_apply_leaderboards_replaces_generated_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "leaderboards.md"
            path.write_text(
                "keep me\n<!-- refresh:generated -->\nold\n<!-- /refresh:generated -->\nalso keep\n",
                encoding="utf-8",
            )
            apply_leaderboards(path, "\nnew\n", "2026-08-18")
            text = path.read_text(encoding="utf-8")
            self.assertIn("keep me", text)
            self.assertIn("also keep", text)
            self.assertIn("new", text)
            self.assertNotIn("old", text)

    def test_parse_source_deepswe(self) -> None:
        scores: dict[str, dict[str, float]] = {}
        parse_source("deepswe", DEEPSWE, scores, {})
        self.assertEqual(scores["claude-opus-5"]["deepswe"], 73.6)
        self.assertEqual(scores["gemini-3.1-pro"]["deepswe"], 11.7)


if __name__ == "__main__":
    unittest.main()
