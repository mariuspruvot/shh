"""Recording service - orchestrates the recording and transcription flow."""

import asyncio
import contextlib
import sys
import uuid
from collections.abc import Callable
from datetime import UTC, datetime

import numpy as np
import pyperclip  # type: ignore[import-untyped]
from numpy.typing import NDArray

from shh.adapters.audio.processor import SAMPLE_RATE, save_audio_to_wav
from shh.adapters.audio.recorder import AudioRecorder
from shh.adapters.history.store import HistoryStore
from shh.adapters.llm.formatter import format_transcription
from shh.adapters.whisper.client import transcribe_audio
from shh.cli.ui.base import UIOutput
from shh.config.settings import Settings
from shh.core.models import HistoryEntry, RecordingOptions, TranscriptionOutput
from shh.core.styles import TranscriptionStyle
from shh.utils.logger import logger


class RecordingService:
    """Service for recording audio and transcribing it."""

    def __init__(
        self,
        settings: Settings,
        ui: UIOutput,
        history_store: HistoryStore,
    ) -> None:
        """
        Initialize the recording service.

        Args:
            settings: Application settings
            ui: UI output implementation
            history_store: History persistence store
        """
        self.settings = settings
        self._ui = ui
        self._history_store = history_store

    async def record_audio(
        self,
        on_progress: Callable[[float, float], None] | None = None,
    ) -> NDArray[np.float32]:
        """
        Record audio from the microphone until Enter is pressed or max duration reached.

        Args:
            on_progress: Optional callback for progress updates (elapsed, max_duration)

        Returns:
            Audio data as NumPy array

        Raises:
            KeyboardInterrupt: If user cancels with Ctrl+C
        """
        async with AudioRecorder() as recorder:
            # Start waiting for Enter in background
            enter_task = asyncio.create_task(self._wait_for_enter())

            # Show live progress
            while not enter_task.done() and not recorder.is_max_duration_reached():
                if on_progress:
                    elapsed = recorder.elapsed_time()
                    max_duration = recorder._max_duration
                    on_progress(elapsed, max_duration)

                await asyncio.sleep(0.1)

            # Cancel Enter task if we hit max duration
            if not enter_task.done():
                enter_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await enter_task

            # Get recorded audio
            return recorder.get_audio()

    async def transcribe_and_format(
        self,
        audio_data: NDArray[np.float32],
        options: RecordingOptions,
        skip_history: bool = False,
    ) -> TranscriptionOutput:
        """
        Transcribe audio and optionally format/translate it.

        Args:
            audio_data: Raw audio data
            options: Recording options (style, translation, etc.)
            skip_history: If True, skip persisting to history even when enabled

        Returns:
            TranscriptionOutput with the processed text
        """
        self._ui.show_processing_step("Saving audio")
        wav_path = save_audio_to_wav(audio_data)

        try:
            self._ui.show_processing_step("Transcribing")
            whisper_result = await transcribe_audio(
                audio_file_path=wav_path,
                api_key=self.settings.openai_api_key or "",
                model=self.settings.whisper_model,
            )

            needs_formatting = (
                options.style != TranscriptionStyle.NEUTRAL
                or options.translate is not None
            )

            if needs_formatting:
                label = "Formatting"
                if options.translate:
                    label = f"Formatting ({options.translate})"
                self._ui.show_processing_step(label)
                formatted = await format_transcription(
                    whisper_result.text,
                    style=options.style,
                    api_key=self.settings.openai_api_key or "",
                    target_language=options.translate,
                )
                final_text = formatted.text
            else:
                final_text = whisper_result.text

            # Copy to clipboard
            clipboard_success = self._copy_to_clipboard(final_text)

            # Persist to history
            if self.settings.history_enabled and not skip_history:
                entry = HistoryEntry(
                    id=uuid.uuid4().hex[:8],
                    ts=datetime.now(tz=UTC),
                    text=final_text,
                    style=options.style,
                    translate_to=options.translate,
                    duration_s=len(audio_data) / SAMPLE_RATE,
                    detected_lang=whisper_result.detected_lang,
                )
                try:
                    self._history_store.append(entry)
                except OSError as exc:
                    logger.warning(f"Failed to persist history entry: {exc}")

            return TranscriptionOutput(
                text=final_text,
                style=options.style,
                translated_to=options.translate,
                copied_to_clipboard=clipboard_success,
            )

        finally:
            with contextlib.suppress(Exception):
                wav_path.unlink(missing_ok=True)

    async def record_and_transcribe(
        self,
        options: RecordingOptions,
        on_progress: Callable[[float, float], None] | None = None,
    ) -> TranscriptionOutput:
        """
        Full recording flow: record, transcribe, format, and copy to clipboard.

        Args:
            options: Recording options
            on_progress: Optional callback for recording progress

        Returns:
            TranscriptionOutput with the final result
        """
        audio_data = await self.record_audio(on_progress=on_progress)

        if len(audio_data) == 0:
            raise ValueError("No audio recorded")

        return await self.transcribe_and_format(audio_data, options)

    @staticmethod
    async def _wait_for_enter() -> None:
        """Wait for user to press Enter (runs in thread pool)."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, sys.stdin.readline)

    @staticmethod
    def _copy_to_clipboard(text: str) -> bool:
        """
        Copy text to clipboard.

        Args:
            text: Text to copy

        Returns:
            True if successful, False otherwise
        """
        try:
            pyperclip.copy(text)
            return True
        except Exception:
            return False
