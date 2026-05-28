"""OpenAI Whisper API client adapter."""

from pathlib import Path

from openai import AsyncOpenAI
from openai.types.audio import TranscriptionVerbose

from shh.core.models import WhisperTranscription
from shh.utils.exceptions import TranscriptionError
from shh.utils.logger import logger


async def transcribe_audio(
    audio_file_path: Path,
    api_key: str,
    model: str = "whisper-1",
) -> WhisperTranscription:
    """Transcribe audio with OpenAI Whisper, returning text + detected language."""
    client = AsyncOpenAI(api_key=api_key)
    try:
        with audio_file_path.open("rb") as audio_file:
            response: TranscriptionVerbose = await client.audio.transcriptions.create(
                file=audio_file,
                model=model,
                response_format="verbose_json",
            )
            return WhisperTranscription(text=response.text, detected_lang=response.language)
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise TranscriptionError("Failed to transcribe audio.") from e
