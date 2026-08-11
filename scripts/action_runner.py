from __future__ import annotations

import os
import sys
from dataclasses import replace
from pathlib import Path

from subtitleops.checking import run_check
from subtitleops.config import ConfigError, load_config, validate_check_config
from subtitleops.fileio import write_text_atomic
from subtitleops.formats import SubtitleParseError
from subtitleops.reporting import render_sarif, render_text


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


def _boolean(value: str, *, name: str) -> bool | None:
    if not value:
        return None
    normalized = value.lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise ConfigError(f"{name} must be true or false")


def _integer(value: str, *, name: str) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc


def _set_output(name: str, value: object) -> None:
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with Path(output).open("a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")


def _summary(markdown: str) -> None:
    destination = os.environ.get("GITHUB_STEP_SUMMARY")
    if destination:
        with Path(destination).open("a", encoding="utf-8") as handle:
            handle.write(markdown.rstrip() + "\n")


def _paths() -> list[str]:
    values = [line.strip() for line in os.environ.get("SUBTITLEOPS_ACTION_PATHS", ".").splitlines()]
    return [value for value in values if value] or ["."]


def main() -> int:
    report_path = Path(_env("SUBTITLEOPS_ACTION_REPORT_PATH") or "subtitleops.sarif")
    try:
        no_config = _boolean(_env("SUBTITLEOPS_ACTION_NO_CONFIG"), name="no-config") or False
        config_path = _env("SUBTITLEOPS_ACTION_CONFIG") or None
        loaded = load_config(config_path, no_config=no_config)
        updates: dict[str, object] = {}

        fail_on = _env("SUBTITLEOPS_ACTION_FAIL_ON")
        if fail_on:
            updates["fail_on"] = fail_on
        allow_empty = _boolean(_env("SUBTITLEOPS_ACTION_ALLOW_EMPTY"), name="allow-empty")
        if allow_empty is not None:
            updates["allow_empty"] = allow_empty
        max_file_bytes = _integer(
            _env("SUBTITLEOPS_ACTION_MAX_FILE_BYTES"), name="max-file-bytes"
        )
        if max_file_bytes is not None:
            updates["max_file_bytes"] = max_file_bytes

        config = validate_check_config(replace(loaded.check, **updates))
        explicit_format = _env("SUBTITLEOPS_ACTION_FORMAT") or None
        if explicit_format not in {None, "srt", "vtt", "ttml"}:
            raise ConfigError("format must be one of: srt, vtt, ttml")

        report = run_check(
            _paths(),
            config,
            explicit_format=explicit_format,  # type: ignore[arg-type]
            base_dir=Path.cwd(),
            config_source=loaded.path,
        )
        write_text_atomic(report_path, render_sarif(report))
        text = render_text(report, show_clean=True)
        sys.stdout.write(text)
        exit_code = report.exit_code()
        _set_output("exit-code", exit_code)
        _set_output("files-checked", report.files_checked)
        _set_output("issues", report.issue_count)
        _set_output("report-path", report_path.as_posix())
        _set_output("report-exists", "true")
        _summary(
            "## SubtitleOps\n\n"
            f"- Exit code: `{exit_code}`\n"
            f"- Files checked: `{report.files_checked}`\n"
            f"- Cues: `{report.cue_count}`\n"
            f"- Findings: `{report.issue_count}`\n"
            f"- Operational errors: `{report.operational_error_count}`\n"
            f"- SARIF: `{report_path.as_posix()}`"
        )
    except (ConfigError, OSError, UnicodeError, SubtitleParseError, ValueError) as exc:
        print(f"subtitleops action: error: {exc}", file=sys.stderr)
        _set_output("exit-code", 2)
        _set_output("files-checked", 0)
        _set_output("issues", 0)
        _set_output("report-path", report_path.as_posix())
        _set_output("report-exists", "false")
        _summary(f"## SubtitleOps\n\nOperational error: `{exc}`")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
