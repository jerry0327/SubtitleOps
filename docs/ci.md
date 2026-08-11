# CI integration

SubtitleOps is designed to run as a quality gate after subtitle generation/localization and before publication.

## Basic GitHub Actions check

Until a package release is published, pin installation to a reviewed Git commit or tag rather than an unbounded branch.

```yaml
name: Subtitle quality

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  subtitleops:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with:
          persist-credentials: false
      - uses: actions/setup-python@v6
        with:
          python-version: "3.14"
          cache: pip
      - name: Install SubtitleOps
        run: python -m pip install "subtitleops @ git+https://github.com/jerry0327/SubtitleOps.git@<PINNED_COMMIT>"
      - name: Check subtitles
        run: subtitleops check subtitles/ --config .subtitleops.toml
```

Replace `<PINNED_COMMIT>` with a reviewed immutable commit SHA.

## Upload SARIF to GitHub Code Scanning

The checker must be allowed to finish with exit `1` long enough for the SARIF upload step to run. Re-apply the failure after upload:

```yaml
permissions:
  contents: read
  security-events: write

steps:
  - uses: actions/checkout@v6
    with:
      persist-credentials: false
  - uses: actions/setup-python@v6
    with:
      python-version: "3.14"
  - run: python -m pip install "subtitleops @ git+https://github.com/jerry0327/SubtitleOps.git@<PINNED_COMMIT>"

  - name: Run SubtitleOps
    id: subtitleops
    continue-on-error: true
    run: subtitleops check subtitles/ --sarif -o subtitleops.sarif

  - name: Upload SARIF
    if: always() && hashFiles('subtitleops.sarif') != ''
    uses: github/codeql-action/upload-sarif@v4
    with:
      sarif_file: subtitleops.sarif

  - name: Enforce SubtitleOps result
    if: steps.subtitleops.outcome == 'failure'
    run: exit 1
```

GitHub permissions for pull requests from forks can differ. Consult the repository's Code Scanning policy before enabling SARIF upload on untrusted fork events.

## Preserve JSON as an artifact

```yaml
- name: Generate aggregate report
  id: subtitleops_json
  continue-on-error: true
  run: subtitleops check subtitles/ --json -o subtitleops.json

- uses: actions/upload-artifact@v7
  if: always()
  with:
    name: subtitleops-report
    path: subtitleops.json

- if: steps.subtitleops_json.outcome == 'failure'
  run: exit 1
```

## Threshold rollout

A staged adoption pattern avoids suppressing useful diagnostics:

1. begin with `fail_on = "error"` so warnings remain visible;
2. fix or explicitly assess warning classes;
3. move to `fail_on = "warning"` when the corpus is ready;
4. reserve `ignore` for rules that are structurally inapplicable.

Operational errors always return `2` and should not be downgraded.

## Generated subtitle pipelines

Recommended sequence:

```text
ASR/translation -> export SRT/VTT -> SubtitleOps check -> optional fix -> re-check -> publish
```

Run `check` after `fix`; conservative repair can resolve only specific timing conditions and does not guarantee a clean track.
