# Commands Reference

## `shh`

Start recording. Press Enter to stop.

**Options:**

- `--style, -s` - Formatting style: `neutral`, `casual`, `business`
- `--translate, -t` - Target language for translation
- `--duration, -d` - Recording duration in seconds

**Examples:**

```bash
shh
shh --style casual
shh --duration 60
shh --style business --translate French
```

---

## `shh setup`

Configure OpenAI API key interactively.

```bash
shh setup
```

---

## `shh config`

### `shh config show`

Display all configuration settings.

```bash
shh config show
```

### `shh config get <key>`

Get a specific configuration value.

```bash
shh config get default_style
```

Available keys: `openai_api_key`, `default_style`, `show_progress`, `whisper_model`

### `shh config set <key> <value>`

Update a configuration setting.

```bash
shh config set default_style casual
shh config set show_progress true
```

### `shh config reset`

Reset all settings to defaults (requires confirmation).

```bash
shh config reset
```

---

## Global Options

- `--help` - Show help message
- `--version` - Show version information
