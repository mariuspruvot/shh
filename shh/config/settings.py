"""Configuration management using pydantic-settings."""

import json
from enum import StrEnum
from pathlib import Path

from platformdirs import user_config_dir
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from shh.core.styles import TranscriptionStyle


class WhisperModel(StrEnum):
    """Available Whisper models."""

    WHISPER_1 = "whisper-1"


class Settings(BaseSettings):
    """
    Application settings with environment variable support & config file loading.
    Priority: CLI flags > environment > config file > defaults
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SHH_",
        extra="ignore",
    )

    openai_api_key: str | None = Field(default=None)
    default_style: TranscriptionStyle = Field(default=TranscriptionStyle.NEUTRAL)
    show_progress: bool = Field(default=True)
    whisper_model: WhisperModel = Field(default=WhisperModel.WHISPER_1)
    default_output: list[str] = Field(default_factory=lambda: ["clipboard", "stdout"])

    @classmethod
    def get_config_path(cls) -> Path:
        """Get platform-specific config file path.

        Returns path like:
        - macOS: ~/Library/Application Support/shh/settings.json
        - Linux: ~/.config/shh/settings.json
        - Windows: %APPDATA%/shh/settings.json
        """

        config_dir = Path(user_config_dir("shh"))
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "settings.json"

    @classmethod
    def load_from_file(cls) -> "Settings | None":
        """
        Load settings from config file if it exists.
        Returns Settings instance or None if file not found.
        """

        config_path = cls.get_config_path()
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                data = json.load(f)
            return cls.model_validate(data)
        return None

    def save_to_file(self) -> None:
        """
        Save current settings to config file.
        """

        config_path = self.get_config_path()
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=4)
