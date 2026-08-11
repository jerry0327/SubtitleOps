import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from subtitleops.discovery import discover_files


class DiscoveryTests(unittest.TestCase):
    def test_recursive_discovery_is_sorted_and_excludes_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "nested").mkdir()
            (root / "build").mkdir()
            (root / "z.srt").write_text("", encoding="utf-8")
            (root / "nested" / "a.vtt").write_text("", encoding="utf-8")
            (root / "build" / "ignored.srt").write_text("", encoding="utf-8")
            result = discover_files(
                [root],
                recursive=True,
                include=("*.srt", "*.vtt"),
                exclude=("build/**", "**/build/**"),
            )
            self.assertEqual([path.name for path in result.files], ["a.vtt", "z.srt"])
            self.assertEqual(result.errors, ())

    def test_non_recursive_discovery_skips_nested_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "nested").mkdir()
            (root / "top.srt").write_text("", encoding="utf-8")
            (root / "nested" / "deep.srt").write_text("", encoding="utf-8")
            result = discover_files(
                [root], recursive=False, include=("*.srt",), exclude=(), allow_empty=False
            )
            self.assertEqual([path.name for path in result.files], ["top.srt"])

    def test_explicit_unsupported_file_reports_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "captions.txt"
            path.write_text("data", encoding="utf-8")
            result = discover_files([path], recursive=True, include=("*",), exclude=())
            self.assertEqual(result.files, ())
            self.assertEqual(result.errors[0].code, "UNSUPPORTED_FORMAT")

    def test_format_override_accepts_extensionless_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "captions"
            path.write_text("data", encoding="utf-8")
            result = discover_files(
                [path], recursive=True, include=("*",), exclude=(), explicit_format="srt"
            )
            self.assertEqual(result.files, (path,))

    def test_missing_input_reports_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.srt"
            result = discover_files([missing], recursive=True, include=("*.srt",), exclude=())
            self.assertEqual(result.errors[0].code, "INPUT_NOT_FOUND")

    def test_duplicate_inputs_are_deduplicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "one.srt"
            path.write_text("", encoding="utf-8")
            result = discover_files([path, path], recursive=True, include=("*.srt",), exclude=())
            self.assertEqual(len(result.files), 1)

    def test_empty_directory_is_error_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = discover_files([tmp], recursive=True, include=("*.srt",), exclude=())
            self.assertEqual(result.errors[0].code, "NO_FILES")

    def test_walk_errors_are_reported_instead_of_silently_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            def failing_walk(*args, **kwargs):
                kwargs["onerror"](PermissionError("permission denied"))
                return iter(())

            with patch("subtitleops.discovery.os.walk", side_effect=failing_walk):
                result = discover_files(
                    [root],
                    recursive=True,
                    include=("*.srt",),
                    exclude=(),
                )
            self.assertEqual(result.files, ())
            self.assertEqual(result.errors[0].code, "IO_ERROR")
            self.assertIn("permission denied", result.errors[0].message)

    def test_directory_enumeration_error_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("subtitleops.discovery.os.walk", side_effect=PermissionError("denied")):
                result = discover_files(
                    [tmp], recursive=True, include=("*.srt",), exclude=()
                )
            self.assertEqual(result.files, ())
            self.assertEqual(result.errors[0].code, "IO_ERROR")
            self.assertIn("denied", result.errors[0].message)

    def test_allow_empty_suppresses_no_files_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = discover_files(
                [tmp], recursive=True, include=("*.srt",), exclude=(), allow_empty=True
            )
            self.assertEqual(result.files, ())
            self.assertEqual(result.errors, ())


if __name__ == "__main__":
    unittest.main()
