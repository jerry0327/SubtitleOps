from __future__ import annotations

import argparse
import json
import os
import stat
import sys
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Sequence

from . import __version__
from .checking import run_check
from .config import CheckConfig, ConfigError, load_config, validate_check_config
from .formats import SubtitleFormat, SubtitleParseError, detect_format, parse_text, render_text as render_subtitle
from .reporting import render_json, render_sarif, render_text as render_text_report
from .rules import LINT_RULE_CODES, iter_rules
from .transforms import normalize_text, resolve_overlaps, shift_cues


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _write(path: Path, content: str) -> None:
    """Atomically replace a UTF-8 text file while preserving its mode when possible."""
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_mode: int | None = None
    try:
        existing_mode = stat.S_IMODE(path.stat().st_mode)
    except FileNotFoundError:
        pass

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if existing_mode is not None:
            os.chmod(temporary, existing_mode)
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _format_for_path(path: Path, explicit: str | None = None) -> SubtitleFormat:
    return detect_format(path, explicit)


def _split_values(values: list[str] | None) -> tuple[str, ...]:
    if not values:
        return ()
    parts: list[str] = []
    for value in values:
        parts.extend(part.strip() for part in value.split(",") if part.strip())
    return tuple(parts)


def _effective_check_config(base: CheckConfig, args: argparse.Namespace) -> CheckConfig:
    updates: dict[str, object] = {}
    for name in (
        "max_cps",
        "max_line_length",
        "max_lines",
        "min_duration_ms",
        "max_duration_ms",
        "fail_on",
        "recursive",
        "jobs",
        "allow_empty",
    ):
        value = getattr(args, name, None)
        if value is not None:
            updates[name] = value

    includes = _split_values(args.include)
    excludes = _split_values(args.exclude)
    ignored = tuple(code.upper() for code in _split_values(args.ignore))
    if includes:
        updates["include"] = includes
    if excludes:
        updates["exclude"] = tuple(base.exclude) + excludes
    if ignored:
        unknown = sorted(set(ignored) - LINT_RULE_CODES)
        if unknown:
            raise ConfigError(f"unknown ignored rule code(s): {', '.join(unknown)}")
        updates["ignore"] = tuple(dict.fromkeys((*base.ignore, *ignored)))
    return validate_check_config(replace(base, **updates))


def _emit(content: str, output: str | None) -> None:
    if output and output != "-":
        _write(Path(output), content)
    else:
        sys.stdout.write(content)


def cmd_check(args: argparse.Namespace) -> int:
    loaded = load_config(args.config, no_config=args.no_config)
    config = _effective_check_config(loaded.check, args)
    report = run_check(
        args.inputs,
        config,
        explicit_format=args.format,
        config_source=loaded.path,
    )
    output_format = args.output_format or "text"
    if output_format == "json":
        content = render_json(report)
    elif output_format == "sarif":
        content = render_sarif(report)
    else:
        show_clean = args.show_clean or (len(report.files) == 1 and report.operational_error_count == 0)
        content = render_text_report(report, show_clean=show_clean)
    _emit(content, args.output)
    return report.exit_code()


def cmd_fix(args: argparse.Namespace) -> int:
    src = Path(args.input)
    out = Path(args.output) if args.output else src
    input_fmt = _format_for_path(src, args.input_format)
    if args.output_format:
        output_fmt = _format_for_path(out, args.output_format)
    elif args.output:
        output_fmt = _format_for_path(out)
    else:
        output_fmt = input_fmt
    cues = parse_text(_read(src), input_fmt)
    cues = normalize_text(cues)

    effective_shift = 0
    if args.shift_ms:
        cues, effective_shift = shift_cues(cues, args.shift_ms)
    overlap_changes = 0
    if args.resolve_overlaps:
        cues, overlap_changes = resolve_overlaps(cues, min_duration_ms=args.min_duration_ms)

    _write(out, render_subtitle(cues, output_fmt))
    summary = [f"wrote {len(cues)} cues to {out}"]
    if args.shift_ms:
        summary.append(f"shift={effective_shift}ms")
    if args.resolve_overlaps:
        summary.append(f"overlaps_fixed={overlap_changes}")
    print("; ".join(summary))
    return 0


