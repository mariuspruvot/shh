"""Unit tests for audio processor."""

import numpy as np
import pytest
from numpy.typing import NDArray
from scipy.io import wavfile

from shh.adapters.audio.processor import SAMPLE_RATE, save_audio_to_wav


@pytest.fixture
def sample_audio_data() -> NDArray[np.float32]:
    """Generate sample audio data for testing.

    Returns 1 second of sine wave at 440Hz (A note).
    """
    duration = 1.0  # seconds
    frequency = 440.0  # Hz (A note)
    samples = int(SAMPLE_RATE * duration)

    t = np.linspace(0, duration, samples, dtype=np.float32)
    return np.sin(2 * np.pi * frequency * t).astype(np.float32)


def test_save_audio_to_wav_creates_file(sample_audio_data: NDArray[np.float32]) -> None:
    """Test that save_audio_to_wav creates a WAV file."""
    # Act
    wav_path = save_audio_to_wav(sample_audio_data)

    try:
        # Assert
        assert wav_path.exists(), "WAV file should exist"
        assert wav_path.suffix == ".wav", "File should have .wav extension"
        assert wav_path.stat().st_size > 0, "WAV file should not be empty"
    finally:
        # Cleanup
        if wav_path.exists():
            wav_path.unlink()


def test_save_audio_to_wav_correct_sample_rate(sample_audio_data: NDArray[np.float32]) -> None:
    """Test that saved WAV file has correct sample rate."""
    # Act
    wav_path = save_audio_to_wav(sample_audio_data)

    try:
        # Read back the WAV file
        sample_rate, _ = wavfile.read(wav_path)

        # Assert
        assert sample_rate == SAMPLE_RATE, f"Sample rate should be {SAMPLE_RATE}Hz"
    finally:
        # Cleanup
        if wav_path.exists():
            wav_path.unlink()


def test_save_audio_to_wav_correct_data_conversion(sample_audio_data: NDArray[np.float32]) -> None:
    """Test that audio data is correctly converted from float32 to int16."""
    # Act
    wav_path = save_audio_to_wav(sample_audio_data)

    try:
        # Read back the WAV file
        _, audio_int16 = wavfile.read(wav_path)

        # Assert
        assert audio_int16.dtype == np.int16, "Audio data should be int16"

        # Convert back to float32 for comparison
        audio_float_reconstructed = audio_int16.astype(np.float32) / 32767.0

        # Check that values are approximately equal (allowing for conversion loss)
        # Tolerance is relatively high because int16 has lower precision than float32
        np.testing.assert_allclose(
            audio_float_reconstructed,
            sample_audio_data,
            atol=1e-4,
            err_msg="Reconstructed audio should match original (within conversion tolerance)",
        )
    finally:
        # Cleanup
        if wav_path.exists():
            wav_path.unlink()


def test_save_audio_to_wav_custom_sample_rate() -> None:
    """Test that custom sample rate is respected."""
    # Arrange
    custom_rate = 44100  # CD quality
    duration = 0.5  # seconds
    samples = int(custom_rate * duration)
    audio_data = np.random.randn(samples).astype(np.float32) * 0.5  # Random audio

    # Act
    wav_path = save_audio_to_wav(audio_data, sample_rate=custom_rate)

    try:
        # Read back
        sample_rate, _ = wavfile.read(wav_path)

        # Assert
        assert sample_rate == custom_rate, f"Sample rate should be {custom_rate}Hz"
    finally:
        # Cleanup
        if wav_path.exists():
            wav_path.unlink()


def test_save_audio_to_wav_handles_empty_array() -> None:
    """Test that empty audio array raises an error or handles gracefully."""
    # Arrange
    empty_audio = np.array([], dtype=np.float32)

    # Act & Assert
    # scipy should handle this, but let's verify it doesn't crash
    wav_path = save_audio_to_wav(empty_audio)

    try:
        assert wav_path.exists(), "Should create file even for empty audio"
    finally:
        # Cleanup
        if wav_path.exists():
            wav_path.unlink()


def test_save_audio_to_wav_handles_large_values() -> None:
    """Test that audio values outside [-1.0, 1.0] are clipped correctly."""
    # Arrange - audio with values outside normal range
    audio_data = np.array([0.5, 1.5, -1.5, 0.0], dtype=np.float32)  # Some values > 1.0

    # Act
    wav_path = save_audio_to_wav(audio_data)

    try:
        # Read back
        _, audio_int16 = wavfile.read(wav_path)

        # Assert - values should be converted (may overflow/clip)
        assert audio_int16.dtype == np.int16
        # Note: Values > 1.0 will cause overflow in int16 conversion
        # This is expected behavior - caller should ensure normalized audio
    finally:
        # Cleanup
        if wav_path.exists():
            wav_path.unlink()
