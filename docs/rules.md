# Diagnostic rules

Rule codes are automation-facing identifiers. Default severities may be overridden only by future documented functionality; they are listed here for the current release. Use `subtitleops rules --json` for machine-readable metadata.

## Timing

<a id="timing-order"></a>
### `TIMING_ORDER` — error

Cue end time is equal to or earlier than its start time. This is structurally invalid and blocks meaningful duration/readability calculations.

<a id="negative-start"></a>
### `NEGATIVE_START` — error

Cue starts before timestamp zero.

<a id="out-of-order"></a>
### `OUT_OF_ORDER` — error

A cue starts before the preceding cue's start. This is distinct from overlap: two ordered cues can overlap without being out of order.

<a id="overlap"></a>
### `OVERLAP` — error

A cue starts before the preceding cue ends. `fix --resolve-overlaps` can clip the earlier cue only when the resulting duration remains above its repair minimum.

## Readability

<a id="duration-too-short"></a>
### `DURATION_TOO_SHORT` — warning

Positive cue duration is below `min_duration_ms`. Set the limit to `0` to disable this rule.

<a id="duration-too-long"></a>
### `DURATION_TOO_LONG` — warning

Cue duration exceeds `max_duration_ms`. Set the limit to `0` to disable this rule.

<a id="reading-speed"></a>
### `READING_SPEED` — warning

Visible non-whitespace characters divided by cue duration exceeds `max_cps`. This is a deterministic character-rate measure, not language-aware reading-time prediction.

<a id="line-too-long"></a>
### `LINE_TOO_LONG` — warning

At least one cue line exceeds `max_line_length` characters.

<a id="too-many-lines"></a>
### `TOO_MANY_LINES` — warning

Cue line count exceeds `max_lines`.

## Content and structure

<a id="empty-text"></a>
### `EMPTY_TEXT` — warning

Cue has no visible text after whitespace is ignored.

<a id="trailing-whitespace"></a>
### `TRAILING_WHITESPACE` — warning

At least one cue line ends in spaces or tabs. `fix` normalizes this condition.

<a id="control-character"></a>
### `CONTROL_CHARACTER` — warning

Cue text contains an unexpected ASCII control character. Newline and tab are not flagged.

<a id="duplicate-identifier"></a>
### `DUPLICATE_IDENTIFIER` — warning

A non-empty cue identifier is reused in the same document.

## Operational diagnostics

Operational codes are included by `subtitleops rules --all`. They return exit code `2` when encountered.

<a id="parse-error"></a>
### `PARSE_ERROR` — error

The selected parser could not interpret the document.

<a id="io-error"></a>
### `IO_ERROR` — error

A path could not be listed/read or was not a regular file/directory.

<a id="decode-error"></a>
### `DECODE_ERROR` — error

Input is not valid UTF-8/UTF-8-BOM text.

<a id="input-not-found"></a>
### `INPUT_NOT_FOUND` — error

A requested input path does not exist.

<a id="unsupported-format"></a>
### `UNSUPPORTED_FORMAT` — error

An explicit file is not `.srt`/`.vtt` and no `--format` override was supplied.

<a id="no-files"></a>
### `NO_FILES` — error

No supported file was discovered and `allow_empty` is false.
