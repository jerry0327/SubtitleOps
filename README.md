# SubtitleOps

[![CI](https://github.com/jerry0327/SubtitleOps/actions/workflows/ci.yml/badge.svg)](https://github.com/jerry0327/SubtitleOps/actions/workflows/ci.yml)

**SubtitleOps** is a dependency-light Python CLI and library for checking and repairing subtitle files in automation pipelines.

It focuses on deterministic operations that are safe to run in CI, batch jobs, media pipelines, and pre-release checks: parse subtitles, flag common timing/readability problems, normalize files, repair simple overlaps, shift timing, and convert between SRT and WebVTT.

> Status: early alpha. The command surface is usable, but format coverage and lint rules will grow before a 1.0 release.

## Why SubtitleOps?

Subtitle tooling is often either a GUI editor or a large media stack. SubtitleOps targets the smaller operational layer between transcription and publishing:

- fail CI when a subtitle track contains structural or timing problems;
- produce machine-readable lint output for other tools;
- normalize generated subtitles before diffing or committing them;
- perform conservative timing repairs without rewriting dialogue;
- convert common text subtitle formats without pulling in a multimedia runtime.

## Features

- SRT and WebVTT parsing/rendering
- lint rules for:
  - invalid or reversed timing;
  - negative starts;
  - out-of-order cues;
  - overlapping cues;
  - empty cues;
  - excessive reading speed (characters per second);
  - long lines and too many lines;
- JSON lint output
- whitespace normalization
- global timing shift with negative-time protection
- conservative overlap repair
- SRT ↔ WebVTT conversion
- no runtime dependencies
- standard-library unit tests and GitHub Actions CI

## Install

From a local checkout:

```bash
python -m pip install -e .
```

Then verify the CLI:

```bash
subtitleops --version
```

Python 3.10+ is supported.

## Quick start

### Check a file

```bash
subtitleops check subtitles.srt
```

A clean file exits with status `0`. A file with lint findings exits with status `1`; parse or I/O failures exit with status `2`.

Customize readability limits:

```bash
subtitleops check subtitles.srt --max-cps 18 --max-line-length 40 --max-lines 2
```

Machine-readable output:

```bash
subtitleops check subtitles.srt --json
```

Example shape:

```json
{
  "file": "subtitles.srt",
  "cues": 24,
  "issues": [
    {
      "code": "OVERLAP",
      "severity": "error",
      "cue": 8,
      "message": "overlaps previous cue by 120 ms"
    }
  ]
}
```

### Normalize or repair

Normalize whitespace and rewrite a canonical subtitle file:

```bash
subtitleops fix subtitles.srt -o normalized.srt
```

Shift the entire track by 750 ms:

```bash
subtitleops fix subtitles.srt -o shifted.srt --shift-ms 750
```

Resolve simple adjacent overlaps by clipping the earlier cue when the result remains valid:

```bash
subtitleops fix subtitles.srt -o repaired.srt --resolve-overlaps
```

### Convert formats

```bash
subtitleops convert subtitles.srt subtitles.vtt
subtitleops convert subtitles.vtt subtitles.srt
```

## Use as a Python library

```python
from subtitleops import lint_cues, parse_srt

with open("subtitles.srt", encoding="utf-8-sig") as handle:
    cues = parse_srt(handle.read())

for issue in lint_cues(cues, max_cps=18):
    print(issue.code, issue.cue, issue.message)
```

## Design principles

1. **Deterministic first.** Given the same input and options, output should be reproducible.
2. **Conservative repair.** SubtitleOps should not silently rewrite dialogue or guess semantic edits.
3. **Pipeline-friendly.** Exit codes and JSON output are part of the product, not afterthoughts.
4. **Dependency-light.** Core text-subtitle operations should not require ffmpeg or a large runtime.
5. **Test malformed input.** Subtitle files in production are frequently imperfect; failure behavior should be explicit.

See [docs/design.md](docs/design.md) for the current architecture and compatibility rules.

## Development

```bash
git clone https://github.com/jerry0327/SubtitleOps.git
cd SubtitleOps
python -m pip install -e .
python -m unittest discover -s tests -v
```

Try the bundled samples:

```bash
subtitleops check examples/clean.srt
subtitleops check examples/problematic.srt
```

The second command is expected to report findings and exit with status `1`.

## Roadmap

Near-term work is tracked in GitHub issues. Candidate directions include:

- TTML/DFXP support;
- richer WebVTT block preservation;
- configurable rule profiles for broadcast/web/social workflows;
- batch-directory checking with aggregate JSON/SARIF output;
- semantic-preserving line reflow;
- fuzz/property tests for malformed subtitle inputs;
- stable public Python API documentation.

## Contributing

Bug reports, format edge cases, tests, and narrowly scoped features are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

For security-sensitive reports, follow [SECURITY.md](SECURITY.md) rather than opening a public issue.

## License

MIT. See [LICENSE](LICENSE).
