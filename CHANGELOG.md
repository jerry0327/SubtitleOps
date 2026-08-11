# Changelog

All notable user-facing changes are documented here.

SubtitleOps follows semantic versioning once public releases begin. Before 1.0, minor versions may refine public APIs and defaults; diagnostic codes are not repurposed without an explicit changelog entry.

## 0.3.0 - 2026-08-12

### Added

- TTML/DFXP discovery, parsing, linting, and conversion;
- media-time clock, offset, frame, sub-frame, and tick expression support;
- nested parallel TTML timing resolution, `xml:space`, span text, and `<br>` handling;
- canonical TTML rendering for SRT/WebVTT/TTML conversion workflows;
- document-aware WebVTT parsing that preserves signature metadata and `NOTE`, `STYLE`, and `REGION` blocks during same-format fixes;
- configurable `max_file_bytes` bounded reads with `FILE_TOO_LARGE` operational diagnostics;
- reusable composite GitHub Action with SARIF generation, optional Code Scanning upload, job summary, and structured outputs;
- seeded deterministic format round-trip tests and dedicated TTML, file-I/O, and action-runner regression suites;
- format support and GitHub Action documentation.

### Changed

- default discovery includes `.ttml` and `.dfxp`;
- package description and keywords include TTML/DFXP;
- `fix` and `convert` accept `--max-file-bytes`;
- CI checks SRT, WebVTT, and TTML, validates conversion, and executes the repository's own composite action;
- version advanced to `0.3.0`.

### Safety and compatibility

- TTML `DOCTYPE`/`ENTITY`, non-media time bases, wallclock expressions, and sequential time containers are rejected rather than guessed;
- same-format TTML rewriting is refused because the cue-only model cannot preserve arbitrary style, layout, metadata, and inline structure;
- existing SRT/WebVTT CLI commands, Python APIs, JSON schema version 1, SARIF 2.1.0, diagnostic codes, and exit codes remain compatible.

## 0.2.0 - 2026-08-12

### Added

- recursive, multi-input SRT/WebVTT discovery with include/exclude globs and duplicate-path removal;
- deterministic concurrent batch checking with configurable worker count;
- `.subtitleops.toml` and `[tool.subtitleops]` project configuration;
- aggregate text, JSON schema v1, and SARIF 2.1.0 reports;
- source-line and cue-timing coordinates in findings;
- deterministic SARIF partial fingerprints;
- failure thresholds independent of finding visibility;
- cue duration, trailing whitespace, control character, and duplicate identifier rules;
- rule metadata, per-file operational isolation, expanded CI, CodeQL, packaging, governance, and documentation.

## 0.1.0 - 2026-08-12

### Added

- SRT and WebVTT parsing/rendering;
- `check`, `fix`, and `convert` commands;
- timing, overlap, readability, line, and empty-text rules;
- JSON output, conservative transforms, tests, CI, and MIT licensing.
