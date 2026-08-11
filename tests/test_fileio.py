import stat
import tempfile
import unittest
from pathlib import Path

from subtitleops.fileio import FileTooLargeError, read_utf8, write_text_atomic


class FileIOTests(unittest.TestCase):
    def test_bounded_read_rejects_oversized_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "large.srt"
            path.write_bytes(b"x" * 11)
            with self.assertRaises(FileTooLargeError) as caught:
                read_utf8(path, max_file_bytes=10)
            self.assertEqual(caught.exception.limit, 10)
            self.assertEqual(caught.exception.observed, 11)

    def test_zero_disables_size_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.txt"
            path.write_text("hello", encoding="utf-8")
            self.assertEqual(read_utf8(path, max_file_bytes=0), "hello")

    def test_atomic_write_preserves_mode_and_leaves_no_temporary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "out.txt"
            path.write_text("old", encoding="utf-8")
            path.chmod(0o640)
            write_text_atomic(path, "new")
            self.assertEqual(path.read_text(encoding="utf-8"), "new")
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)
            self.assertEqual(list(root.glob(".out.txt.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
