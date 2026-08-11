import unittest

from subtitleops.models import Cue
from subtitleops.transforms import normalize_text, resolve_overlaps, shift_cues


class TransformTests(unittest.TestCase):
    def test_normalize_text_trims_edge_whitespace(self):
        cue = normalize_text([Cue(0, 1000, "\n hello  \nworld   \n")])[0]
        self.assertEqual(cue.text, " hello\nworld")

    def test_shift_clips_globally_and_preserves_duration(self):
        cues, effective = shift_cues([Cue(200, 1200, "a"), Cue(2000, 3000, "b")], -500)
        self.assertEqual(effective, -200)
        self.assertEqual(cues[0].start_ms, 0)
        self.assertEqual(cues[0].duration_ms, 1000)
        self.assertEqual(cues[1].duration_ms, 1000)

    def test_resolve_overlaps(self):
        cues, changes = resolve_overlaps([Cue(0, 1500, "a"), Cue(1200, 2000, "b")])
        self.assertEqual(changes, 1)
        self.assertEqual(cues[0].end_ms, 1200)

    def test_overlap_not_fixed_if_cue_would_be_too_short(self):
        cues, changes = resolve_overlaps([Cue(1150, 1500, "a"), Cue(1200, 2000, "b")], min_duration_ms=100)
        self.assertEqual(changes, 0)
        self.assertEqual(cues[0].end_ms, 1500)


if __name__ == "__main__":
    unittest.main()
