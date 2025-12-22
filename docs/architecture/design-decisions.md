# Design Decisions

This document explains the "why" behind key architectural and implementation choices in shh.

## Architecture Decisions

### Why Layered Architecture?

**Decision:** Separate CLI, Core, and Adapters layers with unidirectional dependencies.

**Rationale:**

- **Testability**: Core logic can be tested without mocking external APIs
- **Flexibility**: Could swap Typer for argparse, or add a web UI
- **Clarity**: Clear separation of concerns makes code easier to understand
- **Maintenance**: Changes to UI don't affect business logic

**Trade-offs:**

- ✅ Easier to test and maintain
- ✅ Framework-independent core
- ⚠️ More boilerplate (but not much in this small app)

**Alternatives considered:**

- Single-file script: Too messy for a production app
- Full hexagonal architecture: Overkill for a CLI tool

---

### Why Pragmatic vs. Pure Clean Architecture?

**Decision:** Orchestration happens in CLI layer, not Core layer.

**Rationale:**

- shh is small (< 1000 lines of code)
- Orchestration logic is tightly coupled to CLI UX
- Moving orchestration to Core would add complexity without benefit

**When to move to Core:**

- If we add a web UI (need shared orchestration)
- If orchestration logic becomes complex
- If we need to test orchestration without CLI

**Current approach:**

```python
# CLI layer handles orchestration (pragmatic)
async def record_command(...):
    audio = await record_audio()
    text = await transcribe_audio(audio)
    formatted = await format_transcription(text)
    await copy_to_clipboard(formatted)
```

**Pure approach (not used):**

```python
# Core layer handles orchestration (overkill for now)
class TranscriptionService:
    def __init__(self, whisper, llm, clipboard):
        ...

    async def transcribe(self, audio):
        text = await self.whisper.transcribe(audio)
        formatted = await self.llm.format(text)
        await self.clipboard.copy(formatted)
        return formatted
```

---

## Technology Choices

### Why Typer over argparse?

**Decision:** Use Typer for CLI framework.

**Rationale:**

- **Type hints**: Typer uses Python type hints for argument parsing
- **Automatic help**: Generates beautiful help messages
- **Subcommands**: Clean syntax for command groups (`config show`, `config set`)
- **Rich integration**: Works seamlessly with Rich for terminal UI

**Trade-offs:**

- ✅ Less boilerplate than argparse
- ✅ Better UX (help messages, validation)
- ⚠️ Extra dependency (but lightweight)

**Alternatives considered:**

- argparse: Built-in but verbose and less ergonomic
- click: Popular but less type-safe than Typer

---

### Why Rich for Terminal UI?

**Decision:** Use Rich for all terminal output.

**Rationale:**

- **Beautiful output**: Colors, tables, panels, progress bars
- **Live updates**: Real-time progress display while recording
- **Minimal effort**: Simple API for complex formatting
- **Professional look**: Makes the CLI feel polished

**Examples:**

```python
# Rich table
table = Table(title="Configuration")
table.add_column("Setting", style="cyan")
console.print(table)

# Rich panel
panel = Panel("Success!", title="Setup Complete", border_style="green")
console.print(panel)

# Rich live display
with Live(auto_refresh=False) as live:
    live.update(Text("Recording... 12.3s"))
```

**Alternatives considered:**

- Plain print(): Works but looks amateur
- colorama: Colors only, no tables or live updates
- blessed: More complex API

---

### Why PydanticAI over LangChain?

**Decision:** Use PydanticAI for LLM formatting.

**Rationale:**

- **Structured outputs**: Pydantic models ensure valid responses
- **Type safety**: Full type hints, integrates with mypy
- **Simplicity**: Less complex than LangChain for this use case
- **Modern**: Built by Pydantic team, first-class async support

**Example:**

```python
class FormattedTranscription(BaseModel):
    text: str

agent = Agent(model, result_type=FormattedTranscription)
result = await agent.run(f"Format this: {text}")
# result.output.text is guaranteed to be a string
```

