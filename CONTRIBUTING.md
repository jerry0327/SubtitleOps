# Contributing to SubtitleOps

SubtitleOps is early-stage, so small, test-backed changes are preferred over broad rewrites.

## Set up

```bash
git clone https://github.com/jerry0327/SubtitleOps.git
cd SubtitleOps
python -m venv .venv
# activate .venv for your shell
python -m pip install -e .
python -m unittest discover -s tests -v
```

No runtime dependencies are required.

## Good first contributions

Useful contributions include:

- a minimal subtitle sample that exposes a parser edge case;
- a regression test for malformed SRT/WebVTT input;
- a narrowly defined lint rule with a stable code and documentation;
- improved CLI diagnostics;
- documentation for integration in CI or batch pipelines.

When reporting a parser bug, reduce the sample as much as possible and remove private/copyrighted dialogue when it is not necessary to reproduce the issue.

## Pull requests

Please:

1. keep one logical change per pull request;
2. add or update tests for behavior changes;
3. run `python -m unittest discover -s tests -v` locally;
4. update `README.md` or `docs/design.md` if the CLI/API contract changes;
5. avoid adding runtime dependencies unless the benefit clearly justifies them.

## Behavior changes

Subtitle transformations can corrupt deliverables if they are surprising. Repairs should therefore be conservative and opt-in when they alter timing. A proposed auto-fix should document:

- what exact condition triggers it;
- whether it can lose information;
- how it behaves at boundary cases;
- how users can detect or disable it.

## Commit messages

Clear imperative messages are preferred, for example:

- `Add WebVTT cue setting preservation`
- `Reject out-of-range SRT timestamps`
- `Document check command exit codes`

## Code of conduct

Be specific, technical, and respectful. Harassment, discrimination, and personal attacks are not acceptable in project spaces. Maintainers may remove disruptive content or restrict participation when necessary to keep collaboration productive.
