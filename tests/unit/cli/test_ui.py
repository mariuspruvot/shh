"""Tests for UI layer."""

from io import StringIO
from unittest.mock import patch

from shh.cli.ui import QuietUI, RichUI
from shh.cli.ui.base import RecordingProgress, TranscriptionResult


def test_quiet_ui_minimal_output() -> None:
    """Test that QuietUI only shows minimal output."""
    ui = QuietUI()

    # Test that most methods produce no output
    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        ui.show_info("This should be silent")
        ui.show_recording_start()
        ui.show_recording_progress(RecordingProgress(elapsed=5.0, max_duration=300.0))
        ui.show_recording_stopped()
        ui.show_processing_step("Processing...")

        output = mock_stdout.getvalue()
        assert output == ""

    # Test that result shows text and "Done"
    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        result = TranscriptionResult(
            text="Hello world",
            copied_to_clipboard=True,
        )
        ui.show_result(result)

        output = mock_stdout.getvalue()
        assert "Hello world" in output
        assert "Done" in output


def test_quiet_ui_errors() -> None:
    """Test that QuietUI shows errors."""
    ui = QuietUI()

    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        ui.show_error("Something went wrong", "Details here")
        ui.show_warning("Warning message")

        output = mock_stdout.getvalue()
        assert "Error: Something went wrong" in output
        assert "Details here" in output
        assert "Warning: Warning message" in output


def test_rich_ui_shows_progress() -> None:
    """Test that RichUI displays progress."""
    ui = RichUI()

    # Should not raise any exceptions
    ui.show_recording_start()
    ui.show_recording_progress(RecordingProgress(elapsed=5.0, max_duration=300.0))
    ui.show_recording_stopped()
    ui.cleanup()


def test_rich_ui_result_formatting() -> None:
    """Test RichUI result display."""
    ui = RichUI()

    result = TranscriptionResult(
        text="Test transcription",
        copied_to_clipboard=True,
        style="casual",
        translated_to="English",
    )

    # Should not raise any exceptions
    ui.show_result(result)
    ui.cleanup()


def test_rich_ui_cleanup_multiple_calls() -> None:
    """Test that cleanup can be called multiple times safely."""
    ui = RichUI()

    ui.show_recording_progress(RecordingProgress(elapsed=1.0, max_duration=300.0))
    ui.cleanup()
    ui.cleanup()  # Should not raise
