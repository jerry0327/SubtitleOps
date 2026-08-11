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

    def test_duration_bounds_are_configurable(self):
        cues = [Cue(0, 200, "Hi"), Cue(500, 8500, "Long enough")]
        codes = {issue.code for issue in lint_cues(cues)}
        self.assertIn("DURATION_TOO_SHORT", codes)
        self.assertIn("DURATION_TOO_LONG", codes)
        self.assertNotIn(
            "DURATION_TOO_SHORT",
            {issue.code for issue in lint_cues(cues, min_duration_ms=0, max_duration_ms=0)},
        )

    def test_formatting_and_control_character_rules(self):
        issues = lint_cues([Cue(0, 2000, "line  \nsecond\x00")])
        codes = {issue.code for issue in issues}
        self.assertIn("TRAILING_WHITESPACE", codes)
        self.assertIn("CONTROL_CHARACTER", codes)

    def test_duplicate_identifier_is_reported(self):
        issues = lint_cues(
            [Cue(0, 1000, "one", identifier="id"), Cue(1200, 2200, "two", identifier="id")]
        )
        duplicate = next(issue for issue in issues if issue.code == "DUPLICATE_IDENTIFIER")
        self.assertIn("cue 1", duplicate.message)

    def test_ignore_filters_rule(self):
        issues = lint_cues(
            [Cue(0, 1000, "one"), Cue(900, 1900, "two")], ignore={"OVERLAP"}
        )
        self.assertNotIn("OVERLAP", {issue.code for issue in issues})

    def test_issue_dictionary_includes_source_coordinates(self):
        issue = lint_cues([Cue(0, 200, "Hi", source_line=7)])[0].to_dict()
        self.assertEqual(issue["line"], 7)
        self.assertEqual(issue["start_ms"], 0)
        self.assertEqual(issue["end_ms"], 200)

    def test_invalid_lint_options_raise(self):
        with self.assertRaises(ValueError):
            lint_cues([], max_cps=0)
        with self.assertRaises(ValueError):
            lint_cues([], min_duration_ms=1000, max_duration_ms=500)


if __name__ == "__main__":
    unittest.main()
