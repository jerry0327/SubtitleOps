import tempfile
import unittest
from pathlib import Path

from subtitleops.config import ConfigError, CheckConfig, find_config, load_config, parse_config, validate_check_config


class ConfigTests(unittest.TestCase):
    def test_no_config_uses_defaults(self):
        loaded = load_config(no_config=True)
        self.assertIsNone(loaded.path)
        self.assertEqual(loaded.check.max_cps, 20.0)
        self.assertIn("*.srt", loaded.check.include)

    def test_parse_dedicated_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".subtitleops.toml"
            path.write_text(
                """version = 1
[check]
max_cps = 17.5
fail_on = "error"
ignore = ["overlap"]
include = ["*.srt"]
exclude = ["vendor/**"]
recursive = false
jobs = 3
allow_empty = true
""",
                encoding="utf-8",
            )
            loaded = parse_config(path)
            self.assertEqual(loaded.check.max_cps, 17.5)
            self.assertEqual(loaded.check.fail_on, "error")
            self.assertEqual(loaded.check.ignore, ("OVERLAP",))
            self.assertFalse(loaded.check.recursive)
            self.assertEqual(loaded.check.jobs, 3)
            self.assertTrue(loaded.check.allow_empty)

    def test_parse_pyproject_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pyproject.toml"
            path.write_text(
                """[project]
name = "demo"
[tool.subtitleops]
version = 1
[tool.subtitleops.check]
max_line_length = 38
""",
                encoding="utf-8",
            )
            loaded = parse_config(path)
            self.assertEqual(loaded.check.max_line_length, 38)

    def test_find_config_walks_upward(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / ".subtitleops.toml"
            config.write_text("[check]\nmax_cps = 18\n", encoding="utf-8")
            nested = root / "a" / "b"
            nested.mkdir(parents=True)
            self.assertEqual(find_config(nested), config)

    def test_programmatic_config_is_normalized(self):
        config = validate_check_config(
            CheckConfig(
                max_cps=18,
                fail_on="ERROR",
                ignore=("overlap", "OVERLAP"),
                include=["*.srt"],  # type: ignore[arg-type]
                exclude=[],  # type: ignore[arg-type]
            )
        )
        self.assertEqual(config.max_cps, 18.0)
        self.assertEqual(config.fail_on, "error")
        self.assertEqual(config.ignore, ("OVERLAP",))
        self.assertEqual(config.include, ("*.srt",))
        self.assertEqual(config.exclude, ())

    def test_programmatic_boolean_integer_is_rejected(self):
        with self.assertRaises(ConfigError):
            validate_check_config(CheckConfig(jobs=True))  # type: ignore[arg-type]

    def test_unknown_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".subtitleops.toml"
            path.write_text("[check]\nmagic = true\n", encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "unknown check"):
                parse_config(path)

    def test_unknown_ignored_rule_is_rejected(self):
        with self.assertRaisesRegex(ConfigError, "unknown ignored"):
            validate_check_config(CheckConfig(ignore=("NOT_A_RULE",)))

    def test_invalid_duration_range_is_rejected(self):
        with self.assertRaisesRegex(ConfigError, "cannot be lower"):
            validate_check_config(CheckConfig(min_duration_ms=1000, max_duration_ms=500))

    def test_explicit_missing_config_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ConfigError, "not found"):
                load_config(Path(tmp) / "missing.toml")

    def test_explicit_and_no_config_conflict(self):
        with self.assertRaisesRegex(ConfigError, "cannot be used together"):
            load_config("anything.toml", no_config=True)


if __name__ == "__main__":
    unittest.main()
