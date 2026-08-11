from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .config import CheckConfig, validate_check_config
from .discovery import DiscoveryError, discover_files
from .fileio import FileTooLargeError, read_utf8
from .formats import SubtitleParseError, detect_format, parse_text
from .linting import LintIssue, lint_cues
from .models import SubtitleFormat
from .rules import SEVERITY_ORDER


@dataclass(frozen=True, slots=True)
class FileError:
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class FileReport:
    path: Path
    format: SubtitleFormat | None
    cues: int
    issues: tuple[LintIssue, ...]
    error: FileError | None = None


@dataclass(frozen=True, slots=True)
class BatchReport:
    files: tuple[FileReport, ...]
    errors: tuple[DiscoveryError, ...]
    base_dir: Path
    config_source: Path | None = None
    fail_on: str = "warning"

    @property
    def files_discovered(self) -> int:
        return len(self.files)

    @property
    def files_checked(self) -> int:
        return sum(file.error is None for file in self.files)

    @property
    def files_failed(self) -> int:
        return sum(file.error is not None for file in self.files)

    @property
    def cue_count(self) -> int:
        return sum(file.cues for file in self.files if file.error is None)

    @property
    def issues(self) -> tuple[LintIssue, ...]:
        return tuple(issue for file in self.files for issue in file.issues)

    @property
    def issue_count(self) -> int:
        return sum(len(file.issues) for file in self.files)

    @property
    def operational_error_count(self) -> int:
        return len(self.errors) + self.files_failed

    def severity_count(self, severity: str) -> int:
        return sum(issue.severity == severity for issue in self.issues)

    def exit_code(self, fail_on: str | None = None) -> int:
        if self.operational_error_count:
            return 2
        threshold = self.fail_on if fail_on is None else fail_on
        if threshold == "none":
            return 0
        rank = SEVERITY_ORDER[threshold]
        return 1 if any(SEVERITY_ORDER[issue.severity] >= rank for issue in self.issues) else 0


def _check_file(path: Path, config: CheckConfig, explicit_format: SubtitleFormat | None) -> FileReport:
    fmt: SubtitleFormat | None = None
    try:
        fmt = detect_format(path, explicit_format)
        cues = parse_text(read_utf8(path, max_file_bytes=config.max_file_bytes), fmt)
        issues = lint_cues(
            cues,
            max_cps=config.max_cps,
            max_line_length=config.max_line_length,
            max_lines=config.max_lines,
            min_duration_ms=config.min_duration_ms,
            max_duration_ms=config.max_duration_ms,
            ignore=config.ignore,
        )
        return FileReport(path, fmt, len(cues), tuple(issues))
    except FileTooLargeError as exc:
        return FileReport(path, fmt, 0, (), FileError("FILE_TOO_LARGE", str(exc)))
    except UnicodeError as exc:
        return FileReport(path, fmt, 0, (), FileError("DECODE_ERROR", str(exc)))
    except SubtitleParseError as exc:
        return FileReport(path, fmt, 0, (), FileError("PARSE_ERROR", str(exc)))
    except OSError as exc:
        return FileReport(path, fmt, 0, (), FileError("IO_ERROR", str(exc)))


def _worker_count(configured: int, file_count: int) -> int:
    if file_count <= 1:
        return 1
    if configured > 0:
        return min(configured, file_count)
    return min(file_count, 32, (os.cpu_count() or 1) + 4)


def run_check(
    inputs: Iterable[str | Path],
    config: CheckConfig,
    *,
    explicit_format: SubtitleFormat | None = None,
    base_dir: Path | None = None,
    config_source: Path | None = None,
) -> BatchReport:
    config = validate_check_config(config)
    base = (base_dir or Path.cwd()).resolve()
    discovery = discover_files(
        inputs,
        recursive=config.recursive,
        include=config.include,
        exclude=config.exclude,
        explicit_format=explicit_format,
        allow_empty=config.allow_empty,
    )
    workers = _worker_count(config.jobs, len(discovery.files))
    if workers == 1:
        checked = [_check_file(path, config, explicit_format) for path in discovery.files]
    else:
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="subtitleops") as executor:
            checked = list(executor.map(lambda path: _check_file(path, config, explicit_format), discovery.files))
    files = tuple(sorted(checked, key=lambda report: report.path.as_posix().casefold()))
    return BatchReport(files, discovery.errors, base, config_source, config.fail_on)
