"""Tests for PipeUI - the non-TTY minimal output."""

import pytest

from shh.cli.ui.base import RecordingProgress, TranscriptionResult
from shh.cli.ui.pipe_ui import PipeUI


def test_show_result_prints_text_only(capsys: pytest.CaptureFixture[str]) -> None:
    ui = PipeUI()
    ui.show_result(TranscriptionResult(text="Hello world", copied_to_clipboard=True))
    captured = capsys.readouterr()
    assert captured.out == "Hello world\n"
    assert captured.err == ""


def test_show_error_writes_to_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    ui = PipeUI()
    ui.show_error("oops", details="api key missing")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "oops" in captured.err


def test_show_warning_writes_to_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    ui = PipeUI()
    ui.show_warning("low disk space")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Warning: low disk space" in captured.err


def test_progress_and_steps_are_noop(capsys: pytest.CaptureFixture[str]) -> None:
    ui = PipeUI()
    ui.show_recording_start()
    ui.show_recording_progress(RecordingProgress(elapsed=1.0, max_duration=10.0))
    ui.show_processing_step("Transcribing")
    ui.show_recording_stopped()
    ui.cleanup()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
