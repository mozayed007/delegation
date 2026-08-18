"""Tests for doctor.py helpers. Stdlib only."""

from __future__ import annotations

import unittest

from doctor import bundled_skills, dump_yaml, refresh_script_path, yaml_escape


class YamlTests(unittest.TestCase):
    def test_escape_colon(self) -> None:
        self.assertEqual(yaml_escape("a: b"), '"a: b"')

    def test_dump_nested(self) -> None:
        text = dump_yaml({"roles": {"T0": {"harnesses": ["codex", "grok"]}}})
        self.assertIn("roles:", text)
        self.assertIn("- codex", text)
        self.assertIn("- grok", text)

    def test_dump_null_bool(self) -> None:
        text = dump_yaml({"a": None, "b": True, "c": False})
        self.assertIn("a: null", text)
        self.assertIn("b: true", text)
        self.assertIn("c: false", text)


class SkillPackTests(unittest.TestCase):
    def test_bundled_skills_include_roster_refresh(self) -> None:
        names = {path.name for path in bundled_skills()}
        self.assertIn("delegation", names)
        self.assertIn("roster-refresh", names)

    def test_refresh_script_exists(self) -> None:
        path = refresh_script_path()
        self.assertIsNotNone(path)
        assert path is not None
        self.assertTrue(path.is_file())


if __name__ == "__main__":
    unittest.main()
