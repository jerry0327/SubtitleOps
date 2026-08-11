from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path

DEFAULT_MAX_FILE_BYTES = 10 * 1024 * 1024


class FileTooLargeError(ValueError):
    """Raised when a subtitle exceeds the configured bounded-read limit."""

    def __init__(self, path: Path, *, limit: int, observed: int | None = None) -> None:
        self.path = path
        self.limit = limit
        self.observed = observed
        size = f"{observed} bytes" if observed is not None else f"more than {limit} bytes"
        super().__init__(f"{path} is {size}; configured limit is {limit} bytes")


def read_utf8(path: Path, *, max_file_bytes: int = DEFAULT_MAX_FILE_BYTES) -> str:
    """Read UTF-8/BOM text without allocating beyond a configured byte limit."""
    if not isinstance(max_file_bytes, int) or isinstance(max_file_bytes, bool):
        raise ValueError("max_file_bytes must be an integer")
    if max_file_bytes < 0:
        raise ValueError("max_file_bytes cannot be negative")

    with path.open("rb") as handle:
        if max_file_bytes:
            data = handle.read(max_file_bytes + 1)
            if len(data) > max_file_bytes:
                observed: int | None
                try:
                    observed = path.stat().st_size
                except OSError:
                    observed = None
                raise FileTooLargeError(path, limit=max_file_bytes, observed=observed)
        else:
            data = handle.read()
    return data.decode("utf-8-sig")


def write_text_atomic(path: Path, content: str, *, preserve_mode: bool = True) -> None:
    """Atomically replace a UTF-8 text file and optionally retain its mode."""
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_mode: int | None = None
    if preserve_mode:
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
