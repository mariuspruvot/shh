# Welcome to shh

<div align="center">
  <img src="../assets/shh-logo.png" alt="shh logo" width="200"/>
  <p><strong>Voice transcription CLI powered by OpenAI Whisper</strong></p>
  <p>Record, transcribe, format. All from your terminal.</p>
</div>

---

## What is shh?

**shh** is a command-line tool for recording audio, transcribing it using OpenAI's Whisper API, and optionally formatting or translating the output with AI.

## Key Features

🎤 **One-command recording** - Start recording with `shh`, stop with Enter
✨ **AI-powered formatting** - Clean up transcriptions in casual, business, or neutral styles
🌍 **Translation** - Transcribe and translate to any language
📋 **Clipboard integration** - Results automatically copied for instant use
⚡ **Async architecture** - Non-blocking operations for responsive UX
🎨 **Beautiful UI** - Rich terminal output with live progress indicators

## Quick Example

```bash
# Install
uv pip install -e .

# Configure API key
shh setup

# Start recording (press Enter to stop)
shh

# Output appears in terminal and clipboard
```

## Use Cases

- **Meeting notes** - Record conversations and get formatted transcriptions
- **Voice memos** - Capture ideas quickly without typing
- **Content creation** - Transcribe interviews, podcasts, or videos
- **Multilingual work** - Transcribe and translate in one step
- **Accessibility** - Convert speech to text for documentation

## Architecture

shh follows a pragmatic layered architecture:

```
CLI Layer (Typer)     → User interaction and commands
    ↓
Core Layer            → Business logic and orchestration
    ↓
Adapters Layer        → External APIs, audio hardware, clipboard
```

This separation ensures clean dependencies and makes testing straightforward.

## What's Next?

- [Installation Guide](getting-started/installation.md) - Set up shh on your system
- [Quick Start](getting-started/quickstart.md) - Get transcribing in 2 minutes
- [Commands Reference](user-guide/commands.md) - Learn all available commands
- [Architecture Overview](architecture/overview.md) - Understand how shh works

## Requirements

- Python 3.11 or higher
- OpenAI API key
- Microphone (for recording)
