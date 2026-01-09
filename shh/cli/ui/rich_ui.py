"""Rich UI output with beautiful terminal formatting."""

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from shh.cli.ui.base import RecordingProgress, TranscriptionResult, UIOutput

console = Console()


class RichUI(UIOutput):
    """Rich-based UI with colors, panels, and live updates."""

    def __init__(self) -> None:
        """Initialize Rich UI."""
        self._live: Live | None = None

    def show_error(self, message: str, details: str | None = None) -> None:
        """Display error with Rich formatting."""
        console.print(f"[red]Error: {message}[/red]")
        if details:
            console.print(f"[dim]{details}[/dim]")

    def show_warning(self, message: str) -> None:
        """Display warning with Rich formatting."""
        console.print(f"[yellow]{message}[/yellow]")

    def show_info(self, message: str) -> None:
        """Display info with Rich formatting."""
        console.print(f"[cyan]{message}[/cyan]")

    def show_recording_start(self) -> None:
        """Display recording started."""
        console.print()

    def show_recording_progress(self, progress: RecordingProgress) -> None:
        """Display live recording progress."""
        # Create live display if not exists
        if self._live is None:
            self._live = Live(auto_refresh=False, console=console)
            self._live.start()

        # Create progress text
        progress_text = Text()
        progress_text.append("Recording... ", style="bold green")
        progress_text.append(f"{progress.elapsed:.1f}s ", style="cyan")
        progress_text.append(f"/ {progress.max_duration:.0f}s ", style="dim")
        progress_text.append("[Press Enter to stop]", style="dim")

        self._live.update(progress_text)
        self._live.refresh()

    def show_recording_stopped(self, reason: str | None = None) -> None:
        """Display recording stopped."""
        if self._live:
            self._live.stop()
            self._live = None

        if reason:
            console.print(f"\n[yellow]{reason}[/yellow]")

    def show_processing_step(self, step: str) -> None:
        """Display a processing step."""
        console.print(f"[cyan]{step}[/cyan]")

    def show_result(self, result: TranscriptionResult) -> None:
        """Display the final transcription in a panel."""
        console.print()

        # Build title with context
        title_parts = ["Transcription"]
        if result.translated_to:
            title_parts.append(f"(translated to {result.translated_to})")
        if result.style and result.style != "neutral":
            title_parts.append(f"[{result.style}]")
        if result.copied_to_clipboard:
            title_parts.append("✓ copied to clipboard")

        title = " ".join(title_parts)

        result_panel = Panel(
            result.text,
            title=title,
            border_style="green" if result.copied_to_clipboard else "yellow",
        )
        console.print(result_panel)
        console.print()

    def cleanup(self) -> None:
        """Stop any live displays."""
        if self._live:
            self._live.stop()
            self._live = None
