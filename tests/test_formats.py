import unittest

from subtitleops.formats import SubtitleParseError, parse_srt, parse_vtt, render_srt, render_vtt


SRT = """1\n00:00:01,000 --> 00:00:02,500\nHello world.\n\n2\n00:00:03,000 --> 00:00:04,000\nSecond cue.\n"""

VTT = """WEBVTT\n\nintro\n00:00:01.000 --> 00:00:02.500 align:start\nHello world.\n"""


class FormatTests(unittest.TestCase):
    def test_parse_srt(self):
        cues = parse_srt(SRT)
        self.assertEqual(len(cues), 2)
        self.assertEqual(cues[0].start_ms, 1000)
        self.assertEqual(cues[0].end_ms, 2500)
        self.assertEqual(cues[1].text, "Second cue.")

    def test_srt_render_renumbers(self):
        rendered = render_srt(parse_srt(SRT))
        self.assertIn("1\n00:00:01,000 --> 00:00:02,500", rendered)
        self.assertIn("2\n00:00:03,000 --> 00:00:04,000", rendered)

    def test_parse_webvtt_settings_and_identifier(self):
        cue = parse_vtt(VTT)[0]
        self.assertEqual(cue.identifier, "intro")
        self.assertEqual(cue.settings, "align:start")
        self.assertIn("align:start", render_vtt([cue]))

    def test_rejects_invalid_srt_timestamp(self):
        with self.assertRaises(SubtitleParseError):
            parse_srt("1\n00:61:00,000 --> 00:00:02,000\nBad\n")

    def test_source_line_tracks_timing_line(self):
        cues = parse_srt(
            "\ufeff1\r\n00:00:00,000 --> 00:00:01,000\r\nOne\r\n\r\n"
            "2\r\n00:00:02,000 --> 00:00:03,000\r\nTwo\r\n"
        )
        self.assertEqual([cue.source_line for cue in cues], [2, 6])

    def test_webvtt_skips_note_style_and_region_blocks(self):
        text = """WEBVTT

NOTE comment
ignored

STYLE
::cue { color: white; }

REGION
id:fred

00:00:01.000 --> 00:00:02.000
Visible
"""
        cues = parse_vtt(text)
        self.assertEqual(len(cues), 1)
        self.assertEqual(cues[0].text, "Visible")
        self.assertEqual(cues[0].source_line, 12)


if __name__ == "__main__":
    unittest.main()
