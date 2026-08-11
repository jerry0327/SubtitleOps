"""SubtitleOps public package API."""

from .checking import BatchReport, FileReport, run_check
from .config import CheckConfig, ConfigError, load_config
from .formats import SubtitleParseError, parse_srt, parse_vtt, render_srt, render_vtt
from .linting import LintIssue, lint_cues
from .models import Cue

__all__ = [
    "BatchReport",
    "CheckConfig",
    "ConfigError",
    "Cue",
    "FileReport",
    "LintIssue",
    "SubtitleParseError",
    "lint_cues",
    "load_config",
    "parse_srt",
    "parse_vtt",
    "render_srt",
    "render_vtt",
    "run_check",
]

__version__ = "0.2.0"
