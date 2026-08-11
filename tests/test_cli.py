import contextlib
import io
import json
import stat
import tempfile
import unittest
from pathlib import Path

from subtitleops.cli import main


class CliTests(unittest.TestCase):
    def test_check_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            clean = Path(tmp) / "clean.srt"
            clean.write_text("1\n00:00:00,000 --> 00:00:02,000\nHello\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["check", str(clean), "--no-config"]), 0)

            bad = Path(tmp) / "bad.srt"
            bad.write_text(
                "1\n00:00:00,000 --> 00:00:02,000\nFirst\n\n2\n00:00:01,500 --> 00:00:03,000\nSecond\n",
                encoding="utf-8",
            )
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["check", str(bad), "--no-config"]), 1)

    def test_convert_srt_to_vtt(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "in.srt"
            out = Path(tmp) / "out.vtt"
            src.write_text("1\n00:00:00,000 --> 00:00:01,000\nHi\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["convert", str(src), str(out)]), 0)
            self.assertTrue(out.read_text(encoding="utf-8").startswith("WEBVTT"))

    def test_fix_uses_output_extension_for_conversion(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "in.srt"
            out = Path(tmp) / "out.vtt"
            src.write_text("1\n00:00:00,000 --> 00:00:01,000\nHi\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["fix", str(src), "-o", str(out)]), 0)
            self.assertTrue(out.read_text(encoding="utf-8").startswith("WEBVTT"))

    def test_in_place_fix_is_atomic_and_preserves_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "in.srt"
            src.write_text(
                "1\n00:00:00,000 --> 00:00:01,000\nHi   \n",
                encoding="utf-8",
            )
            src.chmod(0o640)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["fix", str(src)]), 0)
            self.assertEqual(stat.S_IMODE(src.stat().st_mode), 0o640)
            self.assertNotIn("Hi   ", src.read_text(encoding="utf-8"))
            self.assertEqual(list(root.glob(".in.srt.*.tmp")), [])

    def test_directory_check_emits_aggregate_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "clean.srt").write_text(
                "1\n00:00:00,000 --> 00:00:02,000\nHello\n", encoding="utf-8"
            )
            (root / "short.srt").write_text(
                "1\n00:00:00,000 --> 00:00:00,200\nHi\n", encoding="utf-8"
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["check", str(root), "--json", "--no-config", "--jobs", "2"])
            payload = json.loads(output.getvalue())
            self.assertEqual(code, 1)
            self.assertEqual(payload["summary"]["files_discovered"], 2)
            self.assertEqual(payload["summary"]["issues"], 1)

    def test_sarif_can_be_written_to_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "short.srt"
            out = root / "reports" / "subtitleops.sarif"
            src.write_text("1\n00:00:00,000 --> 00:00:00,200\nHi\n", encoding="utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = main(
                    ["check", str(src), "--sarif", "--output", str(out), "--no-config"]
                )
            self.assertEqual(code, 1)
            self.assertEqual(stdout.getvalue(), "")
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["version"], "2.1.0")

    def test_dash_output_target_writes_to_stdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "clean.srt"
            src.write_text(
                "1\n00:00:00,000 --> 00:00:02,000\nHello\n", encoding="utf-8"
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["check", str(src), "--json", "-o", "-", "--no-config"])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output.getvalue())["summary"]["exit_code"], 0)

    def test_rules_command_has_machine_readable_metadata(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main(["rules", "--json"]), 0)
        codes = {item["code"] for item in json.loads(output.getvalue())}
        self.assertIn("OVERLAP", codes)
        self.assertNotIn("PARSE_ERROR", codes)

    def test_unknown_ignored_rule_is_operational_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "clean.srt"
            src.write_text("1\n00:00:00,000 --> 00:00:02,000\nHello\n", encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(["check", str(src), "--ignore", "NOT_REAL", "--no-config"])
            self.assertEqual(code, 2)
            self.assertIn("unknown ignored rule", stderr.getvalue())

    def test_allow_empty_returns_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["check", tmp, "--allow-empty", "--no-config"]), 0)

    def test_fail_on_error_allows_warning_only_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "short.srt"
            src.write_text("1\n00:00:00,000 --> 00:00:00,200\nHi\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    main(["check", str(src), "--fail-on", "error", "--no-config"]), 0
                )

    def test_explicit_config_controls_failure_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "short.srt"
            config = root / ".subtitleops.toml"
            src.write_text("1\n00:00:00,000 --> 00:00:00,200\nHi\n", encoding="utf-8")
            config.write_text("[check]\nfail_on = \"error\"\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["check", str(src), "--config", str(config)]), 0)

    def test_parse_error_is_present_in_json_and_returns_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "broken.srt"
            src.write_text("broken", encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["check", str(src), "--json", "--no-config"])
            payload = json.loads(output.getvalue())
            self.assertEqual(code, 2)
            self.assertEqual(payload["files"][0]["error"]["code"], "PARSE_ERROR")


if __name__ == "__main__":
    unittest.main()
