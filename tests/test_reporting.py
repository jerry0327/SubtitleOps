import json
import tempfile
import unittest
from pathlib import Path

from subtitleops.checking import run_check
from subtitleops.config import CheckConfig
from subtitleops.reporting import render_json, render_sarif, render_text


class ReportingTests(unittest.TestCase):
    def test_json_report_has_stable_envelope_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "bad.srt"
            path.write_text(
                "1\n00:00:00,000 --> 00:00:00,200\nHi\n", encoding="utf-8"
            )
            payload = json.loads(render_json(run_check([path], CheckConfig(), base_dir=root)))
            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(payload["tool"]["name"], "SubtitleOps")
            self.assertEqual(payload["summary"]["issues"], 1)
            self.assertEqual(payload["files"][0]["path"], "bad.srt")

    def test_sarif_contains_rule_result_and_source_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "bad.srt"
            path.write_text(
                "1\n00:00:00,000 --> 00:00:00,200\nHi\n", encoding="utf-8"
            )
            payload = json.loads(render_sarif(run_check([path], CheckConfig(), base_dir=root)))
            self.assertEqual(payload["version"], "2.1.0")
            run = payload["runs"][0]
            result = run["results"][0]
            self.assertEqual(result["ruleId"], "DURATION_TOO_SHORT")
            self.assertEqual(
                result["locations"][0]["physicalLocation"]["region"]["startLine"], 2
            )
            self.assertIn("DURATION_TOO_SHORT", {rule["id"] for rule in run["tool"]["driver"]["rules"]})
            fingerprint = result["partialFingerprints"]["subtitleops/v1"]
            self.assertEqual(len(fingerprint), 64)
            self.assertTrue(all(char in "0123456789abcdef" for char in fingerprint))

    def test_sarif_fingerprint_is_stable_across_repeated_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "bad.srt"
            path.write_text(
                "1\n00:00:00,000 --> 00:00:00,200\nHi\n", encoding="utf-8"
            )
            first = json.loads(render_sarif(run_check([path], CheckConfig(), base_dir=root)))
            second = json.loads(render_sarif(run_check([path], CheckConfig(), base_dir=root)))
            first_value = first["runs"][0]["results"][0]["partialFingerprints"]["subtitleops/v1"]
            second_value = second["runs"][0]["results"][0]["partialFingerprints"]["subtitleops/v1"]
            self.assertEqual(first_value, second_value)

    def test_operational_sarif_results_have_fingerprints(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = root / "missing.srt"
            payload = json.loads(render_sarif(run_check([missing], CheckConfig(), base_dir=root)))
            result = payload["runs"][0]["results"][0]
            self.assertEqual(result["ruleId"], "INPUT_NOT_FOUND")
            self.assertIn("subtitleops/v1", result["partialFingerprints"])

    def test_sarif_represents_parse_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "broken.srt"
            path.write_text("broken", encoding="utf-8")
            payload = json.loads(render_sarif(run_check([path], CheckConfig(), base_dir=root)))
            self.assertEqual(payload["runs"][0]["results"][0]["ruleId"], "PARSE_ERROR")
            self.assertFalse(payload["runs"][0]["invocations"][0]["executionSuccessful"])

    def test_text_report_hides_or_shows_clean_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "clean.srt"
            path.write_text("1\n00:00:00,000 --> 00:00:02,000\nHello\n", encoding="utf-8")
            report = run_check([path], CheckConfig(), base_dir=root)
            self.assertNotIn("OK  clean.srt", render_text(report, show_clean=False))
            self.assertIn("OK  clean.srt", render_text(report, show_clean=True))

    def test_discovery_error_is_in_json_and_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = root / "missing.srt"
            report = run_check([missing], CheckConfig(), base_dir=root)
            self.assertEqual(json.loads(render_json(report))["errors"][0]["code"], "INPUT_NOT_FOUND")
            self.assertIn("INPUT_NOT_FOUND", render_text(report))


if __name__ == "__main__":
    unittest.main()
