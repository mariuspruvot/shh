# Core API Reference

The core layer contains business logic and orchestration for the shh application. These modules have no dependencies on external frameworks or adapters.

## Transcription Styles

::: shh.core.styles
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

The `TranscriptionStyle` enum defines the available formatting styles:

- **NEUTRAL**: No formatting, raw Whisper output
- **CASUAL**: Conversational tone with filler words removed
- **BUSINESS**: Professional, formal formatting

**Example usage:**

```python
from shh.core.styles import TranscriptionStyle

# Use in configuration
style = TranscriptionStyle.CASUAL

# Convert from string
style = TranscriptionStyle("casual")

# All available values
styles = list(TranscriptionStyle)
```

## Core Orchestration

The core layer orchestrates the transcription workflow:

1. **Audio Recording** → Capture audio from microphone
2. **Transcription** → Send to Whisper API
3. **Formatting** → Apply AI formatting (if not neutral)
4. **Translation** → Translate to target language (if specified)
5. **Output** → Display and copy to clipboard

This orchestration happens in the CLI layer (see [CLI Reference](cli.md)), which calls adapter methods in sequence.

## Design Principles

The core layer follows these principles:

- **Framework-agnostic**: No Typer, Rich, or external framework imports
- **Type-safe**: Full type hints with mypy strict mode
- **Pure logic**: Business rules without I/O operations
- **Testable**: Easy to test without mocking external dependencies

## Related Modules

- [Adapters Reference](adapters.md) - External integrations (Whisper, LLM, audio)
- [CLI Reference](cli.md) - User-facing commands and orchestration