def cmd_convert(args: argparse.Namespace) -> int:
    src = Path(args.input)
    out = Path(args.output)
    input_fmt = _format_for_path(src, args.input_format)
    output_fmt = _format_for_path(out, args.output_format)
    cues = parse_text(_read(src), input_fmt)
    _write(out, render_subtitle(normalize_text(cues), output_fmt))
    print(f"converted {len(cues)} cues: {input_fmt} -> {output_fmt}: {out}")
    return 0


def cmd_rules(args: argparse.Namespace) -> int:
    rules = iter_rules(include_operational=args.all)
    if args.json:
        print(
            json.dumps(
                [
                    {
                        "code": rule.code,
                        "name": rule.name,
                        "default_severity": rule.default_severity,
                        "category": rule.category,
                        "description": rule.description,
                        "help_uri": rule.help_uri,
                    }
                    for rule in rules
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    for rule in rules:
        print(f"{rule.code:<24} {rule.default_severity:<7} {rule.description}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="subtitleops",
        description="Lint, normalize, repair, and convert subtitle files.",
    )
    parser.add_argument("--version", action="version", version=f"subtitleops {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="lint files or directories")
    check.add_argument("inputs", nargs="+", help="subtitle files or directories")
    check.add_argument("--format", choices=["srt", "vtt"], help="force one input format")
    check.add_argument("--config", help="explicit .subtitleops.toml or pyproject.toml")
    check.add_argument("--no-config", action="store_true", help="disable configuration discovery")
    check.add_argument("--max-cps", type=float)
    check.add_argument("--max-line-length", type=int)
    check.add_argument("--max-lines", type=int)
    check.add_argument("--min-duration-ms", type=int, help="0 disables the minimum duration rule")
    check.add_argument("--max-duration-ms", type=int, help="0 disables the maximum duration rule")
    check.add_argument("--fail-on", choices=["info", "warning", "error", "none"])
    check.add_argument("--ignore", action="append", help="ignore a lint rule code; repeat or comma-separate")
    check.add_argument("--include", action="append", help="directory include glob; repeat or comma-separate")
    check.add_argument("--exclude", action="append", help="additional directory exclude glob")
    recursion = check.add_mutually_exclusive_group()
    recursion.add_argument("--recursive", dest="recursive", action="store_true")
    recursion.add_argument("--no-recursive", dest="recursive", action="store_false")
    check.set_defaults(recursive=None)
    check.add_argument("--jobs", type=int, help="parallel workers; 0 selects automatically")
    check.add_argument(
        "--allow-empty",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="treat discovery of zero subtitle files as success",
    )
    output = check.add_mutually_exclusive_group()
    output.add_argument("--output-format", choices=["text", "json", "sarif"])
    output.add_argument("--json", dest="output_format", action="store_const", const="json")
    output.add_argument("--sarif", dest="output_format", action="store_const", const="sarif")
    check.add_argument("-o", "--output", help="write the report to a file instead of stdout")
    check.add_argument("--show-clean", action="store_true", help="include clean files in text output")
    check.set_defaults(func=cmd_check)

    fix = subparsers.add_parser("fix", help="normalize and optionally repair subtitle timing")
    fix.add_argument("input")
    fix.add_argument("-o", "--output")
    fix.add_argument("--input-format", choices=["srt", "vtt"])
    fix.add_argument("--output-format", choices=["srt", "vtt"])
    fix.add_argument("--shift-ms", type=int, default=0)
    fix.add_argument("--resolve-overlaps", action="store_true")
    fix.add_argument("--min-duration-ms", type=int, default=100)
    fix.set_defaults(func=cmd_fix)

    convert = subparsers.add_parser("convert", help="convert SRT <-> WebVTT")
    convert.add_argument("input")
    convert.add_argument("output")
    convert.add_argument("--input-format", choices=["srt", "vtt"])
    convert.add_argument("--output-format", choices=["srt", "vtt"])
    convert.set_defaults(func=cmd_convert)

    rules = subparsers.add_parser("rules", help="list stable diagnostic codes")
    rules.add_argument("--json", action="store_true", help="emit machine-readable rule metadata")
    rules.add_argument("--all", action="store_true", help="include operational diagnostic codes")
    rules.set_defaults(func=cmd_rules)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (OSError, SubtitleParseError, ConfigError, ValueError) as exc:
        print(f"subtitleops: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
