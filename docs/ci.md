# CI integration

SubtitleOps has two CI entry points:

1. the installed CLI, suitable for any CI system;
2. the repository's composite GitHub Action, suitable for GitHub workflows.

## CLI quality gate

```yaml
- uses: actions/setup-python@v7
  with:
    python-version: "3.12"
- run: python -m pip install "git+https://github.com/jerry0327/SubtitleOps.git@v0.3.0"
- run: subtitleops check subtitles/ --sarif -o build/subtitleops.sarif
```

Exit `1` means lint findings met `fail_on`; exit `2` means an operational failure. Do not collapse these codes when downstream automation needs to distinguish content debt from broken inputs or configuration.

## GitHub Action

See [github-action.md](github-action.md) for inputs and outputs.

```yaml
permissions:
  contents: read
  security-events: write

steps:
  - uses: actions/checkout@v7
    with:
      persist-credentials: false
  - uses: jerry0327/SubtitleOps@v0.3.0
    with:
      paths: subtitles/
      upload-sarif: "true"
      fail-on: warning
```

Production callers should pin an immutable semantic version tag or full commit SHA. The floating `v0` tag is available for compatible pre-1.0 updates, while `main` is a development surface.

## Direct SARIF upload

```yaml
permissions:
  contents: read
  security-events: write

steps:
  - run: subtitleops check subtitles/ --sarif -o build/subtitleops.sarif
    continue-on-error: true
  - uses: github/codeql-action/upload-sarif@v4
    with:
      sarif_file: build/subtitleops.sarif
```

Use `continue-on-error` only to ensure the upload step runs; capture and re-apply the SubtitleOps exit code if the workflow must preserve the distinction between `1` and `2`. The composite action already performs this sequence.

## Staged rollout

Existing repositories can first use `--fail-on none`, then block only `error`, and later enforce `warning`. This keeps findings visible while avoiding a clean-slate migration requirement. See the [adoption guide](adoption.md).

## Determinism

Reports omit run timestamps and random identifiers. Files are sorted after concurrent checking, findings remain in cue/rule evaluation order, and SARIF fingerprints use stable path/rule/cue/timing fields.
