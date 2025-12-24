# Design Decisions

## Architecture

**Layered (CLI → Core → Adapters)** - Enables testing without mocking external APIs, framework independence. Orchestration stays in CLI layer (pragmatic for small app).

## Technology Choices

- **Typer** - Type-hint based CLI, automatic help generation, clean subcommand syntax
- **Rich** - Beautiful terminal UI with colors, tables, live progress updates
- **PydanticAI** - Structured LLM outputs with type safety, simpler than LangChain
- **sounddevice** - Cross-platform audio recording with NumPy integration
- **Async/await** - Non-blocking I/O for responsive UX during API calls

## Key Patterns

**Press Enter to stop** - More intuitive than Ctrl+C, cleaner async cancellation

**Temporary WAV files** - Required by Whisper API, auto-cleanup prevents disk bloat

**Enum for styles** - Type-safe, IDE autocomplete, automatic validation

**pydantic-settings** - Type-safe config with automatic env var parsing (`SHH_` prefix)
