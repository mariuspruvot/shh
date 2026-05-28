"""JSONL-backed history store."""

from pathlib import Path

from pydantic import ValidationError

from shh.core.models import HistoryEntry
from shh.utils.logger import logger


class HistoryStore:
    """Append-only JSONL store with size-bounded rotation."""

    def __init__(self, path: Path, retention: int) -> None:
        self._path = path
        self._retention = retention

    def append(self, entry: HistoryEntry) -> None:
        """Append an entry, then rotate if over retention."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(entry.model_dump_json())
            f.write("\n")
        self._rotate_if_needed()

    def read_all(self) -> list[HistoryEntry]:
        """Return all entries, newest first. Skips malformed lines."""
        if not self._path.exists():
            return []
        entries: list[HistoryEntry] = []
        with self._path.open("r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue
                try:
                    entries.append(HistoryEntry.model_validate_json(line))
                except ValidationError as exc:
                    logger.warning(f"Skipping malformed history line: {exc}")
        entries.reverse()
        return entries

    def clear(self) -> None:
        """Truncate the history file. No-op if it does not exist."""
        if not self._path.exists():
            return
        self._path.write_text("", encoding="utf-8")

    def _rotate_if_needed(self) -> None:
        if not self._path.exists():
            return
        with self._path.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) <= self._retention:
            return
        kept = lines[-self._retention :]
        with self._path.open("w", encoding="utf-8") as f:
            f.writelines(kept)
