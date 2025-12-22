# Adapters API Reference

The adapters layer handles all external integrations: audio recording, OpenAI APIs, clipboard, and file I/O. These modules interact with hardware, external services, and the operating system.

## Audio Adapters

### Audio Recorder

::: shh.adapters.audio.recorder
    options:
      show_root_heading: true
      show_source: true
      heading_level: 4

The `AudioRecorder` class handles microphone recording using the `sounddevice` library.

**Key features:**

- Async context manager for clean resource handling
- Automatic audio chunking for memory efficiency
- Configurable sample rate and max duration
- Non-blocking recording with `asyncio`

**Example usage:**

```python
from shh.adapters.audio.recorder import AudioRecorder
import numpy as np

async def record_audio() -> np.ndarray:
    async with AudioRecorder(max_duration=60.0) as recorder:
        # Recording happens in background
        await asyncio.sleep(5.0)  # Record for 5 seconds

    # Get recorded audio
    return recorder.get_audio_data()
```

### Audio Processor

::: shh.adapters.audio.processor
    options:
      show_root_heading: true
      show_source: true
      heading_level: 4

The `processor` module handles WAV file operations using `scipy.io.wavfile`.

**Key functions:**

- `save_audio_to_wav()`: Save NumPy array to WAV file
- Uses temporary files (deleted after transcription)
- 16kHz sample rate (optimized for Whisper)

**Example usage:**

```python
from shh.adapters.audio.processor import save_audio_to_wav
import numpy as np

# Save audio data to WAV
audio_data = np.random.randn(16000).astype(np.float32)
wav_path = save_audio_to_wav(audio_data)

# Use for transcription
try:
    result = await transcribe_audio(wav_path, api_key)
finally:
    wav_path.unlink()  # Clean up temp file
```

---

## Whisper Adapter

::: shh.adapters.whisper.client
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

The Whisper client handles transcription via the OpenAI Whisper API.

**Key features:**

- Async API calls using `httpx`
- Automatic error handling and retries
- Supports all Whisper API parameters

**Example usage:**

```python
from shh.adapters.whisper.client import transcribe_audio
from pathlib import Path

# Transcribe WAV file
wav_path = Path("audio.wav")
api_key = "sk-..."

text = await transcribe_audio(
    audio_file_path=wav_path,
    api_key=api_key,
)
print(text)  # "Hello, this is a test."
```

---

## LLM Adapter

::: shh.adapters.llm.formatter
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

The LLM formatter uses PydanticAI to format and translate transcriptions.

**Key features:**

- Structured output with Pydantic models
- Support for casual and business styles
- Optional translation to any language
- Neutral style bypasses LLM (returns as-is)

**Example usage:**

```python
from shh.adapters.llm.formatter import format_transcription
from shh.core.styles import TranscriptionStyle

# Format with casual style
result = await format_transcription(
    text="Um, like, this is a test, you know?",
    style=TranscriptionStyle.CASUAL,
    api_key="sk-...",
)
print(result.text)  # "This is a test."

# Format with business style and translation
result = await format_transcription(
    text="Bonjour, comment allez-vous?",
    style=TranscriptionStyle.BUSINESS,
    api_key="sk-...",
    target_language="English",
)
print(result.text)  # "Good afternoon. How are you today?"
```

---

## Clipboard Adapter

::: shh.adapters.clipboard.manager
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

The clipboard manager handles copying text to the system clipboard using `pyperclip`.

**Key features:**

- Cross-platform support (macOS, Linux, Windows)
- Graceful fallback if clipboard unavailable
- Simple async interface

**Example usage:**

```python
from shh.adapters.clipboard.manager import copy_to_clipboard

# Copy text to clipboard
await copy_to_clipboard("Hello, world!")

# Text is now available for pasting (Cmd+V / Ctrl+V)
```

---

## Design Principles

The adapters layer follows these principles:

- **Isolated I/O**: All external interactions happen here
- **Error boundaries**: Translate external errors to domain exceptions
- **Async-first**: All I/O uses `async/await` for non-blocking operations
- **Dependency injection**: API keys and config passed as parameters

## Related Modules

- [Core Reference](core.md) - Business logic and styles
- [CLI Reference](cli.md) - User-facing commands
