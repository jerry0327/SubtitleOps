# Configuration

SubtitleOps configuration is versioned TOML. Use either a dedicated `.subtitleops.toml` or a `pyproject.toml` table.

## Discovery

For `subtitleops check`, the CLI searches from the current working directory upward:

1. nearest `.subtitleops.toml`;
2. nearest `pyproject.toml` containing `[tool.subtitleops]`.

The search stops at the first matching file. Use `--config PATH` to select a file directly or `--no-config` to bypass discovery.

Configuration discovery is based on the current directory, not the first subtitle input. This makes monorepo behavior predictable and avoids different settings for different input arguments in one batch.

## Dedicated file

```toml
version = 1

[check]
max_cps = 18.0
max_line_length = 40
max_lines = 2
min_duration_ms = 300
max_duration_ms = 7000
fail_on = "warning"
ignore = ["TRAILING_WHITESPACE"]
include = ["*.srt", "*.vtt"]
exclude = ["archive/**", "vendor/**"]
recursive = true
jobs = 0
allow_empty = false
```

## `pyproject.toml`

```toml
[tool.subtitleops]
version = 1

[tool.subtitleops.check]
max_cps = 18.0
max_line_length = 40
fail_on = "warning"
```

Other `pyproject.toml` tables are ignored.

## Keys

| Key | Type | Default | Meaning |
| --- | --- | --- | --- |
| `max_cps` | number | `20.0` | Maximum visible non-whitespace characters per second. |
| `max_line_length` | integer | `42` | Maximum characters in any cue line. |
| `max_lines` | integer | `2` | Maximum lines in one cue. |
| `min_duration_ms` | integer | `300` | Minimum positive cue duration; `0` disables the rule. |
| `max_duration_ms` | integer | `7000` | Maximum cue duration; `0` disables the rule. |
| `fail_on` | string | `warning` | Exit `1` on `info`, `warning`, `error`, or `none`. |
| `ignore` | string array | `[]` | Rule codes removed from reports. |
| `include` | string array | `*.srt`, `*.vtt` | Directory file-selection globs. |
| `exclude` | string array | build/cache defaults | Directory/file exclusion globs. |
| `recursive` | boolean | `true` | Recurse through input directories. |
| `jobs` | integer | `0` | Worker count; `0` selects automatically, maximum `256`. |
| `allow_empty` | boolean | `false` | Permit zero discovered subtitle files without exit `2`. |

## Glob behavior

Patterns are matched against both the relative POSIX path and basename. Therefore `*.srt` matches nested SRT basenames, while `archive/**` targets a relative directory tree.

Default exclusions cover common `.git`, virtual-environment, build, distribution, and `__pycache__` trees. Command-line `--exclude` values are added to configured defaults. Command-line `--include` values replace the configured include list.

Examples:

```bash
subtitleops check . --include "*.vtt"
subtitleops check . --exclude "fixtures/**" --exclude "legacy/**"
subtitleops check . --no-recursive
```

## Rule suppression versus thresholds

These controls serve different purposes:

- `ignore = ["RULE"]` removes the finding from text, JSON, and SARIF;
- `fail_on = "error"` keeps warnings visible but does not fail the process for them.

Prefer `fail_on` when a team still wants visibility. Use `ignore` only when a rule is not applicable to the project.

## Precedence

Later layers override earlier layers:

1. built-in defaults;
2. configuration file;
3. command line.

List-valued behavior is intentional:

- CLI `--include` replaces configured include patterns;
- CLI `--exclude` extends configured exclusions;
- CLI `--ignore` extends configured ignored codes and de-duplicates them.

## Validation

SubtitleOps rejects:

- unknown configuration keys;
- unknown ignored rule codes;
- incorrect value types;
- empty include lists;
- non-positive CPS/line limits;
- negative duration limits;
- maximum duration below a non-zero minimum;
- invalid `fail_on` values;
- worker counts outside `0..256`.

Strict validation is part of the CI safety model: a typo must not silently weaken the quality gate.
