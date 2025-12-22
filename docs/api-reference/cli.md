# CLI API Reference

The CLI layer provides user-facing commands and orchestrates the transcription workflow. Built with Typer and Rich for an elegant terminal experience.

## Main Application

::: shh.cli.app
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

The main CLI application entry point.

**Key features:**

- Default command for immediate recording
- Global flags (`--style`, `--translate`, `--duration`)
- Async/sync bridge with `asyncio.run()`
- Subcommand registration (`setup`, `config`)

**Example usage:**

```bash
# Run default command (record)
shh

# With options
shh --style casual --duration 60
```

**Programmatic usage:**

```python
from shh.cli.app import app
from typer.testing import CliRunner

runner = CliRunner()
result = runner.invoke(app, ["--style", "casual"])
```

---

## Commands

### Setup Command

::: shh.cli.commands.setup
    options:
      show_root_heading: true
      show_source: true
      heading_level: 4

Interactive setup wizard for configuring the OpenAI API key.

**Features:**

- Hidden input for security
- Validation (non-empty check)
- Masked display in confirmation
- Rich Panel output for visual feedback

**Usage:**

```bash
shh setup
```

**Code example:**

```python
from shh.cli.commands.setup import setup_command

# Called by Typer when user runs 'shh setup'
setup_command()
```

### Config Commands

::: shh.cli.commands.config
    options:
      show_root_heading: true
      show_source: true
      heading_level: 4

Configuration management commands:

- `show` - Display all settings
- `get` - Get a specific setting
- `set` - Update a setting
- `reset` - Reset to defaults

**Features:**

- Strict validation with helpful error messages
- Rich Table output for settings display
- Type conversion for enum values
- Confirmation prompt for destructive operations

**Usage:**

```bash
shh config show
shh config get default_style
shh config set default_style casual
shh config reset
```

**Code example:**

```python
from shh.cli.commands.config import config_show, config_set

# Display config
config_show()

# Update setting
config_set(key="default_style", value="casual")
```

### Record Command

::: shh.cli.commands.record
    options:
      show_root_heading: true
      show_source: true
      heading_level: 4

Main recording and transcription workflow.

**Features:**

- Async recording with Enter to stop
- Rich Live progress display
- Full pipeline orchestration
- Error handling with user-friendly messages

**Workflow:**

1. Check API key (fail early if missing)
2. Start recording (AudioRecorder)
3. Wait for Enter or max duration
4. Save audio to WAV (temporary file)
5. Transcribe with Whisper API
6. Format with LLM (if not neutral)
7. Copy to clipboard
8. Display result
9. Clean up temp files

**Usage:**

```bash
# Called from main app
shh --style casual --translate English
```

**Code example:**

```python
from shh.cli.commands.record import record_command
from shh.core.styles import TranscriptionStyle

# Run recording workflow
await record_command(
    style=TranscriptionStyle.CASUAL,
    translate="English",
    duration=60.0,
)
```

---

## Async Patterns

### Sync-to-Async Bridge

The CLI uses `asyncio.run()` to bridge Typer's synchronous interface with our async backend:

```python
@app.callback(invoke_without_command=True)
def default_command(ctx: typer.Context, ...) -> None:
    if ctx.invoked_subcommand is not None:
        return  # Don't run if subcommand used

    # Bridge to async
    asyncio.run(record_command(...))
```

### Non-blocking Enter Detection

Recording uses thread pools to detect Enter without blocking the event loop:

```python
async def wait_for_enter() -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, sys.stdin.readline)

# In record_command
enter_task = asyncio.create_task(wait_for_enter())
# ... continue recording until enter_task is done
```

### Resource Cleanup

Async context managers ensure cleanup even on errors:

```python
async with AudioRecorder() as recorder:
    # Recording happens here
    pass
# Cleanup happens automatically

try:
    result = await transcribe_audio(wav_path, api_key)
finally:
    wav_path.unlink(missing_ok=True)  # Always delete temp file
```

---

## Rich UI Components

### Live Progress Display

```python
from rich.live import Live
from rich.text import Text

with Live(auto_refresh=False) as live:
    while recording:
        progress = Text()
        progress.append("🔴 Recording... ", style="bold green")
        progress.append(f"{elapsed:.1f}s", style="cyan")
        live.update(progress)
        live.refresh()
```

### Configuration Table

```python
from rich.table import Table

table = Table(title="Configuration Settings")
table.add_column("Setting", style="cyan")
table.add_column("Value", style="green")

for key, value in settings.items():
    table.add_row(key, str(value))

console.print(table)
```

### Success Panels

```python
from rich.panel import Panel

panel = Panel(
    "[green]Configuration saved successfully![/green]",
    title="Setup Complete",
    border_style="green",
)
console.print(panel)
```

---

## Error Handling

The CLI layer provides user-friendly error messages:

```python
try:
    settings = Settings.load_from_file()
except Exception as e:
    console.print(f"[red]Error loading config: {e}[/red]")
    raise typer.Exit(code=1) from e
```

**Exit codes:**

- `0` - Success
- `1` - Error (invalid input, API failure, missing config)

---

## Design Principles

The CLI layer follows these principles:

- **User experience first**: Clear messages, beautiful output, intuitive commands
- **Fail fast**: Validate early (API key, config) before expensive operations
- **Graceful degradation**: Continue if clipboard fails, clean up on errors
- **Async-aware**: Proper event loop management, non-blocking I/O

## Related Modules

- [Core Reference](core.md) - Business logic and styles
- [Adapters Reference](adapters.md) - External integrations
