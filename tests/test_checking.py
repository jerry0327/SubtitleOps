import tempfile
import unittest
from pathlib import Path

from subtitleops.checking import run_check
from subtitleops.config import CheckConfig, ConfigError


CLEAN = "1\n00:00:00,000 --> 00:00:02,000\nReadable line\n"
OVERLAP = (
    "1\n00:00:00,000 --> 00:00:02,000\nFirst\n\n"
    "2\n00:00:01,500 --> 00:00:03,000\nSecond\n"
)


class CheckingTests(unittest.TestCase):
    def test_run_check_validates_programmatic_config(self):
        with self.assertRaises(ConfigError):
            run_check([], CheckConfig(jobs=-1))

    def test_batch_counts_and_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "clean.srt").write_text(CLEAN, encoding="utf-8")
            (root / "bad.srt").write_text(OVERLAP, encoding="utf-8")
            report = run_check([root], CheckConfig(jobs=2), base_dir=root)
            self.assertEqual(report.files_discovered, 2)
            self.assertEqual(report.files_checked, 2)
            self.assertEqual(report.cue_count, 3)
            self.assertIn("OVERLAP", {issue.code for issue in report.issues})
            self.assertEqual(report.exit_code(), 1)

    def test_fail_on_error_does_not_fail_for_warning_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "short.srt"
            path.write_text("1\n00:00:00,000 --> 00:00:00,200\nHi\n", encoding="utf-8")
            report = run_check([path], CheckConfig(fail_on="error"), base_dir=Path(tmp))
            self.assertEqual({issue.code for issue in report.issues}, {"DURATION_TOO_SHORT"})
            self.assertEqual(report.exit_code(), 0)

    def test_parse_failure_is_isolated_and_returns_exit_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "clean.srt").write_text(CLEAN, encoding="utf-8")
            (root / "broken.srt").write_text("not subtitles", encoding="utf-8")
            report = run_check([root], CheckConfig(jobs=2), base_dir=root)
            self.assertEqual(report.files_discovered, 2)
            self.assertEqual(report.files_checked, 1)
            self.assertEqual(report.files_failed, 1)
            self.assertEqual(report.exit_code(), 2)
            self.assertEqual(next(file.error.code for file in report.files if file.error), "PARSE_ERROR")

    def test_parallel_results_remain_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("z.srt", "a.srt", "m.srt"):
                (root / name).write_text(CLEAN, encoding="utf-8")
            report = run_check([root], CheckConfig(jobs=3), base_dir=root)
            self.assertEqual([file.path.name for file in report.files], ["a.srt", "m.srt", "z.srt"])

    def test_ignore_rule_removes_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "overlap.srt"
            path.write_text(OVERLAP, encoding="utf-8")
            report = run_check(
                [path], CheckConfig(ignore=("OVERLAP",), fail_on="warning"), base_dir=Path(tmp)
            )
            self.assertNotIn("OVERLAP", {issue.code for issue in report.issues})
            self.assertEqual(report.exit_code(), 0)

    def test_invalid_utf8_is_decode_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.srt"
            path.write_bytes(b"\xff\xfe\x00")
            report = run_check([path], CheckConfig(), base_dir=Path(tmp))
            self.assertEqual(report.files[0].error.code, "DECODE_ERROR")
            self.assertEqual(report.exit_code(), 2)


if __name__ == "__main__":
    unittest.main()
