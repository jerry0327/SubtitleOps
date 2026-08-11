from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Rule:
    """Metadata for a stable SubtitleOps diagnostic code."""

    code: str
    name: str
    default_severity: str
    category: str
    description: str

    @property
    def help_uri(self) -> str:
        anchor = self.code.lower().replace("_", "-")
        return f"https://github.com/jerry0327/SubtitleOps/blob/main/docs/rules.md#{anchor}"


_RULE_LIST = (
    Rule(
        "TIMING_ORDER",
        "Invalid timing order",
        "error",
        "timing",
        "Cue end time is not after its start time.",
    ),
    Rule("NEGATIVE_START", "Negative start time", "error", "timing", "Cue starts before timestamp zero."),
    Rule("OUT_OF_ORDER", "Out-of-order cue", "error", "timing", "Cue starts before the preceding cue."),
    Rule("OVERLAP", "Overlapping cues", "error", "timing", "Adjacent cues overlap in time."),
    Rule(
        "DURATION_TOO_SHORT",
        "Cue duration too short",
        "warning",
        "readability",
        "Cue duration is below the configured minimum.",
    ),
    Rule(
        "DURATION_TOO_LONG",
        "Cue duration too long",
        "warning",
        "readability",
        "Cue duration exceeds the configured maximum.",
    ),
    Rule("EMPTY_TEXT", "Empty cue", "warning", "content", "Cue contains no visible text."),
    Rule(
        "READING_SPEED",
        "Reading speed too high",
        "warning",
        "readability",
        "Visible characters per second exceed the configured limit.",
    ),
    Rule(
        "LINE_TOO_LONG",
        "Subtitle line too long",
        "warning",
        "readability",
        "A cue line exceeds the configured character limit.",
    ),
    Rule(
        "TOO_MANY_LINES",
        "Too many subtitle lines",
        "warning",
        "readability",
        "A cue contains more lines than configured.",
    ),
    Rule(
        "TRAILING_WHITESPACE",
        "Trailing whitespace",
        "warning",
        "formatting",
        "A cue line ends with spaces or tabs.",
    ),
    Rule(
        "CONTROL_CHARACTER",
        "Control character",
        "warning",
        "content",
        "Cue text contains an unexpected control character.",
    ),
    Rule(
        "DUPLICATE_IDENTIFIER",
        "Duplicate cue identifier",
        "warning",
        "structure",
        "A non-empty cue identifier is reused.",
    ),
    Rule("PARSE_ERROR", "Subtitle parse error", "error", "operational", "The subtitle document could not be parsed."),
    Rule("IO_ERROR", "Input/output error", "error", "operational", "The subtitle file could not be read."),
    Rule("DECODE_ERROR", "Text decoding error", "error", "operational", "The subtitle file is not valid UTF-8 text."),
    Rule("INPUT_NOT_FOUND", "Input not found", "error", "operational", "A requested input path does not exist."),
    Rule(
        "UNSUPPORTED_FORMAT",
        "Unsupported subtitle format",
        "error",
        "operational",
        "A requested file is not SRT or WebVTT and no format override was supplied.",
    ),
    Rule(
        "NO_FILES",
        "No subtitle files discovered",
        "error",
        "operational",
        "Input discovery found no supported subtitle files.",
    ),
)

RULES: dict[str, Rule] = {rule.code: rule for rule in _RULE_LIST}
LINT_RULE_CODES: frozenset[str] = frozenset(rule.code for rule in _RULE_LIST if rule.category != "operational")
SEVERITY_ORDER: dict[str, int] = {"info": 0, "warning": 1, "error": 2}


def iter_rules(*, include_operational: bool = True) -> tuple[Rule, ...]:
    if include_operational:
        return _RULE_LIST
    return tuple(rule for rule in _RULE_LIST if rule.category != "operational")
