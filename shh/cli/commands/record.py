"""Recording command for the shh CLI."""

import logging
import sys

from shh.cli.ui import QuietUI, RichUI, UIOutput
from shh.cli.ui.base import RecordingProgress, TranscriptionResult
from shh.config.settings import Settings
from shh.core.models import RecordingOptions
from shh.core.styles import TranscriptionStyle
from shh.services.recording import RecordingService

# Suppress HTTP request logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)


async def record_command(
    style: TranscriptionStyle | None = None,
    translate: str | None = None,
    quiet: bool = False,
    verbose: bool = False,
) -> None:
    """
    Record audio, transcribe, and optionally format/translate.

    Args:
        style: Formatting style to apply (overrides config default)
        translate: Target language for translation
        quiet: Force minimal output (overrides config)
        verbose: Force rich UI (overrides config)
    """
    # Load settings
    settings = Settings.load_from_file()
    if not settings or not settings.openai_api_key:
        # For error message, default to Rich UI unless quiet explicitly set
        ui: UIOutput = QuietUI() if quiet else RichUI()
        ui.show_error(
            "No API key found.",
            "Run 'shh setup' to configure your OpenAI API key.",
        )
        sys.exit(1)

    # Use provided options or fall back to config defaults
    formatting_style = style if style is not None else settings.default_style
    target_language = translate if translate is not None else settings.default_translation_language

    # Determine quiet mode: CLI flags override config
    if quiet and verbose:
        # Both flags? Verbose wins (more info is better for errors)
        use_quiet_mode = False
    elif quiet:
        use_quiet_mode = True
    elif verbose:
        use_quiet_mode = False
    else:
        # No flags, use config
        use_quiet_mode = settings.quiet_mode

    # Choose UI based on quiet mode
    ui = QuietUI() if use_quiet_mode else RichUI()

    # Create service
    service = RecordingService(settings)
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

        # Processing phases
        ui.show_processing_step("Saving audio...")
        ui.show_processing_step("Transcribing with Whisper...")

        if formatting_style != TranscriptionStyle.NEUTRAL or target_language:
            if target_language:
                ui.show_processing_step(f"Formatting and translating to {target_language}...")
            else:
                ui.show_processing_step(f"Formatting ({formatting_style})...")

        # Transcribe and format
        result = await service.transcribe_and_format(audio_data, options)

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
