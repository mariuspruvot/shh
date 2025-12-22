# Architecture Overview

Three layers: CLI, Core, Adapters.

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

**Flow is unidirectional: CLI → Core → Adapters**

- CLI can import Core and Adapters
- Core **cannot** import CLI or Adapters
- Adapters **cannot** import Core or CLI

This ensures:

- Clean separation of concerns
- Easy testing (core logic has no external dependencies)
- Framework independence (could swap Typer for argparse)

## Layer Responsibilities

### CLI Layer

**Purpose:** User interaction, command handling, terminal UI

**Responsibilities:**

- Parse command-line arguments (Typer)
- Display output with Rich (colors, tables, panels)
- Orchestrate workflow by calling Core and Adapters
- Bridge sync (Typer) to async (backend) with `asyncio.run()`
- Handle user-facing error messages

**Key files:**

- `cli/app.py` - Main CLI entry point
- `cli/commands/setup.py` - API key setup wizard
- `cli/commands/config.py` - Configuration management
- `cli/commands/record.py` - Recording workflow

**Dependencies:**

- Typer (CLI framework)
- Rich (terminal formatting)
- Core and Adapters layers

### Core Layer

**Purpose:** Business logic and orchestration rules

**Responsibilities:**

- Define domain models (TranscriptionStyle enum)
- Contain business rules (when to format, when to translate)
- Pure logic with no I/O operations
- Framework-agnostic (no Typer/Rich imports)

**Key files:**

- `core/styles.py` - TranscriptionStyle enum

**Dependencies:**

- Standard library only
- Pydantic (for types, but not I/O)

**Note:** Currently, orchestration happens in the CLI layer (`record.py`). This is a pragmatic choice for simplicity. In a larger app, orchestration would move to Core.

### Adapters Layer

**Purpose:** All external I/O and integrations

**Responsibilities:**

- Audio recording (sounddevice)
- File I/O (scipy for WAV files)
- OpenAI Whisper API calls (httpx)
- LLM formatting with PydanticAI (OpenAI GPT)
- Clipboard operations (pyperclip)
- Translate external errors to domain exceptions

**Key files:**

- `adapters/audio/recorder.py` - Microphone recording
- `adapters/audio/processor.py` - WAV file operations
- `adapters/whisper/client.py` - Whisper API client
- `adapters/llm/formatter.py` - PydanticAI formatting agent
- `adapters/clipboard/manager.py` - Clipboard wrapper

**Dependencies:**

- sounddevice, scipy (audio)
- httpx, openai (APIs)
- pydantic-ai (LLM agent)
- pyperclip (clipboard)

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

### Why Async?

- **Non-blocking I/O**: API calls don't freeze the UI
- **Responsive UX**: Live progress updates while recording
- **Efficient**: Multiple operations can run concurrently

### Async Patterns

**1. Async Context Managers**

```python
async with AudioRecorder() as recorder:
    # Recording happens in background
    await asyncio.sleep(duration)
# Cleanup happens automatically
```

**2. Thread Pool for Blocking I/O**

```python
# stdin.readline() is blocking, run in thread pool
loop = asyncio.get_running_loop()
await loop.run_in_executor(None, sys.stdin.readline)
```

**3. Task Management**

```python
# Create background tasks
enter_task = asyncio.create_task(wait_for_enter())

# Cancel if not needed
if not enter_task.done():
    enter_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await enter_task
```

## Type Safety

**All code is typed with mypy --strict:**

- Every function has type hints
- No `Any` without justification
- Pydantic models for structured data
- Enums for finite choices (TranscriptionStyle, WhisperModel)

**Benefits:**

- Catch bugs at development time
- Self-documenting code
- IDE autocomplete and hints
- Refactoring confidence

## Error Handling

**Philosophy: Fail fast with clear messages**

### At Adapter Boundaries

```python
try:
    response = await openai_client.transcribe(...)
except Exception as e:
    raise TranscriptionError(f"Failed to transcribe: {e}") from e
```

### In CLI Layer

```python
try:
    settings = Settings.load_from_file()
except Exception:
    console.print("[red]No API key found. Run 'shh setup' first.[/red]")
    raise typer.Exit(code=1)
```

### Resource Cleanup

```python
try:
    result = await transcribe_audio(wav_path, api_key)
finally:
    wav_path.unlink(missing_ok=True)  # Always clean up
```

## Testing Strategy

See [Testing Architecture](testing.md) for detailed testing approach.

**Summary:**

- **Unit tests**: Core logic, isolated functions
- **Integration tests**: Adapters with mocked APIs
- **No E2E tests**: Avoid real API calls in CI
- **80%+ coverage**: Enforced via Codecov

## Next Steps

- [Design Decisions](design-decisions.md) - Why we made specific choices
- [Testing Architecture](testing.md) - Testing strategy and patterns
- [API Reference](../api-reference/core.md) - Detailed code documentation
