from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from .models import Cue


@dataclass(frozen=True, slots=True)
class LintIssue:
    code: str
    severity: str
    cue: int
    message: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _visible_characters(text: str) -> int:
    return sum(1 for char in text if not char.isspace())


def lint_cues(
    cues: Iterable[Cue],
    *,
    max_cps: float = 20.0,
    max_line_length: int = 42,
    max_lines: int = 2,
) -> list[LintIssue]:
    cue_list = list(cues)
    issues: list[LintIssue] = []

    for index, cue in enumerate(cue_list, start=1):
        if cue.end_ms <= cue.start_ms:
            issues.append(LintIssue("TIMING_ORDER", "error", index, "end time must be after start time"))
        if cue.start_ms < 0:
            issues.append(LintIssue("NEGATIVE_START", "error", index, "start time cannot be negative"))
        if not cue.text.strip():
            issues.append(LintIssue("EMPTY_TEXT", "warning", index, "cue contains no visible text"))

        lines = cue.text.splitlines() or [""]
        if len(lines) > max_lines:
            issues.append(
                LintIssue("TOO_MANY_LINES", "warning", index, f"cue has {len(lines)} lines (limit {max_lines})")
            )
        longest = max((len(line) for line in lines), default=0)
        if longest > max_line_length:
            issues.append(
                LintIssue(
                    "LINE_TOO_LONG",
                    "warning",
                    index,
                    f"longest line is {longest} characters (limit {max_line_length})",
                )
            )
        if cue.duration_ms > 0:
            cps = _visible_characters(cue.text) / (cue.duration_ms / 1000)
            if cps > max_cps:
                issues.append(
                    LintIssue("READING_SPEED", "warning", index, f"reading speed is {cps:.1f} cps (limit {max_cps:g})")
                )

        if index > 1:
            previous = cue_list[index - 2]
            if cue.start_ms < previous.start_ms:
                issues.append(LintIssue("OUT_OF_ORDER", "error", index, "cue starts before the previous cue"))
            if cue.start_ms < previous.end_ms:
                overlap = previous.end_ms - cue.start_ms
                issues.append(
                    LintIssue("OVERLAP", "error", index, f"overlaps previous cue by {overlap} ms")
                )

    return issues
