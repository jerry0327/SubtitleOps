# SubtitleOps

[![CI](https://github.com/jerry0327/SubtitleOps/actions/workflows/ci.yml/badge.svg)](https://github.com/jerry0327/SubtitleOps/actions/workflows/ci.yml)
[![CodeQL](https://github.com/jerry0327/SubtitleOps/actions/workflows/codeql.yml/badge.svg)](https://github.com/jerry0327/SubtitleOps/actions/workflows/codeql.yml)
[![GitHub Release](https://img.shields.io/github/v/release/jerry0327/SubtitleOps?display_name=tag)](https://github.com/jerry0327/SubtitleOps/releases)
[![Python 3.10–3.14](https://img.shields.io/badge/python-3.10%E2%80%933.14-blue)](https://github.com/jerry0327/SubtitleOps/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**SubtitleOps** is a deterministic subtitle quality gate for **SRT**, **WebVTT**, and a conservative **TTML/DFXP** subset. It checks individual files or directory trees, emits text, JSON, or SARIF reports, and performs bounded, opt-in normalization and timing repair without rewriting dialogue.

It belongs between transcription/localization and publication: generated-caption validation, localization handoff, batch media pipelines, CI quality gates, and pre-release checks.

> **Status:** `0.3.0` alpha. The CLI and Python API are tested on Python 3.10–3.14, with additional Windows and macOS CI coverage. Public APIs and defaults may evolve before 1.0; stable diagnostic codes are not silently repurposed.

## Why SubtitleOps

Subtitle defects are often discovered only after a video or learning asset reaches review. General-purpose linters do not understand cue timing, while interactive subtitle editors are difficult to enforce consistently in CI.

SubtitleOps provides:

- reproducible, explainable rules rather than an opaque score;
- stable exit codes, rule IDs, JSON, and SARIF for automation;
- conservative conversion and repair behavior that rejects unsafe loss;
- bounded reads and per-file isolation for untrusted batch inputs;
- a dependency-light runtime suitable for local and CI use.

SubtitleOps deliberately does **not** perform speech recognition, translation, semantic rewriting, media muxing, or visual rendering comparison.

## Quick start

Install from the release tag:

```bash
python -m pip install "git+https://github.com/jerry0327/SubtitleOps.git@v0.3.0"
subtitleops --version
subtitleops check subtitles/
```

For development from a checkout:

```bash
git clone https://github.com/jerry0327/SubtitleOps.git
cd SubtitleOps
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
```

SubtitleOps is not currently claimed as published on PyPI. GitHub release artifacts and checksums are the public release channel.

## Reusable GitHub Action

Pin an immutable release tag or full commit SHA in production:

```yaml
name: Subtitle quality
on: [pull_request]

permissions:
  contents: read
  security-events: write

jobs:
  subtitleops:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with:
          persist-credentials: false
      - uses: jerry0327/SubtitleOps@v0.3.0
        with:
          paths: |
            subtitles/
            trailers/captions.vtt
          upload-sarif: "true"
          fail-on: warning
```

The action exposes `exit-code`, `files-checked`, `issues`, and `report-path`. A floating `v0` tag follows the latest compatible 0.x action release, but immutable version tags or commit SHAs provide stronger supply-chain pinning. See [GitHub Action](docs/github-action.md).

## Capabilities

- recursive `.srt`, `.vtt`, `.ttml`, and `.dfxp` discovery with include/exclude globs;
- deterministic concurrent checking with per-file parse/decode/I/O isolation;
- timing, overlap, duration, reading-speed, line-length, line-count, whitespace, control-character, and identifier diagnostics;
- aggregate text, JSON schema v1, and SARIF 2.1.0 output;
- strict `.subtitleops.toml` and `[tool.subtitleops]` configuration;
- a default 10 MiB per-file bounded-read guard for untrusted inputs;
- SRT ↔ WebVTT ↔ canonical TTML conversion;
- same-format WebVTT repairs that preserve signature metadata plus `NOTE`, `STYLE`, and `REGION` blocks;
- a reusable composite GitHub Action with optional Code Scanning upload;
- standard-library runtime on Python 3.11+; Python 3.10 uses only `tomli` for TOML compatibility.

## Check subtitle files

```bash
subtitleops check subtitles/en.srt
subtitleops check subtitles/
subtitleops check captions/ trailers/ release.ttml --jobs 8
```

Useful controls:

```bash
subtitleops check subtitles/ \
  --max-cps 18 \
  --max-line-length 40 \
  --max-lines 2 \
  --min-duration-ms 300 \
  --max-duration-ms 7000 \
  --max-file-bytes 10485760 \
  --exclude "archive/**" \
  --ignore TRAILING_WHITESPACE
```

`--max-file-bytes 0` disables the size guard. `--no-recursive` checks only an immediate directory. `--jobs 0` selects a bounded automatic worker count.

## Reports and exit contract

```bash
subtitleops check subtitles/ --json -o build/subtitleops.json
subtitleops check subtitles/ --sarif -o build/subtitleops.sarif
```

| Exit | Meaning |
| ---: | --- |
| `0` | Check completed; no finding met the configured failure threshold. |
| `1` | Check completed; at least one finding met `fail_on`. |
| `2` | Configuration, discovery, size guard, decoding, parsing, or I/O failed. |

The failure threshold does not hide findings:

```bash
subtitleops check subtitles/ --fail-on error
subtitleops check subtitles/ --fail-on none
```

See [reporting](docs/reporting.md), [CI integration](docs/ci.md), and the staged [adoption guide](docs/adoption.md).

## Configuration

SubtitleOps searches upward for `.subtitleops.toml`, then for a `pyproject.toml` with `[tool.subtitleops]`.

```toml
version = 1

[check]
max_cps = 18.0
max_line_length = 40
max_lines = 2
min_duration_ms = 300
max_duration_ms = 7000
max_file_bytes = 10485760
fail_on = "warning"
ignore = ["TRAILING_WHITESPACE"]
include = ["*.srt", "*.vtt", "*.ttml", "*.dfxp"]
exclude = ["vendor/**", "archive/**"]
recursive = true
jobs = 0
allow_empty = false
```

Command-line values override file settings. Use `--config PATH` to select a file or `--no-config` for reproducible defaults. See [configuration](docs/configuration.md).

## Formats

### SRT and WebVTT

```bash
subtitleops convert captions.srt captions.vtt
subtitleops fix captions.vtt --shift-ms 750
```

SRT output is renumbered. WebVTT cue identifiers and cue settings are preserved. When a WebVTT document is repaired without changing format, its header metadata and document-level `NOTE`, `STYLE`, and `REGION` blocks retain their relative placement.

### TTML / DFXP

```bash
subtitleops check captions.ttml
subtitleops convert captions.ttml captions.srt
subtitleops convert captions.vtt captions.ttml
```

The TTML parser accepts media-time documents with parallel timing, nested timed containers, clock/offset/frame/tick expressions, `xml:space`, untimed spans, and `<br>`. Canonical TTML output intentionally contains cue text and timing only.

Same-format TTML rewriting is refused because flattening an arbitrary TTML document could discard styling, layout, metadata, and inline semantics. Convert TTML to SRT/WebVTT, or generate a new canonical TTML file from another format. The exact supported subset is documented in [formats](docs/formats.md).

## Rules

```bash
subtitleops rules
subtitleops rules --json
subtitleops rules --all
```

Every lint and operational diagnostic has a stable code, default severity, category, and documentation URI. See [rule reference](docs/rules.md).

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

`parse_srt`, `parse_vtt`, `parse_ttml`, document-aware WebVTT APIs, renderers, and `lint_cues` are also exported.

## Project and maintenance

- [Project brief](docs/project-brief.md): problem, intended users, current evidence, and adoption status.
- [Architecture](docs/design.md): deterministic and safety constraints.
- [Roadmap](ROADMAP.md): planned 0.x increments and 1.0 criteria.
- [Governance](GOVERNANCE.md): maintainer roles and decision process.
- [Maintainer playbook](docs/maintainer-playbook.md): triage, review, dependency, and release workflows.
- [Support](SUPPORT.md) and [security](SECURITY.md): public and private reporting paths.
- [Contributing](CONTRIBUTING.md) and [code of conduct](CODE_OF_CONDUCT.md).

The project is newly public and does not claim external adoption, downloads, or ecosystem-critical status without verifiable evidence. Public users can submit an adoption report without sharing private subtitle data.

## Design constraints

1. **Deterministic output:** thread scheduling and filesystem order do not alter reports.
2. **Conservative mutation:** unsupported lossless edits fail instead of silently discarding data.
3. **Stable automation contracts:** exit codes, rule IDs, JSON, and SARIF are product surfaces.
4. **Bounded resource use:** files are read through a configurable byte limit by default.
5. **Untrusted input:** malformed XML/text is isolated and unsafe TTML declarations are rejected.
6. **No opaque scoring:** all checks are explainable and reproducible.

## License and citation

MIT. See [LICENSE](LICENSE). Citation metadata is provided in [CITATION.cff](CITATION.cff).
