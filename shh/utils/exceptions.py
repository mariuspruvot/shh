"""Custom exceptions for the shh CLI application."""


class ShhError(Exception):
    """Base exception for all shh errors."""

    def __init__(self, message: str) -> None:
        super().__init__(f"[shh] {message}")


class ConfigurationError(ShhError):
    """Raised when there is a configuration problem."""


class AudioRecordingError(ShhError):
    """Raised when there is an audio recording issue."""


class AudioProcessingError(ShhError):
    """Raised when there is an error in audio processing."""


class TranscriptionError(ShhError):
    """Raised when there is an error during transcription."""


class FormattingError(ShhError):
    """Raised when there is an error in formatting the output."""


class APIError(ShhError):
    """Raised when there is an API related error."""


class ClipboardError(ShhError):
    """Raised when there is an error with clipboard operations."""
