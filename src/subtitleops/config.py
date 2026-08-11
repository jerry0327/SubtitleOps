from __future__ import annotations

from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import Any, Mapping

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10 CI
    import tomli as tomllib  # type: ignore[no-redef]

from .rules import LINT_RULE_CODES, SEVERITY_ORDER

DEFAULT_INCLUDE = ("*.srt", "*.vtt")
DEFAULT_EXCLUDE = (
    ".git/**",
    "**/.git/**",
    ".venv/**",
    "**/.venv/**",
    "venv/**",
    "**/venv/**",
    "build/**",
    "**/build/**",
    "dist/**",
    "**/dist/**",
    "**/__pycache__/**",
)


class ConfigError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class CheckConfig:
    max_cps: float = 20.0
    max_line_length: int = 42
    max_lines: int = 2
    min_duration_ms: int = 300
    max_duration_ms: int = 7000
    fail_on: str = "warning"
    ignore: tuple[str, ...] = ()
    include: tuple[str, ...] = DEFAULT_INCLUDE
    exclude: tuple[str, ...] = DEFAULT_EXCLUDE
    recursive: bool = True
    jobs: int = 0
    allow_empty: bool = False


@dataclass(frozen=True, slots=True)
class LoadedConfig:
    check: CheckConfig
    path: Path | None = None


_ALLOWED_CHECK_KEYS = frozenset(field.name for field in fields(CheckConfig))


