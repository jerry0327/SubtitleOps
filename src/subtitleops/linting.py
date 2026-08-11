from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Collection, Iterable

from .models import Cue
from .rules import RULES


@dataclass(frozen=True, slots=True)
class LintIssue:
    code: str
    severity: str
    cue: int
    message: str
    line: int | None = None
    start_ms: int | None = None
    end_ms: int | None = None

    def to_dict(self) -> dict[str, object]:
        return {key: value for key, value in asdict(self).items() if value is not None}


def _visible_characters(text: str) -> int:
    return sum(1 for char in text if not char.isspace())


def _has_control_character(text: str) -> bool:
    return any((ord(char) < 32 and char not in {"\n", "\t"}) or ord(char) == 127 for char in text)


def _issue(code: str, cue_number: int, cue: Cue, message: str) -> LintIssue:
    return LintIssue(
        code=code,
        severity=RULES[code].default_severity,
        cue=cue_number,
        message=message,
        line=cue.source_line,
        start_ms=cue.start_ms,
        end_ms=cue.end_ms,
    )


def lint_cues(
    cues: Iterable[Cue],
    *,
    max_cps: float = 20.0,
    max_line_length: int = 42,
    max_lines: int = 2,
    min_duration_ms: int = 300,
    max_duration_ms: int = 7000,
    ignore: Collection[str] = (),
) -> list[LintIssue]:
    """Return deterministic, non-mutating diagnostics for a subtitle track."""

    if max_cps <= 0:
        raise ValueError("max_cps must be greater than zero")
    if max_line_length <= 0:
        raise ValueError("max_line_length must be greater than zero")
    if max_lines <= 0:
        raise ValueError("max_lines must be greater than zero")
    if min_duration_ms < 0 or max_duration_ms < 0:
        raise ValueError("duration limits cannot be negative")
    if min_duration_ms and max_duration_ms and max_duration_ms < min_duration_ms:
        raise ValueError("max_duration_ms cannot be lower than min_duration_ms")

    ignored = set(ignore)
    cue_list = list(cues)
    issues: list[LintIssue] = []
    identifiers: dict[str, int] = {}

    def add(code: str, cue_number: int, cue: Cue, message: str) -> None:
        if code not in ignored:
            issues.append(_issue(code, cue_number, cue, message))

    for index, cue in enumerate(cue_list, start=1):
        if cue.end_ms <= cue.start_ms:
            add("TIMING_ORDER", index, cue, "end time must be after start time")
        if cue.start_ms < 0:
            add("NEGATIVE_START", index, cue, "start time cannot be negative")
        if not cue.text.strip():
            add("EMPTY_TEXT", index, cue, "cue contains no visible text")

        if cue.identifier:
            identifier = cue.identifier.strip()
            if identifier:
                if identifier in identifiers:
                    add(
                        "DUPLICATE_IDENTIFIER",
                        index,
                        cue,
                        f"identifier {identifier!r} was already used by cue {identifiers[identifier]}",
                    )
                else:
                    identifiers[identifier] = index

        lines = cue.text.splitlines() or [""]
        if len(lines) > max_lines:
            add("TOO_MANY_LINES", index, cue, f"cue has {len(lines)} lines (limit {max_lines})")
        longest = max((len(line) for line in lines), default=0)
        if longest > max_line_length:
            add(
                "LINE_TOO_LONG",
                index,
                cue,
                f"longest line is {longest} characters (limit {max_line_length})",
            )
        if any(line != line.rstrip(" \t") for line in lines):
            add("TRAILING_WHITESPACE", index, cue, "one or more lines contain trailing whitespace")
        if _has_control_character(cue.text):
            add("CONTROL_CHARACTER", index, cue, "cue contains an unexpected control character")

        if cue.duration_ms > 0:
            if min_duration_ms and cue.duration_ms < min_duration_ms:
                add(
                    "DURATION_TOO_SHORT",
                    index,
                    cue,
                    f"duration is {cue.duration_ms} ms (minimum {min_duration_ms} ms)",
                )
            if max_duration_ms and cue.duration_ms > max_duration_ms:
                add(
                    "DURATION_TOO_LONG",
                    index,
                    cue,
                    f"duration is {cue.duration_ms} ms (maximum {max_duration_ms} ms)",
                )
            cps = _visible_characters(cue.text) / (cue.duration_ms / 1000)
            if cps > max_cps:
                add("READING_SPEED", index, cue, f"reading speed is {cps:.1f} cps (limit {max_cps:g})")

        if index > 1:
            previous = cue_list[index - 2]
            if cue.start_ms < previous.start_ms:
                add("OUT_OF_ORDER", index, cue, "cue starts before the previous cue")
            if cue.start_ms < previous.end_ms:
                overlap = previous.end_ms - cue.start_ms
                add("OVERLAP", index, cue, f"overlaps previous cue by {overlap} ms")

    return issues
