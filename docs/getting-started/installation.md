# Installation

Requires Python 3.11 or higher.

## Prerequisites

- Python 3.11, 3.12, or 3.13
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- Microphone (for recording)

## Using uv

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install shh:

```bash
# Clone the repository
git clone https://github.com/mpruvot/shh.git
cd shh

# Install in editable mode
uv pip install -e .
```

## Using pip

```bash
# Clone the repository
git clone https://github.com/mpruvot/shh.git
cd shh

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode
pip install -e .
```

## Development Installation

For development, install with dev dependencies:

```bash
# Using uv
uv pip install -e ".[dev]"

# Using pip
pip install -e ".[dev]"
```

This includes:
- pytest and testing tools
- mypy for type checking
- ruff for linting and formatting
- pre-commit hooks

## Verify Installation

```bash
shh --help
```

## Next Steps

- [Configure your API key](../getting-started/quickstart.md#setup)
- [Record your first transcription](../getting-started/quickstart.md#basic-usage)

## Troubleshooting

### Command not found

If `shh` isn't found, ensure your virtual environment is activated:

```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Audio issues

If recording doesn't work, check your microphone permissions:

- **macOS**: System Preferences → Security & Privacy → Microphone
- **Linux**: Ensure ALSA or PulseAudio is configured
- **Windows**: Settings → Privacy → Microphone

### Import errors

If you see import errors, reinstall dependencies:

```bash
uv pip install -e .  # or pip install -e .
```
