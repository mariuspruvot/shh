<div align="center">
  <img src="assets/shh-logo.png" alt="shh logo" width="200"/>

  # shh

  **Voice transcription CLI powered by OpenAI Whisper**

  Record, transcribe, format. All from your terminal.

  [![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
  [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

---

## Quick Start

```bash
# Install
uv pip install -e .

# Setup API key
shh setup

# Record and transcribe
shh
```

## Features

- <¤ **Record** from microphone or transcribe files
- > **Format** with AI (casual, business, or neutral)
- < **Translate** to any language
- =Ë **Copy** to clipboard automatically
- ¡ **Fast** async architecture

## Usage

```bash
# Quick record (press Ctrl+C to stop)
shh

# Record for 60 seconds
shh record --duration 60

# Format with style
shh --style business

# Translate
shh --translate fr

# Transcribe file
shh transcribe audio.mp3
```

## Tech Stack

Python 3.11+ " OpenAI Whisper " PydanticAI " Typer " Rich

---

Built with d for developers who live in the terminal
