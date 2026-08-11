from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from .models import Cue


def normalize_text(cues: Iterable[Cue]) -> list[Cue]:
    """Normalize whitespace without rewriting the subtitle wording."""
    normalized: list[Cue] = []
    for cue in cues:
        lines = [line.rstrip() for line in cue.text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        normalized.append(replace(cue, text="\n".join(lines)))
    return normalized


def shift_cues(cues: Iterable[Cue], offset_ms: int) -> tuple[list[Cue], int]:
    """Shift all cues while preserving durations and preventing negative timestamps.

    Returns the transformed cues and the effective offset. If a negative shift would
    move the first cue before zero, the shift is clipped for the entire track.
    """
    cue_list = list(cues)
    if not cue_list or offset_ms == 0:
        return cue_list, offset_ms
    earliest = min(cue.start_ms for cue in cue_list)
    effective = max(offset_ms, -earliest)
    shifted = [
        cue.with_timing(
            start_ms=cue.start_ms + effective,
            end_ms=cue.end_ms + effective,
        )
        for cue in cue_list
    ]
    return shifted, effective


def resolve_overlaps(cues: Iterable[Cue], *, min_duration_ms: int = 100) -> tuple[list[Cue], int]:
    """Clip a cue's end to the next cue's start when doing so keeps it valid."""
    fixed = list(cues)
    changes = 0
    for i in range(len(fixed) - 1):
        current = fixed[i]
        nxt = fixed[i + 1]
        if current.end_ms > nxt.start_ms and nxt.start_ms - current.start_ms >= min_duration_ms:
            fixed[i] = current.with_timing(end_ms=nxt.start_ms)
            changes += 1
    return fixed, changes
