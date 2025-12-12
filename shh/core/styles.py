"""Transcription style definitions."""

from enum import StrEnum


class TranscriptionStyle(StrEnum):
    """Available transcription formatting styles."""

    NEUTRAL = "neutral"
    CASUAL = "casual"
    BUSINESS = "business"
