# Changelog

All notable user-facing changes will be documented here.

The project follows semantic versioning once public releases begin. Until 1.0, minor versions may contain API changes.

## 0.1.0 - 2026-08-12

### Added

- SRT and WebVTT parsing/rendering.
- CLI commands: `check`, `fix`, and `convert`.
- lint rules for timing order, negative starts, cue ordering, overlaps, empty text, reading speed, line length, and line count.
- JSON lint output for automation.
- whitespace normalization, timing shift, and conservative overlap repair.
- SRT/WebVTT conversion.
- standard-library unit test suite and multi-version GitHub Actions CI.
