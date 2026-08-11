# SubtitleOps rule reference

<a id="timing-order"></a>
## `TIMING_ORDER` — Invalid timing order

- Default severity: `error`
- Category: `timing`

Cue end time is not after its start time.

<a id="negative-start"></a>
## `NEGATIVE_START` — Negative start time

- Default severity: `error`
- Category: `timing`

Cue starts before timestamp zero.

<a id="out-of-order"></a>
## `OUT_OF_ORDER` — Out-of-order cue

- Default severity: `error`
- Category: `timing`

Cue starts before the preceding cue.

<a id="overlap"></a>
## `OVERLAP` — Overlapping cues

- Default severity: `error`
- Category: `timing`

Adjacent cues overlap in time.

<a id="duration-too-short"></a>
## `DURATION_TOO_SHORT` — Cue duration too short

- Default severity: `warning`
- Category: `readability`

Cue duration is below the configured minimum.

<a id="duration-too-long"></a>
## `DURATION_TOO_LONG` — Cue duration too long

- Default severity: `warning`
- Category: `readability`

Cue duration exceeds the configured maximum.

<a id="empty-text"></a>
## `EMPTY_TEXT` — Empty cue

- Default severity: `warning`
- Category: `content`

Cue contains no visible text.

<a id="reading-speed"></a>
## `READING_SPEED` — Reading speed too high

- Default severity: `warning`
- Category: `readability`

Visible characters per second exceed the configured limit.

<a id="line-too-long"></a>
## `LINE_TOO_LONG` — Subtitle line too long

- Default severity: `warning`
- Category: `readability`

A cue line exceeds the configured character limit.

<a id="too-many-lines"></a>
## `TOO_MANY_LINES` — Too many subtitle lines

- Default severity: `warning`
- Category: `readability`

A cue contains more lines than configured.

<a id="trailing-whitespace"></a>
## `TRAILING_WHITESPACE` — Trailing whitespace

- Default severity: `warning`
- Category: `formatting`

A cue line ends with spaces or tabs.

<a id="control-character"></a>
## `CONTROL_CHARACTER` — Control character

- Default severity: `warning`
- Category: `content`

Cue text contains an unexpected control character.

<a id="duplicate-identifier"></a>
## `DUPLICATE_IDENTIFIER` — Duplicate cue identifier

- Default severity: `warning`
- Category: `structure`

A non-empty cue identifier is reused.

<a id="parse-error"></a>
## `PARSE_ERROR` — Subtitle parse error

- Default severity: `error`
- Category: `operational`

The subtitle document could not be parsed.

<a id="io-error"></a>
## `IO_ERROR` — Input/output error

- Default severity: `error`
- Category: `operational`

The subtitle file could not be read.

<a id="decode-error"></a>
## `DECODE_ERROR` — Text decoding error

- Default severity: `error`
- Category: `operational`

The subtitle file is not valid UTF-8 text.

<a id="file-too-large"></a>
## `FILE_TOO_LARGE` — Subtitle file too large

- Default severity: `error`
- Category: `operational`

The subtitle exceeds the configured bounded-read limit.

<a id="input-not-found"></a>
## `INPUT_NOT_FOUND` — Input not found

- Default severity: `error`
- Category: `operational`

A requested input path does not exist.

<a id="unsupported-format"></a>
## `UNSUPPORTED_FORMAT` — Unsupported subtitle format

- Default severity: `error`
- Category: `operational`

A requested file is not a supported text subtitle and no format override was supplied.

<a id="no-files"></a>
## `NO_FILES` — No subtitle files discovered

- Default severity: `error`
- Category: `operational`

Input discovery found no supported subtitle files.
