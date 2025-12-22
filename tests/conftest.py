"""Pytest configuration and shared fixtures."""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest

from shh.config.settings import Settings


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Provide a temporary config directory for testing."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    yield config_dir


@pytest.fixture
def mock_settings(temp_config_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Settings:
    """Provide mock settings with test API key."""
    # Mock the config path to use temp directory
    def get_test_config_path(cls: type) -> Path:
        return temp_config_dir / "settings.json"

    monkeypatch.setattr(
        "shh.config.settings.Settings.get_config_path",
        classmethod(get_test_config_path),
    )

    settings = Settings(openai_api_key="sk-test-key-1234567890")
    settings.save_to_file()
    return settings


@pytest.fixture
def sample_audio_1s() -> np.ndarray:
    """Generate 1 second of sample audio (440Hz sine wave)."""
    sample_rate = 16000
    duration = 1.0
    frequency = 440.0  # A note

    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
    return np.sin(2 * np.pi * frequency * t).astype(np.float32)


@pytest.fixture
def mock_audio_recorder() -> MagicMock:
    """Provide a mock AudioRecorder for testing."""
    mock = MagicMock()
    mock.__aenter__.return_value = mock
    mock.__aexit__.return_value = None
    mock.elapsed_time.return_value = 3.5
    mock.is_max_duration_reached.return_value = False
    mock.get_audio.return_value = np.zeros(16000, dtype=np.float32)
    return mock


@pytest.fixture
def mock_openai_response() -> dict:
    """Provide a mock OpenAI Whisper API response."""
    return {"text": "This is a test transcription."}


@pytest.fixture
def mock_pydantic_ai_response() -> str:
    """Provide a mock PydanticAI formatting response."""
    return "This is a formatted transcription."
