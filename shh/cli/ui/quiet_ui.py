"""Minimal quiet UI output - progress bar and 'Done'."""

from shh.cli.ui.base import RecordingProgress, TranscriptionResult, UIOutput


class QuietUI(UIOutput):
    """Minimal UI: shows recording time, then 'Done'. Text copied to clipboard only."""

    def show_error(self, message: str, details: str | None = None) -> None:
        """Display error to stderr."""
        print(f"Error: {message}")
        if details:
            print(f"  {details}")

    def show_warning(self, message: str) -> None:
        """Display warning."""
        print(f"Warning: {message}")

    def show_info(self, message: str) -> None:
        """No info messages in quiet mode."""

    def show_recording_start(self) -> None:
        """Start is shown by first progress update."""

    def show_recording_progress(self, progress: RecordingProgress) -> None:
        """Show minimal recording progress on same line."""
        print(
            f"\rRecording... {progress.elapsed:.1f}s / {progress.max_duration:.0f}s",
            end="",
            flush=True,
        )

    def show_recording_stopped(self, reason: str | None = None) -> None:
        """Clear the progress line."""
        print()  # New line after progress

    def show_processing_step(self, step: str) -> None:
        """No processing step output."""

    def show_result(self, result: TranscriptionResult) -> None:
        """Silent result. Text is in clipboard only."""

    def cleanup(self) -> None:
        """Nothing to cleanup in quiet mode."""
