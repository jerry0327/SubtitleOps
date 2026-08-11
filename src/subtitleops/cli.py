from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from . import __version__
from .formats import SubtitleFormat, SubtitleParseError, detect_format, parse_text, render_text
from .linting import lint_cues
from .transforms import normalize_text, resolve_overlaps, shift_cues


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _format_for_path(path: Path, explicit: str | None = None) -> SubtitleFormat:
    return detect_format(path, explicit)


def cmd_check(args: argparse.Namespace) -> int:
    path = Path(args.input)
    fmt = _format_for_path(path, args.format)
    cues = parse_text(_read(path), fmt)
    issues = lint_cues(
        cues,
        max_cps=args.max_cps,
        max_line_length=args.max_line_length,
        max_lines=args.max_lines,
    )
    if args.json:
        print(json.dumps({"file": str(path), "cues": len(cues), "issues": [i.to_dict() for i in issues]}, indent=2))
    elif not issues:
        print(f"OK  {path} ({len(cues)} cues)")
    else:
        for issue in issues:
            print(f"{path}: cue {issue.cue}: {issue.severity.upper()} {issue.code}: {issue.message}")
        print(f"{len(issues)} issue(s) across {len(cues)} cue(s)")
    return 1 if issues else 0


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

    _write(out, render_text(cues, output_fmt))
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
    _write(out, render_text(normalize_text(cues), output_fmt))
    print(f"converted {len(cues)} cues: {input_fmt} -> {output_fmt}: {out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="subtitleops", description="Lint, normalize, repair, and convert subtitle files.")
    parser.add_argument("--version", action="version", version=f"subtitleops {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="lint a subtitle file")
    check.add_argument("input")
    check.add_argument("--format", choices=["srt", "vtt"])
    check.add_argument("--max-cps", type=float, default=20.0)
    check.add_argument("--max-line-length", type=int, default=42)
    check.add_argument("--max-lines", type=int, default=2)
    check.add_argument("--json", action="store_true", help="emit machine-readable JSON")
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (OSError, SubtitleParseError, ValueError) as exc:
        print(f"subtitleops: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
