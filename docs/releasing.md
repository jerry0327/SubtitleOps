# Release process

SubtitleOps uses a tag-driven GitHub release workflow. It builds source and wheel artifacts but does not claim a PyPI publication until that distribution channel is configured separately.

## Prepare

1. update `src/subtitleops/__init__.py` and `pyproject.toml` to the same version;
2. add a dated changelog section;
3. update `CITATION.cff` when the public version or release date changes;
4. run:

```bash
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python -m compileall -q src tests scripts
python scripts/validate_repository.py
python -m build
```

5. install the wheel into a clean virtual environment and run SRT, WebVTT, and TTML CLI smoke checks;
6. merge through a reviewed pull request with green CI and CodeQL;
7. confirm no release-blocking issue remains open.

## Tag

Create an annotated tag whose name is the package version prefixed with `v`:

```bash
git tag -a v0.3.0 -m "SubtitleOps 0.3.0"
git push origin v0.3.0
```

`.github/workflows/release.yml` verifies that the tag matches `pyproject.toml`, reruns tests, builds artifacts, smoke-installs the wheel, creates SHA-256 checksums, publishes a GitHub Release, and then moves the floating `v0` action tag to the release commit.

Consumers that require immutable dependencies should pin `v0.3.0` or a full commit SHA. The `v0` tag is a convenience alias and is intentionally movable within the compatible pre-1.0 line.

## Post-release verification

- confirm the GitHub Release contains the wheel, source distribution, and `SHA256SUMS`;
- verify the release workflow conclusion is successful;
- install the released artifact in a clean environment;
- run the repository action pinned to the immutable release tag;
- confirm `v0` resolves to the release commit;
- create follow-up issues for non-blocking work.

## Failure handling

If validation fails before publication, correct the release state and retry only after the cause is understood. If a semantic version tag or release has already been published, do not move or reuse it. Fix the issue, increment the version when necessary, and publish a new immutable version tag. The checksum file provides an integrity record for attached artifacts.
