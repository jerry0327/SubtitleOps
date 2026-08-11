import unittest

from subtitleops.formats import SubtitleParseError, parse_ttml, render_ttml
from subtitleops.models import Cue

TTML = """<?xml version="1.0" encoding="UTF-8"?>
<tt xmlns="http://www.w3.org/ns/ttml">
  <body begin="1s">
    <div begin="500ms">
      <p xml:id="intro" begin="500ms" dur="2s">Hello <span>world</span>.<br/>Second line.</p>
      <p begin="3s" end="5s">Second cue.</p>
    </div>
  </body>
</tt>
"""


class TTMLTests(unittest.TestCase):
    def test_parent_relative_timing_and_text(self):
        cues = parse_ttml(TTML)
        self.assertEqual([(cue.start_ms, cue.end_ms) for cue in cues], [(2000, 4000), (4500, 6500)])
        self.assertEqual(cues[0].identifier, "intro")
        self.assertEqual(cues[0].text, "Hello world.\nSecond line.")

    def test_clock_offset_frame_and_tick_expressions(self):
        text = """<tt xmlns="http://www.w3.org/ns/ttml" xmlns:ttp="http://www.w3.org/ns/ttml#parameter"
 ttp:frameRate="25" ttp:tickRate="100">
<body><div>
<p begin="00:00:01:12" dur="25f">Frame cue</p>
<p begin="250t" dur="500ms">Tick cue</p>
</div></body></tt>"""
        cues = parse_ttml(text)
        self.assertEqual((cues[0].start_ms, cues[0].end_ms), (1480, 2480))
        self.assertEqual((cues[1].start_ms, cues[1].end_ms), (2500, 3000))

    def test_fractional_clock_rounds_to_nearest_millisecond(self):
        cue = parse_ttml(
            '<tt xmlns="http://www.w3.org/ns/ttml"><body><div>'
            '<p begin="00:00:00.0005" end="00:00:01.0005">x</p>'
            '</div></body></tt>'
        )[0]
        self.assertEqual((cue.start_ms, cue.end_ms), (1, 1001))

    def test_xml_space_preserve(self):
        cue = parse_ttml(
            '<tt xmlns="http://www.w3.org/ns/ttml"><body><div>'
            '<p begin="0s" dur="1s" xml:space="preserve">  keep   spacing  </p>'
            '</div></body></tt>'
        )[0]
        self.assertEqual(cue.text, "  keep   spacing  ")

    def test_render_round_trip(self):
        cues = [Cue(0, 1250, "Hello & <world>\nSecond", identifier="intro")]
        rendered = render_ttml(cues)
        parsed = parse_ttml(rendered)
        self.assertEqual([(c.start_ms, c.end_ms, c.text, c.identifier) for c in parsed], [
            (0, 1250, "Hello & <world>\nSecond", "intro")
        ])

    def test_rejects_doctype_and_entity(self):
        text = """<!DOCTYPE tt [<!ENTITY x "boom">]>
<tt xmlns="http://www.w3.org/ns/ttml"><body><div><p begin="0s" dur="1s">&x;</p></div></body></tt>"""
        with self.assertRaisesRegex(SubtitleParseError, "DOCTYPE"):
            parse_ttml(text)

    def test_rejects_unsupported_time_base(self):
        with self.assertRaisesRegex(SubtitleParseError, "only media"):
            parse_ttml(
                '<tt xmlns="http://www.w3.org/ns/ttml" '
                'xmlns:ttp="http://www.w3.org/ns/ttml#parameter" ttp:timeBase="clock">'
                '<body><div><p begin="0s" dur="1s">x</p></div></body></tt>'
            )

    def test_rejects_seq_time_container(self):
        with self.assertRaisesRegex(SubtitleParseError, "timeContainer"):
            parse_ttml(
                '<tt xmlns="http://www.w3.org/ns/ttml"><body timeContainer="seq">'
                '<div><p begin="0s" dur="1s">x</p></div></body></tt>'
            )

    def test_rejects_timed_inline_descendant(self):
        with self.assertRaisesRegex(SubtitleParseError, "timed descendants"):
            parse_ttml(
                '<tt xmlns="http://www.w3.org/ns/ttml"><body><div>'
                '<p begin="0s" dur="2s">one <span begin="1s">two</span></p>'
                '</div></body></tt>'
            )

    def test_rejects_non_integer_timing_parameters(self):
        with self.assertRaisesRegex(SubtitleParseError, "positive integer"):
            parse_ttml(
                '<tt xmlns="http://www.w3.org/ns/ttml" '
                'xmlns:ttp="http://www.w3.org/ns/ttml#parameter" ttp:frameRate="25.0">'
                '<body><div><p begin="0s" dur="1s">x</p></div></body></tt>'
            )

    def test_p_requires_resolved_end(self):
        with self.assertRaisesRegex(SubtitleParseError, "requires end"):
            parse_ttml(
                '<tt xmlns="http://www.w3.org/ns/ttml"><body><div>'
                '<p begin="0s">x</p></div></body></tt>'
            )


if __name__ == "__main__":
    unittest.main()
