"""SubtitleOps public package API."""

from .checking import BatchReport, FileReport, run_check
from .config import CheckConfig, ConfigError, load_config
from .formats import (
    SubtitleParseError,
    parse_document,
    parse_srt,
    parse_ttml,
    parse_vtt,
    parse_vtt_document,
    render_document,
    render_srt,
    render_ttml,
    render_vtt,
    render_vtt_document,
)
from .linting import LintIssue, lint_cues
from .models import Cue, DocumentBlock, SubtitleDocument, SubtitleFormat

__all__ = [
    "BatchReport",
    "CheckConfig",
    "ConfigError",
    "Cue",
    "DocumentBlock",
    "FileReport",
    "LintIssue",
    "SubtitleDocument",
    "SubtitleFormat",
    "SubtitleParseError",
    "lint_cues",
    "load_config",
    "parse_document",
    "parse_srt",
    "parse_ttml",
    "parse_vtt",
    "parse_vtt_document",
    "render_document",
    "render_srt",
    "render_ttml",
    "render_vtt",
    "render_vtt_document",
    "run_check",
]

__version__ = "0.3.0"
