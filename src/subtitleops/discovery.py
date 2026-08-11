from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .models import SubtitleFormat

_SUPPORTED_SUFFIXES = {".srt", ".vtt", ".ttml", ".dfxp"}


@dataclass(frozen=True, slots=True)
class DiscoveryError:
    path: Path | None
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    files: tuple[Path, ...]
    errors: tuple[DiscoveryError, ...]


def _matches(relative: Path, patterns: Iterable[str]) -> bool:
    value = relative.as_posix()
    name = relative.name
    return any(fnmatch.fnmatchcase(value, pattern) or fnmatch.fnmatchcase(name, pattern) for pattern in patterns)


def _directory_is_excluded(relative: Path, patterns: Iterable[str]) -> bool:
    if str(relative) in {"", "."}:
        return False
    value = relative.as_posix().rstrip("/")
    probes = (value, f"{value}/", f"{value}/__subtitleops_probe__")
    return any(fnmatch.fnmatchcase(probe, pattern) for pattern in patterns for probe in probes)


def _walk_directory(
    root: Path,
    *,
    recursive: bool,
    include: tuple[str, ...],
    exclude: tuple[str, ...],
) -> Iterable[Path]:
    if not recursive:
        for candidate in root.iterdir():
            if candidate.is_file():
                relative = candidate.relative_to(root)
                if _matches(relative, include) and not _matches(relative, exclude):
                    yield candidate
        return

    def raise_walk_error(error: OSError) -> None:
        raise error

    for current, dirnames, filenames in os.walk(
        root,
        followlinks=False,
        onerror=raise_walk_error,
    ):
        current_path = Path(current)
        current_relative = current_path.relative_to(root)
        dirnames[:] = sorted(
            (
                name
                for name in dirnames
                if not _directory_is_excluded(current_relative / name, exclude)
                and not (current_path / name).is_symlink()
            ),
            key=str.casefold,
        )
        for filename in sorted(filenames, key=str.casefold):
            candidate = current_path / filename
            relative = candidate.relative_to(root)
            if _matches(relative, include) and not _matches(relative, exclude):
                yield candidate


def discover_files(
    inputs: Iterable[str | Path],
    *,
    recursive: bool,
    include: tuple[str, ...],
    exclude: tuple[str, ...],
    explicit_format: SubtitleFormat | None = None,
    allow_empty: bool = False,
) -> DiscoveryResult:
    files: dict[str, Path] = {}
    errors: list[DiscoveryError] = []
    input_paths = [Path(value).expanduser() for value in inputs]

    for input_path in input_paths:
        if not input_path.exists():
            errors.append(DiscoveryError(input_path, "INPUT_NOT_FOUND", "input path does not exist"))
            continue
        if input_path.is_file():
            if explicit_format is None and input_path.suffix.lower() not in _SUPPORTED_SUFFIXES:
                errors.append(
                    DiscoveryError(
                        input_path,
                        "UNSUPPORTED_FORMAT",
                        "file extension is not .srt, .vtt, .ttml, or .dfxp; use --format to override",
                    )
                )
                continue
            key = os.path.normcase(str(input_path.resolve()))
            files[key] = input_path
            continue
        if input_path.is_dir():
            try:
                for candidate in _walk_directory(
                    input_path,
                    recursive=recursive,
                    include=include,
                    exclude=exclude,
                ):
                    if explicit_format is None and candidate.suffix.lower() not in _SUPPORTED_SUFFIXES:
                        continue
                    key = os.path.normcase(str(candidate.resolve()))
                    files[key] = candidate
            except OSError as exc:
                errors.append(DiscoveryError(input_path, "IO_ERROR", str(exc)))
            continue
        errors.append(DiscoveryError(input_path, "IO_ERROR", "input path is not a regular file or directory"))

    ordered = tuple(sorted(files.values(), key=lambda path: path.as_posix().casefold()))
    if not ordered and not allow_empty and not errors:
        target = input_paths[0] if len(input_paths) == 1 else None
        errors.append(DiscoveryError(target, "NO_FILES", "no supported subtitle files were discovered"))
    return DiscoveryResult(ordered, tuple(errors))
