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
    help="Voice transcription CLI powered by OpenAI Whisper",
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
            help="Formatting: neutral (raw), casual, or business",
        ),
    ] = None,
    translate: Annotated[
        str | None,
        typer.Option(
            "--translate",
            "-t",
            help="Translate to language (e.g., English, French)",
        ),
    ] = None,
) -> None:
    """Record audio and transcribe. Press Enter to stop."""
    # If a subcommand was invoked, don't run the default
    if ctx.invoked_subcommand is not None:
        return

    # Run the async record command
    asyncio.run(record_command(style=style, translate=translate))


def main() -> None:
    """Main entry point for the CLI application."""
    app()
