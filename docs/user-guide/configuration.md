# Configuration

Config stored at:
- macOS: `~/Library/Application Support/shh/config.json`
- Linux: `~/.config/shh/config.json`
- Windows: `%APPDATA%\shh\config.json`

## Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `openai_api_key` | string | - | OpenAI API key (required) |
| `default_style` | enum | `neutral` | Formatting style: `neutral`, `casual`, `business` |
| `default_translation_language` | string | - | Auto-translate to this language |
| `show_progress` | bool | `true` | Show live recording progress |
| `whisper_model` | string | `whisper-1` | Whisper model to use |

## Environment Variables

Prefix with `SHH_`:

```bash
export SHH_OPENAI_API_KEY="sk-..."
export SHH_DEFAULT_STYLE="casual"
export SHH_DEFAULT_TRANSLATION_LANGUAGE="English"
export SHH_SHOW_PROGRESS="true"
export SHH_WHISPER_MODEL="whisper-1"
```

## Priority

Command-line flags > Environment variables > Config file > Defaults
