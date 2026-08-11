from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from html import escape
from pathlib import Path
from typing import Iterable, Sequence, cast

from .models import Cue, DocumentBlock, SubtitleDocument, SubtitleFormat

_SRT_TS = re.compile(r"^(?P<h>\d{1,3}):(?P<m>\d{2}):(?P<s>\d{2}),(?P<ms>\d{3})$")
_VTT_TS = re.compile(r"^(?:(?P<h>\d{1,3}):)?(?P<m>\d{2}):(?P<s>\d{2})\.(?P<ms>\d{3})$")
_TTML_CLOCK = re.compile(
    r"^(?P<h>\d+):(?P<m>\d{2}):(?P<s>\d{2})(?P<fraction>\.\d+)?$"
)
_TTML_CLOCK_FRAMES = re.compile(
    r"^(?P<h>\d+):(?P<m>\d{2}):(?P<s>\d{2}):(?P<f>\d+)(?:\.(?P<sf>\d+))?$"
)
_TTML_OFFSET = re.compile(r"^(?P<count>\d+(?:\.\d+)?)(?P<metric>ms|h|m|s|f|t)$")
_TTML_UNSAFE_DECLARATION = re.compile(r"<!\s*(?:DOCTYPE|ENTITY)\b", re.IGNORECASE)
_TTML_P_TAG = re.compile(r"<(?:[A-Za-z_][\w.-]*:)?p(?=\s|/?>)", re.IGNORECASE)
_VTT_SIGNATURE = re.compile(r"^WEBVTT(?:[ \t].*)?$")
_XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
_XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
_XML_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")


class SubtitleParseError(ValueError):
    pass


def detect_format(path: str | Path, explicit: str | None = None) -> SubtitleFormat:
    if explicit:
        fmt = explicit.lower().lstrip(".")
    else:
        suffix = Path(path).suffix.lower().lstrip(".")
        fmt = "ttml" if suffix in {"ttml", "dfxp"} else suffix
    if fmt == "dfxp":
        fmt = "ttml"
    if fmt not in {"srt", "vtt", "ttml"}:
        raise SubtitleParseError(
            "Could not determine subtitle format; use .srt/.vtt/.ttml/.dfxp or --format"
        )
    return cast(SubtitleFormat, fmt)


