# Changelog

All notable user-facing changes are documented here.

SubtitleOps follows semantic versioning once public releases begin. Before 1.0, minor versions may refine public APIs and defaults; diagnostic codes will not be repurposed without an explicit changelog entry.

## 0.2.0 - 2026-08-12

### Added

- recursive, multi-input SRT/WebVTT discovery with include/exclude globs and duplicate-path removal;
- deterministic concurrent batch checking with configurable worker count;
- `.subtitleops.toml` and `[tool.subtitleops]` project configuration;
- aggregate text, JSON schema v1, and SARIF 2.1.0 reports;
- source-line and cue-timing coordinates in findings;
- deterministic SARIF partial fingerprints for cross-run code-scanning identity;
- failure thresholds (`info`, `warning`, `error`, `none`) independent of finding visibility;
- lint rules for cue duration, trailing whitespace, control characters, and duplicate identifiers;
- rule metadata via `subtitleops rules`;
- per-file decode/parse/I/O isolation and explicit batch operational errors;
- CI packaging validation across Python 3.10–3.14, CodeQL analysis, release workflow with SHA-256 checksums, Dependabot configuration, issue forms, and pull-request template;
- configuration, rule, reporting, CI, architecture, and release documentation;
- typed-package marker and expanded public batch-checking API;
- comprehensive regression coverage for batch, config, discovery, reporting, and CLI behavior.

### Changed

- `check` now accepts one or more files or directories while retaining single-file compatibility;
- JSON output is now an aggregate versioned report instead of a single-file ad hoc object;
- the default lint profile includes 300 ms minimum and 7000 ms maximum cue-duration warnings;
- Python 3.10 uses `tomli` for TOML configuration; Python 3.11+ remains standard-library-only at runtime;
- report, conversion, and repair outputs use atomic replacement; in-place repair preserves existing file permissions when supported.

### Preserved

- `check --json`, `fix`, `convert`, SRT/WebVTT parsing, timing shift, overlap repair, and CI-oriented exit codes remain available.

## 0.1.0 - 2026-08-12

### Added

- SRT and WebVTT parsing/rendering;
- CLI commands: `check`, `fix`, and `convert`;
- lint rules for timing order, negative starts, cue ordering, overlaps, empty text, reading speed, line length, and line count;
- JSON lint output for automation;
- whitespace normalization, timing shift, and conservative overlap repair;
- SRT/WebVTT conversion;
- standard-library unit test suite and multi-version GitHub Actions CI.
