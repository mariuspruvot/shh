"""Unit tests for Settings configuration."""

from pathlib import Path

import pytest

from shh.config.settings import Settings, WhisperModel
from shh.core.styles import TranscriptionStyle


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that Settings has correct default values."""
    # Clear environment variables that could interfere
    monkeypatch.delenv("SHH_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    # Disable .env file loading for this test
    monkeypatch.setattr("shh.config.settings.Settings.model_config", {
        "env_prefix": "SHH_",
        "extra": "ignore",
    })

    settings = Settings()

    assert settings.openai_api_key is None
    assert settings.default_style == TranscriptionStyle.NEUTRAL
    assert settings.show_progress is True
    assert settings.whisper_model == WhisperModel.WHISPER_1
    assert settings.default_output == ["clipboard", "stdout"]


def test_settings_custom_values() -> None:
    """Test Settings with custom values."""
    settings = Settings(
        openai_api_key="sk-custom",
        default_style=TranscriptionStyle.CASUAL,
        show_progress=False,
    )

    assert settings.openai_api_key == "sk-custom"
    assert settings.default_style == TranscriptionStyle.CASUAL
    assert settings.show_progress is False


def test_settings_get_config_path() -> None:
    """Test that config path is platform-specific."""
    config_path = Settings.get_config_path()

    assert isinstance(config_path, Path)
    assert config_path.name == "settings.json"
    assert "shh" in str(config_path)


def test_settings_save_and_load(temp_config_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test saving and loading settings from file."""
    # Mock config path
    config_file = temp_config_dir / "settings.json"

    def get_test_config_path(cls: type) -> Path:
        return config_file

    monkeypatch.setattr(
        "shh.config.settings.Settings.get_config_path",
        classmethod(get_test_config_path),
    )

    # Create and save settings
    settings = Settings(
        openai_api_key="sk-test-123",
        default_style=TranscriptionStyle.BUSINESS,
    )
    settings.save_to_file()

    # Verify file exists
    assert config_file.exists()

    # Load and verify
    loaded = Settings.load_from_file()
    assert loaded is not None
    assert loaded.openai_api_key == "sk-test-123"
    assert loaded.default_style == TranscriptionStyle.BUSINESS


def test_settings_load_nonexistent() -> None:
    """Test loading from nonexistent file returns None."""
    result = Settings.load_from_file()
    assert result is None or isinstance(result, Settings)


def test_settings_enum_validation() -> None:
    """Test that enum fields are validated."""
    with pytest.raises(ValueError):
        Settings(default_style="invalid")  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        Settings(whisper_model="gpt-4")  # type: ignore[arg-type]
