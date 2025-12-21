import asyncio
import time

import numpy as np
import sounddevice as sd  # type: ignore[import-untyped]
from numpy.typing import NDArray

from shh.utils.exceptions import AudioRecordingError
from shh.utils.logger import logger

SAMPLE_RATE = 16000  # Whisper recommended sample rate


class AudioRecorder:
    """
    Async Context Manager for recording audio from the microphone.
    Usage:
        async with AudioRecorder(sample_rate=16000, max_duration=60) as recorder:
            # Recording in progress
            await do_something()
    """

    MAX_RECORDING_DURATION = 300  # seconds

    def __init__(self, sample_rate: int = SAMPLE_RATE, max_duration: float | None = None) -> None:
        """
        Initialize the AudioRecorder.
        """
        self._sample_rate = sample_rate
        self._max_duration = max_duration or self.MAX_RECORDING_DURATION
        self._chunks: list[NDArray[np.float32]] = []
        self._stream: sd.InputStream | None = None
        self._start_time: float | None = None

    async def __aenter__(self) -> "AudioRecorder":
        """
        Start the audio recording stream.
        Returns:
            Self for use within the async context manager.
        """

        def callback(
            indata: NDArray[np.float32], frames: int, time_info: object, status: sd.CallbackFlags
        ) -> None:
            """
            Called by sounddevice for each audio block every 100ms.
            Args:
                indata: The recorded audio data.
                frames: Number of frames.
                time_info: Time information.
                status: Status flags.
            """
            if status:
                logger.warning(f"Audio recording status: {status}")

            self._chunks.append(indata.copy())

        try:
            self._stream = sd.InputStream(
                samplerate=self._sample_rate,
                channels=1,
                dtype=np.float32,
                callback=callback,
            )
            await asyncio.to_thread(self._stream.start)
            self._start_time = time.time()

            return self
        except Exception as e:
            raise AudioRecordingError(f"Failed to start audio recording: {e}") from e

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object,
    ) -> None:
        """
        Stop the audio recording stream and finalize the recording.
        """
        if self._stream:
            try:
                await asyncio.to_thread(self._stream.stop)
                await asyncio.to_thread(self._stream.close)
            except Exception as e:
                logger.error(f"Error stopping audio stream: {e}")

    def get_audio(self) -> NDArray[np.float32]:
        """
        Retrieve the recorded audio data as a single NumPy array.
        Returns:
            A NumPy array containing the recorded audio data.
        """
        if not self._chunks:
            return np.array([], dtype=np.float32)

        audio = np.concatenate(self._chunks, axis=0)
        return audio.flatten()

    def elapsed_time(self) -> float:
        """
        Get the elapsed recording time in seconds.
        Returns:
            Elapsed time in seconds.
        """
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time

    def is_max_duration_reached(self) -> bool:
        """
        return True if the maximum recording duration has been exceeded.
        """
        return self.elapsed_time() >= self._max_duration
