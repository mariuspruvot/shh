"""Core domain models."""

from dataclasses import dataclass

from shh.core.styles import TranscriptionStyle


@dataclass
class RecordingOptions:
    """Options for recording and transcription."""

    style: TranscriptionStyle = TranscriptionStyle.NEUTRAL
    translate: str | None = None
    show_progress: bool = True


@dataclass
class TranscriptionOutput:
    """Output from the transcription process."""

    text: str
    style: TranscriptionStyle
    translated_to: str | None = None
    copied_to_clipboard: bool = False
