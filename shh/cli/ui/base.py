"""Base UI abstraction for output formatting."""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class RecordingProgress:
    """Recording progress state."""

    elapsed: float
    max_duration: float


@dataclass
class TranscriptionResult:
    """Result of a transcription operation."""

    text: str
    copied_to_clipboard: bool = True
    style: str | None = None
    translated_to: str | None = None


class UIOutput(Protocol):
    """
    Protocol for UI output implementations.

    Using Protocol instead of ABC for structural typing - more Pythonic and flexible.
    Any class implementing these methods can be used as UIOutput without explicit inheritance.
    """

    def show_error(self, message: str, details: str | None = None) -> None:
        """Display an error message."""
        ...

    def show_warning(self, message: str) -> None:
        """Display a warning message."""
        ...

    def show_info(self, message: str) -> None:
        """Display an info message."""
        ...

    def show_recording_start(self) -> None:
        """Display recording started."""
        ...

    def show_recording_progress(self, progress: RecordingProgress) -> None:
        """Display recording progress (called repeatedly)."""
        ...

    def show_recording_stopped(self, reason: str | None = None) -> None:
        """Display recording stopped."""
        ...

    def show_processing_step(self, step: str) -> None:
        """Display a processing step (e.g., 'Transcribing...', 'Formatting...')."""
        ...

    def show_result(self, result: TranscriptionResult) -> None:
        """Display the final transcription result."""
        ...

    def cleanup(self) -> None:
        """Cleanup any UI resources (e.g., Live displays)."""
        ...
