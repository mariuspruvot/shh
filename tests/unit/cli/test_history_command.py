"""Tests for the shh history command group."""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from shh.adapters.history.store import HistoryStore
from shh.cli.app import app
from shh.config.settings import Settings
from shh.core.models import HistoryEntry
from shh.core.styles import TranscriptionStyle


def _seed(path: Path, n: int = 0) -> None:
    store = HistoryStore(path=path, retention=200)
    for i in range(n):
        store.append(
            HistoryEntry(
                id=f"id{i:04d}",
                ts=datetime(2026, 5, 28, 8, i, tzinfo=UTC),
                text=f"entry {i}",
                style=TranscriptionStyle.NEUTRAL,
                translate_to=None,
                duration_s=1.0,
                detected_lang="en",
            )
        )


def test_history_empty_state(tmp_path: Path) -> None:
    runner = CliRunner()
    history_path = tmp_path / "history.jsonl"
    with patch.object(Settings, "get_history_path", classmethod(lambda cls: history_path)):
        result = runner.invoke(app, ["history"])
    assert result.exit_code == 0
    assert "No history yet" in result.output


def test_history_clear_confirms_and_clears(tmp_path: Path) -> None:
    runner = CliRunner()
    history_path = tmp_path / "history.jsonl"
    _seed(history_path, 3)
    with patch.object(Settings, "get_history_path", classmethod(lambda cls: history_path)):
        result = runner.invoke(app, ["history", "clear"], input="y\n")
    assert result.exit_code == 0
    assert history_path.read_text() == ""


def test_history_clear_declined_keeps_entries(tmp_path: Path) -> None:
    runner = CliRunner()
    history_path = tmp_path / "history.jsonl"
    _seed(history_path, 3)
    with patch.object(Settings, "get_history_path", classmethod(lambda cls: history_path)):
        runner.invoke(app, ["history", "clear"], input="n\n")
    # Typer's confirm(abort=True) exits non-zero on decline, OR Click prints "Aborted"
    # Accept either; the entries must remain
    assert len(history_path.read_text().strip().splitlines()) == 3
