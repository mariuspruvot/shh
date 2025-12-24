# shh

<p align="center">
  <a href="https://pypi.org/project/shh-cli/"><img src="https://img.shields.io/pypi/v/shh-cli.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/shh-cli/"><img src="https://img.shields.io/pypi/pyversions/shh-cli.svg" alt="Python versions"></a>
  <a href="https://github.com/mariuspruvot/shh/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <a href="https://mariuspruvot.github.io/shh/"><img src="https://img.shields.io/badge/docs-mkdocs-blue" alt="Documentation"></a>
</p>

Voice transcription CLI using OpenAI Whisper.

---

## Features

- Record from microphone (press Enter to stop)
- Format with AI (casual, business, neutral)
- Translate to any language
- Auto-copy to clipboard
- Async architecture
- Live progress display

## Quick Start

```bash
# Install with pipx (recommended)
pipx install shh-cli

# Setup API key
shh setup

# Start recording (press Enter to stop)
shh
```

## Installation

### Using pipx (recommended)

```bash
pipx install shh-cli
```

### Using pip

```bash
pip install shh-cli
```

### Development Setup

```bash
git clone https://github.com/mariuspruvot/shh.git
cd shh
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

## Usage

### Basic Recording

```bash
# Quick record - press Enter to stop
shh

# Record for specific duration
shh --duration 60
```

### Formatting Styles

```bash
# Casual style (removes filler words, conversational)
shh --style casual

# Business style (professional, formal)
shh --style business

# Neutral style (no formatting, Whisper output as-is)
shh --style neutral
```

### Translation

```bash
# Transcribe and translate to English
shh --translate English

# Combine formatting and translation
shh --style business --translate French

# Set default translation language
shh config set default_translation_language English

# Now recordings auto-translate without --translate flag
shh
```

### Configuration

```bash
# Show current configuration
shh config show

# Set default style
shh config set default_style casual

# Set default translation language
shh config set default_translation_language English

# Get specific setting
shh config get default_style

# Reset to defaults (preserves API key)
shh config reset

# Edit config file directly in $EDITOR
shh config edit
```

## Configuration File

Configuration is stored in a platform-specific location:

- **macOS**: `~/Library/Application Support/shh/config.json`
- **Linux**: `~/.config/shh/config.json`
- **Windows**: `%APPDATA%\shh\config.json`

You can also use environment variables with the `SHH_` prefix:

```bash
export SHH_OPENAI_API_KEY="sk-..."
export SHH_DEFAULT_STYLE="casual"
export SHH_DEFAULT_TRANSLATION_LANGUAGE="English"
```

## Tech Stack

- Python 3.11+ (async/await)
- OpenAI Whisper (transcription)
- PydanticAI (formatting)
- Typer (CLI)
- Rich (terminal UI)
- sounddevice (audio recording)

## Development

```bash
# Run tests
uv run poe test

# Type checking
uv run poe type

# Linting
uv run poe lint

# Formatting
uv run poe format

# All checks (type + lint + test)
uv run poe check
```

## Architecture

Three layers: CLI → Core → Adapters

```
CLI        → Commands, user interaction
Core       → Business logic
Adapters   → APIs, audio, clipboard
```

See [docs/architecture.md](docs/architecture.md) for details.

## License

MIT

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
