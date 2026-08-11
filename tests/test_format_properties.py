import random
import string
import unittest

from subtitleops.formats import parse_srt, parse_ttml, parse_vtt, render_srt, render_ttml, render_vtt
from subtitleops.models import Cue


class FormatPropertyTests(unittest.TestCase):
    def test_seeded_round_trips_are_deterministic(self):
        rng = random.Random(8172026)
        for _ in range(100):
            cues = []
            cursor = rng.randint(0, 1000)
            for index in range(rng.randint(0, 8)):
                duration = rng.randint(100, 5000)
                alphabet = string.ascii_letters + string.digits + " &<>.-"
                lines = [("".join(rng.choice(alphabet) for _ in range(rng.randint(1, 20))).strip() or "x") for _ in range(rng.randint(1, 2))]
                identifier = f"id{index}" if rng.choice([True, False]) else None
                cues.append(Cue(cursor, cursor + duration, "\n".join(lines), identifier=identifier))
                cursor += duration + rng.randint(0, 1000)

            expected = [(cue.start_ms, cue.end_ms, cue.text) for cue in cues]
            for render, parse in ((render_srt, parse_srt), (render_vtt, parse_vtt), (render_ttml, parse_ttml)):
                first = render(cues)
                second = render(parse(first))
                self.assertEqual(first, second)
                actual = [(cue.start_ms, cue.end_ms, cue.text) for cue in parse(first)]
                self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
