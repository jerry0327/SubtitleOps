# SubtitleOps architecture and contracts

SubtitleOps is organized as small layers with explicit data flow:

```text
inputs -> discovery -> decode/parse -> lint -> aggregate -> text/JSON/SARIF
                         |                         |
                         +-> transforms/render ----+
```

The separation is intentional: discovery and reporting can evolve without coupling format parsing to filesystem or CI concerns.

## 1. Cue model

`subtitleops.models.Cue` is immutable and stores:

- `start_ms` and `end_ms` as integer milliseconds;
- `text` with preserved cue line boundaries;
- optional cue `identifier` and WebVTT `settings`;
- optional `source_line` for diagnostics.

Integer milliseconds avoid floating-point drift during repeated shifts and repairs. Transform functions return new cue objects rather than mutating caller-owned values.

## 2. Formats

`subtitleops.formats` owns SRT and WebVTT parsing/rendering.

Current guarantees:

- the CLI accepts UTF-8 and UTF-8 BOM input;
- CRLF and CR input are normalized during parsing;
- rendered output uses LF newlines;
- SRT output is renumbered deterministically;
- supported WebVTT identifiers and cue settings survive parse/render;
- malformed timestamps raise `SubtitleParseError` instead of being guessed;
- timing-line source locations are retained for diagnostics.

WebVTT `NOTE`, `STYLE`, and `REGION` blocks are skipped in the current cue-only representation. They are not silently claimed to round-trip. A future document model is required before arbitrary document-level blocks can be preserved correctly.

## 3. Rule registry and linting

`subtitleops.rules` is the canonical registry for diagnostic metadata. A rule has a code, name, default severity, category, description, and documentation URI.

`subtitleops.linting` is read-only. A `LintIssue` includes:

- stable diagnostic code;
- effective severity;
- cue number and message;
- optional source line;
- cue start/end milliseconds.

Rule codes may be added before 1.0, but existing codes must not be repurposed for unrelated behavior. Rule suppression removes a finding; `fail_on` changes only the exit threshold and leaves reports complete.

## 4. Configuration

`subtitleops.config` loads a versioned TOML subset from either:

- `.subtitleops.toml` using `[check]`; or
- `pyproject.toml` using `[tool.subtitleops.check]`.

Configuration is validated strictly. Unknown keys, invalid types, impossible duration ranges, unsupported failure levels, and unknown rule codes are operational errors. This prevents misspellings from silently weakening a quality gate.

Precedence is:

1. built-in defaults;
2. nearest discovered project configuration or explicit `--config`;
3. command-line overrides.

## 5. Discovery

`subtitleops.discovery` accepts files and directories.

Properties:

- explicit files are retained even when supplied more than once;
- resolved paths are de-duplicated;
- directory files are selected by include and exclude globs;
- directory symlinks are not followed;
- default build, virtual-environment, cache, and Git directories are excluded;
- final order is normalized and deterministic;
- missing, unsupported, and empty inputs are represented as structured operational errors.

Discovery does not parse files. That keeps path policy separate from subtitle syntax.

## 6. Batch checking

`subtitleops.checking` joins discovery, decoding, parsing, and linting.

A `FileReport` contains a path, detected format, cue count, findings, and an optional operational error. A `BatchReport` contains ordered file reports plus input/discovery errors.

Concurrency uses threads because the workload is dominated by small filesystem reads and parsing. Worker completion order is never exposed; results are sorted before reporting. One unreadable or malformed file does not prevent other discovered files from being checked.

### Exit contract

- `0`: no finding at or above `fail_on`, and no operational error;
- `1`: checking completed and at least one finding reached `fail_on`;
- `2`: configuration, discovery, decoding, parsing, or I/O produced an operational error.

Operational errors take precedence over lint thresholds.

## 7. Reporting

`subtitleops.reporting` renders one `BatchReport` into:

- deterministic human-readable text;
- versioned JSON (`schema_version = 1`);
- SARIF 2.1.0.

Machine-readable output does not include timestamps or nondeterministic identifiers. Repeated runs over unchanged inputs and options should produce byte-equivalent output, except where absolute input paths necessarily differ.

SARIF maps rule severities to `note`, `warning`, or `error`, includes rule metadata, source regions where available, and invocation status. Parse/discovery failures are represented as operational SARIF results rather than disappearing into stderr.

## 8. Transforms

Transforms remain separate from linting. CLI output is committed with atomic file replacement so interrupted writes do not leave partial deliverables. Existing permission bits are retained for in-place fixes when supported by the platform.

### Whitespace normalization

Only edge whitespace is normalized. Wording and line boundaries are not semantically rewritten.

### Timing shift

A negative shift is clipped globally when needed so the earliest cue starts at zero. Cue durations remain unchanged.

### Overlap repair

The earlier cue is clipped to the next cue's start only when the remaining duration meets `min_duration_ms`. Otherwise no edit is made and the overlap remains visible to `check`.

## 9. CLI boundary

`subtitleops.cli` is an adapter. It handles argument parsing, configuration precedence, output destination, and exit codes. Core parsing, linting, discovery, reporting, and batch execution remain importable without invoking the CLI.

Compatibility retained from 0.1:

- single-file `subtitleops check FILE`;
- `check --json` alias;
- `fix` and `convert` commands;
- exit codes `0`, `1`, and `2`.

## Security and resource model

Subtitle files are untrusted text input. Current protections and constraints include:

- no shell execution or media-codec invocation;
- UTF-8 decoding is explicit;
- malformed files are isolated per input;
- directory symlinks are not recursively followed;
- all automatic fixes are bounded by parsed cue data;
- no network access occurs during subtitle checking.

The current parser reads each file into memory. A configurable maximum file-size guard is a candidate for a later release; callers processing adversarial, very large inputs should impose an upstream size limit today.

## Non-goals

- speech recognition or diarization;
- machine translation;
- automatic dialogue rewriting;
- media muxing/demuxing;
- bitmap subtitle formats;
- visual rendering comparison;
- opaque AI quality scoring.

SubtitleOps is intended to compose with those systems, not replace them.
