"""Tests for RecordingService."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from shh.config.settings import Settings
from shh.core.models import RecordingOptions
from shh.core.styles import TranscriptionStyle
from shh.services.recording import RecordingService


@pytest.mark.asyncio
async def test_transcribe_and_format_neutral(tmp_path: Path) -> None:
    """Test transcription without formatting."""
    settings = Settings(openai_api_key="sk-test-key")
    service = RecordingService(settings)

    audio_data = np.random.randn(16000).astype(np.float32) * 0.5
    options = RecordingOptions(style=TranscriptionStyle.NEUTRAL)

    with (
        patch("shh.services.recording.save_audio_to_wav") as mock_save,
        patch("shh.services.recording.transcribe_audio") as mock_transcribe,
        patch("shh.services.recording.pyperclip.copy") as mock_clipboard,
    ):
        temp_file = tmp_path / "test.wav"
        mock_save.return_value = temp_file
        mock_transcribe.return_value = "Test transcription"
        temp_file.touch()

        result = await service.transcribe_and_format(audio_data, options)

        assert result.text == "Test transcription"
        assert result.style == TranscriptionStyle.NEUTRAL
        assert result.translated_to is None
        assert result.copied_to_clipboard
        mock_clipboard.assert_called_once_with("Test transcription")


@pytest.mark.asyncio
async def test_transcribe_and_format_with_style(tmp_path: Path) -> None:
    """Test transcription with formatting style."""
    settings = Settings(openai_api_key="sk-test-key")
    service = RecordingService(settings)

    audio_data = np.random.randn(16000).astype(np.float32) * 0.5
    options = RecordingOptions(style=TranscriptionStyle.CASUAL)

    with (
        patch("shh.services.recording.save_audio_to_wav") as mock_save,
        patch("shh.services.recording.transcribe_audio") as mock_transcribe,
        patch("shh.services.recording.format_transcription") as mock_format,
        patch("shh.services.recording.pyperclip.copy"),
    ):
        temp_file = tmp_path / "test.wav"
        mock_save.return_value = temp_file
        mock_transcribe.return_value = "Um, test transcription, you know"

        mock_formatted_result = MagicMock()
        mock_formatted_result.text = "Test transcription"
        mock_format.return_value = mock_formatted_result

        temp_file.touch()

        result = await service.transcribe_and_format(audio_data, options)

        assert result.text == "Test transcription"
        assert result.style == TranscriptionStyle.CASUAL
        mock_format.assert_called_once()


@pytest.mark.asyncio
async def test_transcribe_and_format_with_translation(tmp_path: Path) -> None:
    """Test transcription with translation."""
    settings = Settings(openai_api_key="sk-test-key")
    service = RecordingService(settings)

    audio_data = np.random.randn(16000).astype(np.float32) * 0.5
    options = RecordingOptions(style=TranscriptionStyle.NEUTRAL, translate="English")

    with (
        patch("shh.services.recording.save_audio_to_wav") as mock_save,
        patch("shh.services.recording.transcribe_audio") as mock_transcribe,
        patch("shh.services.recording.format_transcription") as mock_format,
        patch("shh.services.recording.pyperclip.copy"),
    ):
        temp_file = tmp_path / "test.wav"
        mock_save.return_value = temp_file
        mock_transcribe.return_value = "Bonjour, ceci est un test"

        mock_formatted_result = MagicMock()
        mock_formatted_result.text = "Hello, this is a test"
        mock_format.return_value = mock_formatted_result

        temp_file.touch()

        result = await service.transcribe_and_format(audio_data, options)

        assert result.text == "Hello, this is a test"
        assert result.translated_to == "English"
        mock_format.assert_called_once()


@pytest.mark.asyncio
async def test_clipboard_failure(tmp_path: Path) -> None:
    """Test handling of clipboard failures."""
    settings = Settings(openai_api_key="sk-test-key")
    service = RecordingService(settings)

    audio_data = np.random.randn(16000).astype(np.float32) * 0.5
    options = RecordingOptions(style=TranscriptionStyle.NEUTRAL)

    with (
        patch("shh.services.recording.save_audio_to_wav") as mock_save,
        patch("shh.services.recording.transcribe_audio") as mock_transcribe,
        patch("shh.services.recording.pyperclip.copy") as mock_clipboard,
    ):
        temp_file = tmp_path / "test.wav"
        mock_save.return_value = temp_file
        mock_transcribe.return_value = "Test transcription"
        mock_clipboard.side_effect = Exception("Clipboard error")
        temp_file.touch()

        result = await service.transcribe_and_format(audio_data, options)

        # Should still succeed but clipboard flag should be False
        assert result.text == "Test transcription"
        assert not result.copied_to_clipboard
