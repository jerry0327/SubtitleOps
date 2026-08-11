# Reporting contracts

SubtitleOps renders one batch result as text, JSON, or SARIF. Output order is deterministic by normalized path and cue/rule evaluation order.

## Text

Text output is intended for terminals and CI logs.

```text
subtitles/en.srt:18: cue 6: ERROR OVERLAP: overlaps previous cue by 120 ms
Checked 3/3 file(s), 74 cue(s): 1 issue(s) (1 error, 0 warning, 0 info); 0 operational error(s).
```

A clean single-file check prints an `OK` line. For directory batches, clean files are omitted unless `--show-clean` is supplied.

## JSON schema version 1

Use:

```bash
subtitleops check subtitles/ --json
```

Top-level fields:

| Field | Meaning |
| --- | --- |
| `schema_version` | Integer report schema version; currently `1`. |
| `tool` | Tool name and version. |
| `config.source` | Selected configuration path relative to the run directory, or `null`. |
| `summary` | Aggregate file, cue, issue, severity, error, threshold, and exit counts. |
| `errors` | Input/discovery errors not associated with a parsed file. |
| `files` | Ordered per-file records. |

Per-file fields:

- `path`;
- detected `format` or `null`;
- parsed `cues` count;
- `issues` array;
- `error` object or `null`.

A finding may contain:

```json
{
  "code": "OVERLAP",
  "severity": "error",
  "cue": 8,
  "message": "overlaps previous cue by 120 ms",
  "line": 31,
  "start_ms": 15200,
  "end_ms": 17400
}
```

Optional coordinates are omitted when unavailable.

### Compatibility policy

Within schema version 1:

- existing fields will retain their meaning;
- new optional fields may be added;
- new diagnostic codes may be added;
- array ordering remains deterministic.

A breaking structural change requires incrementing `schema_version`.

## SARIF 2.1.0

Use:

```bash
subtitleops check subtitles/ --sarif -o subtitleops.sarif
```

SARIF contains:

- a `SubtitleOps` driver with version and rule metadata;
- one result per lint or operational diagnostic;
- `artifactLocation.uri` relative to the run directory where possible;
- `region.startLine` for parsed cue findings;
- cue number and timing in result properties;
- deterministic `partialFingerprints` so code-scanning systems can correlate findings across source-line movement;
- one invocation with exit code, execution status, and aggregate counts.

Severity mapping:

| SubtitleOps | SARIF |
| --- | --- |
| `info` | `note` |
| `warning` | `warning` |
| `error` | `error` |

Parse, decode, input, and I/O failures are emitted as SARIF results with operational rule IDs. `executionSuccessful` is false when any such error occurs.

## Output files

`-o/--output` writes the selected report atomically and creates parent directories. Use `-o -` to force stdout. Machine output is not mixed with status prose on stdout.

```bash
subtitleops check subtitles --json -o artifacts/report.json
subtitleops check subtitles --sarif -o artifacts/report.sarif
```

The command's exit status remains the quality-gate result even when output is written to a file.
