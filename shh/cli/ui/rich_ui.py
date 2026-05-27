"""Rich UI output with a single morphing spinner across the pipeline."""

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

from shh.cli.ui.base import RecordingProgress, TranscriptionResult, UIOutput

_DEFAULT_CONSOLE = Console()


class RichUI(UIOutput):
    """Single Live spinner across recording → processing phases. Plain final output."""

    def __init__(self, console: Console | None = None) -> None:
        self._console = console or _DEFAULT_CONSOLE
        self._live: Live | None = None
        self._spinner = Spinner("dots")

    def _ensure_live(self) -> Live:
        if self._live is None:
            self._live = Live(
                self._spinner,
                console=self._console,
                transient=True,
                refresh_per_second=12,
            )
            self._live.start()
        return self._live

    def _set_phase_text(self, text: Text) -> None:
        self._spinner.update(text=text)
        live = self._ensure_live()
        live.refresh()

    def show_error(self, message: str, details: str | None = None) -> None:
        if self._live is not None:
            self._live.stop()
            self._live = None
        self._console.print(f"[red]Error: {message}[/red]")
        if details:
            self._console.print(f"[dim]{details}[/dim]")

    def show_warning(self, message: str) -> None:
        self._console.print(f"[yellow]{message}[/yellow]")

    def show_info(self, message: str) -> None:
        self._console.print(f"[cyan]{message}[/cyan]")

    def show_recording_start(self) -> None:
        self._console.print()

    def show_recording_progress(self, progress: RecordingProgress) -> None:
        text = Text()
        text.append("Recording ", style="bold green")
        text.append(f"{progress.elapsed:.1f}s ", style="cyan")
        text.append("(Enter to stop)", style="dim")
        self._set_phase_text(text)

    def show_recording_stopped(self, reason: str | None = None) -> None:
        if reason:
            if self._live is not None:
                self._live.stop()
                self._live = None
            self._console.print(f"[yellow]{reason}[/yellow]")

    def show_processing_step(self, step: str) -> None:
        self._set_phase_text(Text(step, style="cyan"))

    def show_result(self, result: TranscriptionResult) -> None:
        if self._live is not None:
            self._live.stop()
            self._live = None
        self._console.print(result.text)
        if result.copied_to_clipboard:
            self._console.print("[dim green]✓ copied to clipboard[/dim green]")

    def cleanup(self) -> None:
        if self._live is not None:
            self._live.stop()
            self._live = None
