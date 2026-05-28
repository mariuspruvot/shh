# CLAUDE.md - shh Project

This file provides **project-specific** guidance to Claude Code when working on the **shh** voice transcription CLI.

For general Python development preferences, see `~/.claude/CLAUDE.md`. **This project file overrides global preferences where specified.**

---

## Project Overview

**shh** is a voice transcription CLI powered by OpenAI Whisper. It allows users to record audio from their terminal, transcribe it using the Whisper API, and optionally format or translate the output using AI.

**Core Features**:
- Record audio from microphone or transcribe existing files
- Format transcriptions with AI (casual, business, or neutral style)
- Translate transcriptions to any language
- Copy results to clipboard automatically
- Async architecture for responsive UX

**Tech Stack**: Python 3.11+ • OpenAI Whisper • PydanticAI (`gpt-4o-mini`) • Typer • Rich • sounddevice

---

## Architecture

This project follows a **Pragmatic Layered Architecture**. The CLI calls a thin service layer that orchestrates the recording/transcription/formatting flow.

```
   CLI (Typer + Rich/Quiet)
              ↓
        Services Layer            RecordingService
              ↓
      ┌───────┴────────┐
    Core            Adapters
  (models,        (audio, whisper,
   styles)         llm, clipboard)
```

**Dependency Rule**: `CLI → Services → (Core + Adapters)`. Lower layers never import from upper layers. Adapters are framework-agnostic and never import `cli/` or `services/`.

### Directory Structure

```
shh/
├── cli/                    # CLI Layer - Typer commands + UI abstraction
│   ├── app.py             # Typer app entry point (callback pattern, default = record)
│   ├── commands/          # Subcommands: record, setup, config
│   └── ui/                # UIOutput Protocol + RichUI + QuietUI implementations
├── services/               # Orchestration layer
│   └── recording.py       # RecordingService (record + transcribe + format)
├── core/                   # Domain models & enums (no I/O, framework-agnostic)
│   ├── models.py          # RecordingOptions, TranscriptionOutput
│   └── styles.py          # TranscriptionStyle enum
├── adapters/               # External Integrations (framework-agnostic)
│   ├── audio/             # sounddevice recording + scipy WAV processing
│   ├── whisper/           # OpenAI Whisper API client (AsyncOpenAI)
│   ├── llm/               # PydanticAI formatting agent (gpt-4o-mini)
│   └── clipboard/         # pyperclip wrapper
├── config/                 # Configuration management
│   └── settings.py        # pydantic-settings (env + JSON config file)
└── utils/                  # Shared utilities
    ├── exceptions.py      # Custom exceptions
    └── logger.py          # rich.logging setup
```

### Key Architectural Principles

1. **Async-first**: All I/O operations use `async/await` (Whisper API, LLM calls, recording service).
2. **Type safety**: Full type hints + `mypy --strict` enforcement.
3. **Service layer for orchestration**: Record/transcribe/format flow lives in `RecordingService`, not in a CLI command. Commands stay thin.
4. **Protocol-based UI**: Output is abstracted through the `UIOutput` Protocol (`shh/cli/ui/base.py`). New UIs (e.g., `QuietUI`, `RichUI`) implement the methods structurally — no inheritance required.
5. **Framework-agnostic core/adapters/services**: No Typer / Rich imports outside `cli/`.
6. **Temporary files**: Audio recorded to temp WAV, deleted immediately after transcription (`try/finally`).

---

## Development Commands

### Environment Setup

```bash
# Create virtual environment and install
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# Setup API key
shh setup
```

### Running the CLI

```bash
# Quick record (press Ctrl+C to stop or enter)
shh

# Record with duration
shh record --duration 60

# Format with style
shh --style business

# Translate
shh --translate fr

# Minimal output (for scripts / piping)
shh --quiet

# Verbose output (overrides quiet_mode config)
shh --verbose
```

### Testing

**Recommended (using Poe):**
```bash
uv run poe test              # Run all tests
uv run poe test-cov          # Run with coverage
uv run poe test-unit         # Run only unit tests
uv run poe test-integration  # Run only integration tests
uv run poe test-no-e2e       # Skip E2E tests (no real API calls)
```

**Direct pytest commands:**
```bash
pytest                                               # Run all tests
pytest --cov=shh --cov-report=html --cov-report=term # With coverage
pytest tests/unit/test_formatting.py                 # Specific test file
pytest -m "not e2e"                                  # Excluding E2E tests
pytest -v                                            # Verbose output
```

### Code Quality

This project uses **Poe the Poet** for task automation. All tasks are run via `uv run poe <task>`.

```bash
# Type checking (strict mode enforced)
uv run poe type              # mypy --strict shh/

# Linting
uv run poe lint              # ruff check .
uv run poe lint-fix          # ruff check . --fix

# Formatting
uv run poe format            # ruff format .

# Combined quality check (before commit)
uv run poe check             # Runs: type + lint + test

# Auto-fix and format
uv run poe fix               # Runs: lint-fix + format
```

**Direct commands (if needed):**
```bash
mypy --strict shh/
ruff check .
ruff check . --fix
```

### Development Utilities

```bash
# Clean cache directories
uv run poe clean

# Install in editable mode
uv pip install -e .

# Install with dev dependencies
uv pip install -e ".[dev]"
```

---

## Configuration

### Config File Location

Platform-specific paths via `platformdirs`:
- **macOS**: `~/Library/Application Support/shh/config.json`
- **Linux**: `~/.config/shh/config.json`
- **Windows**: `%APPDATA%\shh\config.json`

