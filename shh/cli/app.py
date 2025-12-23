"""Main CLI application entry point."""

import asyncio
from typing import Annotated

import typer

from shh.cli.commands.config import config_app
from shh.cli.commands.record import record_command
from shh.cli.commands.setup import setup_command
from shh.core.styles import TranscriptionStyle

app = typer.Typer(
    name="shh",
    help="""Voice transcription CLI powered by OpenAI Whisper.

Record audio, transcribe with Whisper, and optionally format or translate the output.

\b
Examples:
  shh                              Record and transcribe (press Enter to stop)
  shh --style business             Transcribe with professional formatting
  shh --translate English          Transcribe and translate to English
  shh setup                        Configure your OpenAI API key
  shh config show                  View current configuration
  shh config set default_style casual  Set default formatting style
""",
    no_args_is_help=False,  # Allow running 'shh' without args (default command)
    rich_markup_mode="markdown",
)

# Add config subcommand group
app.add_typer(config_app, name="config")


@app.command(name="setup")
def setup() -> None:
    """Configure OpenAI API key and settings."""
    setup_command()


@app.callback(invoke_without_command=True)
def default_command(
    ctx: typer.Context,
    style: Annotated[
        TranscriptionStyle | None,
        typer.Option(
            "--style",
            "-s",
            help=(
                "Formatting style: neutral (raw), casual (conversational), "
                "or business (professional)"
            ),
        ),
    ] = None,
    translate: Annotated[
        str | None,
        typer.Option(
            "--translate",
            "-t",
            help="Translate to target language (e.g., 'English', 'French', 'Spanish')",
        ),
    ] = None,
) -> None:
    """
    Record audio from microphone and transcribe it.

    \b
    Press Enter to stop recording (or auto-stop after 5 minutes).
    Results are automatically copied to clipboard.

    \b
    Examples:
      shh                           Quick recording with defaults
      shh -s casual                 Casual formatting (removes filler words)
      shh -s business               Professional formatting
      shh -t English                Transcribe and translate to English
      shh -s business -t French     Business format + translate to French
    """
    # If a subcommand was invoked, don't run the default
    if ctx.invoked_subcommand is not None:
        return

    # Run the async record command
    asyncio.run(record_command(style=style, translate=translate))


def main() -> None:
    """Main entry point for the CLI application."""
    app()
