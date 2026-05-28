"""Tests for RecordingService."""

from pathlib import Path
from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from shh.adapters.history.store import HistoryStore
from shh.cli.ui.base import RecordingProgress, TranscriptionResult
from shh.config.settings import Settings
from shh.core.models import RecordingOptions, WhisperTranscription
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


def _make_service(
    settings: Settings,
    tmp_path: Path,
    ui: _FakeUI | None = None,
) -> tuple[RecordingService, HistoryStore, _FakeUI]:
    fake_ui = ui if ui is not None else _FakeUI()
    store = HistoryStore(path=tmp_path / "history.jsonl", retention=200)
    service = RecordingService(settings=settings, ui=fake_ui, history_store=store)
    return service, store, fake_ui


@pytest.mark.asyncio
async def test_transcribe_and_format_neutral(tmp_path: Path) -> None:
    """Test transcription without formatting."""
    settings = Settings(openai_api_key="sk-test-key")
    service, _, _ = _make_service(settings, tmp_path)

    audio_data = np.random.randn(16000).astype(np.float32) * 0.5
    options = RecordingOptions(style=TranscriptionStyle.NEUTRAL)

    with (
        patch("shh.services.recording.save_audio_to_wav") as mock_save,
        patch("shh.services.recording.transcribe_audio") as mock_transcribe,
        patch("shh.services.recording.pyperclip.copy") as mock_clipboard,
    ):
        temp_file = tmp_path / "test.wav"
        mock_save.return_value = temp_file
        mock_transcribe.return_value = WhisperTranscription(
            text="Test transcription", detected_lang="en"
        )
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
    service, _, _ = _make_service(settings, tmp_path)

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
        mock_transcribe.return_value = WhisperTranscription(
            text="Um, test transcription, you know", detected_lang="en"
        )

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
    service, _, _ = _make_service(settings, tmp_path)

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
        mock_transcribe.return_value = WhisperTranscription(
            text="Bonjour, ceci est un test", detected_lang="fr"
        )

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
    service, _, _ = _make_service(settings, tmp_path)

    audio_data = np.random.randn(16000).astype(np.float32) * 0.5
    options = RecordingOptions(style=TranscriptionStyle.NEUTRAL)

    with (
        patch("shh.services.recording.save_audio_to_wav") as mock_save,
        patch("shh.services.recording.transcribe_audio") as mock_transcribe,
        patch("shh.services.recording.pyperclip.copy") as mock_clipboard,
    ):
        temp_file = tmp_path / "test.wav"
        mock_save.return_value = temp_file
        mock_transcribe.return_value = WhisperTranscription(
            text="Test transcription", detected_lang="en"
        )
        mock_clipboard.side_effect = Exception("Clipboard error")
        temp_file.touch()

        result = await service.transcribe_and_format(audio_data, options)

        # Should still succeed but clipboard flag should be False
        assert result.text == "Test transcription"
        assert not result.copied_to_clipboard


@pytest.mark.asyncio
async def test_neutral_no_translate_skips_formatting_step(tmp_path: Path) -> None:
    """When style=NEUTRAL and no translate, no Formatting step is emitted."""
    settings = Settings(openai_api_key="sk-test-key")
    fake_ui = _FakeUI()
    service, _, _ = _make_service(settings, tmp_path, ui=fake_ui)

    audio_data = np.random.randn(16000).astype(np.float32) * 0.5
    options = RecordingOptions(style=TranscriptionStyle.NEUTRAL)

    with (
        patch("shh.services.recording.save_audio_to_wav") as mock_save,
        patch("shh.services.recording.transcribe_audio") as mock_transcribe,
        patch("shh.services.recording.pyperclip.copy"),
    ):
        temp_file = tmp_path / "test.wav"
        mock_save.return_value = temp_file
        mock_transcribe.return_value = WhisperTranscription(
            text="Hello world", detected_lang="en"
        )
        temp_file.touch()

        await service.transcribe_and_format(audio_data, options)

    assert "Transcribing" in fake_ui.processing_steps
    assert not any(s.startswith("Formatting") for s in fake_ui.processing_steps)


@pytest.mark.asyncio
async def test_translation_triggers_formatting_step(tmp_path: Path) -> None:
    """With translate_to='french', steps include 'Formatting (french)'."""
    settings = Settings(openai_api_key="sk-test-key")
    fake_ui = _FakeUI()
    service, _, _ = _make_service(settings, tmp_path, ui=fake_ui)

    audio_data = np.random.randn(16000).astype(np.float32) * 0.5
    options = RecordingOptions(style=TranscriptionStyle.NEUTRAL, translate="french")

    with (
        patch("shh.services.recording.save_audio_to_wav") as mock_save,
        patch("shh.services.recording.transcribe_audio") as mock_transcribe,
        patch("shh.services.recording.format_transcription") as mock_format,
        patch("shh.services.recording.pyperclip.copy"),
    ):
        temp_file = tmp_path / "test.wav"
        mock_save.return_value = temp_file
        mock_transcribe.return_value = WhisperTranscription(
            text="Hello world", detected_lang="en"
        )
        mock_formatted = MagicMock()
        mock_formatted.text = "Bonjour monde"
        mock_format.return_value = mock_formatted
        temp_file.touch()

        await service.transcribe_and_format(audio_data, options)

    assert "Formatting (french)" in fake_ui.processing_steps


