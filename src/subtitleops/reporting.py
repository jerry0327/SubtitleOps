from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import quote

from . import __version__
from .checking import BatchReport, FileReport
from .discovery import DiscoveryError
from .linting import LintIssue
from .rules import RULES, iter_rules

_SCHEMA_VERSION = 1
_SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
_INFORMATION_URI = "https://github.com/jerry0327/SubtitleOps"


def display_path(path: Path, base_dir: Path) -> str:
    try:
        return path.resolve().relative_to(base_dir.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _file_to_dict(file: FileReport, base_dir: Path) -> dict[str, object]:
    payload: dict[str, object] = {
        "path": display_path(file.path, base_dir),
        "format": file.format,
        "cues": file.cues,
        "issues": [issue.to_dict() for issue in file.issues],
    }
    if file.error:
        payload["error"] = {"code": file.error.code, "message": file.error.message}
    else:
        payload["error"] = None
    return payload


def report_to_dict(report: BatchReport) -> dict[str, object]:
    return {
        "schema_version": _SCHEMA_VERSION,
        "tool": {"name": "SubtitleOps", "version": __version__},
        "config": {"source": display_path(report.config_source, report.base_dir) if report.config_source else None},
        "summary": {
            "files_discovered": report.files_discovered,
            "files_checked": report.files_checked,
            "files_failed": report.files_failed,
            "cues": report.cue_count,
            "issues": report.issue_count,
            "by_severity": {
                "error": report.severity_count("error"),
                "warning": report.severity_count("warning"),
                "info": report.severity_count("info"),
            },
            "operational_errors": report.operational_error_count,
            "fail_on": report.fail_on,
            "exit_code": report.exit_code(),
        },
        "errors": [
            {
                "path": display_path(error.path, report.base_dir) if error.path else None,
                "code": error.code,
                "message": error.message,
            }
            for error in report.errors
        ],
        "files": [_file_to_dict(file, report.base_dir) for file in report.files],
    }


def render_json(report: BatchReport) -> str:
    return json.dumps(report_to_dict(report), ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def _text_issue(path: str, issue: LintIssue) -> str:
    location = f"{path}:{issue.line}" if issue.line else path
    return f"{location}: cue {issue.cue}: {issue.severity.upper()} {issue.code}: {issue.message}"


def _text_discovery_error(error: DiscoveryError, base_dir: Path) -> str:
    path = display_path(error.path, base_dir) if error.path else "<inputs>"
    return f"{path}: ERROR {error.code}: {error.message}"


def render_text(report: BatchReport, *, show_clean: bool = False) -> str:
    lines: list[str] = []
    for error in report.errors:
        lines.append(_text_discovery_error(error, report.base_dir))

    for file in report.files:
        path = display_path(file.path, report.base_dir)
        if file.error:
            lines.append(f"{path}: ERROR {file.error.code}: {file.error.message}")
            continue
        if file.issues:
            lines.extend(_text_issue(path, issue) for issue in file.issues)
        elif show_clean:
            lines.append(f"OK  {path} ({file.cues} cues)")

    summary = (
        f"Checked {report.files_checked}/{report.files_discovered} file(s), {report.cue_count} cue(s): "
        f"{report.issue_count} issue(s) "
        f"({report.severity_count('error')} error, {report.severity_count('warning')} warning, "
        f"{report.severity_count('info')} info); {report.operational_error_count} operational error(s)."
    )
    lines.append(summary)
    return "\n".join(lines) + "\n"


def _artifact_uri(path: Path, base_dir: Path) -> str:
    try:
        relative = path.resolve().relative_to(base_dir.resolve()).as_posix()
        return quote(relative, safe="/-._~")
    except ValueError:
        return path.resolve().as_uri()


def _sarif_location(path: Path, base_dir: Path, *, line: int | None = None) -> dict[str, object]:
    physical: dict[str, object] = {"artifactLocation": {"uri": _artifact_uri(path, base_dir)}}
    if line:
        physical["region"] = {"startLine": line}
    return {"physicalLocation": physical}


def _sarif_rule(code: str) -> dict[str, object]:
    rule = RULES[code]
    return {
        "id": rule.code,
        "name": rule.name.replace(" ", ""),
        "shortDescription": {"text": rule.name},
        "fullDescription": {"text": rule.description},
        "defaultConfiguration": {
            "level": {"info": "note", "warning": "warning", "error": "error"}[rule.default_severity]
        },
        "helpUri": rule.help_uri,
        "properties": {"category": rule.category, "defaultSeverity": rule.default_severity},
    }


def _fingerprint(*parts: object) -> str:
    """Return a deterministic SARIF identity independent of source-line movement."""
    payload = "\x1f".join("" if part is None else str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _sarif_issue(file: FileReport, issue: LintIssue, base_dir: Path) -> dict[str, object]:
    result: dict[str, object] = {
        "ruleId": issue.code,
        "level": {"info": "note", "warning": "warning", "error": "error"}[issue.severity],
        "message": {"text": issue.message},
        "locations": [_sarif_location(file.path, base_dir, line=issue.line)],
        "partialFingerprints": {
            "subtitleops/v1": _fingerprint(
                _artifact_uri(file.path, base_dir),
                issue.code,
                issue.cue,
                issue.start_ms,
                issue.end_ms,
            )
        },
        "properties": {
            "cue": issue.cue,
            "startMs": issue.start_ms,
            "endMs": issue.end_ms,
            "severity": issue.severity,
        },
    }
    return result


def _sarif_file_error(file: FileReport, base_dir: Path) -> dict[str, object]:
    assert file.error is not None
    return {
        "ruleId": file.error.code,
        "level": "error",
        "message": {"text": file.error.message},
        "locations": [_sarif_location(file.path, base_dir)],
        "partialFingerprints": {
            "subtitleops/v1": _fingerprint(
                _artifact_uri(file.path, base_dir), file.error.code, file.error.message
            )
        },
        "properties": {"operational": True},
    }


def _sarif_discovery_error(error: DiscoveryError, base_dir: Path) -> dict[str, object]:
    result: dict[str, object] = {
        "ruleId": error.code,
        "level": "error",
        "message": {"text": error.message},
        "properties": {"operational": True},
    }
    artifact = _artifact_uri(error.path, base_dir) if error.path else "<inputs>"
    result["partialFingerprints"] = {
        "subtitleops/v1": _fingerprint(artifact, error.code, error.message)
    }
    if error.path:
        result["locations"] = [_sarif_location(error.path, base_dir)]
    return result


def report_to_sarif(report: BatchReport) -> dict[str, object]:
    results: list[dict[str, object]] = []
    for error in report.errors:
        results.append(_sarif_discovery_error(error, report.base_dir))
    for file in report.files:
        if file.error:
            results.append(_sarif_file_error(file, report.base_dir))
        else:
            results.extend(_sarif_issue(file, issue, report.base_dir) for issue in file.issues)

    return {
        "$schema": _SARIF_SCHEMA,
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "SubtitleOps",
                        "version": __version__,
                        "informationUri": _INFORMATION_URI,
                        "rules": [_sarif_rule(rule.code) for rule in iter_rules()],
                    }
                },
                "results": results,
                "invocations": [
                    {
                        "executionSuccessful": report.operational_error_count == 0,
                        "exitCode": report.exit_code(),
                        "properties": {
                            "filesChecked": report.files_checked,
                            "cues": report.cue_count,
                            "issues": report.issue_count,
                            "operationalErrors": report.operational_error_count,
                            "failOn": report.fail_on,
                        },
                    }
                ],
            }
        ],
    }


def render_sarif(report: BatchReport) -> str:
    return json.dumps(report_to_sarif(report), ensure_ascii=False, indent=2, sort_keys=False) + "\n"
