"""Setup command for configuring the shh CLI."""

import typer
from rich.console import Console
from rich.panel import Panel

from shh.config.settings import Settings

console = Console()


def setup_command() -> None:
    """
    Interactive setup to configure OpenAI API key.

    Prompts the user for their API key and saves it to the config file.
    """
    console.print("\n[bold]shh Setup[/bold]", style="cyan")
    console.print("Let's configure your OpenAI API key.\n")

    # Prompt for API key (hidden input for security)
    api_key = typer.prompt(
        "Enter your OpenAI API key",
        hide_input=True,  # Don't show the key as they type
    )

    # Validate it's not empty
    if not api_key or not api_key.strip():
        console.print("[red]Error: API key cannot be empty[/red]")
        raise typer.Exit(code=1)

    # Load existing settings or create new ones
    settings = Settings.load_from_file() or Settings()

    # Update the API key
    settings.openai_api_key = api_key.strip()

    # Save to file
    settings.save_to_file()
    config_path = Settings.get_config_path()

    # Success message with details
    success_panel = Panel(
        f"""[green]Configuration saved successfully![/green]

[bold]Config file:[/bold] {config_path}

[bold]Settings:[/bold]
  • OpenAI API Key: sk-***{api_key[-4:]}
  • Default style: {settings.default_style}
  • Show progress: {settings.show_progress}
  • Whisper model: {settings.whisper_model}

[dim]You can now run 'shh' to start recording![/dim]""",
        title="Setup Complete",
        border_style="green",
    )

    console.print(success_panel)
