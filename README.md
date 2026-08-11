# SubtitleOps

[![CI](https://github.com/jerry0327/SubtitleOps/actions/workflows/ci.yml/badge.svg)](https://github.com/jerry0327/SubtitleOps/actions/workflows/ci.yml)
[![CodeQL](https://github.com/jerry0327/SubtitleOps/actions/workflows/codeql.yml/badge.svg)](https://github.com/jerry0327/SubtitleOps/actions/workflows/codeql.yml)

**SubtitleOps** is a deterministic subtitle quality gate for SRT and WebVTT files. It checks single files or entire directory trees, produces text, JSON, or SARIF reports, and performs conservative normalization and timing repairs without rewriting dialogue.

It is designed for the operational layer between transcription and publication: CI checks, batch media pipelines, localization handoff, generated-caption validation, and pre-release quality control.

> **Status:** `0.2.0` alpha. The CLI is usable and tested on Python 3.10–3.14, but public APIs and rule defaults may still evolve before 1.0.

## What it does

- recursively discovers `.srt` and `.vtt` files with include/exclude globs;
- checks files concurrently while preserving deterministic output order;
- isolates parse and decode failures so one damaged file does not hide results from the rest of a batch;
- reports stable diagnostic codes for timing, structure, readability, and formatting;
- emits aggregate **JSON** for automation and **SARIF 2.1.0** for code-scanning systems;
- reads project settings from `.subtitleops.toml` or `[tool.subtitleops]` in `pyproject.toml`;
- normalizes whitespace, shifts timing, repairs safe adjacent overlaps, and converts SRT ↔ WebVTT;
- uses only the Python standard library on 3.11+; Python 3.10 installs the small `tomli` compatibility package.

SubtitleOps deliberately does **not** perform speech recognition, translation, dialogue rewriting, or media-container muxing. Those jobs belong to other pipeline stages.

## Install

From a checkout:

```bash
python -m pip install -e .
subtitleops --version
```

For development and package-building tools:

```bash
python -m pip install -e ".[dev]"
```

## Check subtitles

### One file

```bash
subtitleops check subtitles/en.srt
```

### A directory tree

```bash
subtitleops check subtitles/
```

Multiple inputs are accepted and duplicate paths are de-duplicated:

```bash
subtitleops check captions/ trailers/ release-notes.vtt --jobs 8
```

Useful controls:

```bash
subtitleops check subtitles/ \
  --max-cps 18 \
  --max-line-length 40 \
  --max-lines 2 \
  --min-duration-ms 300 \
  --max-duration-ms 7000 \
  --exclude "archive/**" \
  --ignore TRAILING_WHITESPACE
```

`--no-recursive` limits directory discovery to the immediate directory. `--include` replaces the configured include patterns; `--exclude` adds patterns to the configured exclusions. `--jobs 0` selects a bounded automatic worker count.

## Reports

### JSON

```bash
subtitleops check subtitles/ --json -o build/subtitleops.json
```

The JSON envelope contains tool/schema versions, configuration source, aggregate counts, discovery errors, per-file parse state, cues, and structured findings. Use `-o -` when an explicit stdout target is useful in scripts.

### SARIF

```bash
subtitleops check subtitles/ --sarif -o build/subtitleops.sarif
```

SARIF results include stable rule IDs, severity, artifact URI, source line where available, cue number, cue timing, and deterministic partial fingerprints for cross-run tracking. See [docs/ci.md](docs/ci.md) for GitHub Code Scanning integration and [docs/reporting.md](docs/reporting.md) for the report contract.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Check completed and no finding met the configured failure threshold. |
| `1` | Check completed and at least one finding met `fail_on`. |
| `2` | Configuration, discovery, decoding, parsing, or I/O failed. |

The threshold can be changed without suppressing findings:

```bash
subtitleops check subtitles/ --fail-on error
subtitleops check subtitles/ --fail-on none
```

Operational failures still return `2`.

## Configuration

SubtitleOps searches from the current directory upward for the nearest `.subtitleops.toml`, then for a `pyproject.toml` containing `[tool.subtitleops]`.

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
exclude = ["vendor/**", "archive/**"]
recursive = true
jobs = 0
allow_empty = false
```

The equivalent `pyproject.toml` location is `[tool.subtitleops.check]`. Command-line values override file settings. Use `--config PATH` to select a file explicitly or `--no-config` for reproducible default-only execution.

Full details: [docs/configuration.md](docs/configuration.md).

## Rules

List lint rule metadata:

```bash
subtitleops rules
subtitleops rules --json
subtitleops rules --all
```

The current rules cover:

- reversed/negative/out-of-order timing and overlaps;
- minimum and maximum cue duration;
- reading speed, line length, and line count;
- empty text, trailing whitespace, control characters, and duplicate identifiers.

Every code and default severity is documented in [docs/rules.md](docs/rules.md). Codes are intended for automation and will not be silently repurposed to mean unrelated conditions.

## Normalize or repair

Normalize edge whitespace and write canonical output:

```bash
subtitleops fix subtitles.srt -o normalized.srt
```

Shift the entire track while preventing negative timestamps:

```bash
subtitleops fix subtitles.srt -o shifted.srt --shift-ms 750
```

Resolve simple adjacent overlaps by clipping the earlier cue only when the `--min-duration-ms` repair minimum remains valid:

```bash
subtitleops fix subtitles.srt -o repaired.srt --resolve-overlaps
```

Repairs are conservative and opt-in. SubtitleOps does not invent wording or semantic line breaks.
Output files are written by atomic replacement so an interrupted command does not leave a partially written subtitle or report; in-place fixes preserve the existing permission mode when the platform permits it.

## Convert formats

```bash
subtitleops convert subtitles.srt subtitles.vtt
subtitleops convert subtitles.vtt subtitles.srt
```

SRT output is renumbered. Supported WebVTT cue identifiers and settings are preserved; document-level `STYLE`, `REGION`, and `NOTE` blocks are recognized and skipped, not round-tripped.

## Python API

```python
from pathlib import Path

from subtitleops import CheckConfig, run_check

report = run_check(
    [Path("subtitles")],
    CheckConfig(max_cps=18.0, fail_on="error", jobs=4),
)

for file in report.files:
    for issue in file.issues:
        print(file.path, issue.code, issue.cue, issue.message)

raise SystemExit(report.exit_code())
```

The package also exports cue parsing/rendering and `lint_cues` for focused integrations.

## Development

```bash
git clone https://github.com/jerry0327/SubtitleOps.git
cd SubtitleOps
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python -m compileall -q src tests
subtitleops check examples/clean.srt --no-config
python -m build
```

The test suite covers parsing, source locations, rule behavior, configuration, recursive discovery, concurrency, batch error isolation, CLI compatibility, JSON, SARIF, transforms, and conversion.

## Design constraints

1. **Deterministic output:** file and finding order must not depend on thread scheduling.
2. **Conservative mutation:** repairs must be explicit and must not rewrite dialogue.
3. **Pipeline contracts:** exit codes, rule IDs, and machine-readable schemas are product surfaces.
4. **Bounded dependencies:** text-subtitle checks must not require ffmpeg or a multimedia runtime.
5. **Untrusted input:** malformed files fail explicitly and are isolated within batch reports.
6. **No fabricated intelligence:** rules are explainable and reproducible rather than opaque scoring.

See [docs/design.md](docs/design.md).

## Roadmap

The next likely increments are richer WebVTT document preservation, TTML/DFXP, configurable rule profiles, semantic-preserving line reflow, and fuzz/property testing. These are roadmap items, not current capabilities.

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and [SECURITY.md](SECURITY.md). Do not place private or copyrighted subtitle dialogue in public bug reports unless it is necessary and authorized.

## License

MIT. See [LICENSE](LICENSE).
