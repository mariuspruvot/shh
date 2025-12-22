# Quick Start

## Setup

After [installation](installation.md), configure your API key:

```bash
shh setup
```

!!! tip "API Key Storage"
    Your API key is stored locally in:

    - **macOS**: `~/Library/Application Support/shh/config.json`
    - **Linux**: `~/.config/shh/config.json`
    - **Windows**: `%APPDATA%\shh\config.json`

## Basic Usage

### Record and Transcribe

```bash
shh
```

Press Enter to stop. Output appears in terminal and clipboard.

### Record with Duration

```bash
shh --duration 60
```

## Formatting Styles

```bash
# Casual style - conversational, filler words removed
shh --style casual

# Business style - professional, formal tone
shh --style business

# Neutral style - no formatting, raw Whisper output
shh --style neutral
```

!!! example "Style Comparison"
    **Raw Whisper output:**
    > Um, so like, I was thinking we should probably update the database schema, you know?

    **Casual style:**
    > I was thinking we should update the database schema.

    **Business style:**
    > I recommend updating the database schema to improve data integrity and performance.

## Translation

```bash
# Transcribe French audio to English
shh --translate English

# Combine with formatting
shh --style business --translate English
```

## Configuration

```bash
# View settings
shh config show

# Set default style
shh config set default_style casual
```

## Common Workflows

### Quick Voice Note

```bash
shh
# Press Enter when done
# Result is in clipboard - paste anywhere
```

### Meeting Transcription

```bash
# Business formatting for professional output
shh --style business
```

### Multilingual Interview

```bash
# Record French, transcribe to English, business format
shh --style business --translate English
```

## Next Steps

- [Learn all commands](../user-guide/commands.md)
- [Customize configuration](../user-guide/configuration.md)
- [Understand formatting styles](../user-guide/styles.md)

## Tips

!!! tip "Clipboard Integration"
    Results are automatically copied to clipboard.

!!! tip "Progress Indicator"
    Live timer shows elapsed time while recording.

!!! warning "Maximum Duration"
    Default limit: 5 minutes. Use multiple sessions for longer recordings.
