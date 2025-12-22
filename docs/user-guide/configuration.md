# Configuration

shh stores configuration in a JSON file at a platform-specific location. You can also use environment variables or command-line flags.

## Configuration File Location

```
macOS:    ~/Library/Application Support/shh/config.json
Linux:    ~/.config/shh/config.json
Windows:  %APPDATA%\shh\config.json
```

The file is created automatically when you run `shh setup`.

## Configuration Priority

Settings are loaded in this order (highest priority first):

1. **Command-line flags** - `--style casual`
2. **Environment variables** - `SHH_DEFAULT_STYLE=casual`
3. **Config file** - `config.json`
4. **Defaults** - Built-in defaults

## Available Settings

### `openai_api_key`

**Type:** String
**Required:** Yes
**Default:** None

Your OpenAI API key for Whisper and GPT APIs.

```bash
# Set via setup command (recommended)
shh setup

# Set via environment variable
export SHH_OPENAI_API_KEY="sk-..."

# Set via config command
shh config set openai_api_key "sk-..."
```

!!! warning "Security"
    Never commit your API key to version control. Use environment variables or the config file.

### `default_style`

**Type:** String
**Options:** `neutral`, `casual`, `business`
**Default:** `neutral`

Default formatting style for transcriptions.

```bash
# Set via config command
shh config set default_style casual

# Set via environment variable
export SHH_DEFAULT_STYLE=casual

# Override via flag
shh --style business
```

See [Formatting Styles](styles.md) for details on each style.

### `show_progress`

**Type:** Boolean
**Options:** `true`, `false`
**Default:** `true`

Show live progress indicator while recording.

```bash
# Set via config command
shh config set show_progress false

# Set via environment variable
export SHH_SHOW_PROGRESS=false
```

When enabled, you'll see:
```
🔴 Recording... 12.3s [Press Enter to stop]
```

When disabled, recording is silent until you press Enter.

### `whisper_model`

**Type:** String
**Options:** `whisper-1`
**Default:** `whisper-1`

OpenAI Whisper model to use for transcription.

```bash
# Set via config command
shh config set whisper_model whisper-1

# Set via environment variable
export SHH_WHISPER_MODEL=whisper-1
```

!!! note "Model Availability"
    Currently, `whisper-1` is the only available model via the OpenAI API. This setting exists for future compatibility.

## Environment Variables

All settings can be configured via environment variables with the `SHH_` prefix:

```bash
export SHH_OPENAI_API_KEY="sk-..."
export SHH_DEFAULT_STYLE="casual"
export SHH_SHOW_PROGRESS="true"
export SHH_WHISPER_MODEL="whisper-1"
```

Add these to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.) for persistence.

## Example Configuration File

Here's what a typical `config.json` looks like:

```json
{
  "openai_api_key": "sk-proj-...",
  "default_style": "casual",
  "show_progress": true,
  "whisper_model": "whisper-1"
}
```

## Managing Configuration

### View Current Config

```bash
shh config show
```

### Get Single Setting

```bash
shh config get default_style
```

### Update Setting

```bash
shh config set default_style business
```

### Reset to Defaults

```bash
shh config reset
```

!!! warning "Reset Warning"
    `shh config reset` clears **all** settings, including your API key. You'll need to run `shh setup` again.

## Common Configurations

### Casual User

Always use casual formatting, hide progress:

```bash
shh config set default_style casual
shh config set show_progress false
```

Or in environment variables:

```bash
export SHH_DEFAULT_STYLE=casual
export SHH_SHOW_PROGRESS=false
```

### Business User

Professional formatting by default:

```bash
shh config set default_style business
```

### Developer Testing

Use environment variables to avoid modifying config:

```bash
SHH_DEFAULT_STYLE=casual shh
```

## Troubleshooting

### Config file not found

If you see "No API key found", run:

```bash
shh setup
```

This creates the config file and prompts for your API key.

### Permission errors

If you can't write to the config file, check directory permissions:

```bash
# macOS/Linux
ls -la ~/Library/Application\ Support/shh/  # macOS
ls -la ~/.config/shh/  # Linux

# Windows
dir %APPDATA%\shh\
```

### Invalid values

If you manually edit `config.json` and enter invalid values, shh will show an error:

```
Error: Invalid style 'foo'
Valid styles: neutral, casual, business
```

Fix by running:

```bash
shh config set default_style neutral
```

## Next Steps

- [Learn about formatting styles](styles.md)
- [Translation options](translation.md)
- [All commands reference](commands.md)