def _as_string_tuple(value: object, *, key: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ConfigError(f"{key} must be an array of non-empty strings")
    return tuple(value)


def _string_tuple(value: object, *, key: str, allow_empty: bool) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or not all(isinstance(item, str) and item for item in value):
        raise ConfigError(f"{key} must be a sequence of non-empty strings")
    result = tuple(dict.fromkeys(value))
    if not allow_empty and not result:
        raise ConfigError(f"{key} must contain at least one pattern")
    return result


def validate_check_config(config: CheckConfig) -> CheckConfig:
    """Validate and normalize a programmatically constructed check configuration."""
    if not isinstance(config.max_cps, (int, float)) or isinstance(config.max_cps, bool):
        raise ConfigError("check.max_cps must be a number")
    integer_fields = {
        "max_line_length": config.max_line_length,
        "max_lines": config.max_lines,
        "min_duration_ms": config.min_duration_ms,
        "max_duration_ms": config.max_duration_ms,
        "jobs": config.jobs,
    }
    for key, value in integer_fields.items():
        if not isinstance(value, int) or isinstance(value, bool):
            raise ConfigError(f"check.{key} must be an integer")
    if not isinstance(config.recursive, bool) or not isinstance(config.allow_empty, bool):
        raise ConfigError("check.recursive and check.allow_empty must be true or false")
    if not isinstance(config.fail_on, str):
        raise ConfigError("check.fail_on must be a string")

    include = _string_tuple(config.include, key="check.include", allow_empty=False)
    exclude = _string_tuple(config.exclude, key="check.exclude", allow_empty=True)
    ignore = tuple(code.upper() for code in _string_tuple(config.ignore, key="check.ignore", allow_empty=True))
    normalized = replace(
        config,
        max_cps=float(config.max_cps),
        fail_on=config.fail_on.lower(),
        include=include,
        exclude=exclude,
        ignore=tuple(dict.fromkeys(ignore)),
    )

    if normalized.max_cps <= 0:
        raise ConfigError("check.max_cps must be greater than zero")
    if normalized.max_line_length <= 0:
        raise ConfigError("check.max_line_length must be greater than zero")
    if normalized.max_lines <= 0:
        raise ConfigError("check.max_lines must be greater than zero")
    if normalized.min_duration_ms < 0 or normalized.max_duration_ms < 0:
        raise ConfigError("check duration limits cannot be negative")
    if (
        normalized.min_duration_ms
        and normalized.max_duration_ms
        and normalized.max_duration_ms < normalized.min_duration_ms
    ):
        raise ConfigError("check.max_duration_ms cannot be lower than check.min_duration_ms")
    if normalized.fail_on not in {*SEVERITY_ORDER, "none"}:
        raise ConfigError("check.fail_on must be one of: info, warning, error, none")
    if normalized.jobs < 0 or normalized.jobs > 256:
        raise ConfigError("check.jobs must be between 0 and 256")
    unknown_rules = sorted(set(normalized.ignore) - LINT_RULE_CODES)
    if unknown_rules:
        raise ConfigError(f"unknown ignored rule code(s): {', '.join(unknown_rules)}")
    return normalized


def _parse_check_table(table: Mapping[str, Any]) -> CheckConfig:
    unknown = sorted(set(table) - _ALLOWED_CHECK_KEYS)
    if unknown:
        raise ConfigError(f"unknown check configuration key(s): {', '.join(unknown)}")

    values: dict[str, Any] = {}
    for key, value in table.items():
        if key in {"include", "exclude", "ignore"}:
            parsed = _as_string_tuple(value, key=f"check.{key}")
            values[key] = tuple(item.upper() for item in parsed) if key == "ignore" else parsed
        elif key in {"max_line_length", "max_lines", "min_duration_ms", "max_duration_ms", "jobs"}:
            if not isinstance(value, int) or isinstance(value, bool):
                raise ConfigError(f"check.{key} must be an integer")
            values[key] = value
        elif key == "max_cps":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ConfigError("check.max_cps must be a number")
            values[key] = float(value)
        elif key in {"recursive", "allow_empty"}:
            if not isinstance(value, bool):
                raise ConfigError(f"check.{key} must be true or false")
            values[key] = value
        elif key == "fail_on":
            if not isinstance(value, str):
                raise ConfigError("check.fail_on must be a string")
            values[key] = value.lower()

    return validate_check_config(CheckConfig(**values))


def _read_toml(path: Path) -> Mapping[str, Any]:
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except OSError as exc:
        raise ConfigError(f"could not read configuration {path}: {exc}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"invalid TOML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"configuration root in {path} must be a table")
    return data


def _extract_subtitleops_table(path: Path, data: Mapping[str, Any]) -> Mapping[str, Any]:
    if path.name == "pyproject.toml":
        tool = data.get("tool", {})
        if not isinstance(tool, dict):
            raise ConfigError("pyproject.toml [tool] must be a table")
        subtitleops = tool.get("subtitleops")
        if subtitleops is None:
            raise ConfigError(f"{path} does not contain [tool.subtitleops]")
        if not isinstance(subtitleops, dict):
            raise ConfigError("[tool.subtitleops] must be a table")
        return subtitleops
    return data


def parse_config(path: Path) -> LoadedConfig:
    path = path.expanduser().resolve()
    data = _extract_subtitleops_table(path, _read_toml(path))
    unknown = sorted(set(data) - {"version", "check"})
    if unknown:
        raise ConfigError(f"unknown SubtitleOps configuration key(s): {', '.join(unknown)}")
    version = data.get("version", 1)
    if version != 1:
        raise ConfigError("SubtitleOps configuration version must be 1")
    check_table = data.get("check", {})
    if not isinstance(check_table, dict):
        raise ConfigError("[check] / [tool.subtitleops.check] must be a table")
    return LoadedConfig(_parse_check_table(check_table), path)


def find_config(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).expanduser().resolve()
    if current.is_file():
        current = current.parent
    for directory in (current, *current.parents):
        dedicated = directory / ".subtitleops.toml"
        if dedicated.is_file():
            return dedicated
        pyproject = directory / "pyproject.toml"
        if pyproject.is_file():
            try:
                data = _read_toml(pyproject)
            except ConfigError:
                raise
            tool = data.get("tool", {})
            if isinstance(tool, dict) and "subtitleops" in tool:
                return pyproject
    return None


def load_config(
    explicit: str | Path | None = None,
    *,
    no_config: bool = False,
    start: Path | None = None,
) -> LoadedConfig:
    if explicit is not None and no_config:
        raise ConfigError("--config and --no-config cannot be used together")
    if no_config:
        return LoadedConfig(CheckConfig(), None)
    if explicit is not None:
        path = Path(explicit)
        if not path.is_file():
            raise ConfigError(f"configuration file not found: {path}")
        return parse_config(path)
    discovered = find_config(start)
    return parse_config(discovered) if discovered else LoadedConfig(CheckConfig(), None)
