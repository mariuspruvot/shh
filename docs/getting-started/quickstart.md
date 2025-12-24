# Quick Start

## Setup

```bash
shh setup
```

API key stored in `~/Library/Application Support/shh/config.json` (macOS), `~/.config/shh/config.json` (Linux), or `%APPDATA%\shh\config.json` (Windows).

## Basic Usage

```bash
shh                        # Record, press Enter to stop
shh --duration 60          # Record for 60 seconds
shh --style casual         # Format output (neutral/casual/business)
shh --translate English    # Translate to English
```

Output appears in terminal and clipboard.

## Configuration

```bash
shh config show                              # View settings
shh config set default_style casual          # Set default style
shh config set default_translation_language English
```
