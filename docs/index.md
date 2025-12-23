# shh

Voice transcription CLI powered by OpenAI Whisper.

Record audio, transcribe with Whisper, and optionally format or translate the output.

## Features

- **One-command recording** - Start with `shh`, stop with Enter
- **AI formatting** - Clean up transcriptions (casual, business, neutral)
- **Translation** - Transcribe and translate to any language
- **Clipboard integration** - Results automatically copied
- **Async architecture** - Non-blocking operations
- **Live progress** - Real-time recording indicators

## Quick Start

```bash
# Install
pipx install shh

# Configure API key
shh setup

# Record (press Enter to stop)
shh
```

Results appear in terminal and clipboard.

## Documentation

- [Installation](getting-started/installation.md) - Setup instructions
- [Quick Start](getting-started/quickstart.md) - Get started in 2 minutes
- [Commands](user-guide/commands.md) - All available commands
- [Configuration](user-guide/configuration.md) - Settings and defaults
- [API Reference](api-reference/core.md) - Code documentation

## Requirements

- Python 3.11+
- OpenAI API key
- Microphone
