# Architecture Overview

Pragmatic layered architecture: CLI → Core → Adapters.

## Layered Architecture

```
┌─────────────────────────────────────────────────┐
│              CLI Layer (Typer)                  │
│  ┌───────────┐  ┌─────────┐  ┌──────────┐     │
│  │   app.py  │  │  setup  │  │  config  │     │
│  └─────┬─────┘  └────┬────┘  └────┬─────┘     │
│        │             │            │            │
│        └─────────────┴────────────┘            │
└────────────────────┬────────────────────────────┘
                     │ depends on
                     ↓
┌─────────────────────────────────────────────────┐
│            Core Layer (Business Logic)          │
│  ┌──────────────┐   ┌──────────────────┐       │
│  │   styles.py  │   │  orchestration   │       │
│  └──────────────┘   └──────────────────┘       │
└────────────────────┬────────────────────────────┘
                     │ depends on
                     ↓
┌─────────────────────────────────────────────────┐
│         Adapters Layer (External I/O)           │
│  ┌───────┐  ┌──────────┐  ┌──────┐  ┌────────┐│
│  │ audio │  │ whisper  │  │ llm  │  │clipboard││
│  └───────┘  └──────────┘  └──────┘  └────────┘│
└─────────────────────────────────────────────────┘
                     │
                     ↓
        ┌───────────────────────────┐
        │  External Dependencies    │
        │  • OpenAI APIs           │
        │  • sounddevice           │
        │  • pyperclip             │
        └───────────────────────────┘
```

## Dependency Rule

**Unidirectional flow:** CLI → Core → Adapters

- CLI imports Core and Adapters
- Core imports nothing (pure logic)
- Adapters import nothing (isolated I/O)

Benefits: Clean separation, easy testing, framework independence.

## Layer Responsibilities

### CLI Layer

User interaction and terminal UI.

**Key responsibilities:**
- Parse arguments (Typer)
- Display output (Rich)
- Orchestrate workflows
- Bridge sync CLI to async backend

**Main files:** `cli/app.py`, `cli/commands/`

### Core Layer

Business logic and domain models.

**Key responsibilities:**
- Define domain models (TranscriptionStyle)
- Business rules (when to format/translate)
- Pure logic, no I/O
- Framework-agnostic

**Main files:** `core/styles.py`

**Dependencies:** Standard library, Pydantic types only

### Adapters Layer

All external I/O and integrations.

**Key responsibilities:**
- Audio recording (sounddevice)
- WAV file I/O (scipy)
- Whisper API (httpx)
- LLM formatting (PydanticAI)
- Clipboard (pyperclip)

**Main files:** `adapters/audio/`, `adapters/whisper/`, `adapters/llm/`, `adapters/clipboard/`

## Data Flow

### Recording Workflow

```
User runs: shh --style casual --translate English

1. CLI Layer (app.py)
   ├─ Parse args (Typer)
   ├─ Validate API key exists
   └─ Call asyncio.run(record_command(...))

2. CLI Layer (record.py)
   ├─ Create AudioRecorder
   ├─ Display progress (Rich Live)
   └─ Wait for Enter or max duration

3. Adapters Layer (audio/recorder.py)
   └─ Record audio chunks (sounddevice)

4. Adapters Layer (audio/processor.py)
   └─ Save to WAV file (scipy)

5. Adapters Layer (whisper/client.py)
   └─ Transcribe audio (OpenAI Whisper API)

6. Adapters Layer (llm/formatter.py)
   ├─ Translate to English (PydanticAI + GPT)
   └─ Format with casual style (PydanticAI + GPT)

7. Adapters Layer (clipboard/manager.py)
   └─ Copy to clipboard (pyperclip)

8. CLI Layer (record.py)
   ├─ Display result (Rich Panel)
   └─ Clean up temp WAV file
```

### Configuration Workflow

```
User runs: shh config set default_style casual

1. CLI Layer (config.py)
   ├─ Parse args (key, value)
   ├─ Validate key exists
   └─ Validate value is valid enum

2. Config Layer (settings.py)
   ├─ Load existing config
   ├─ Update setting
   └─ Save to JSON file

3. Config Layer (storage.py)
   └─ Write JSON to platform-specific path
```

## Configuration Architecture

```
┌─────────────────────────────────────────────┐
│         Configuration Priority              │
│  1. CLI Flags        (--style casual)       │
│  2. Environment Vars (SHH_DEFAULT_STYLE)    │
│  3. Config File      (config.json)          │
│  4. Defaults         (hardcoded)            │
└─────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────┐
│      pydantic-settings (Settings class)     │
│  • Type validation                          │
│  • Environment variable parsing             │
│  • Default values                           │
└─────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────┐
│         Platform-specific Storage           │
│  macOS:   ~/Library/Application Support/   │
│  Linux:   ~/.config/shh/                   │
│  Windows: %APPDATA%\shh\                   │
└─────────────────────────────────────────────┘
```

## Async Architecture

All I/O operations use async/await for non-blocking execution and responsive UX.

**Key patterns:**
- Async context managers for resource cleanup
- Thread pool executors for blocking I/O (stdin)
- Task cancellation for graceful shutdowns

```python
async with AudioRecorder() as recorder:
    await asyncio.sleep(duration)
# Cleanup happens automatically
```

## Type Safety

Full `mypy --strict` compliance with type hints on all functions.

**Stack:**
- Pydantic models for structured data
- Enums for finite choices (TranscriptionStyle)
- No `Any` without justification

## Error Handling

Fail fast with clear messages. Adapters translate external errors to domain exceptions. Resources cleaned up in `try/finally` blocks.

```python
try:
    result = await transcribe_audio(wav_path, api_key)
finally:
    wav_path.unlink(missing_ok=True)  # Always clean up
```

## Testing Strategy

Unit tests for core logic, integration tests with mocked APIs. No E2E tests in CI (avoid real API calls).

Target: 80%+ code coverage.

## Next Steps

- [Design Decisions](design-decisions.md)
- [Testing Architecture](testing.md)
- [API Reference](../api-reference/core.md)
