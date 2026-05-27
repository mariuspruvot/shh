"""Integration tests for the full recording flow (with mocked APIs)."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from shh.adapters.audio.processor import save_audio_to_wav
from shh.adapters.history.store import HistoryStore
from shh.adapters.llm.formatter import format_transcription
from shh.adapters.whisper.client import transcribe_audio
from shh.cli.ui.base import RecordingProgress, TranscriptionResult
from shh.config.settings import Settings
from shh.core.models import RecordingOptions
from shh.core.styles import TranscriptionStyle
from shh.services.recording import RecordingService


class _FakeUI:
    def __init__(self) -> None:
        self.processing_steps: list[str] = []
        self.errors: list[str] = []

    def show_error(self, message: str, details: str | None = None) -> None:
        self.errors.append(message)

    def show_warning(self, message: str) -> None:
        pass

    def show_info(self, message: str) -> None:
        pass

    def show_recording_start(self) -> None:
        pass

    def show_recording_progress(self, progress: RecordingProgress) -> None:
        pass

    def show_recording_stopped(self, reason: str | None = None) -> None:
        pass

    def show_processing_step(self, step: str) -> None:
        self.processing_steps.append(step)

    def show_result(self, result: TranscriptionResult) -> None:
        pass

    def cleanup(self) -> None:
        pass


@pytest.mark.asyncio
async def test_transcribe_audio_success(tmp_path: Path) -> None:
    """Test successful transcription with mocked OpenAI API."""
    audio_data = np.random.randn(16000).astype(np.float32) * 0.5
    wav_path = save_audio_to_wav(audio_data)

    try:
        with patch("shh.adapters.whisper.client.AsyncOpenAI") as mock_client:
            mock_transcription = MagicMock()
            mock_transcription.text = "Hello, this is a test transcription."
            mock_transcription.language = "en"

            mock_instance = mock_client.return_value
            mock_instance.audio.transcriptions.create = AsyncMock(return_value=mock_transcription)

            result = await transcribe_audio(
                audio_file_path=wav_path,
                api_key="sk-test-key",
            )

            assert result.text == "Hello, this is a test transcription."
            mock_instance.audio.transcriptions.create.assert_called_once()

    finally:
        wav_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_transcribe_audio_api_error(tmp_path: Path) -> None:
    """Test that transcription errors are properly raised."""
    audio_data = np.random.randn(16000).astype(np.float32) * 0.5
    wav_path = save_audio_to_wav(audio_data)

    try:
        with patch("shh.adapters.whisper.client.AsyncOpenAI") as mock_client:
            mock_instance = mock_client.return_value
            mock_instance.audio.transcriptions.create = AsyncMock(
                side_effect=Exception("API Error")
            )

            with pytest.raises(Exception, match="Failed to transcribe audio"):
                await transcribe_audio(wav_path, "sk-test-key")

    finally:
        wav_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_format_transcription_neutral() -> None:
    """Test that neutral style returns text as-is (no LLM call)."""
    text = "This is a test transcription."

    result = await format_transcription(
        text,
        style=TranscriptionStyle.NEUTRAL,
        api_key="sk-test-key",
    )

    assert result.text == text


@pytest.mark.asyncio
async def test_format_transcription_casual() -> None:
    """Test casual formatting with mocked PydanticAI."""
    text = "Um, hello, this is like a test."

    with (
        patch("shh.adapters.llm.formatter.OpenAIChatModel"),
        patch("shh.adapters.llm.formatter.Agent") as mock_agent_class,
    ):
        mock_agent = MagicMock()
        mock_result = MagicMock()
        mock_result.output.text = "Hello, this is a test."

        mock_agent.run = AsyncMock(return_value=mock_result)
        mock_agent_class.return_value = mock_agent

        result = await format_transcription(
            text,
            style=TranscriptionStyle.CASUAL,
            api_key="sk-test-key",
        )

        assert result.text == "Hello, this is a test."
        mock_agent.run.assert_called_once()


@pytest.mark.asyncio
async def test_format_transcription_with_translation() -> None:
    """Test formatting with translation."""
    text = "Bonjour, ceci est un test."

    with (
        patch("shh.adapters.llm.formatter.OpenAIChatModel"),
        patch("shh.adapters.llm.formatter.Agent") as mock_agent_class,
    ):
        mock_agent = MagicMock()
        mock_result = MagicMock()
        mock_result.output.text = "Hello, this is a test."

        mock_agent.run = AsyncMock(return_value=mock_result)
        mock_agent_class.return_value = mock_agent

        result = await format_transcription(
            text,
            style=TranscriptionStyle.CASUAL,
            api_key="sk-test-key",
            target_language="English",
        )

        assert result.text == "Hello, this is a test."
        call_args = mock_agent.run.call_args
        assert "English" in call_args[0][0]


@pytest.mark.asyncio
async def test_full_pipeline_mock(tmp_path: Path) -> None:
    """Test the complete pipeline: audio → transcribe → format."""
    audio_data = np.random.randn(16000).astype(np.float32) * 0.5
    wav_path = save_audio_to_wav(audio_data)

    try:
        with patch("shh.adapters.whisper.client.AsyncOpenAI") as mock_whisper:
            mock_transcription = MagicMock()
            mock_transcription.text = "Um, this is a test transcription."
            mock_transcription.language = "en"

            mock_whisper_instance = mock_whisper.return_value
            mock_whisper_instance.audio.transcriptions.create = AsyncMock(
                return_value=mock_transcription
            )

            whisper_result = await transcribe_audio(wav_path, "sk-test-key")
            assert whisper_result.text == "Um, this is a test transcription."

            with (
                patch("shh.adapters.llm.formatter.OpenAIChatModel"),
                patch("shh.adapters.llm.formatter.Agent") as mock_agent_class,
            ):
                mock_agent = MagicMock()
                mock_result = MagicMock()
                mock_result.output.text = "This is a test transcription."

                mock_agent.run = AsyncMock(return_value=mock_result)
                mock_agent_class.return_value = mock_agent

                formatted = await format_transcription(
                    whisper_result.text,
                    style=TranscriptionStyle.CASUAL,
                    api_key="sk-test-key",
                )

                assert formatted.text == "This is a test transcription."

    finally:
        wav_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_service_full_pipeline_mock(tmp_path: Path) -> None:
    """Test RecordingService.transcribe_and_format with mocked APIs."""
    settings = Settings(openai_api_key="sk-test-key")
    fake_ui = _FakeUI()
    store = HistoryStore(path=tmp_path / "history.jsonl", retention=200)
    service = RecordingService(settings=settings, ui=fake_ui, history_store=store)

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
        mock_transcribe.return_value = MagicMock(
            text="Um, test transcription.", detected_lang="en"
        )

        mock_formatted = MagicMock()
        mock_formatted.text = "Test transcription."
        mock_format.return_value = mock_formatted
        temp_file.touch()

        result = await service.transcribe_and_format(audio_data, options)

    assert result.text == "Test transcription."
    assert result.style == TranscriptionStyle.CASUAL
    assert "Transcribing" in fake_ui.processing_steps
    assert "Formatting" in fake_ui.processing_steps
