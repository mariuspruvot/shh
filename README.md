<div align="center">
  <img src="assets/shh-logo.png" alt="shh logo" width="200"/>

  # shh

  **Voice transcription CLI powered by OpenAI Whisper**

  Record, transcribe, format. All from your terminal.

  [![CI](https://github.com/mpruvot/shh/actions/workflows/ci.yml/badge.svg)](https://github.com/mpruvot/shh/actions/workflows/ci.yml)
  [![codecov](https://codecov.io/gh/mpruvot/shh/branch/main/graph/badge.svg)](https://codecov.io/gh/mpruvot/shh)
  [![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/downloads/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
  [![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

</div>

---

## Features

- 🎤 **Record** from microphone with a single command
- 🎯 **Press Enter to stop** - simple, intuitive control
- ✨ **AI Formatting** - casual, business, or neutral styles
- 🌍 **Translation** - transcribe and translate to any language
- 📋 **Auto-copy** - results instantly in your clipboard
- ⚡ **Async** - non-blocking architecture for responsive UX
- 🎨 **Rich UI** - beautiful terminal output with live progress

## Quick Start

```bash
# Install with uv
uv pip install -e .

# Setup API key
shh setup

# Start recording (press Enter to stop)
shh
```

## Installation

### Using uv

```bash
uv pip install -e .
```

### Using pip

```bash
pip install -e .
```

### Development

```bash
git clone https://github.com/mpruvot/shh.git
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
```

### Configuration

```bash
# Show current configuration
shh config show

# Set default style
shh config set default_style casual

# Get specific setting
shh config get default_style

# Reset to defaults
shh config reset
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
```

## Tech Stack

- **Python 3.11+** - Modern async/await patterns
- **OpenAI Whisper** - State-of-the-art speech recognition
- **PydanticAI** - Type-safe AI agent framework
- **Typer** - Elegant CLI framework
- **Rich** - Beautiful terminal formatting
- **sounddevice** - Cross-platform audio recording

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

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development guidelines.

## Architecture

**shh** follows a pragmatic layered architecture:

```
CLI Layer (Typer)     → User interaction, commands
    ↓
Core Layer            → Business logic, orchestration
    ↓
Adapters Layer        → External APIs, hardware, clipboard
```

**Dependency Rule**: CLI → Core → Adapters (unidirectional flow)

See the [Architecture Documentation](docs/architecture.md) for detailed design decisions.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
