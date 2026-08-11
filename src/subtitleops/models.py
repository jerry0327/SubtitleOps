from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, Literal

SubtitleFormat = Literal["srt", "vtt", "ttml"]
WebVTTBlockKind = Literal["note", "style", "region"]


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


@dataclass(frozen=True, slots=True)
class DocumentBlock:
    """A preserved WebVTT document-level block.

    ``before_cue`` is the number of cues that preceded the block in the source
    document. This retains NOTE placement while keeping the cue model immutable.
    """

    kind: WebVTTBlockKind
    lines: tuple[str, ...]
    before_cue: int
    source_line: int | None = None


@dataclass(frozen=True, slots=True)
class SubtitleDocument:
    """A parsed subtitle document plus format-level data that can be preserved."""

    format: SubtitleFormat
    cues: tuple[Cue, ...]
    header: tuple[str, ...] = ()
    blocks: tuple[DocumentBlock, ...] = ()

    def with_cues(self, cues: Iterable[Cue]) -> "SubtitleDocument":
        return replace(self, cues=tuple(cues))