**Trade-offs:**

- ✅ Simpler than LangChain for our needs
- ✅ Type-safe outputs
- ⚠️ Newer library (less mature)

**Alternatives considered:**

- LangChain: Too heavyweight, complex API
- Direct OpenAI SDK: No structured outputs

---

### Why sounddevice over pyaudio?

**Decision:** Use sounddevice for audio recording.

**Rationale:**

- **Cross-platform**: Works on macOS, Linux, Windows
- **NumPy integration**: Returns audio as NumPy arrays
- **Modern**: Active development, Python 3+ focused
- **Simple API**: Easy to use for basic recording

**Example:**

```python
import sounddevice as sd

# Record audio
audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
sd.wait()  # Wait until recording is finished
```

**Trade-offs:**

- ✅ Simpler than pyaudio
- ✅ Better documentation
- ⚠️ Requires PortAudio system library

**Alternatives considered:**

- pyaudio: More complex, less Pythonic API
- python-sounddevice: Same as sounddevice (it's an alias)

---

## Implementation Patterns

### Why Async/Await?

**Decision:** Use async/await for all I/O operations.

**Rationale:**

- **Non-blocking**: API calls don't freeze the UI
- **Responsive UX**: Live progress updates while recording
- **Modern Python**: async/await is the standard for I/O-bound tasks

**Where async is used:**

- Recording audio (async context manager)
- API calls (Whisper, GPT)
- Clipboard operations
- File I/O (when possible)

**Bridge to sync:**

```python
# Typer callbacks are sync, bridge to async backend
def default_command(...):
    asyncio.run(record_command(...))
```

**Trade-offs:**

- ✅ Better UX (non-blocking operations)
- ✅ Modern Python patterns
- ⚠️ Slightly more complex (async/await syntax)

---

### Why Press Enter (not Ctrl+C) to Stop?

**Decision:** Use Enter key to stop recording, not Ctrl+C.

**Rationale:**

- **Intuitive**: Enter is a natural "done" signal
- **No signal handling**: Ctrl+C sends SIGINT, complicates error handling
- **Graceful shutdown**: Enter allows clean async cancellation
- **User testing**: Felt more natural than Ctrl+C

**Implementation:**

```python
async def wait_for_enter():
    loop = asyncio.get_running_loop()
    # Run blocking stdin.readline in thread pool
    await loop.run_in_executor(None, sys.stdin.readline)

enter_task = asyncio.create_task(wait_for_enter())
while not enter_task.done():
    # Continue recording
    await asyncio.sleep(0.1)
```

**Trade-offs:**

- ✅ Cleaner async code
- ✅ More intuitive UX
- ⚠️ Different from typical CLI tools (which use Ctrl+C)

**Alternative considered:**

- Ctrl+C: More common but requires signal handling and is less graceful

---

### Why Temporary Files for Audio?

**Decision:** Save audio to temporary WAV files, delete immediately after transcription.

**Rationale:**

- **Whisper API requirement**: Requires file upload (not raw bytes)
- **Disk space**: Auto-cleanup prevents accumulation
- **Security**: Temporary files are automatically cleaned up

**Implementation:**

```python
try:
    wav_path = save_audio_to_wav(audio_data)
    text = await transcribe_audio(wav_path, api_key)
finally:
    wav_path.unlink(missing_ok=True)  # Always delete
```

**Trade-offs:**

- ✅ Required by API
- ✅ Auto-cleanup prevents disk bloat
- ⚠️ Temporary I/O overhead (minimal)

**Alternative considered:**

- Persistent files: Would require manual cleanup or config for storage location

---

### Why Enum for TranscriptionStyle?

**Decision:** Use Python Enum for style choices.

**Rationale:**

- **Type safety**: Can't pass invalid styles
- **IDE autocomplete**: Enum members appear in autocomplete
- **Validation**: Automatic validation in Pydantic models
- **Self-documenting**: All valid values in one place

**Example:**

```python
class TranscriptionStyle(str, Enum):
    NEUTRAL = "neutral"
    CASUAL = "casual"
    BUSINESS = "business"

# Type-safe usage
style = TranscriptionStyle.CASUAL

# Pydantic validates automatically
class Settings(BaseModel):
    default_style: TranscriptionStyle
```

**Trade-offs:**

- ✅ Type-safe
- ✅ Validated automatically
- ⚠️ Slightly more verbose than plain strings

**Alternative considered:**

- Plain strings: Easier but error-prone (typos not caught)

---

### Why pydantic-settings for Configuration?

**Decision:** Use pydantic-settings for config management.

**Rationale:**

- **Type safety**: Settings are typed and validated
- **Environment variables**: Automatic parsing with `SHH_` prefix
- **Multiple sources**: Supports env vars, JSON files, defaults
- **Validation**: Automatic validation on load
- **Platform-agnostic**: Works across macOS, Linux, Windows

**Example:**

```python
class Settings(BaseSettings):
    openai_api_key: str = ""
    default_style: TranscriptionStyle = TranscriptionStyle.NEUTRAL

    class Config:
        env_prefix = "SHH_"  # SHH_OPENAI_API_KEY
```

**Trade-offs:**

- ✅ Type-safe configuration
- ✅ Automatic validation
- ⚠️ Extra dependency (but small)

**Alternatives considered:**

- ConfigParser: Built-in but less type-safe
- python-dotenv: Only handles .env files
- YAML: Requires extra library, more complex

---

## Testing Decisions

### Why No E2E Tests?

**Decision:** No end-to-end tests with real APIs in CI.

**Rationale:**

- **Cost**: Real API calls cost money (OpenAI charges per request)
- **Speed**: API calls are slow, would make CI sluggish
- **Reliability**: External APIs can fail, causing flaky tests
- **Coverage**: Integration tests with mocks provide 80%+ coverage

**What we test instead:**

- **Unit tests**: Core logic, isolated functions
- **Integration tests**: Full pipeline with mocked APIs

**Example:**

```python
# Integration test with mocked Whisper API
with patch("shh.adapters.whisper.client.AsyncOpenAI") as mock:
    mock_instance = mock.return_value
    mock_instance.audio.transcriptions.create = AsyncMock(
        return_value=MagicMock(text="Hello world")
    )

    result = await transcribe_audio(wav_path, "sk-test-key")
    assert result == "Hello world"
```

**Trade-offs:**

- ✅ Fast CI (no API waits)
- ✅ Free (no API costs)
- ⚠️ Doesn't catch API changes (mitigated by integration tests)

**When to add E2E:**

- If we see production bugs not caught by mocks
- For release validation (not in regular CI)

---

## Future Considerations

### When to Add a Database?

**Currently:** Settings stored in JSON file.

**Add a database when:**

- We need to store transcription history
- We add user accounts or multi-user support
- We need search or querying of past transcriptions

**Likely choice:** SQLite (local, no server needed)

---

### When to Add a Web UI?

**Currently:** CLI only.

**Add a web UI when:**

- Users request it (not yet)
- We need remote access (record on server, access from browser)

**Architecture impact:**

- Move orchestration from CLI to Core layer
- Add FastAPI or Flask adapter layer
- Shared Core logic between CLI and Web

---

### When to Support Local Whisper?

**Currently:** OpenAI API only (requires internet and API key).

**Add local Whisper when:**

- Users request offline support
- Privacy concerns arise (local processing)

**Implementation:**

- Add `LocalWhisperAdapter` implementing same interface
- Configuration setting to choose API vs. Local
- Download model on first run

---

## Next Steps

- [Architecture Overview](overview.md) - High-level architecture
- [Testing Architecture](testing.md) - Testing strategy and patterns
- [API Reference](../api-reference/core.md) - Detailed code documentation
