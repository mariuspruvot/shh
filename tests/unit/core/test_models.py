"""Tests for core Pydantic models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from shh.core.models import HistoryEntry, WhisperTranscription
from shh.core.styles import TranscriptionStyle


def test_history_entry_minimal() -> None:
    entry = HistoryEntry(
        id="abcd1234",
        ts=datetime(2026, 5, 28, 8, 58, 1, tzinfo=UTC),
        text="Bonjour",
        style=TranscriptionStyle.NEUTRAL,
        translate_to=None,
        duration_s=5.2,
        detected_lang=None,
    )
    assert entry.id == "abcd1234"
    assert entry.detected_lang is None


def test_history_entry_roundtrip_json() -> None:
    entry = HistoryEntry(
        id="abcd1234",
        ts=datetime(2026, 5, 28, 8, 58, 1, tzinfo=UTC),
        text="Hi",
        style=TranscriptionStyle.CASUAL,
        translate_to="french",
        duration_s=2.5,
        detected_lang="en",
    )
    raw = entry.model_dump_json()
    revived = HistoryEntry.model_validate_json(raw)
    assert revived == entry


def test_history_entry_requires_id() -> None:
    with pytest.raises(ValidationError):
        HistoryEntry.model_validate(
            {
                "ts": datetime.now(tz=UTC).isoformat(),
                "text": "x",
                "style": TranscriptionStyle.NEUTRAL,
                "translate_to": None,
                "duration_s": 0.1,
                "detected_lang": None,
            }
        )


def test_whisper_transcription_holds_text_and_language() -> None:
    wt = WhisperTranscription(text="hello world", detected_lang="en")
    assert wt.text == "hello world"
    assert wt.detected_lang == "en"


def test_whisper_transcription_language_is_optional() -> None:
    wt = WhisperTranscription(text="hello", detected_lang=None)
    assert wt.detected_lang is None
