# Subtitle format support

SubtitleOps converts every supported format into an immutable cue sequence with integer millisecond timing. A document layer retains format-level data only where lossless behavior is explicitly implemented.

## Support matrix

| Capability | SRT | WebVTT | TTML / DFXP |
| --- | --- | --- | --- |
| Check/lint | Yes | Yes | Yes, documented subset |
| Directory discovery | `.srt` | `.vtt` | `.ttml`, `.dfxp` |
| Convert into format | Yes | Yes | Canonical cue-only TTML |
| Convert out of format | Yes | Yes | Yes |
| Same-format `fix` | Yes | Yes, document blocks preserved | Refused |
| Cue identifiers | Renumbered on output | Preserved | `xml:id` when valid |
| Format-level metadata | Not modeled | Header + NOTE/STYLE/REGION preserved | Not round-tripped |

## SRT

- UTF-8 and UTF-8 BOM are accepted.
- CRLF/CR are normalized while parsing; rendered output uses LF.
- Timing uses `HH:MM:SS,mmm`.
- Output cue numbers are generated sequentially.
- Non-timing content before a timing line is accepted as the source identifier but is not retained in rendered SRT because output is canonical and renumbered.

## WebVTT

SubtitleOps requires a valid `WEBVTT` signature and a blank line between the header and body.

The document model retains:

- the signature line and following header metadata lines;
- cue identifiers and cue settings;
- `STYLE`, `REGION`, and `NOTE` blocks;
- the number of cues preceding each document block, so NOTE placement remains stable after timing or whitespace repair.

When converting WebVTT to another format, only cues are transferred. Format-specific header and document blocks do not have a general equivalent in SRT or canonical TTML.

## TTML / DFXP

SubtitleOps implements a deliberately bounded media-time subset suitable for deterministic QA and cue conversion. It is not a full TTML presentation engine.

### Accepted structure

- a `tt` root element;
- nested `body`, `div`, and other parallel containers;
- timed `p` elements as cues;
- untimed nested spans and `<br>` for text extraction;
- `xml:id` plus inherited/container-or-`p` `xml:space="default|preserve"`;
- inherited timing from timed ancestors.

Namespace prefixes are not fixed; elements and attributes are matched by local name where appropriate.

### Accepted time expressions

- clock time: `HH:MM:SS` or `HH:MM:SS.fraction`;
- frame clock: `HH:MM:SS:frames` with optional sub-frames;
- offsets with explicit `h`, `m`, `s`, `ms`, `f`, or `t` metrics;
- `ttp:frameRate`, `ttp:frameRateMultiplier`, `ttp:subFrameRate`, and `ttp:tickRate`.

Timing is resolved against ancestor begin times under `timeContainer="par"`. A cue must obtain a finite end through `end`, `dur`, or a timed ancestor.

### Explicitly rejected

- `DOCTYPE` and `ENTITY` declarations;
- malformed XML;
- `ttp:timeBase` values other than `media`;
- wallclock expressions;
- sequential (`timeContainer="seq"`) timing;
- simultaneous `end` and `dur` on one element;
- frame/tick expressions without the required timing parameters;
- timed inline descendants, nested `p` elements, and descendant-level `xml:space` changes that cannot be represented by one cue;
- cue timing that cannot resolve to a finite end.

These cases fail with `PARSE_ERROR`; SubtitleOps does not guess timing semantics.

### Rendering and mutation policy

`render_ttml` creates canonical TTML with one `<p>` per cue, explicit begin/end clock times, escaped text, `<br />` line breaks, and `xml:space="preserve"`.

Arbitrary TTML may contain styling, layout, metadata, animations, regions, nested timed spans, and profile-specific semantics. Because the current cue model cannot preserve all of those, `fix input.ttml` and same-format `convert input.ttml output.ttml` fail explicitly. Converting **from** TTML to SRT/WebVTT or **to** new canonical TTML remains supported.

## Resource limits

All CLI and batch reads pass through the same bounded UTF-8 reader. The default `max_file_bytes` is 10 MiB per file. Set it to `0` only when an upstream component already enforces an appropriate limit.
