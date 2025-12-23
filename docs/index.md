<div align="center">

<img src="assets/shh-logo.png" alt="shh logo" width="150"/>

# shh

**Voice transcription CLI powered by OpenAI Whisper**

Record audio, transcribe with Whisper, and optionally format or translate the output.

[Get Started](getting-started/installation.md){ .md-button .md-button--primary }
[View on GitHub](https://github.com/mariuspruvot/shh){ .md-button }

</div>

---

## Features

<div class="grid cards" markdown>

-   :material-record-circle-outline: __One-command recording__

    ---

    Start with `shh`, stop with Enter. No configuration needed.

-   :material-auto-fix: __AI formatting__

    ---

    Clean up transcriptions in casual, business, or neutral styles.

-   :material-translate: __Translation__

    ---

    Transcribe and translate to any language in one command.

-   :material-content-copy: __Clipboard integration__

    ---

    Results automatically copied for instant use.

-   :material-lightning-bolt: __Async architecture__

    ---

    Non-blocking operations for responsive UX.

-   :material-chart-line: __Live progress__

    ---

    Real-time recording indicators with elapsed time.

</div>

## Quick Start

```bash
# Install
pipx install shh

# Configure API key
shh setup

# Record (press Enter to stop)
shh
```

Results appear in terminal and clipboard.

## Documentation

- [Installation](getting-started/installation.md) - Setup instructions
- [Quick Start](getting-started/quickstart.md) - Get started in 2 minutes
- [Commands](user-guide/commands.md) - All available commands
- [Configuration](user-guide/configuration.md) - Settings and defaults
- [API Reference](api-reference/core.md) - Code documentation

## Requirements

- Python 3.11+
- OpenAI API key
- Microphone
