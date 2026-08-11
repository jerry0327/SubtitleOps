# SubtitleOps design notes

SubtitleOps separates subtitle processing into four small layers so each can be tested independently.

## 1. Model

`Cue` is the internal representation. Timing is stored as integer milliseconds rather than floating point seconds to avoid precision drift during repeated transformations.

Fields:

- `start_ms`
- `end_ms`
- `text`
- optional `identifier`
- optional format-specific `settings`

The model deliberately does not encode a global subtitle document object yet. That keeps the first API small, while leaving room for document-level metadata when richer WebVTT/TTML support is added.

## 2. Formats

`subtitleops.formats` owns parsing and rendering.

Current guarantees:

- UTF-8 and UTF-8 BOM input are accepted by the CLI;
- CRLF/CR input is normalized while parsing;
- rendered output uses LF newlines;
- SRT cues are renumbered on output;
- WebVTT cue identifiers and cue settings are preserved for supported cues;
- malformed timestamp syntax raises `SubtitleParseError` rather than being silently guessed.

The parser intentionally skips WebVTT `NOTE`, `STYLE`, and `REGION` blocks in v0.1. Preserving arbitrary non-cue blocks requires a document-level representation and is a roadmap item.

## 3. Linting

Linting is read-only. Each finding has a stable-ish code, severity, cue number, and human-readable message.

Current codes:

| Code | Severity | Meaning |
| --- | --- | --- |
| `TIMING_ORDER` | error | cue end is not after its start |
| `NEGATIVE_START` | error | cue starts before 0 |
| `OUT_OF_ORDER` | error | cue starts before the previous cue |
| `OVERLAP` | error | adjacent cues overlap |
| `EMPTY_TEXT` | warning | no visible cue text |
| `READING_SPEED` | warning | visible characters per second exceed limit |
| `LINE_TOO_LONG` | warning | a cue line exceeds the configured length |
| `TOO_MANY_LINES` | warning | cue has more than the configured number of lines |

Before 1.0, codes may still be added or refined. Existing codes should not be repurposed to mean something unrelated.

## 4. Transforms

Transforms return new immutable `Cue` objects instead of mutating input objects.

### Whitespace normalization

Only edge whitespace is normalized. Wording and line boundaries are not semantically rewritten.

### Timing shift

A requested negative shift is clipped globally when needed so the earliest cue starts at zero. All cue durations remain unchanged.

### Overlap repair

Overlap repair is intentionally conservative. The earlier cue is clipped to the next cue's start only when the remaining duration is at least `min_duration_ms`. Otherwise the overlap is left unchanged and can still be reported by `check`.

## CLI contract

Exit codes are designed for CI:

- `0`: command succeeded; for `check`, no findings were produced;
- `1`: `check` completed and found lint issues;
- `2`: parse, input, output, or argument-related operational failure.

`check --json` prints one JSON document to stdout so callers do not need to parse human-readable text.

## Non-goals for the initial release

- media-container muxing/demuxing;
- speech recognition;
- machine translation;
- automatic dialogue rewriting;
- pixel-perfect subtitle rendering.

Those jobs belong to other layers of a media pipeline. SubtitleOps is intended to compose with them.
