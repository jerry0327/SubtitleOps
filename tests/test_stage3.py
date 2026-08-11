import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from subtitleops.checking import run_check
from subtitleops.cli import main
from subtitleops.config import DEFAULT_INCLUDE, CheckConfig, ConfigError, parse_config, validate_check_config
from subtitleops.discovery import discover_files
from subtitleops.formats import parse_vtt_document, render_vtt_document
from subtitleops.reporting import render_sarif


class StageThreeIntegrationTests(unittest.TestCase):
    def test_default_discovery_and_config_include_ttml_and_size_guard(self):
        self.assertIn("*.ttml", DEFAULT_INCLUDE)
        self.assertIn("*.dfxp", DEFAULT_INCLUDE)
        self.assertEqual(CheckConfig().max_file_bytes, 10 * 1024 * 1024)
        with self.assertRaisesRegex(ConfigError, "max_file_bytes"):
            validate_check_config(CheckConfig(max_file_bytes=-1))

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".subtitleops.toml"
            path.write_text("[check]\nmax_file_bytes = 4096\n", encoding="utf-8")
            self.assertEqual(parse_config(path).check.max_file_bytes, 4096)

    def test_discovery_and_batch_check_ttml_and_dfxp(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = (
                '<tt xmlns="http://www.w3.org/ns/ttml"><body><div>'
                '<p begin="0s" dur="2s">Readable line</p></div></body></tt>'
            )
            (root / "one.ttml").write_text(payload, encoding="utf-8")
            (root / "two.dfxp").write_text(payload, encoding="utf-8")
            discovery = discover_files(
                [root], recursive=True, include=DEFAULT_INCLUDE, exclude=(), allow_empty=False
            )
            self.assertEqual({path.suffix for path in discovery.files}, {".ttml", ".dfxp"})
            report = run_check([root], CheckConfig(), base_dir=root)
            self.assertEqual(report.files_checked, 2)
            self.assertEqual(report.cue_count, 2)
            self.assertEqual({file.format for file in report.files}, {"ttml"})

    def test_oversized_file_is_structured_operational_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "large.srt"
            path.write_text("x" * 100, encoding="utf-8")
            report = run_check([path], CheckConfig(max_file_bytes=10), base_dir=root)
            self.assertEqual(report.files[0].error.code, "FILE_TOO_LARGE")
            self.assertEqual(report.exit_code(), 2)
            sarif = json.loads(render_sarif(report))
            self.assertEqual(sarif["runs"][0]["results"][0]["ruleId"], "FILE_TOO_LARGE")

    def test_vtt_fix_preserves_document_blocks(self):
        text = (
            "WEBVTT\nKind: captions\n\nSTYLE\n::cue { color: white; }\n\n"
            "00:00:00.000 --> 00:00:01.000\nHi   \n\n"
            "NOTE after\nkeep this\n"
        )
        document = parse_vtt_document(text)
        self.assertEqual(render_vtt_document(document), text)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "captions.vtt"
            path.write_text(text, encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["fix", str(path)]), 0)
            output = path.read_text(encoding="utf-8")
            self.assertIn("STYLE\n::cue { color: white; }", output)
            self.assertIn("NOTE after\nkeep this", output)
            self.assertNotIn("Hi   ", output)

    def test_cli_converts_srt_to_ttml_and_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            srt = root / "in.srt"
            ttml = root / "out.ttml"
            vtt = root / "out.vtt"
            srt.write_text("1\n00:00:00,000 --> 00:00:01,250\nHi & bye\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["convert", str(srt), str(ttml)]), 0)
                self.assertEqual(main(["convert", str(ttml), str(vtt)]), 0)
            self.assertIn("<tt", ttml.read_text(encoding="utf-8"))
            self.assertIn("Hi & bye", vtt.read_text(encoding="utf-8"))

    def test_same_format_ttml_rewrite_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "in.ttml"
            path.write_text(
                '<tt xmlns="http://www.w3.org/ns/ttml"><body><div>'
                '<p begin="0s" dur="1s">Hi</p></div></body></tt>',
                encoding="utf-8",
            )
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(main(["fix", str(path)]), 2)
            self.assertIn("styling and layout", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
