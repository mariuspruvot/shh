"""Minimal quiet UI output - just prints 'Done' when finished."""

from shh.cli.ui.base import RecordingProgress, TranscriptionResult, UIOutput


class QuietUI(UIOutput):
    """Minimal UI that only prints the final result and 'Done'."""

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
        """No output on recording start."""

    def show_recording_progress(self, progress: RecordingProgress) -> None:
        """No progress output in quiet mode."""

    def show_recording_stopped(self, reason: str | None = None) -> None:
        """No output on recording stop."""

    def show_processing_step(self, step: str) -> None:
        """No processing step output."""

    def show_result(self, result: TranscriptionResult) -> None:
        """Just print the text and 'Done'."""
        print(result.text)
        print("Done")

    def cleanup(self) -> None:
        """Nothing to cleanup in quiet mode."""
