from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class Cue:
    """A subtitle cue with millisecond timing and optional source location."""

    start_ms: int
    end_ms: int
    text: str
    identifier: str | None = None
    settings: str | None = None
    source_line: int | None = None

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms

    def with_timing(self, *, start_ms: int | None = None, end_ms: int | None = None) -> "Cue":
        return replace(
            self,
            start_ms=self.start_ms if start_ms is None else start_ms,
            end_ms=self.end_ms if end_ms is None else end_ms,
        )
