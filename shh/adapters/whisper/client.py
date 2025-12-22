from pathlib import Path

from openai import AsyncOpenAI

from shh.utils.exceptions import TranscriptionError
from shh.utils.logger import logger


async def transcribe_audio(
    audio_file_path: Path,
    api_key: str,
    model: str = "whisper-1",
) -> str:
    """
    Transcribe audio using OpenAI's Whisper API.
    """
    client = AsyncOpenAI(api_key=api_key)
    try:
        with audio_file_path.open("rb") as audio_file:
            audio_transcription = await client.audio.transcriptions.create(
                file=audio_file,
                model=model,
            )
            return audio_transcription.text

    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise TranscriptionError("Failed to transcribe audio.") from e
