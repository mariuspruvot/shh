"""Unit tests for CLI commands."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from shh.cli.app import app
from shh.cli.commands import record as record_module
from shh.cli.ui.pipe_ui import PipeUI
from shh.cli.ui.quiet_ui import QuietUI
from shh.cli.ui.rich_ui import RichUI
from shh.config.settings import Settings
from shh.core.styles import TranscriptionStyle

runner = CliRunner()


def test_cli_help() -> None:
    """Test that CLI help works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Voice transcription CLI" in result.stdout
    assert "setup" in result.stdout
    assert "config" in result.stdout


def test_setup_command(temp_config_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test setup command saves API key."""
    config_file = temp_config_dir / "settings.json"

    def get_test_config_path(cls: type) -> Path:
        return config_file

    monkeypatch.setattr(
        "shh.config.settings.Settings.get_config_path",
        classmethod(get_test_config_path),
    )

    result = runner.invoke(app, ["setup"], input="sk-test-key-12345678\n")

    assert result.exit_code == 0
    assert "Setup Complete" in result.stdout
    assert "sk-***5678" in result.stdout

    assert config_file.exists()
    settings = Settings.load_from_file()
    assert settings is not None
    assert settings.openai_api_key == "sk-test-key-12345678"


def test_config_show(mock_settings: Settings) -> None:
    """Test config show command."""
    result = runner.invoke(app, ["config", "show"])

    assert result.exit_code == 0
    assert "Configuration Settings" in result.stdout
    assert "openai_api_key" in result.stdout
    assert "sk-***" in result.stdout
    assert "neutral" in result.stdout


def test_config_get(mock_settings: Settings) -> None:
    """Test config get command."""
    result = runner.invoke(app, ["config", "get", "default_style"])

    assert result.exit_code == 0
    assert "default_style: neutral" in result.stdout


def test_config_get_invalid_key(mock_settings: Settings) -> None:
    """Test config get with invalid key."""
    result = runner.invoke(app, ["config", "get", "invalid_key"])

    assert result.exit_code == 1
    assert "Error: Unknown setting" in result.stdout


def test_config_set_valid(mock_settings: Settings) -> None:
    """Test config set command with valid value."""
    result = runner.invoke(app, ["config", "set", "default_style", "casual"])

    assert result.exit_code == 0
    assert "Updated default_style = casual" in result.stdout

    settings = Settings.load_from_file()
    assert settings is not None
    assert settings.default_style == TranscriptionStyle.CASUAL


def test_config_set_invalid_value(mock_settings: Settings) -> None:
    """Test config set with invalid value."""
    result = runner.invoke(app, ["config", "set", "default_style", "invalid"])

    assert result.exit_code == 1
    assert "Error: Invalid style" in result.stdout
    assert "Valid styles:" in result.stdout


def test_config_set_invalid_key(mock_settings: Settings) -> None:
    """Test config set with invalid key."""
    result = runner.invoke(app, ["config", "set", "invalid_key", "value"])

    assert result.exit_code == 1
    assert "Error: Unknown setting" in result.stdout


def test_config_reset(mock_settings: Settings) -> None:
    """Test config reset command."""
    # First change a setting
    runner.invoke(app, ["config", "set", "default_style", "casual"])

    # Reset with confirmation
    result = runner.invoke(app, ["config", "reset"], input="y\n")

    assert result.exit_code == 0
    assert "Configuration reset to defaults" in result.stdout

    # Verify reset worked
    settings = Settings.load_from_file()
    assert settings is not None
    assert settings.default_style == TranscriptionStyle.NEUTRAL


def test_config_reset_cancelled(mock_settings: Settings) -> None:
    """Test config reset when user cancels."""
    result = runner.invoke(app, ["config", "reset"], input="n\n")

    assert result.exit_code == 0
    assert "Reset cancelled" in result.stdout


@patch("shh.cli.commands.record.record_command")
def test_record_command_no_api_key(
    mock_record: MagicMock,
    temp_config_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that record command fails without API key."""
    config_file = temp_config_dir / "settings.json"

    def get_test_config_path(cls: type) -> Path:
        return config_file

    monkeypatch.setattr(
        "shh.config.settings.Settings.get_config_path",
        classmethod(get_test_config_path),
    )

    # Don't create config file (no API key)
    result = runner.invoke(app, [])

    # Should fail with error about missing API key
    # Error may go to stderr (PipeUI when not a TTY) or stdout (RichUI)
    assert result.exit_code == 1
    combined = result.stdout + result.stderr
    assert "No API key found" in combined or mock_record.called


def test_record_command_uses_pipe_ui_when_not_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that _select_ui returns PipeUI when stdout is not a TTY."""
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    ui = record_module._select_ui(quiet=False, verbose=False, quiet_default=False)
    assert isinstance(ui, PipeUI)


def test_record_command_uses_quiet_ui_when_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that _select_ui returns QuietUI when --quiet is passed."""
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    ui = record_module._select_ui(quiet=True, verbose=False, quiet_default=False)
    assert isinstance(ui, QuietUI)


def test_record_command_uses_rich_ui_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that _select_ui returns RichUI when no special flags are set."""
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    ui = record_module._select_ui(quiet=False, verbose=False, quiet_default=False)
    assert isinstance(ui, RichUI)


def test_record_command_verbose_overrides_quiet_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that --verbose overrides quiet_default setting."""
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    ui = record_module._select_ui(quiet=False, verbose=True, quiet_default=True)
    assert isinstance(ui, RichUI)


def test_record_command_uses_quiet_ui_when_config_default_and_no_verbose(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When Settings.quiet_mode=True and user doesn't pass --verbose, QuietUI is selected."""
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    ui = record_module._select_ui(quiet=False, verbose=False, quiet_default=True)
    assert isinstance(ui, QuietUI)
