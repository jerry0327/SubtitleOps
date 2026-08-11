# Reporting contracts

One `BatchReport` can be rendered as text, JSON schema version 1, or SARIF 2.1.0.

## JSON schema version 1

The top-level envelope contains:

- `schema_version`;
- tool name/version;
- selected configuration source;
- aggregate summary and effective failure threshold;
- discovery errors;
- per-file path, detected format (`srt`, `vtt`, or `ttml`), cue count, issues, and optional operational error.

Adding TTML and `FILE_TOO_LARGE` is additive within schema version 1. Consumers should treat diagnostic codes and format values as extensible strings rather than closed enums unless they deliberately enforce a version-specific allow-list.

## SARIF 2.1.0

SARIF output includes:

- the full diagnostic registry;
- severity mapped to `note`, `warning`, or `error`;
- artifact URI and source line where available;
- cue number and cue start/end milliseconds;
- deterministic `subtitleops/v1` partial fingerprints;
- operational results for missing, unsupported, oversized, undecodable, unreadable, and malformed files;
- invocation success, exit code, counts, and effective threshold.

TTML source locations identify the source `<p>` line using deterministic lexical scanning. They are intended for navigation, not as a full XML source map.

## Text

Text output is line-oriented and suitable for logs. `--show-clean` includes successful files. A final aggregate summary is always printed.

## Stability

- Existing diagnostic codes are not repurposed.
- JSON schema changes that break existing consumers require a schema-version increment.
- New optional fields, rule codes, and supported format values may be added within a schema version.
- SARIF rule metadata and help URIs are generated from the same registry used by linting.
