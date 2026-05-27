"""Recording command for the shh CLI."""

import logging
import sys

from shh.adapters.history.store import HistoryStore
from shh.cli.ui import PipeUI, QuietUI, RichUI, UIOutput
from shh.cli.ui.base import RecordingProgress, TranscriptionResult
from shh.config.settings import Settings
from shh.core.models import RecordingOptions
from shh.core.styles import TranscriptionStyle
from shh.services.recording import RecordingService

# Suppress HTTP request logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)


def _select_ui(*, quiet: bool, verbose: bool, quiet_default: bool) -> UIOutput:
    """Pick the UI based on TTY + flags.

    - Not a TTY -> PipeUI (minimal stdout, errors to stderr).
    - --quiet or config quiet_mode (without --verbose override) -> QuietUI.
    - Default -> RichUI.
    """
    if not sys.stdout.isatty():
        return PipeUI()
    if quiet or (quiet_default and not verbose):
        return QuietUI()
    return RichUI()


async def record_command(
    style: TranscriptionStyle | None = None,
    translate: str | None = None,
    quiet: bool = False,
    verbose: bool = False,
    no_history: bool = False,
) -> None:
    """
    Record audio, transcribe, and optionally format/translate.

    Args:
        style: Formatting style to apply (overrides config default)
        translate: Target language for translation
        quiet: Force minimal output (overrides config)
        verbose: Force rich UI (overrides config)
        no_history: Skip persisting this transcription to history
    """
    # Load settings
    settings = Settings.load_from_file()
    if not settings or not settings.openai_api_key:
        # For error message, use TTY-aware selection with settings default
        quiet_default = settings.quiet_mode if settings else False
        ui = _select_ui(quiet=quiet, verbose=verbose, quiet_default=quiet_default)
        ui.show_error(
            "No API key found.",
            "Run 'shh setup' to configure your OpenAI API key.",
        )
        sys.exit(1)

    # Use provided options or fall back to config defaults
    formatting_style = style if style is not None else settings.default_style
    target_language = translate if translate is not None else settings.default_translation_language
    ui = _select_ui(quiet=quiet, verbose=verbose, quiet_default=settings.quiet_mode)

    # Create service
    store = HistoryStore(
        path=Settings.get_history_path(),
        retention=settings.history_retention,
    )
    service = RecordingService(settings=settings, ui=ui, history_store=store)
    options = RecordingOptions(
        style=formatting_style,
        translate=target_language,
        show_progress=settings.show_progress,
    )

    try:
        # Recording phase
        ui.show_recording_start()

        def progress_callback(elapsed: float, max_duration: float) -> None:
            ui.show_recording_progress(RecordingProgress(elapsed, max_duration))

        # Always pass progress callback - UI decides how to display it
        audio_data = await service.record_audio(on_progress=progress_callback)

        ui.show_recording_stopped()

        # Check if we got any audio
        if len(audio_data) == 0:
            ui.show_warning("No audio recorded.")
            sys.exit(1)

        # Transcribe and format
        result = await service.transcribe_and_format(audio_data, options, skip_history=no_history)

        # Display result
        ui.show_result(
            TranscriptionResult(
                text=result.text,
                copied_to_clipboard=result.copied_to_clipboard,
                style=result.style.value,
                translated_to=result.translated_to,
            )
        )

    except KeyboardInterrupt:
        ui.show_warning("Recording cancelled.")
        sys.exit(130)  # Standard exit code for Ctrl+C
    except ValueError as e:
        ui.show_error(str(e))
        sys.exit(1)
    finally:
        ui.cleanup()
