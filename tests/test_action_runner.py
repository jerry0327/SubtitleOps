import os
import runpy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class ActionRunnerTests(unittest.TestCase):
    def _run(self, root: Path, *, paths: str, extra: dict[str, str] | None = None):
        output = root / "github-output"
        summary = root / "summary"
        env = {
            "GITHUB_OUTPUT": str(output),
            "GITHUB_STEP_SUMMARY": str(summary),
            "SUBTITLEOPS_ACTION_PATHS": paths,
            "SUBTITLEOPS_ACTION_NO_CONFIG": "true",
            "SUBTITLEOPS_ACTION_REPORT_PATH": "report.sarif",
        }
        env.update(extra or {})
        cwd = Path.cwd()
        try:
            os.chdir(root)
            with patch.dict(os.environ, env, clear=False):
                with self.assertRaises(SystemExit) as caught:
                    runpy.run_path(str(cwd / "scripts" / "action_runner.py"), run_name="__main__")
                self.assertEqual(caught.exception.code, 0)
        finally:
            os.chdir(cwd)
        values = dict(line.split("=", 1) for line in output.read_text(encoding="utf-8").splitlines())
        return values, summary.read_text(encoding="utf-8")

    def test_clean_action_run_writes_sarif_and_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "clean.srt").write_text(
                "1\n00:00:00,000 --> 00:00:02,000\nHello\n", encoding="utf-8"
            )
            values, summary = self._run(root, paths="clean.srt")
            self.assertEqual(values["exit-code"], "0")
            self.assertEqual(values["report-exists"], "true")
            self.assertTrue((root / "report.sarif").is_file())
            self.assertIn("Files checked", summary)

    def test_invalid_action_input_returns_operational_exit_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            values, _ = self._run(root, paths=".", extra={"SUBTITLEOPS_ACTION_FORMAT": "bad"})
            self.assertEqual(values["exit-code"], "2")
            self.assertEqual(values["report-exists"], "false")


if __name__ == "__main__":
    unittest.main()
