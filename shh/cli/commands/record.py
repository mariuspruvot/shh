"""Recording command for the shh CLI."""

import asyncio
import contextlib
import logging
import sys

import pyperclip  # type: ignore[import-untyped]
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from shh.adapters.audio.processor import save_audio_to_wav
from shh.adapters.audio.recorder import AudioRecorder
from shh.adapters.llm.formatter import format_transcription
from shh.adapters.whisper.client import transcribe_audio
from shh.config.settings import Settings
from shh.core.styles import TranscriptionStyle

# Suppress HTTP request logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

console = Console()


async def wait_for_enter() -> None:
    """Wait for user to press Enter (runs in thread pool)."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, sys.stdin.readline)


async def record_command(
    style: TranscriptionStyle | None = None,
    translate: str | None = None,
) -> None:
    """
    Record audio, transcribe, and optionally format/translate.

    Args:
        style: Formatting style to apply (overrides config default)
        translate: Target language for translation
    """
    # Load settings
    settings = Settings.load_from_file()
    if not settings or not settings.openai_api_key:
        console.print("[red]Error: No API key found.[/red]")
        console.print("[dim]Run 'shh setup' to configure your OpenAI API key.[/dim]")
        sys.exit(1)

    # Use provided options or fall back to config defaults
    formatting_style = style if style is not None else settings.default_style
    target_language = translate if translate is not None else settings.default_translation_language

    # Step 1: Recording
    console.print()

    try:
        async with AudioRecorder() as recorder:
            # Start waiting for Enter in background
            enter_task = asyncio.create_task(wait_for_enter())

            # Show live progress
            with Live(auto_refresh=False, console=console) as live:
                while not enter_task.done() and not recorder.is_max_duration_reached():
                    elapsed = recorder.elapsed_time()
                    max_duration = recorder._max_duration

                    # Create progress text
                    progress = Text()
                    progress.append("Recording... ", style="bold green")
                    progress.append(f"{elapsed:.1f}s ", style="cyan")
                    progress.append(f"/ {max_duration:.0f}s ", style="dim")
                    progress.append("[Press Enter to stop]", style="dim")

                    live.update(progress)
                    live.refresh()
                    await asyncio.sleep(0.1)

                # Check if max duration reached
                if recorder.is_max_duration_reached():
                    console.print(
                        "\n[yellow]Maximum recording duration reached (5 minutes)[/yellow]"
                    )

            # Cancel Enter task if we hit max duration
            if not enter_task.done():
                enter_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await enter_task

            # Get recorded audio
            audio_data = recorder.get_audio()

    except KeyboardInterrupt:
        console.print("\n[yellow]Recording cancelled.[/yellow]")
        sys.exit(130)  # Standard exit code for Ctrl+C

    # Check if we got any audio
    if len(audio_data) == 0:
        console.print("[yellow]No audio recorded.[/yellow]")
        sys.exit(1)

    # Step 2: Save to WAV
    console.print("\n[cyan]Saving audio...[/cyan]")
    audio_file_path = save_audio_to_wav(audio_data)

    try:
        # Step 3: Transcribe
        console.print("[cyan]Transcribing with Whisper...[/cyan]")
        transcription = await transcribe_audio(
            audio_file_path=audio_file_path,
            api_key=settings.openai_api_key,
        )

        # Step 4: Format/Translate (if requested)
        if formatting_style != TranscriptionStyle.NEUTRAL or target_language:
            if target_language:
                console.print(f"[cyan]Formatting and translating to {target_language}...[/cyan]")
            else:
                console.print(f"[cyan]Formatting ({formatting_style})...[/cyan]")

            formatted = await format_transcription(
                transcription,
                style=formatting_style,
                api_key=settings.openai_api_key,
                target_language=target_language,
            )
            final_text = formatted.text
        else:
            final_text = transcription

        # Step 5: Copy to clipboard
        clipboard_success = True
        try:
            pyperclip.copy(final_text)
        except Exception as e:
            clipboard_success = False
            console.print(f"[yellow]Warning: Could not copy to clipboard: {e}[/yellow]")

        # Step 6: Display result
        console.print()
        result_panel = Panel(
            final_text,
            title="Transcription" + (" (copied to clipboard)" if clipboard_success else ""),
            border_style="green" if clipboard_success else "yellow",
        )
        console.print(result_panel)
        console.print()

    finally:
        # Cleanup temp file
        audio_file_path.unlink(missing_ok=True)
