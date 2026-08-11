import unittest

from subtitleops.linting import lint_cues
from subtitleops.models import Cue


class LintTests(unittest.TestCase):
    def test_detects_overlap_and_reading_speed(self):
        cues = [
            Cue(0, 1000, "short"),
            Cue(900, 1000, "This subtitle is intentionally much too dense for one tenth of a second."),
        ]
        codes = {issue.code for issue in lint_cues(cues)}
        self.assertIn("OVERLAP", codes)
        self.assertIn("READING_SPEED", codes)
        self.assertIn("LINE_TOO_LONG", codes)

    def test_clean_track_has_no_issues(self):
        cues = [Cue(0, 2000, "Readable line"), Cue(2200, 4200, "Another line")]
        self.assertEqual(lint_cues(cues), [])

    def test_invalid_duration_is_error(self):
        issues = lint_cues([Cue(1000, 1000, "bad")])
        self.assertEqual(issues[0].code, "TIMING_ORDER")
        self.assertEqual(issues[0].severity, "error")


if __name__ == "__main__":
    unittest.main()
