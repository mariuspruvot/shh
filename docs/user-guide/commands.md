# Commands Reference

Complete reference for all shh commands.

## Default Command

### `shh`

Start recording immediately. Press Enter to stop.

```bash
shh
```

**Options:**

- `--style, -s` - Formatting style (neutral, casual, business)
- `--translate, -t` - Target language for translation
- `--duration, -d` - Recording duration in seconds (optional)

**Examples:**

```bash
# Basic recording
shh

# With casual formatting
shh --style casual

# Record for 60 seconds
shh --duration 60

# Translate to French with business formatting
shh --style business --translate French
```

---

## Setup Command

### `shh setup`

Interactive setup wizard to configure your OpenAI API key.

```bash
shh setup
```

Your API key is stored securely in a platform-specific location. The key is hidden while typing for security.

**What it does:**

1. Prompts for your OpenAI API key (input hidden)
2. Validates the key is not empty
3. Saves to config file
4. Displays masked key confirmation (e.g., `sk-***xyz`)

**Example:**

```bash
$ shh setup
Enter your OpenAI API key: ****************

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃           Setup Complete                    ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
Configuration saved successfully!
Config file: /Users/you/Library/Application Support/shh/config.json
Settings:
  • OpenAI API Key: sk-***xyz
  • Default style: neutral
  • Show progress: true
```

---

## Config Commands

### `shh config show`

Display all current configuration settings.

```bash
shh config show
```

**Example output:**

```
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Setting         ┃ Value                    ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ openai_api_key  │ sk-***xyz                │
│ default_style   │ casual                   │
│ show_progress   │ True                     │
│ whisper_model   │ whisper-1                │
└─────────────────┴──────────────────────────┘
```

### `shh config get <key>`

Get a specific configuration value.

```bash
shh config get default_style
```

**Available keys:**

- `openai_api_key`
- `default_style`
- `show_progress`
- `whisper_model`

**Example:**

```bash
$ shh config get default_style
default_style: casual
```

### `shh config set <key> <value>`

Update a configuration setting.

```bash
shh config set default_style casual
```

**Examples:**

```bash
# Set default formatting style
shh config set default_style business

# Enable/disable progress indicator
shh config set show_progress true

# Change Whisper model (if needed)
shh config set whisper_model whisper-1
```

**Validation:**

The command validates input and provides helpful error messages:

```bash
$ shh config set default_style invalid
Error: Invalid style 'invalid'
Valid styles: neutral, casual, business
```

### `shh config reset`

Reset all settings to defaults (requires confirmation).

```bash
shh config reset
```

You'll be prompted to confirm:

```bash
$ shh config reset
This will reset all configuration to defaults.
Continue? [y/N]: y

Configuration reset to defaults.
Run 'shh setup' to configure your API key.
```

**What gets reset:**

- `default_style` → neutral
- `show_progress` → true
- `whisper_model` → whisper-1
- **Note:** Your API key is also cleared - you'll need to run `shh setup` again

---

## Global Options

All commands support these options:

- `--help` - Show help message
- `--version` - Show version information

**Examples:**

```bash
# Get help for any command
shh --help
shh config --help
shh config set --help

# Check version
shh --version
```

---

## Exit Codes

shh uses standard exit codes:

- `0` - Success
- `1` - Error (invalid input, API failure, etc.)

Use these in scripts:

```bash
if shh --style casual; then
    echo "Transcription successful"
else
    echo "Transcription failed"
fi
```

---

## Next Steps

- [Configuration details](configuration.md)
- [Understanding formatting styles](styles.md)
- [Translation guide](translation.md)
