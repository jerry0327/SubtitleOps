# SubtitleOps architecture and contracts

```text
inputs -> discovery -> bounded read -> parse document -> lint cues -> aggregate -> text/JSON/SARIF
                                           |                              |
                                           +-> transforms/render ----------+
```

## Cue and document models

`Cue` is immutable and stores millisecond timing, text, optional identifier/settings, and an optional source line. Integer milliseconds avoid floating-point drift.

`SubtitleDocument` wraps a cue tuple and format-level state. SRT and TTML currently use cue-only documents. WebVTT additionally stores signature/header lines and typed document blocks with a cue-relative insertion position.

Transforms return new cues. `SubtitleDocument.with_cues` lets same-format WebVTT rendering preserve document-level data while replacing only transformed cues.

## Format layer

`formats.py` owns detection, timestamp handling, parsing, and rendering.

- SRT and WebVTT parsing is line/block based.
- TTML parsing uses the standard-library XML parser after rejecting `DOCTYPE`/`ENTITY` declarations.
- TTML timing is resolved recursively under parallel containers.
- Canonical TTML rendering is cue-only and sets `xml:space="preserve"` for deterministic text round trips.
- Same-format TTML mutation is rejected at the CLI boundary because the document model cannot promise lossless styling/layout preservation.

See [formats.md](formats.md).

## Bounded I/O

`fileio.py` centralizes UTF-8/BOM reads and atomic writes.

A positive `max_file_bytes` reads at most `limit + 1` bytes, detects overflow before decoding, and raises `FileTooLargeError`. Setting the limit to zero opts out. Reports map this to stable `FILE_TOO_LARGE` operational diagnostics.

Writes use a same-directory temporary file, flush/fsync, optional mode preservation, and `os.replace`.

## Discovery and checking

Discovery selects supported suffixes through include/exclude policy and does not follow directory symlinks. Resolved paths are de-duplicated and sorted.

Checking uses bounded reads, format detection, parsing, and linting. Threads are used for small filesystem-bound workloads; completion order is hidden by final sorting. A damaged file never suppresses results for other files.

## Reporting and exit codes

Operational errors take precedence:

- `0`: no finding reaches the threshold;
- `1`: at least one finding reaches the threshold;
- `2`: configuration/discovery/read/decode/parse/I/O failure.

JSON and SARIF are deterministic for unchanged inputs and options. No timestamps or random IDs are emitted.

## Composite action

The action is intentionally a thin adapter:

1. set up Python;
2. install the action checkout as a package;
3. run `scripts/action_runner.py` in the caller's selected working directory;
4. optionally upload SARIF;
5. apply the recorded SubtitleOps exit code.

The runner always exits zero internally so SARIF upload and outputs are available before the final quality-gate step fails.

## Security model

- no shell execution from subtitle content;
- no network access during checking;
- no multimedia codec invocation;
- UTF-8 decoding is explicit;
- XML declarations capable of defining entities are rejected;
- file reads are bounded by default;
- directory symlinks are not traversed;
- unsupported lossless mutations fail rather than discard data.

## Non-goals

Speech recognition, translation, semantic rewriting, muxing, bitmap subtitles, browser/player rendering parity, full TTML presentation processing, and opaque AI scoring remain out of scope.
