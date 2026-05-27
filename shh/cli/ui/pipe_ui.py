"""Minimal UI for non-TTY stdout (pipes, redirects)."""

import sys

from shh.cli.ui.base import RecordingProgress, TranscriptionResult, UIOutput


class PipeUI(UIOutput):
    """Writes only the transcribed text to stdout. Errors go to stderr."""

    def show_error(self, message: str, details: str | None = None) -> None:
        print(f"Error: {message}", file=sys.stderr)
        if details:
            print(details, file=sys.stderr)

    def show_warning(self, message: str) -> None:
        print(f"Warning: {message}", file=sys.stderr)

    def show_info(self, message: str) -> None:
        pass

    def show_recording_start(self) -> None:
        pass

    def show_recording_progress(self, progress: RecordingProgress) -> None:
        pass

    def show_recording_stopped(self, reason: str | None = None) -> None:
        pass

    def show_processing_step(self, step: str) -> None:
        pass

    def show_result(self, result: TranscriptionResult) -> None:
        print(result.text)

    def cleanup(self) -> None:
        pass
