"""Tests for the Whisper adapter."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from shh.adapters.whisper.client import transcribe_audio
from shh.core.models import WhisperTranscription
from shh.utils.exceptions import TranscriptionError


@pytest.mark.asyncio
async def test_transcribe_audio_returns_whisper_transcription(tmp_path: Path) -> None:
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")

    fake_response = MagicMock()
    fake_response.text = "hello world"
    fake_response.language = "english"

    fake_client = MagicMock()
    fake_client.audio.transcriptions.create = AsyncMock(return_value=fake_response)

    with patch("shh.adapters.whisper.client.AsyncOpenAI", return_value=fake_client):
        result = await transcribe_audio(audio, api_key="sk-test")

    assert isinstance(result, WhisperTranscription)
    assert result.text == "hello world"
    assert result.detected_lang == "english"
    kwargs = fake_client.audio.transcriptions.create.call_args.kwargs
    assert kwargs["response_format"] == "verbose_json"
    assert kwargs["model"] == "whisper-1"
    assert kwargs["file"] is not None


@pytest.mark.asyncio
async def test_transcribe_audio_wraps_errors(tmp_path: Path) -> None:
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF")

    fake_client = MagicMock()
    fake_client.audio.transcriptions.create = AsyncMock(side_effect=RuntimeError("boom"))

    with (
        patch("shh.adapters.whisper.client.AsyncOpenAI", return_value=fake_client),
        pytest.raises(TranscriptionError),
    ):
        await transcribe_audio(audio, api_key="sk-test")
