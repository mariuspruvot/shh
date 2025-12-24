# Architecture Overview

## Layered Architecture

```
CLI Layer (Typer)
  ├─ app.py, commands/
  ├─ Orchestrates workflows
  └─ Calls ↓

Core Layer
  └─ styles.py (TranscriptionStyle enum)

Adapters Layer (I/O)
  ├─ audio/ (sounddevice, scipy)
  ├─ whisper/ (OpenAI API)
  ├─ llm/ (PydanticAI)
  └─ clipboard/ (pyperclip)
```

## Dependency Rule

Unidirectional flow: CLI → Core → Adapters

- CLI imports Core and Adapters
- Core imports nothing
- Adapters import nothing

## Data Flow

```
1. CLI (app.py) - Parse args, validate API key
2. CLI (record.py) - Display progress, wait for Enter
3. Adapters (audio) - Record and save WAV
4. Adapters (whisper) - Transcribe via OpenAI
5. Adapters (llm) - Translate/format via PydanticAI
6. Adapters (clipboard) - Copy result
7. CLI (record.py) - Display result, cleanup
```
