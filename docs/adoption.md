# Adoption guide

SubtitleOps can be introduced incrementally. Existing repositories do not need to make every warning blocking on the first day.

## 1. Inventory without blocking

Run a report while disabling the lint failure threshold:

```bash
subtitleops check subtitles/ --fail-on none --sarif -o build/subtitleops.sarif
```

Operational failures still return exit code `2`. Review unsupported formats, parse failures, and file-size limits before changing rule thresholds.

## 2. Block structural and timing errors

Adopt a project configuration and allow warnings to remain visible:

```toml
version = 1

[check]
fail_on = "error"
max_cps = 20.0
max_line_length = 42
max_lines = 2
```

```bash
subtitleops check subtitles/
```

## 3. Enforce readability rules

After existing warnings are understood, move to:

```toml
[check]
fail_on = "warning"
```

Use targeted `ignore` entries only with a documented reason. Do not disable parse or operational errors to make CI green.

## 4. Add GitHub review annotations

Pin an immutable release tag or commit:

```yaml
name: Subtitle quality
on: [pull_request]

permissions:
  contents: read
  security-events: write

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with:
          persist-credentials: false
      - uses: jerry0327/SubtitleOps@v0.3.0
        with:
          paths: subtitles/
          upload-sarif: "true"
          fail-on: error
```

See [GitHub Action](github-action.md) for all inputs and outputs.

## 5. Report public adoption

A public adoption report helps the maintainer understand compatibility and scale without collecting private subtitle data. Use the repository's adoption issue form and share only information your project is allowed to disclose.

## Current limitation

Baseline/diff-aware suppression is planned but not yet implemented. Until then, staged `fail_on` settings and narrow, documented ignores are the safest migration path.
