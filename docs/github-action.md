# Reusable GitHub Action

The repository root contains a composite action that installs the checked-out SubtitleOps source, runs the quality gate, writes SARIF, exposes outputs, optionally uploads SARIF, and finally applies the normal SubtitleOps exit code.

## Basic workflow

```yaml
name: Subtitle quality
on: [pull_request]

permissions:
  contents: read

jobs:
  check-subtitles:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with:
          persist-credentials: false
      - id: subtitles
        uses: jerry0327/SubtitleOps@main # pin a tag or full commit for production
        with:
          paths: |
            subtitles/
            trailers/captions.vtt
          fail-on: warning
          report-path: build/subtitleops.sarif
      - if: ${{ always() }}
        run: |
          echo "files=${{ steps.subtitles.outputs.files-checked }}"
          echo "issues=${{ steps.subtitles.outputs.issues }}"
```

`paths` is newline-delimited rather than shell-parsed. This avoids quoting ambiguity and supports paths containing spaces.

## Code Scanning upload

```yaml
permissions:
  contents: read
  security-events: write

steps:
  - uses: actions/checkout@v6
    with:
      persist-credentials: false
  - uses: jerry0327/SubtitleOps@main
    with:
      paths: subtitles/
      upload-sarif: "true"
```

The caller must grant the permissions required by GitHub's SARIF upload action. SubtitleOps uploads only when report generation succeeded; lint findings and operational file errors remain represented in the report.

## Inputs

| Input | Default | Behavior |
| --- | --- | --- |
| `paths` | `.` | Newline-delimited files/directories. |
| `config` | empty | Explicit `.subtitleops.toml` or `pyproject.toml`. |
| `no-config` | `false` | Disable upward config discovery. |
| `format` | empty | Force `srt`, `vtt`, or `ttml`. |
| `fail-on` | config/default | `info`, `warning`, `error`, or `none`. |
| `allow-empty` | config/default | Override empty-discovery behavior. |
| `max-file-bytes` | config/default | Per-file byte limit; `0` disables. |
| `report-path` | `subtitleops.sarif` | SARIF path relative to `working-directory`. |
| `upload-sarif` | `false` | Upload to Code Scanning. |
| `python-version` | `3.12` | Python used by the action. |
| `working-directory` | `.` | Caller-repository directory used as the process working directory. |

Boolean overrides accept `true`/`false`, `1`/`0`, or `yes`/`no` in the runner. The upload step itself is enabled by the literal action input value `true`.

## Outputs

| Output | Meaning |
| --- | --- |
| `exit-code` | `0`, `1`, or `2` according to the SubtitleOps contract. |
| `files-checked` | Successfully parsed and checked files. |
| `issues` | Lint findings, independent of `fail-on`. |
| `report-path` | SARIF path supplied to the runner. |

The action's final step exits with `exit-code`. Use `continue-on-error: true` at the caller step only when another step should inspect outputs before the job is allowed to fail.

## Pinning

`@main` is useful while the project is alpha. Production workflows should pin a reviewed release tag or full commit SHA to avoid unreviewed action changes.
