# Contributing to SubtitleOps

SubtitleOps is pre-1.0. Small, test-backed changes are preferred over broad rewrites, especially where subtitle mutation or machine-readable contracts are involved.

## Set up

```bash
git clone https://github.com/jerry0327/SubtitleOps.git
cd SubtitleOps
python -m venv .venv
# activate .venv for your shell
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
```

Python 3.10–3.14 are supported. Python 3.10 installs `tomli`; Python 3.11+ uses the standard-library TOML parser.

## Useful contributions

- a minimized subtitle sample that exposes a parser edge case;
- a regression test for malformed SRT/WebVTT input;
- a narrowly defined lint rule with stable code and documentation;
- improvements to directory discovery, JSON/SARIF interoperability, or diagnostics;
- documentation for reproducible CI and localization workflows;
- fuzz/property-test infrastructure that does not obscure a minimal failing case.

Remove private, identifying, or copyrighted dialogue from samples when it is not required to reproduce the behavior.

## Development checks

Run before opening a pull request:

```bash
python -m unittest discover -s tests -v
python -m compileall -q src tests
subtitleops check examples/clean.srt --no-config
subtitleops check examples/clean.srt --json --no-config > /tmp/subtitleops.json
subtitleops check examples/clean.srt --sarif --no-config > /tmp/subtitleops.sarif
python -m build
```

CI repeats tests across supported Python versions and validates the built wheel in a clean virtual environment.

## Pull requests

Please:

1. keep one coherent product change per pull request;
2. add/update tests for behavior changes;
3. update `README.md` and relevant `docs/` contracts;
4. update `CHANGELOG.md` for user-visible changes;
5. describe compatibility impact for rule IDs, JSON, SARIF, configuration, CLI, or public API;
6. avoid new runtime dependencies unless their value and maintenance cost are explicit.

## Parser changes

A parser change should document and test:

- accepted syntax;
- rejected syntax and error message class;
- newline/BOM handling;
- source-line behavior;
- parse/render round-trip expectations;
- whether unsupported document blocks are preserved, skipped, or rejected.

Do not silently guess malformed timestamps when the result could change cue timing.

## New lint rules

A new rule requires:

- a unique uppercase code;
- default severity and category in `subtitleops.rules`;
- deterministic trigger conditions;
- focused positive and negative tests;
- documentation in `docs/rules.md`;
- SARIF-compatible metadata;
- a changelog entry.

Codes must not be reused for unrelated behavior. Prefer a new code over changing the meaning of an existing one.

## Transform changes

Subtitle transforms can corrupt deliverables when surprising. Repairs must be conservative and opt-in when they alter timing. Document:

- exact trigger conditions;
- information-loss risk;
- boundary behavior;
- whether the operation is idempotent;
- how users can re-check the result.

Automatic dialogue rewriting is outside project scope.

## Machine-readable compatibility

JSON `schema_version` and SARIF output are product contracts. Additive optional fields are acceptable within a schema version; breaking structural changes require a schema-version increment and migration notes.

## Commit messages

Clear imperative messages are preferred:

- `Add deterministic directory discovery`
- `Report cue source lines in SARIF`
- `Reject unknown configuration keys`

## Conduct and security

Follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Report security issues according to [SECURITY.md](SECURITY.md), not through a public issue.