def _decimal_milliseconds(seconds: Decimal) -> int:
    return int((seconds * Decimal(1000)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


@dataclass(frozen=True, slots=True)
class _TTMLTimingContext:
    frame_rate: Decimal | None
    sub_frame_rate: Decimal
    tick_rate: Decimal


def _parse_positive_decimal(value: str, *, name: str) -> Decimal:
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise SubtitleParseError(f"Invalid TTML {name}: {value!r}") from exc
    if not result.is_finite() or result <= 0:
        raise SubtitleParseError(f"TTML {name} must be greater than zero")
    return result


def _parse_positive_integer(value: str, *, name: str) -> Decimal:
    if not value.isdigit() or int(value) <= 0:
        raise SubtitleParseError(f"TTML {name} must be a positive integer")
    return Decimal(value)


def _parse_ttml_time(value: str, context: _TTMLTimingContext) -> int:
    raw = value.strip()
    clock = _TTML_CLOCK.fullmatch(raw)
    if clock:
        hours = int(clock.group("h"))
        minutes = int(clock.group("m"))
        seconds = int(clock.group("s"))
        if minutes >= 60 or seconds >= 60:
            raise SubtitleParseError(f"Out-of-range TTML clock time: {value!r}")
        fraction = Decimal(clock.group("fraction") or "0")
        total = Decimal(hours * 3600 + minutes * 60 + seconds) + fraction
        return _decimal_milliseconds(total)

    frame_clock = _TTML_CLOCK_FRAMES.fullmatch(raw)
    if frame_clock:
        if context.frame_rate is None:
            raise SubtitleParseError(
                f"TTML frame clock {value!r} requires ttp:frameRate on the tt element"
            )
        hours = int(frame_clock.group("h"))
        minutes = int(frame_clock.group("m"))
        seconds = int(frame_clock.group("s"))
        frames = Decimal(frame_clock.group("f"))
        subframes = Decimal(frame_clock.group("sf") or "0")
        if minutes >= 60 or seconds >= 60:
            raise SubtitleParseError(f"Out-of-range TTML clock time: {value!r}")
        if frames >= context.frame_rate:
            raise SubtitleParseError(f"TTML frame component is out of range: {value!r}")
        if subframes >= context.sub_frame_rate:
            raise SubtitleParseError(f"TTML sub-frame component is out of range: {value!r}")
        total = Decimal(hours * 3600 + minutes * 60 + seconds)
        total += frames / context.frame_rate
        if subframes:
            total += subframes / (context.frame_rate * context.sub_frame_rate)
        return _decimal_milliseconds(total)

    offset = _TTML_OFFSET.fullmatch(raw)
    if offset:
        count = Decimal(offset.group("count"))
        metric = offset.group("metric")
        if metric == "h":
            seconds_value = count * Decimal(3600)
        elif metric == "m":
            seconds_value = count * Decimal(60)
        elif metric == "s":
            seconds_value = count
        elif metric == "ms":
            seconds_value = count / Decimal(1000)
        elif metric == "f":
            if context.frame_rate is None:
                raise SubtitleParseError(
                    f"TTML frame offset {value!r} requires ttp:frameRate on the tt element"
                )
            seconds_value = count / context.frame_rate
        else:
            seconds_value = count / context.tick_rate
        return _decimal_milliseconds(seconds_value)

    if raw.startswith("wallclock("):
        raise SubtitleParseError("TTML wallclock time expressions are not supported")
    raise SubtitleParseError(f"Invalid TTML time expression: {value!r}")


def parse_timestamp(value: str, fmt: SubtitleFormat) -> int:
    if fmt == "ttml":
        return _parse_ttml_time(
            value,
            _TTMLTimingContext(frame_rate=None, sub_frame_rate=Decimal(1), tick_rate=Decimal(1)),
        )
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
    separator = "," if fmt == "srt" else "."
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}{separator}{millis:03d}"


def _normalized_lines(text: str) -> list[str]:
    return text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff").split("\n")


def _split_blocks(lines: Sequence[str], *, first_line: int = 1) -> list[tuple[int, list[str]]]:
    blocks: list[tuple[int, list[str]]] = []
    current: list[str] = []
    current_start = first_line
    for offset, line in enumerate(lines):
        line_number = first_line + offset
        if line.strip() == "":
            if current:
                blocks.append((current_start, current))
                current = []
            current_start = line_number + 1
        else:
            if not current:
                current_start = line_number
            current.append(line)
    if current:
        blocks.append((current_start, current))
    return blocks


def parse_srt_document(text: str) -> SubtitleDocument:
    cues: list[Cue] = []
    for block_no, (block_start, lines) in enumerate(_split_blocks(_normalized_lines(text)), start=1):
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
        cues.append(
            Cue(
                start_ms,
                end_ms,
                cue_text,
                identifier=identifier,
                source_line=block_start + timing_idx,
            )
        )
    return SubtitleDocument("srt", tuple(cues))


def parse_srt(text: str) -> list[Cue]:
    return list(parse_srt_document(text).cues)


def _vtt_block_kind(first: str) -> str | None:
    if first == "STYLE":
        return "style"
    if first == "REGION":
        return "region"
    if first == "NOTE" or first.startswith("NOTE ") or first.startswith("NOTE\t"):
        return "note"
    return None


def parse_vtt_document(text: str) -> SubtitleDocument:
    lines = _normalized_lines(text)
    if not lines or not _VTT_SIGNATURE.fullmatch(lines[0].strip()):
        raise SubtitleParseError("WebVTT input must start with a valid WEBVTT signature")

    separator = next((i for i, line in enumerate(lines[1:], start=1) if line.strip() == ""), None)
    if separator is None:
        if any("-->" in line for line in lines[1:]):
            raise SubtitleParseError("WebVTT header must be followed by a blank line before cues")
        header = tuple(line for line in lines if line != "") or ("WEBVTT",)
        return SubtitleDocument("vtt", (), header=header)
    if any("-->" in line for line in lines[1:separator]):
        raise SubtitleParseError("WebVTT header must be followed by a blank line before cues")

    header = tuple(lines[:separator])
    cues: list[Cue] = []
    blocks: list[DocumentBlock] = []
    body = lines[separator + 1 :]
    for block_no, (block_start, block) in enumerate(
        _split_blocks(body, first_line=separator + 2), start=1
    ):
        first = block[0].strip()
        kind = _vtt_block_kind(first)
        if kind is not None:
            blocks.append(
                DocumentBlock(
                    cast(str, kind),  # narrowed by _vtt_block_kind
                    tuple(block),
                    len(cues),
                    source_line=block_start,
                )
            )
            continue

        timing_idx = next((i for i, line in enumerate(block) if "-->" in line), None)
        if timing_idx is None:
            raise SubtitleParseError(f"WebVTT block {block_no} has no timing line")
        identifier = block[0].strip() if timing_idx > 0 else None
        start_raw, right = (part.strip() for part in block[timing_idx].split("-->", 1))
        right_parts = right.split(maxsplit=1)
        end_raw = right_parts[0]
        settings = right_parts[1] if len(right_parts) == 2 else None
        start_ms = parse_timestamp(start_raw, "vtt")
        end_ms = parse_timestamp(end_raw, "vtt")
        cue_text = "\n".join(block[timing_idx + 1 :])
        cues.append(
            Cue(
                start_ms,
                end_ms,
                cue_text,
                identifier=identifier,
                settings=settings,
                source_line=block_start + timing_idx,
            )
        )
    return SubtitleDocument("vtt", tuple(cues), header=header, blocks=tuple(blocks))


def parse_vtt(text: str) -> list[Cue]:
    return list(parse_vtt_document(text).cues)


def _local_name(value: str) -> str:
    return value.rsplit("}", 1)[-1].rsplit(":", 1)[-1]


def _attribute(element: ET.Element, local_name: str) -> str | None:
    for name, value in element.attrib.items():
        if _local_name(name) == local_name:
            return value
    return None


def _ttml_timing_context(root: ET.Element) -> _TTMLTimingContext:
    time_base = (_attribute(root, "timeBase") or "media").lower()
    if time_base != "media":
        raise SubtitleParseError(
            f"TTML time base {time_base!r} is not supported; only media time is accepted"
        )

    frame_rate_raw = _attribute(root, "frameRate")
    frame_rate = (
        _parse_positive_integer(frame_rate_raw, name="frameRate") if frame_rate_raw else None
    )
    multiplier_raw = _attribute(root, "frameRateMultiplier")
    if multiplier_raw:
        if frame_rate is None:
            raise SubtitleParseError("TTML frameRateMultiplier requires frameRate")
        parts = multiplier_raw.split()
        if len(parts) != 2:
            raise SubtitleParseError("TTML frameRateMultiplier must contain two positive integers")
        numerator = _parse_positive_integer(parts[0], name="frameRateMultiplier numerator")
        denominator = _parse_positive_integer(parts[1], name="frameRateMultiplier denominator")
        frame_rate *= numerator / denominator

    sub_frame_rate = _parse_positive_integer(
        _attribute(root, "subFrameRate") or "1", name="subFrameRate"
    )
    tick_rate_raw = _attribute(root, "tickRate")
    if tick_rate_raw:
        tick_rate = _parse_positive_integer(tick_rate_raw, name="tickRate")
    elif frame_rate is not None:
        tick_rate = frame_rate * sub_frame_rate
    else:
        tick_rate = Decimal(1)
    return _TTMLTimingContext(frame_rate, sub_frame_rate, tick_rate)


def _ttml_source_lines(text: str) -> list[int]:
    return [text.count("\n", 0, match.start()) + 1 for match in _TTML_P_TAG.finditer(text)]


def _validate_ttml_p_descendants(element: ET.Element) -> None:
    timing_names = {"begin", "end", "dur", "timeContainer"}
    for descendant in element.iter():
        if descendant is element:
            continue
        if _local_name(descendant.tag) == "p":
            raise SubtitleParseError("nested TTML p elements are not supported")
        if any(_local_name(name) in timing_names for name in descendant.attrib):
            raise SubtitleParseError("timed descendants inside a TTML p element are not supported")
        if _XML_SPACE in descendant.attrib:
            raise SubtitleParseError("descendant xml:space changes inside a TTML p element are not supported")


def _ttml_text(element: ET.Element, *, preserve_space: bool) -> str:
    pieces: list[str] = []

    def visit(node: ET.Element) -> None:
        if node.text:
            pieces.append(node.text)
        for child in node:
            if _local_name(child.tag) == "br":
                pieces.append("\n")
            else:
                visit(child)
            if child.tail:
                pieces.append(child.tail)

    visit(element)
    raw = "".join(pieces).replace("\r\n", "\n").replace("\r", "\n")
    if preserve_space:
        return raw.strip("\n")

    lines = [re.sub(r"[\t\f\v ]+", " ", line).strip() for line in raw.split("\n")]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def parse_ttml_document(text: str) -> SubtitleDocument:
    normalized = text.lstrip("\ufeff")
    if _TTML_UNSAFE_DECLARATION.search(normalized):
        raise SubtitleParseError("TTML DOCTYPE and ENTITY declarations are not accepted")
    try:
        root = ET.fromstring(normalized)
    except ET.ParseError as exc:
        raise SubtitleParseError(f"Invalid TTML XML: {exc}") from exc
    if _local_name(root.tag) != "tt":
        raise SubtitleParseError("TTML document root must be a tt element")

    context = _ttml_timing_context(root)
    source_lines = iter(_ttml_source_lines(normalized))
    cues: list[Cue] = []

    def walk(
        element: ET.Element,
        *,
        parent_begin: int,
        parent_end: int | None,
        inherited_space: bool,
    ) -> None:
        container = (_attribute(element, "timeContainer") or "par").lower()
        if container != "par":
            raise SubtitleParseError("TTML timeContainer values other than 'par' are not supported")

        begin_raw = _attribute(element, "begin")
        begin = parent_begin + (_parse_ttml_time(begin_raw, context) if begin_raw else 0)
        end_raw = _attribute(element, "end")
        duration_raw = _attribute(element, "dur")
        if end_raw and duration_raw:
            raise SubtitleParseError("TTML element cannot specify both end and dur")
        if end_raw:
            end = parent_begin + _parse_ttml_time(end_raw, context)
        elif duration_raw:
            end = begin + _parse_ttml_time(duration_raw, context)
        else:
            end = parent_end
        if parent_end is not None and end is not None:
            end = min(end, parent_end)

        space_value = element.attrib.get(_XML_SPACE)
        preserve_space = inherited_space if space_value is None else space_value == "preserve"
        if space_value not in {None, "default", "preserve"}:
            raise SubtitleParseError(f"Invalid xml:space value: {space_value!r}")

        if _local_name(element.tag) == "p":
            _validate_ttml_p_descendants(element)
            line = next(source_lines, None)
            if end is None:
                raise SubtitleParseError("TTML p element requires end/dur or a timed ancestor")
            identifier = element.attrib.get(_XML_ID) or _attribute(element, "id")
            cues.append(
                Cue(
                    begin,
                    end,
                    _ttml_text(element, preserve_space=preserve_space),
                    identifier=identifier,
                    source_line=line,
                )
            )
            return

        for child in element:
            if _local_name(child.tag) in {"head", "metadata", "styling", "layout"}:
                continue
            walk(
                child,
                parent_begin=begin,
                parent_end=end,
                inherited_space=preserve_space,
            )

    walk(root, parent_begin=0, parent_end=None, inherited_space=False)
    return SubtitleDocument("ttml", tuple(cues))


def parse_ttml(text: str) -> list[Cue]:
    return list(parse_ttml_document(text).cues)


def parse_document(text: str, fmt: SubtitleFormat) -> SubtitleDocument:
    if fmt == "srt":
        return parse_srt_document(text)
    if fmt == "vtt":
        return parse_vtt_document(text)
    return parse_ttml_document(text)


def parse_text(text: str, fmt: SubtitleFormat) -> list[Cue]:
    return list(parse_document(text, fmt).cues)


def render_srt(cues: Iterable[Cue]) -> str:
    blocks: list[str] = []
    for index, cue in enumerate(cues, start=1):
        blocks.append(
            f"{index}\n"
            f"{format_timestamp(cue.start_ms, 'srt')} --> {format_timestamp(cue.end_ms, 'srt')}\n"
            f"{cue.text}"
        )
    return "\n\n".join(blocks).rstrip() + "\n"


def _render_vtt_cue(cue: Cue) -> str:
    identifier = f"{cue.identifier}\n" if cue.identifier and not cue.identifier.isdigit() else ""
    settings = f" {cue.settings}" if cue.settings else ""
    return (
        f"{identifier}"
        f"{format_timestamp(cue.start_ms, 'vtt')} --> {format_timestamp(cue.end_ms, 'vtt')}{settings}\n"
        f"{cue.text}"
    )


def render_vtt_document(document: SubtitleDocument) -> str:
    header = document.header if document.format == "vtt" and document.header else ("WEBVTT",)
    grouped: dict[int, list[DocumentBlock]] = {}
    for block in document.blocks if document.format == "vtt" else ():
        if block.before_cue < 0 or block.before_cue > len(document.cues):
            raise ValueError("WebVTT block position is outside the cue range")
        grouped.setdefault(block.before_cue, []).append(block)

    sections: list[str] = ["\n".join(header)]
    for index in range(len(document.cues) + 1):
        sections.extend("\n".join(block.lines) for block in grouped.get(index, ()))
        if index < len(document.cues):
            sections.append(_render_vtt_cue(document.cues[index]))
    body = "\n\n".join(sections).rstrip()
    return body + "\n" if len(sections) > 1 else body + "\n\n"


def render_vtt(cues: Iterable[Cue]) -> str:
    return render_vtt_document(SubtitleDocument("vtt", tuple(cues), header=("WEBVTT",)))


def _ttml_text_markup(text: str) -> str:
    return "<br />".join(escape(line, quote=False) for line in text.split("\n"))


def render_ttml(cues: Iterable[Cue]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<tt xmlns="http://www.w3.org/ns/ttml" xml:space="preserve">',
        "  <body>",
        "    <div>",
    ]
    for cue in cues:
        identifier = (
            f' xml:id="{escape(cue.identifier, quote=True)}"'
            if cue.identifier and _XML_NAME.fullmatch(cue.identifier)
            else ""
        )
        begin = format_timestamp(cue.start_ms, "ttml")
        end = format_timestamp(cue.end_ms, "ttml")
        lines.append(
            f'      <p{identifier} begin="{begin}" end="{end}">{_ttml_text_markup(cue.text)}</p>'
        )
    lines.extend(["    </div>", "  </body>", "</tt>"])
    return "\n".join(lines) + "\n"


def render_document(document: SubtitleDocument, fmt: SubtitleFormat | None = None) -> str:
    target = document.format if fmt is None else fmt
    if target == "vtt" and document.format == "vtt":
        return render_vtt_document(document)
    return render_text(document.cues, target)


def render_text(cues: Iterable[Cue], fmt: SubtitleFormat) -> str:
    if fmt == "srt":
        return render_srt(cues)
    if fmt == "vtt":
        return render_vtt(cues)
    return render_ttml(cues)
