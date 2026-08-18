"""Tests for new_packet.py. Stdlib only."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from new_packet import PACKET_FILES, new_packet


class NewPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.templates = (
            Path(__file__).resolve().parent.parent / "templates" / "packet"
        )

    def test_creates_seven_files_and_gitignore(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            dest = new_packet(repo, "billing", self.templates, force=False)
            self.assertEqual(dest, repo / ".agents" / "packets" / "billing")
            for name in PACKET_FILES:
                path = dest / name
                self.assertTrue(path.is_file(), name)
            task = (dest / "TASK.md").read_text(encoding="utf-8")
            self.assertIn("billing", task)
            self.assertNotIn("{{PACKET_ID}}", task)
            self.assertTrue((repo / ".agents" / "packets" / ".gitignore").is_file())
            ignore = (repo / ".gitignore").read_text(encoding="utf-8")
            self.assertIn(".agents/packets/", ignore)

    def test_refuses_existing_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            new_packet(repo, "once", self.templates, force=False)
            with self.assertRaises(FileExistsError):
                new_packet(repo, "once", self.templates, force=False)

    def test_appends_gitignore_marker_once(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            (repo / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
            new_packet(repo, "a", self.templates, force=False)
            new_packet(repo, "b", self.templates, force=False)
            text = (repo / ".gitignore").read_text(encoding="utf-8")
            self.assertEqual(text.count(".agents/packets/"), 1)


if __name__ == "__main__":
    unittest.main()
