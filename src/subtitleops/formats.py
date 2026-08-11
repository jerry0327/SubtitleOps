from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Literal

from .models import Cue

SubtitleFormat = Literal["srt", "vtt"]

_SRT_TS = re.compile(r"^(?P<h>\d{1,3}):(?P<m>\d{2}):(?P<s>\d{2}),(?P<ms>\d{3})$")
_VTT_TS = re.compile(r"^(?:(?P<h>\d{1,3}):)?(?P<m>\d{2}):(?P<s>\d{2})\.(?P<ms>\d{3})$")


class SubtitleParseError(ValueError):
    pass


def detect_format(path: str | Path, explicit: str | None = None) -> SubtitleFormat:
    if explicit:
        fmt = explicit.lower().lstrip(".")
    else:
        suffix = Path(path).suffix.lower().lstrip(".")
        fmt = suffix
    if fmt not in {"srt", "vtt"}:
        raise SubtitleParseError("Could not determine subtitle format; use .srt/.vtt or --format")
    return fmt  # type: ignore[return-value]


def parse_timestamp(value: str, fmt: SubtitleFormat) -> int:
    match = (_SRT_TS if fmt == "srt" else _VTT_TS).match(value.strip())
    if not match:
        raise SubtitleParseError(f"Invalid {fmt.upper()} timestamp: {value!r}")
    h = int(match.group("h") or 0)
    m = int(match.group("m"))
    s = int(match.group("s"))
    ms = int(match.group("ms"))
    if m >= 60 or s >= 60:
        raise SubtitleParseError(f"Out-of-range timestamp: {value!r}")
    return (((h * 60) + m) * 60 + s) * 1000 + ms


def format_timestamp(value_ms: int, fmt: SubtitleFormat) -> str:
    if value_ms < 0:
        raise ValueError("timestamp cannot be negative")
    hours, rem = divmod(value_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, millis = divmod(rem, 1000)
    if fmt == "srt":
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"


def _split_blocks(text: str) -> list[list[str]]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in normalized.split("\n"):
        if line.strip() == "":
            if current:
                blocks.append(current)
                current = []
        else:
            current.append(line)
    if current:
        blocks.append(current)
    return blocks


def parse_srt(text: str) -> list[Cue]:
    cues: list[Cue] = []
    for block_no, lines in enumerate(_split_blocks(text), start=1):
        timing_idx = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if timing_idx is None:
            raise SubtitleParseError(f"SRT block {block_no} has no timing line")
        identifier = lines[0].strip() if timing_idx > 0 else None
        timing = lines[timing_idx]
        start_raw, end_raw = (part.strip() for part in timing.split("-->", 1))
        end_token = end_raw.split()[0]
        start_ms = parse_timestamp(start_raw, "srt")
        end_ms = parse_timestamp(end_token, "srt")
        cue_text = "\n".join(lines[timing_idx + 1 :])
        cues.append(Cue(start_ms, end_ms, cue_text, identifier=identifier))
    return cues


def parse_vtt(text: str) -> list[Cue]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    lines = normalized.split("\n")
    if not lines or not lines[0].strip().startswith("WEBVTT"):
        raise SubtitleParseError("WebVTT input must start with WEBVTT")

    body = "\n".join(lines[1:])
    cues: list[Cue] = []
    for block_no, block in enumerate(_split_blocks(body), start=1):
        if not block:
            continue
        first = block[0].strip()
        if first == "STYLE" or first == "REGION" or first.startswith("NOTE"):
            continue
        timing_idx = next((i for i, line in enumerate(block) if "-->" in line), None)
        if timing_idx is None:
            if not cues:
                continue
            raise SubtitleParseError(f"WebVTT block {block_no} has no timing line")
        identifier = block[0].strip() if timing_idx > 0 else None
        start_raw, right = (part.strip() for part in block[timing_idx].split("-->", 1))
        right_parts = right.split(maxsplit=1)
        end_raw = right_parts[0]
        settings = right_parts[1] if len(right_parts) == 2 else None
        start_ms = parse_timestamp(start_raw, "vtt")
        end_ms = parse_timestamp(end_raw, "vtt")
        cue_text = "\n".join(block[timing_idx + 1 :])
        cues.append(Cue(start_ms, end_ms, cue_text, identifier=identifier, settings=settings))
    return cues


def parse_text(text: str, fmt: SubtitleFormat) -> list[Cue]:
    return parse_srt(text) if fmt == "srt" else parse_vtt(text)


def render_srt(cues: Iterable[Cue]) -> str:
    blocks: list[str] = []
    for index, cue in enumerate(cues, start=1):
        blocks.append(
            f"{index}\n"
            f"{format_timestamp(cue.start_ms, 'srt')} --> {format_timestamp(cue.end_ms, 'srt')}\n"
            f"{cue.text}"
        )
    return "\n\n".join(blocks).rstrip() + "\n"


def render_vtt(cues: Iterable[Cue]) -> str:
    blocks: list[str] = []
    for cue in cues:
        identifier = f"{cue.identifier}\n" if cue.identifier and not cue.identifier.isdigit() else ""
        settings = f" {cue.settings}" if cue.settings else ""
        blocks.append(
            f"{identifier}"
            f"{format_timestamp(cue.start_ms, 'vtt')} --> {format_timestamp(cue.end_ms, 'vtt')}{settings}\n"
            f"{cue.text}"
        )
    body = "\n\n".join(blocks).rstrip()
    return "WEBVTT\n\n" + body + ("\n" if body else "")


def render_text(cues: Iterable[Cue], fmt: SubtitleFormat) -> str:
    return render_srt(cues) if fmt == "srt" else render_vtt(cues)
