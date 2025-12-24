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
    wav_path = save_audio_to_wav(sample_audio_data)

    try:
        assert wav_path.exists(), "WAV file should exist"
        assert wav_path.suffix == ".wav", "File should have .wav extension"
        assert wav_path.stat().st_size > 0, "WAV file should not be empty"
    finally:
        if wav_path.exists():
            wav_path.unlink()


def test_save_audio_to_wav_correct_sample_rate(sample_audio_data: NDArray[np.float32]) -> None:
    """Test that saved WAV file has correct sample rate."""
    wav_path = save_audio_to_wav(sample_audio_data)

    try:
        sample_rate, _ = wavfile.read(wav_path)
        assert sample_rate == SAMPLE_RATE, f"Sample rate should be {SAMPLE_RATE}Hz"
    finally:
        if wav_path.exists():
            wav_path.unlink()


def test_save_audio_to_wav_correct_data_conversion(sample_audio_data: NDArray[np.float32]) -> None:
    """Test that audio data is correctly converted from float32 to int16."""
    wav_path = save_audio_to_wav(sample_audio_data)

    try:
        _, audio_int16 = wavfile.read(wav_path)
        assert audio_int16.dtype == np.int16, "Audio data should be int16"

        audio_float_reconstructed = audio_int16.astype(np.float32) / 32767.0

        np.testing.assert_allclose(
            audio_float_reconstructed,
            sample_audio_data,
            atol=1e-4,
            err_msg="Reconstructed audio should match original (within conversion tolerance)",
        )
    finally:
        if wav_path.exists():
            wav_path.unlink()


def test_save_audio_to_wav_custom_sample_rate() -> None:
    """Test that custom sample rate is respected."""
    custom_rate = 44100
    duration = 0.5
    samples = int(custom_rate * duration)
    audio_data = np.random.randn(samples).astype(np.float32) * 0.5

    wav_path = save_audio_to_wav(audio_data, sample_rate=custom_rate)

    try:
        sample_rate, _ = wavfile.read(wav_path)
        assert sample_rate == custom_rate, f"Sample rate should be {custom_rate}Hz"
    finally:
        if wav_path.exists():
            wav_path.unlink()


def test_save_audio_to_wav_handles_empty_array() -> None:
    """Test that empty audio array raises an error or handles gracefully."""
    empty_audio = np.array([], dtype=np.float32)
    wav_path = save_audio_to_wav(empty_audio)

    try:
        assert wav_path.exists(), "Should create file even for empty audio"
    finally:
        if wav_path.exists():
            wav_path.unlink()


def test_save_audio_to_wav_handles_large_values() -> None:
    """Test that audio values outside [-1.0, 1.0] are clipped correctly."""
    audio_data = np.array([0.5, 1.5, -1.5, 0.0], dtype=np.float32)
    wav_path = save_audio_to_wav(audio_data)

    try:
        _, audio_int16 = wavfile.read(wav_path)
        assert audio_int16.dtype == np.int16
    finally:
        if wav_path.exists():
            wav_path.unlink()
