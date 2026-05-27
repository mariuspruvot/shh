"""Tests for UI layer."""

import io
from unittest.mock import patch

from rich.console import Console

from shh.cli.ui import QuietUI, RichUI
from shh.cli.ui.base import RecordingProgress, TranscriptionResult


def _make_rich_ui_with_buffer() -> tuple[RichUI, Console, io.StringIO]:
    buf = io.StringIO()
    console = Console(file=buf, force_terminal=True, width=80)
    ui = RichUI(console=console)
    return ui, console, buf


def test_quiet_ui_minimal_output() -> None:
    """Test that QuietUI only shows minimal output."""
    ui = QuietUI()

    # Test that most methods produce no output
    with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
        ui.show_info("This should be silent")
        ui.show_processing_step("Processing...")

        output = mock_stdout.getvalue()
        assert output == ""

    # Test recording progress shows time
    with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
        ui.show_recording_progress(RecordingProgress(elapsed=5.2, max_duration=300.0))

        output = mock_stdout.getvalue()
        assert "Recording" in output
        assert "5.2s" in output
        assert "300s" in output

    # Test result shows nothing (text in clipboard)
    with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
        result = TranscriptionResult(
            text="Hello world",
            copied_to_clipboard=True,
        )
        ui.show_result(result)

        output = mock_stdout.getvalue()
        assert output == ""
        assert "Hello world" not in output


def test_quiet_ui_errors() -> None:
    """Test that QuietUI shows errors."""
    ui = QuietUI()

    with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
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


def test_rich_ui_cleanup_multiple_calls() -> None:
    """Test that cleanup can be called multiple times safely."""
    ui = RichUI()

    ui.show_recording_progress(RecordingProgress(elapsed=1.0, max_duration=300.0))
    ui.cleanup()
    ui.cleanup()  # Should not raise


def test_rich_ui_result_has_no_panel() -> None:
    """Test that RichUI result display uses plain text, not a Panel."""
    ui, _console, buf = _make_rich_ui_with_buffer()
    ui.show_result(TranscriptionResult(text="hello", copied_to_clipboard=True))
    rendered = buf.getvalue()
    assert "hello" in rendered
    # Panel borders include box-drawing characters; assert they are NOT present
    assert "─" not in rendered  # ─
    assert "│" not in rendered  # │
    assert "copied to clipboard" in rendered


def test_rich_ui_single_live_across_phases() -> None:
    """Test that a single Live instance persists across recording and processing phases."""
    ui = RichUI()
    ui.show_recording_progress(RecordingProgress(elapsed=1.0, max_duration=300.0))
    first_live = ui._live
    assert first_live is not None
    ui.show_recording_stopped()
    assert ui._live is first_live  # Same Live persists across the stop
    ui.show_processing_step("Transcribing")
    assert ui._live is first_live  # Still the same one
    ui.show_result(TranscriptionResult(text="hi", copied_to_clipboard=True))
    assert ui._live is None  # Result tears it down


def test_rich_ui_result_skips_clipboard_line_when_not_copied() -> None:
    ui, _console, buf = _make_rich_ui_with_buffer()
    ui.show_result(TranscriptionResult(text="hello", copied_to_clipboard=False))
    rendered = buf.getvalue()
    assert "hello" in rendered
    assert "copied to clipboard" not in rendered


def test_rich_ui_recording_stopped_with_reason_is_visible() -> None:
    ui, _console, buf = _make_rich_ui_with_buffer()
    ui.show_recording_progress(RecordingProgress(elapsed=1.0, max_duration=10.0))
    ui.show_recording_stopped(reason="max duration reached")
    rendered = buf.getvalue()
    assert "max duration reached" in rendered
    assert ui._live is None  # Live was torn down to surface the reason