### Config Structure

```json
{
  "openai_api_key": "sk-...",
  "default_output": ["clipboard", "stdout"],
  "show_progress": true,
  "default_style": "neutral",
  "default_translation_language": null,
  "quiet_mode": false,
  "whisper_model": "whisper-1"
}
```

`quiet_mode` selects `QuietUI` over `RichUI` for `shh` invocations. The CLI flags `--quiet` / `--verbose` override this field at runtime. See `shh/config/settings.py` for the authoritative schema.

### Priority Order

1. CLI flags (highest)
2. Environment variables (`SHH_*` prefix)
3. Config file
4. Defaults (lowest)

---

## Implementation Patterns

### Audio Recording

- **Library**: `sounddevice` for cross-platform recording
- **Format**: WAV (16kHz sample rate, optimal for Whisper)
- **Storage**: Temporary files only, deleted after transcription
- **Modes**: Duration-based (`--duration 60`) or interactive (Ctrl+C to stop)

### Whisper Transcription

- **Client**: `AsyncOpenAI` (from the `openai` SDK)
- **Adapter**: `shh/adapters/whisper/client.py` — uploads the temp WAV, returns the raw transcript.
- **Model**: `whisper-1` (configurable via `Settings.whisper_model`).

### PydanticAI Formatting

- **Agent**: `pydantic_ai.Agent` with `OpenAIChatModel("gpt-4o-mini")` (`shh/adapters/llm/formatter.py:103`).
- **Styles**:
  - `neutral`: No LLM call **unless** a `target_language` is provided — text is returned as-is from Whisper.
  - `casual`: Conversational tone, removes filler words.
  - `business`: Formal tone, structured paragraphs.
- **Output**: Structured `FormattedTranscription` Pydantic model.
- **Errors**: Wrapped in `FormattingError` and re-raised at the adapter boundary.

### UI Output Layer (Protocol)

- **Defined in** `shh/cli/ui/base.py`. `UIOutput` is a `typing.Protocol` — structural typing, no inheritance.
- **Implementations**: `RichUI` (default, animated progress + styled output) and `QuietUI` (minimal: progress bar + final text).
- **Selection**: `RichUI` unless `Settings.quiet_mode` is true or `--quiet` is passed.
- **Adding a new UI**: implement every method of `UIOutput` (`show_error`, `show_recording_progress`, `show_result`, `cleanup`, …) in a new class — no base class to extend.

### CLI Entry Point Pattern

- `shh/cli/app.py` uses Typer's `@app.callback(invoke_without_command=True)` so that the bare `shh` command runs the default record flow while still allowing `shh setup`, `shh config`, `shh record` subcommands.

### Error Handling

- **Philosophy**: Fail fast with clear error messages
- **Custom exceptions**: Defined in `utils/exceptions.py`
- **API errors**: Translated at adapter boundaries, never leaked to core
- **Cleanup**: Temp files deleted in `try/finally` blocks

---

## Critical Constraints

### MUST Do

1. **Full type hints**: Every function must have complete type annotations.
2. **Pass mypy strict**: `mypy --strict shh/` must pass before committing.
3. **Clean up temp files**: Use `try/finally` to ensure WAV files are deleted.
4. **Layer boundaries**: `CLI → Services → (Core + Adapters)`. Never the reverse.
5. **Structured outputs**: Use Pydantic models for all LLM responses.
6. **Orchestration in services**: New record/transcribe/format logic goes in `services/`, not in a command.

### MUST NOT Do

- Import `typer` / `rich` in `core/`, `adapters/`, or `services/`.
- Import `cli/` from `services/`, `core/`, or `adapters/`.
- Put orchestration logic directly in a Typer command — call `RecordingService` instead.
- Leave temp WAV files on disk after transcription.
- Skip type hints or use `Any` without justification.
- Commit code that fails `mypy --strict` or `ruff check`.

---

### Adding a New Feature

1. **Plan**: Identify which layer owns the logic (CLI / Services / Core / Adapters).
2. **Write tests first**: Unit tests for services and adapters, integration tests for end-to-end flows.
3. **Implement**: Follow layer boundaries strictly. Orchestration belongs in `services/`.
4. **Type check**: Run `uv run poe type`.
5. **Lint**: Run `uv run poe lint` (or `uv run poe fix` to auto-fix).
6. **Test**: Run `uv run poe test` to ensure all tests pass.
7. **Document**: Update CLAUDE.md if architectural changes were made.

### Before Committing

```bash
# Full quality check (type + lint + test)
uv run poe check

# If all pass, you're good to commit
git add .
git commit -m "feat: description"
```

**Alternative (manual commands):**
```bash
mypy --strict shh/ && ruff check . && pytest
```


## Roadmap Reference

See `.roadmap.md` for:
- Detailed architectural decisions
- Complete implementation checklist
- Phase-by-phase development plan
- Open questions and design philosophy

**Note**: `.roadmap.md` is gitignored and contains extensive planning details. This CLAUDE.md focuses on practical development guidance.

---

## References

- [PydanticAI Documentation](https://ai.pydantic.dev/)
- [Typer Documentation](https://typer.tiangolo.com/)
- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)
- [Rich Documentation](https://rich.readthedocs.io/)
- [sounddevice Documentation](https://python-sounddevice.readthedocs.io/)
- Use Context7 mcp for access to documentations
