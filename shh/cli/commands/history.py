"""History command group: browse and manage transcription history."""

from datetime import UTC, datetime

import pyperclip  # type: ignore[import-untyped]
import typer
from rich.console import Console

from shh.adapters.history.store import HistoryStore
from shh.cli.ui.history_picker import build_picker_app
from shh.config.settings import Settings
from shh.core.models import HistoryEntry

history_app = typer.Typer(help="Browse and manage transcription history.")
_console = Console()


def _store() -> HistoryStore:
    settings = Settings.load_from_file() or Settings()
    return HistoryStore(
        path=Settings.get_history_path(),
        retention=settings.history_retention,
    )


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _copy_text(entry: HistoryEntry) -> None:
    pyperclip.copy(entry.text)


@history_app.callback(invoke_without_command=True)
def history_default(ctx: typer.Context) -> None:
    """Open the interactive picker. Enter copies the selected entry."""
    if ctx.invoked_subcommand is not None:
        return
    store = _store()
    entries = store.read_all()
    if not entries:
        _console.print("[dim]No history yet. Run `shh` first to create one.[/dim]")
        return
    picker = build_picker_app(entries, on_copy=_copy_text, now_provider=_now)
    selected = picker.run()
    if selected is not None:
        _console.print("[dim green]✓ copied to clipboard[/dim green]")


@history_app.command("clear")
def history_clear() -> None:
    """Delete all history entries (asks for confirmation)."""
    store = _store()
    entries = store.read_all()
    if not entries:
        _console.print("[dim]History is already empty.[/dim]")
        return
    typer.confirm(f"Delete {len(entries)} entries?", abort=True)
    store.clear()
    _console.print(f"[green]Cleared {len(entries)} entries.[/green]")