@pytest.mark.asyncio
async def test_history_append_on_success(tmp_path: Path) -> None:
    """After a successful run, store has one entry with the right fields."""
    settings = Settings(openai_api_key="sk-test-key")
    service, store, _ = _make_service(settings, tmp_path)

    audio_data = np.random.randn(16000).astype(np.float32) * 0.5
    options = RecordingOptions(style=TranscriptionStyle.NEUTRAL)

    with (
        patch("shh.services.recording.save_audio_to_wav") as mock_save,
        patch("shh.services.recording.transcribe_audio") as mock_transcribe,
        patch("shh.services.recording.pyperclip.copy"),
    ):
        temp_file = tmp_path / "test.wav"
        mock_save.return_value = temp_file
        mock_transcribe.return_value = WhisperTranscription(
            text="Persisted text", detected_lang="en"
        )
        temp_file.touch()

        await service.transcribe_and_format(audio_data, options)

    entries = store.read_all()
    assert len(entries) == 1
    assert entries[0].text == "Persisted text"
    assert entries[0].style == TranscriptionStyle.NEUTRAL
    assert entries[0].detected_lang == "en"


@pytest.mark.asyncio
async def test_skip_history_does_not_append(tmp_path: Path) -> None:
    """When skip_history=True, no entry is appended to the store."""
    settings = Settings(openai_api_key="sk-test-key")
    service, store, _ = _make_service(settings, tmp_path)

    audio_data = np.random.randn(16000).astype(np.float32) * 0.5
    options = RecordingOptions(style=TranscriptionStyle.NEUTRAL)

    with (
        patch("shh.services.recording.save_audio_to_wav") as mock_save,
        patch("shh.services.recording.transcribe_audio") as mock_transcribe,
        patch("shh.services.recording.pyperclip.copy"),
    ):
        temp_file = tmp_path / "test.wav"
        mock_save.return_value = temp_file
        mock_transcribe.return_value = WhisperTranscription(
            text="No history", detected_lang="en"
        )
        temp_file.touch()

        await service.transcribe_and_format(audio_data, options, skip_history=True)

    assert store.read_all() == []


@pytest.mark.asyncio
async def test_history_disabled_does_not_append(tmp_path: Path) -> None:
    """When settings.history_enabled=False, no entry is appended."""
    settings = Settings(openai_api_key="sk-test-key", history_enabled=False)
    service, store, _ = _make_service(settings, tmp_path)

    audio_data = np.random.randn(16000).astype(np.float32) * 0.5
    options = RecordingOptions(style=TranscriptionStyle.NEUTRAL)

    with (
        patch("shh.services.recording.save_audio_to_wav") as mock_save,
        patch("shh.services.recording.transcribe_audio") as mock_transcribe,
        patch("shh.services.recording.pyperclip.copy"),
    ):
        temp_file = tmp_path / "test.wav"
        mock_save.return_value = temp_file
        mock_transcribe.return_value = WhisperTranscription(
            text="Disabled history", detected_lang="en"
        )
        temp_file.touch()

        await service.transcribe_and_format(audio_data, options)

    assert store.read_all() == []


@pytest.mark.asyncio
async def test_history_append_failure_does_not_break_pipeline(tmp_path: Path) -> None:
    """If the history store raises an OSError, the transcription still succeeds."""
    ui = _FakeUI()

    class _FailingStore:
        def append(self, entry: object) -> None:
            raise OSError("disk full")

        def read_all(self) -> list[object]:
            return []

        def clear(self) -> None:
            pass

    settings = Settings(openai_api_key="sk-test", history_enabled=True)
    service = RecordingService(
        settings=settings,
        ui=ui,
        history_store=cast(HistoryStore, _FailingStore()),
    )

    audio = np.zeros(16000, dtype=np.float32)
    options = RecordingOptions(style=TranscriptionStyle.NEUTRAL)

    with (
        patch(
            "shh.services.recording.transcribe_audio",
            new_callable=AsyncMock,
            return_value=WhisperTranscription(text="hi", detected_lang="en"),
        ),
        patch("shh.services.recording.save_audio_to_wav") as mock_save,
        patch("shh.services.recording.pyperclip.copy"),
    ):
        temp_file = tmp_path / "test.wav"
        mock_save.return_value = temp_file
        temp_file.touch()

        result = await service.transcribe_and_format(audio, options)

    assert result.text == "hi"
