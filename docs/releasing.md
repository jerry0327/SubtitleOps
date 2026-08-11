# Release process

SubtitleOps uses a tag-driven GitHub release workflow. It builds source and wheel artifacts but does not claim a PyPI publication until that distribution channel is configured separately.

## Prepare

1. update `src/subtitleops/__init__.py` and `pyproject.toml` to the same version;
2. add a dated changelog section;
3. run:

```bash
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python -m compileall -q src tests
python -m build
```

4. install the wheel into a clean virtual environment and run a CLI smoke check;
5. merge through a reviewed pull request with green CI.

## Tag

Create an annotated tag whose name is the package version prefixed with `v`:

```bash
git tag -a v0.2.0 -m "SubtitleOps 0.2.0"
git push origin v0.2.0
```

`.github/workflows/release.yml` verifies that the tag matches `pyproject.toml`, reruns tests, builds artifacts, smoke-installs the wheel, and creates SHA-256 checksums and a GitHub Release with generated notes.

## Failure handling

If validation fails, do not move or reuse the published tag. Correct the release state, increment the version when necessary, and create a new tag. Published tags and attached artifacts should remain immutable; the release checksum file provides an integrity record.
