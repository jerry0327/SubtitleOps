# Configuration

SubtitleOps uses a strict, versioned TOML configuration. Unknown keys and invalid values are errors; misspellings never silently weaken a quality gate.

## Locations and precedence

Search starts at the current directory and walks upward:

1. `.subtitleops.toml`;
2. `pyproject.toml` containing `[tool.subtitleops]`.

Precedence is built-in defaults, discovered/explicit configuration, then CLI overrides. `--config PATH` selects a file; `--no-config` disables discovery. They cannot be combined.

## Dedicated file

```toml
version = 1

[check]
max_cps = 20.0
max_line_length = 42
max_lines = 2
min_duration_ms = 300
max_duration_ms = 7000
max_file_bytes = 10485760
fail_on = "warning"
ignore = []
include = ["*.srt", "*.vtt", "*.ttml", "*.dfxp"]
exclude = ["vendor/**"]
recursive = true
jobs = 0
allow_empty = false
```

In `pyproject.toml`, use `[tool.subtitleops]` and `[tool.subtitleops.check]` with the same keys.

## Check keys

| Key | Type | Default | Constraint |
| --- | --- | ---: | --- |
| `max_cps` | number | `20.0` | Greater than zero. |
| `max_line_length` | integer | `42` | Greater than zero. |
| `max_lines` | integer | `2` | Greater than zero. |
| `min_duration_ms` | integer | `300` | Non-negative; `0` disables. |
| `max_duration_ms` | integer | `7000` | Non-negative; `0` disables. |
| `max_file_bytes` | integer | `10485760` | Non-negative; `0` disables the bounded-read guard. |
| `fail_on` | string | `warning` | `info`, `warning`, `error`, or `none`. |
| `ignore` | string array | `[]` | Known lint codes only. |
| `include` | string array | four format globs | Must not be empty. |
| `exclude` | string array | repository/build defaults | May be empty. |
| `recursive` | boolean | `true` | Directory traversal policy. |
| `jobs` | integer | `0` | `0` auto-selects; otherwise 1–256. |
| `allow_empty` | boolean | `false` | Whether no discovered files is success. |

The size guard is applied after discovery and before UTF-8 decoding. An oversized file becomes a per-file `FILE_TOO_LARGE` operational error; other files in the batch are still checked.

## CLI overrides

`--include` replaces configured include patterns. `--exclude` appends to configured exclusions. Repeated/comma-separated `--ignore` values are merged with configured ignored rules.

```bash
subtitleops check subtitles/ \
  --max-file-bytes 5242880 \
  --fail-on error \
  --include "*.srt,*.ttml" \
  --exclude "legacy/**"
```
