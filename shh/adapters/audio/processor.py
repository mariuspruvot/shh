import tempfile
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from scipy.io import wavfile

from shh.utils.exceptions import AudioProcessingError

SAMPLE_RATE = 16000  # Hz
CHANNELS = 1  # mono audio


def save_audio_to_wav(
    audio_data: NDArray[np.float32],
    sample_rate: int = SAMPLE_RATE,
) -> Path:
    """
    Save audio data to a temporary WAV file.
    This function is not responsible for cleaning up the temporary file.

    Args:
        audio_data (NDArray[np.float32]): The audio data to save.
        sample_rate (int): The sample rate of the audio data.
    Returns:
        Path: The path to the saved WAV file.
    Raises:
        AudioProcessingError: If there is an error saving the audio file.
    """
    try:
        # Convert float32 audio data to int16
        audio_int16: NDArray[np.int16] = (audio_data * 32767).astype(np.int16)

        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file_path = Path(temp_file.name)

        # Write the audio data to the WAV file
        wavfile.write(temp_file_path, sample_rate, audio_int16)

        return temp_file_path

    except Exception as e:
        raise AudioProcessingError(f"Failed to save audio to WAV file: {e}") from e
