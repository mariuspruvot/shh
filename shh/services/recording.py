"""Recording service - orchestrates the recording and transcription flow."""

import asyncio
import contextlib
import sys
from collections.abc import Callable

import pyperclip  # type: ignore[import-untyped]
from numpy.typing import NDArray

from shh.adapters.audio.processor import save_audio_to_wav
from shh.adapters.audio.recorder import AudioRecorder
from shh.adapters.llm.formatter import format_transcription
from shh.adapters.whisper.client import transcribe_audio
from shh.config.settings import Settings
from shh.core.models import RecordingOptions, TranscriptionOutput
from shh.core.styles import TranscriptionStyle


class RecordingService:
    """Service for recording audio and transcribing it."""

    def __init__(self, settings: Settings) -> None:
        """
        Initialize the recording service.

        Args:
            settings: Application settings
        """
        self.settings = settings

    async def record_audio(
        self,
        on_progress: Callable[[float, float], None] | None = None,
    ) -> NDArray:
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
        audio_data: NDArray,
        options: RecordingOptions,
    ) -> TranscriptionOutput:
        """
        Transcribe audio and optionally format/translate it.

        Args:
            audio_data: Raw audio data
            options: Recording options (style, translation, etc.)

        Returns:
            TranscriptionOutput with the processed text
        """
        # Step 1: Save to WAV
        audio_file_path = save_audio_to_wav(audio_data)

        try:
            # Step 2: Transcribe
            transcription = await transcribe_audio(
                audio_file_path=audio_file_path,
                api_key=self.settings.openai_api_key,  # type: ignore
            )

            # Step 3: Format/Translate (if requested)
            if options.style != TranscriptionStyle.NEUTRAL or options.translate:
                formatted = await format_transcription(
                    transcription,
                    style=options.style,
                    api_key=self.settings.openai_api_key,  # type: ignore
                    target_language=options.translate,
                )
                final_text = formatted.text
            else:
                final_text = transcription

            # Step 4: Copy to clipboard
            clipboard_success = self._copy_to_clipboard(final_text)

            return TranscriptionOutput(
                text=final_text,
                style=options.style,
                translated_to=options.translate,
                copied_to_clipboard=clipboard_success,
            )

        finally:
            # Cleanup temp file
            audio_file_path.unlink(missing_ok=True)

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
