"""Core domain models."""

from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, Field

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


class HistoryEntry(BaseModel):
    """A persisted transcription record."""

    id: str = Field(..., min_length=4, max_length=64)
    ts: datetime
    text: str
    style: TranscriptionStyle
    translate_to: str | None = None
    duration_s: float = Field(..., ge=0)
    detected_lang: str | None = None


class WhisperTranscription(BaseModel):
    """Result returned by the Whisper adapter."""

    text: str
    detected_lang: str | None = None
