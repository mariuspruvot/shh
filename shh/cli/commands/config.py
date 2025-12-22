"""Config management commands for the shh CLI."""

import os
import subprocess

import typer
from rich.console import Console
from rich.table import Table

from shh.config.settings import Settings, WhisperModel
from shh.core.styles import TranscriptionStyle

console = Console()

# Create a sub-app for config commands
config_app = typer.Typer(help="Manage configuration settings")


# Valid settings keys for validation
VALID_KEYS = {
    "default_style": list(TranscriptionStyle),
    "show_progress": [True, False],
    "whisper_model": list(WhisperModel),
}


@config_app.command(name="show")
def config_show() -> None:
    """Display current configuration settings."""
    settings = Settings.load_from_file()

    if not settings:
        console.print("[yellow]No configuration found. Run 'shh setup' first.[/yellow]")
        raise typer.Exit(code=1)

    # Create a table for settings
    table = Table(title="Configuration Settings", show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    # Mask API key
    api_key_display = (
        f"sk-***{settings.openai_api_key[-4:]}"
        if settings.openai_api_key
        else "[red]Not configured[/red]"
    )

    table.add_row("openai_api_key", api_key_display)
    table.add_row("default_style", str(settings.default_style))
    table.add_row("show_progress", str(settings.show_progress))
    table.add_row("whisper_model", str(settings.whisper_model))
    table.add_row("default_output", ", ".join(settings.default_output))

    config_path = Settings.get_config_path()
    console.print()
    console.print(table)
    console.print(f"\n[dim]Config file: {config_path}[/dim]")


@config_app.command(name="get")
def config_get(key: str) -> None:
    """Get a single configuration value.

    Args:
        key: The setting key to retrieve (e.g., 'default_style')
    """
    settings = Settings.load_from_file()

    if not settings:
        console.print("[red]No configuration found. Run 'shh setup' first.[/red]")
        raise typer.Exit(code=1)

    # Get the value
    try:
        value = getattr(settings, key)

        # Mask API key
        if key == "openai_api_key" and value:
            value = f"sk-***{value[-4:]}"

        console.print(f"{key}: {value}")
    except AttributeError as e:
        console.print(f"[red]Error: Unknown setting '{key}'[/red]")
        console.print(f"[dim]Valid keys: {', '.join(VALID_KEYS.keys())}, openai_api_key[/dim]")
        raise typer.Exit(code=1) from e


@config_app.command(name="set")
def config_set(key: str, value: str) -> None:
    """Update a configuration setting.

    Args:
        key: The setting key to update
        value: The new value
    """
    settings = Settings.load_from_file() or Settings()

    # Validate key
    if key == "openai_api_key":
        console.print("[yellow]Use 'shh setup' to update API key.[/yellow]")
        raise typer.Exit(code=1)

    if key not in VALID_KEYS:
        console.print(f"[red]Error: Unknown setting '{key}'[/red]")
        console.print(f"[dim]Valid keys: {', '.join(VALID_KEYS.keys())}[/dim]")
        raise typer.Exit(code=1)

    # Validate and convert value
    typed_value: TranscriptionStyle | WhisperModel | bool | str

    if key == "default_style":
        try:
            typed_value = TranscriptionStyle(value)
        except ValueError as e:
            console.print(f"[red]Error: Invalid style '{value}'[/red]")
            valid_styles = [s.value for s in TranscriptionStyle]
            console.print(f"[dim]Valid styles: {', '.join(valid_styles)}[/dim]")
            raise typer.Exit(code=1) from e
    elif key == "show_progress":
        if value.lower() not in ("true", "false"):
            console.print("[red]Error: show_progress must be 'true' or 'false'[/red]")
            raise typer.Exit(code=1)
        typed_value = value.lower() == "true"
    elif key == "whisper_model":
        try:
            typed_value = WhisperModel(value)
        except ValueError as e:
            console.print(f"[red]Error: Invalid model '{value}'[/red]")
            valid_models = [m.value for m in WhisperModel]
            console.print(f"[dim]Valid models: {', '.join(valid_models)}[/dim]")
            raise typer.Exit(code=1) from e
    else:
        typed_value = value

    # Update setting
    setattr(settings, key, typed_value)
    settings.save_to_file()

    console.print(f"[green]✓ Updated {key} = {typed_value}[/green]")


@config_app.command(name="reset")
def config_reset() -> None:
    """Reset configuration to defaults (keeps API key)."""
    settings = Settings.load_from_file()

    if not settings:
        console.print("[yellow]No configuration found.[/yellow]")
        raise typer.Exit(code=1)

    # Confirm with user
    confirm = typer.confirm(
        "Reset all settings to defaults? (API key will be preserved)",
        default=False,
    )

    if not confirm:
        console.print("[yellow]Reset cancelled.[/yellow]")
        raise typer.Exit(code=0)

    # Save the API key
    api_key = settings.openai_api_key

    # Create new defaults
    settings = Settings()
    settings.openai_api_key = api_key

    # Save
    settings.save_to_file()

    console.print("[green]✓ Configuration reset to defaults[/green]")
    console.print(f"[dim]API key preserved: sk-***{api_key[-4:] if api_key else 'None'}[/dim]")


@config_app.command(name="edit")
def config_edit() -> None:
    """Open configuration file in $EDITOR."""
    config_path = Settings.get_config_path()

    if not config_path.exists():
        console.print("[yellow]No configuration file found. Run 'shh setup' first.[/yellow]")
        raise typer.Exit(code=1)

    # Get editor from environment
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")

    if not editor:
        console.print("[red]Error: No editor configured.[/red]")
        console.print("[dim]Set the EDITOR environment variable (e.g., export EDITOR=vim)[/dim]")
        raise typer.Exit(code=1)

    # Open in editor
    try:
        subprocess.run([editor, str(config_path)], check=True)  # noqa: S603
        console.print("[green]✓ Configuration file updated[/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error: Failed to open editor '{editor}'[/red]")
        raise typer.Exit(code=1) from e
    except FileNotFoundError as e:
        console.print(f"[red]Error: Editor '{editor}' not found[/red]")
        raise typer.Exit(code=1) from e
