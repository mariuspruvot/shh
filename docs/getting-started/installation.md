# Installation

## Quick Install (Recommended)

Install using [pipx](https://pipx.pypa.io/) for an isolated, global installation:

```bash
pipx install shh-cli
```

Then run:

```bash
shh setup  # Configure your OpenAI API key
shh        # Start recording!
```

## Prerequisites

- Python 3.11+
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- Microphone (for recording)

## Alternative: Install from Source

**Using uv:**

```bash
git clone https://github.com/mariuspruvot/shh.git
cd shh
uv pip install -e .
```

**Using pip:**

```bash
git clone https://github.com/mariuspruvot/shh.git
cd shh
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

## Development Installation

For development with test/lint tools:

```bash
uv pip install -e ".[dev]"
```

## Troubleshooting

**Command not found:**
```bash
# With pipx - ensure ~/.local/bin is in PATH
export PATH="$HOME/.local/bin:$PATH"

# From source - activate venv
source .venv/bin/activate
```

**Microphone permissions:**
- **macOS**: System Preferences → Privacy → Microphone
- **Linux**: Check ALSA/PulseAudio configuration
- **Windows**: Settings → Privacy → Microphone

## Next Steps

Continue to [Quick Start](quickstart.md) to configure your API key and record your first transcription.
