"""Tests for HistoryStore."""

from datetime import UTC, datetime
from pathlib import Path

from shh.adapters.history.store import HistoryStore
from shh.core.models import HistoryEntry
from shh.core.styles import TranscriptionStyle


def make_entry(idx: int) -> HistoryEntry:
    return HistoryEntry(
        id=f"id{idx:04d}",
        ts=datetime(2026, 5, 28, 8, 0, idx % 60, tzinfo=UTC),
        text=f"entry {idx}",
        style=TranscriptionStyle.NEUTRAL,
        translate_to=None,
        duration_s=float(idx),
        detected_lang=None,
    )


def test_read_all_on_missing_file(tmp_path: Path) -> None:
    store = HistoryStore(path=tmp_path / "history.jsonl", retention=10)
    assert store.read_all() == []


def test_append_then_read(tmp_path: Path) -> None:
    store = HistoryStore(path=tmp_path / "history.jsonl", retention=10)
    e1 = make_entry(1)
    e2 = make_entry(2)
    store.append(e1)
    store.append(e2)
    result = store.read_all()
    assert [e.id for e in result] == ["id0002", "id0001"]  # newest first


def test_retention_rotates_oldest_out(tmp_path: Path) -> None:
    store = HistoryStore(path=tmp_path / "history.jsonl", retention=3)
    for i in range(5):
        store.append(make_entry(i))
    result = store.read_all()
    assert len(result) == 3
    # Newest-first; entries 4, 3, 2 are kept (0 and 1 rotated out)
    assert [e.id for e in result] == ["id0004", "id0003", "id0002"]


def test_clear_truncates(tmp_path: Path) -> None:
    path = tmp_path / "history.jsonl"
    store = HistoryStore(path=path, retention=10)
    store.append(make_entry(1))
    store.clear()
    assert path.exists()
    assert path.stat().st_size == 0
    assert store.read_all() == []


def test_clear_on_missing_file_is_noop(tmp_path: Path) -> None:
    path = tmp_path / "history.jsonl"
    store = HistoryStore(path=path, retention=10)
    store.clear()  # should not raise
    assert store.read_all() == []


def test_read_all_skips_malformed_lines(tmp_path: Path) -> None:
    path = tmp_path / "history.jsonl"
    store = HistoryStore(path=path, retention=10)
    store.append(make_entry(1))
    with path.open("a") as f:
        f.write("not-json-at-all\n")
    store.append(make_entry(2))
    result = store.read_all()
    assert [e.id for e in result] == ["id0002", "id0001"]


def test_append_creates_parent_directory(tmp_path: Path) -> None:
    nested = tmp_path / "subdir" / "history.jsonl"
    store = HistoryStore(path=nested, retention=10)
    store.append(make_entry(1))
    assert nested.exists()
