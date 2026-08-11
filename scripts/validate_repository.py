#!/usr/bin/env python3
"""Validate repository metadata and documentation contracts.

This check intentionally uses the standard library (plus ``tomli`` on Python
3.10, which is already a runtime dependency) so it can run in every supported
CI environment without a documentation toolchain.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "SUPPORT.md",
    "GOVERNANCE.md",
    "ROADMAP.md",
    "CITATION.cff",
    "LICENSE",
    "action.yml",
    "docs/project-brief.md",
    "docs/maintainer-playbook.md",
    "docs/adoption.md",
    ".github/CODEOWNERS",
)
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
CITATION_FIELD_RE = re.compile(r"^(version|date-released):\s*[\"']?([^\"'\s]+)[\"']?\s*$", re.MULTILINE)


class ValidationError(RuntimeError):
    pass


def read(path: str | Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def project_version() -> str:
    project = tomllib.loads(read("pyproject.toml"))["project"]
    version = project.get("version")
    if not isinstance(version, str) or not version:
        raise ValidationError("pyproject.toml has no valid project.version")
    return version


def package_version() -> str:
    module = ast.parse(read("src/subtitleops/__init__.py"))
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets):
            value = ast.literal_eval(node.value)
            if isinstance(value, str) and value:
                return value
    raise ValidationError("src/subtitleops/__init__.py has no literal __version__")


def citation_fields() -> dict[str, str]:
    fields = dict(CITATION_FIELD_RE.findall(read("CITATION.cff")))
    missing = {"version", "date-released"} - fields.keys()
    if missing:
        raise ValidationError(f"CITATION.cff is missing fields: {', '.join(sorted(missing))}")
    return fields


def validate_versions() -> None:
    project = project_version()
    package = package_version()
    citation = citation_fields()
    if project != package:
        raise ValidationError(f"project version {project!r} != package version {package!r}")
    if project != citation["version"]:
        raise ValidationError(f"project version {project!r} != citation version {citation['version']!r}")

    changelog_heading = f"## {project} - {citation['date-released']}"
    if changelog_heading not in read("CHANGELOG.md"):
        raise ValidationError(f"CHANGELOG.md is missing {changelog_heading!r}")

    immutable_ref = f"jerry0327/SubtitleOps@v{project}"
    for path in ("README.md", "docs/github-action.md", "docs/adoption.md"):
        text = read(path)
        if immutable_ref not in text:
            raise ValidationError(f"{path} does not document immutable action ref {immutable_ref!r}")
        if "jerry0327/SubtitleOps@main" in text:
            raise ValidationError(f"{path} recommends @main instead of a release ref")


def _link_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    elif " \"" in target or " '" in target:
        target = re.split(r"\s+[\"']", target, maxsplit=1)[0]
    return target


def validate_markdown_links() -> None:
    failures: list[str] = []
    for source in sorted(ROOT.rglob("*.md")):
        if any(part in {".git", ".venv", "build", "dist"} for part in source.parts):
            continue
        text = source.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK_RE.finditer(text):
            target = _link_target(match.group(1))
            if not target or target.startswith("#"):
                continue
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or target.startswith("mailto:"):
                continue
            path_text = unquote(parsed.path)
            if not path_text:
                continue
            candidate = ROOT / path_text.lstrip("/") if path_text.startswith("/") else source.parent / path_text
            if not candidate.exists():
                line = text.count("\n", 0, match.start()) + 1
                failures.append(f"{source.relative_to(ROOT)}:{line}: missing link target {target!r}")
    if failures:
        raise ValidationError("broken relative Markdown links:\n  " + "\n  ".join(failures))


def validate_required_files() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        raise ValidationError("missing required repository files: " + ", ".join(missing))


def validate_workflow_references() -> None:
    candidates = [ROOT / "action.yml", *sorted((ROOT / ".github" / "workflows").glob("*.yml"))]
    for path in candidates:
        text = path.read_text(encoding="utf-8")
        for obsolete in ("actions/checkout@v6", "actions/setup-python@v6"):
            if obsolete in text:
                raise ValidationError(f"{path.relative_to(ROOT)} still references {obsolete}")


def main() -> int:
    try:
        validate_required_files()
        validate_versions()
        validate_markdown_links()
        validate_workflow_references()
    except (OSError, ValueError, SyntaxError, ValidationError) as exc:
        print(f"repository validation failed: {exc}", file=sys.stderr)
        return 1
    print(f"repository metadata valid for SubtitleOps {project_version()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
