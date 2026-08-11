import contextlib
import io
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
                self.assertEqual(main(["check", str(clean)]), 0)

            bad = Path(tmp) / "bad.srt"
            bad.write_text(
                "1\n00:00:00,000 --> 00:00:02,000\nFirst\n\n2\n00:00:01,500 --> 00:00:03,000\nSecond\n",
                encoding="utf-8",
            )
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["check", str(bad)]), 1)

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


if __name__ == "__main__":
    unittest.main()
