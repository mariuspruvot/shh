# Contributing to shh

Thank you for considering contributing to shh! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful and inclusive. We're all here to build something useful together.

## Getting Started

### Prerequisites

- Python 3.11, 3.12, or 3.13
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Git
- An OpenAI API key for testing (if working on API integrations)

### Development Setup

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/YOUR_USERNAME/shh.git
   cd shh
   ```

2. **Create a virtual environment and install dependencies**

   ```bash
   # Using uv (recommended)
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e ".[dev]"

   # Or using pip
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

3. **Install pre-commit hooks**

   ```bash
   pre-commit install
   ```

   This ensures code quality checks run automatically before commits.

4. **Configure your API key (for testing)**

   ```bash
   shh setup
   # Or use environment variable:
   export SHH_OPENAI_API_KEY="sk-..."
   ```

### Verify Setup

Run the test suite to ensure everything is working:

```bash
uv run poe test
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

**Branch naming conventions:**

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or improvements

### 2. Make Changes

Follow the [Code Style](#code-style) and [Architecture Guidelines](#architecture-guidelines) below.

### 3. Run Quality Checks

Before committing, run all checks:

```bash
# Run all checks (type + lint + test)
uv run poe check

# Or run individually:
uv run poe type      # Type checking (mypy)
uv run poe lint      # Linting (ruff)
uv run poe test      # Tests (pytest)
uv run poe format    # Auto-format code
```

**Pre-commit hooks will also run automatically** when you commit.

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add new feature"
```

**Commit message format:**

```
<type>: <description>

[optional body]
```

**Types:**

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Test additions or improvements
- `chore:` - Maintenance tasks

**Examples:**

```
feat: add support for custom Whisper models
fix: handle API timeout errors gracefully
docs: update installation instructions
refactor: simplify audio recording logic
test: add integration tests for translation
```

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Style

### Type Hints

**All functions must have complete type hints:**

```python
# ✅ Good
def transcribe_audio(audio_path: Path, api_key: str) -> str:
    ...

async def format_text(text: str, style: TranscriptionStyle) -> FormattedTranscription:
    ...

# ❌ Bad - missing type hints
def transcribe_audio(audio_path, api_key):
    ...
```

### Mypy Strict Mode

All code must pass `mypy --strict`:

```bash
uv run poe type
```

This enforces:

- Complete type hints
- No implicit `Any`
- No untyped function calls

### Linting and Formatting

We use **ruff** for linting and formatting:

```bash
# Check for issues
uv run poe lint

# Auto-fix issues
uv run poe lint-fix

# Format code
uv run poe format
```

**Configured rules (pyproject.toml):**

- Line length: 100 characters
- Import sorting (isort-compatible)
- Python 3.11+ syntax
- Strict checks for common issues

### Docstrings

Use Google-style docstrings for public functions:

```python
def transcribe_audio(audio_file_path: Path, api_key: str) -> str:
    """Transcribe audio file using OpenAI Whisper API.

    Args:
        audio_file_path: Path to WAV file to transcribe
        api_key: OpenAI API key

    Returns:
        Transcribed text

    Raises:
        TranscriptionError: If API call fails
    """
    ...
```

## Architecture Guidelines

### Layered Architecture

shh follows a **pragmatic layered architecture**:

```
CLI Layer (Typer)     → User interaction, commands
    ↓
Core Layer            → Business logic, orchestration
    ↓
Adapters Layer        → External APIs, hardware, clipboard
```

**Dependency Rule: CLI → Core → Adapters (unidirectional)**

### Where to Add Code

**CLI Layer (`shh/cli/`)**

Add here if:

- It's a new command or subcommand
- It handles user input or displays output
- It uses Typer or Rich

**Core Layer (`shh/core/`)**

Add here if:

- It's business logic or orchestration
- It has no external dependencies
- It's framework-agnostic

**Adapters Layer (`shh/adapters/`)**

Add here if:

- It interacts with external APIs (OpenAI, etc.)
- It uses hardware (microphone, clipboard)
- It does file I/O

### Async/Await

**Use async for all I/O operations:**

```python
# ✅ Good - async I/O
async def transcribe_audio(path: Path) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(...)
    return response.text

# ❌ Bad - blocking I/O
def transcribe_audio(path: Path) -> str:
    response = requests.post(...)  # Blocks event loop
    return response.text
```

**Bridge sync to async in CLI:**

```python
@app.command()
def my_command() -> None:
    """Typer commands must be sync."""
    asyncio.run(my_async_command())

async def my_async_command() -> None:
    """Actual logic is async."""
    ...
```

### Error Handling

**Fail fast with clear error messages:**

```python
# ✅ Good
try:
    settings = Settings.load_from_file()
except FileNotFoundError:
    console.print("[red]No config found. Run 'shh setup' first.[/red]")
    raise typer.Exit(code=1)

# ❌ Bad - generic error
try:
    settings = Settings.load_from_file()
except Exception as e:
    print(f"Error: {e}")
```

**Translate external errors at adapter boundaries:**

```python
# In adapter layer
try:
    response = await client.post(...)
except httpx.HTTPError as e:
    raise TranscriptionError(f"API call failed: {e}") from e
```

### Resource Cleanup

**Always clean up resources:**

```python
# ✅ Good - async context manager
async with AudioRecorder() as recorder:
    await recorder.record()
# Cleanup happens automatically

# ✅ Good - try/finally
wav_path = save_audio_to_wav(audio_data)
try:
    result = await transcribe_audio(wav_path)
finally:
    wav_path.unlink(missing_ok=True)  # Always delete

# ❌ Bad - no cleanup
wav_path = save_audio_to_wav(audio_data)
result = await transcribe_audio(wav_path)
# File left on disk!
```

## Testing

### Test Requirements

**All new code must have tests:**

- **Unit tests** for isolated functions
- **Integration tests** for workflows
- **Target: 80%+ coverage**

### Writing Tests

**Test file structure:**

```
tests/
├── unit/
│   └── your_module/
│       └── test_your_function.py
└── integration/
    └── test_your_workflow.py
```

**Example unit test:**

```python
def test_settings_defaults() -> None:
    """Test that Settings has correct default values."""
    settings = Settings()

    assert settings.default_style == TranscriptionStyle.NEUTRAL
    assert settings.show_progress is True
```

**Example integration test:**

```python
@pytest.mark.asyncio
async def test_transcribe_audio_with_mock() -> None:
    """Test transcription with mocked Whisper API."""
    with patch("shh.adapters.whisper.client.AsyncOpenAI") as mock:
        mock_instance = mock.return_value
        mock_instance.audio.transcriptions.create = AsyncMock(
            return_value=MagicMock(text="Test result")
        )

        result = await transcribe_audio(Path("test.wav"), "sk-test")

        assert result == "Test result"
```

### Running Tests

```bash
# Run all tests
uv run poe test

# Run unit tests only
uv run poe test-unit

# Run with coverage
uv run poe test-cov

# Run specific test
pytest tests/unit/config/test_settings.py::test_settings_defaults
```

### Test Guidelines

1. **Use descriptive names**: `test_config_set_updates_value` not `test_1`
2. **Arrange-Act-Assert pattern**:
   ```python
   def test_example():
       # Arrange
       settings = Settings()
       # Act
       result = settings.default_style
       # Assert
       assert result == TranscriptionStyle.NEUTRAL
   ```
3. **Mock external APIs**: Never make real API calls in tests
4. **Isolate tests**: Use fixtures for shared setup
5. **Test behavior, not implementation**: Focus on what the code does, not how

## Pull Request Process

### Before Submitting

1. ✅ Run all quality checks: `uv run poe check`
2. ✅ Add tests for new functionality
3. ✅ Update documentation if needed
4. ✅ Ensure CI passes (pre-commit hooks)

### PR Template

When creating a PR, include:

**Description:**

- What does this PR do?
- Why is this change needed?

**Type of change:**

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

**Checklist:**

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Type checking passes (`uv run poe type`)
- [ ] Linting passes (`uv run poe lint`)
- [ ] All tests pass (`uv run poe test`)

### Review Process

1. **Automated checks** will run (CI, pre-commit.ci)
2. **Manual review** by maintainers
3. **Feedback** may be requested
4. **Merge** once approved and all checks pass

## Common Tasks

### Adding a New Command

1. Create command file in `shh/cli/commands/`
2. Add command to `shh/cli/app.py`
3. Add tests in `tests/unit/cli/test_commands.py`
4. Update documentation in `docs/user-guide/commands.md`

**Example:**

```python
# shh/cli/commands/my_command.py
import typer

def my_command() -> None:
    """My new command."""
    typer.echo("Hello from my command!")

# shh/cli/app.py
from shh.cli.commands.my_command import my_command

app.command()(my_command)
```

### Adding a New Adapter

1. Create adapter file in `shh/adapters/`
2. Write async functions with proper error handling
3. Add integration tests with mocked external APIs
4. Update API reference in `docs/api-reference/adapters.md`

### Updating Configuration

1. Update `shh/config/settings.py` (Settings class)
2. Update config commands in `shh/cli/commands/config.py`
3. Add tests in `tests/unit/config/test_settings.py`
4. Update `docs/user-guide/configuration.md`

## Documentation

### When to Update Docs

- **New features**: Update user guide and API reference
- **Configuration changes**: Update configuration docs
- **Architecture changes**: Update architecture docs
- **Breaking changes**: Update README and migration guide

### Building Docs Locally

```bash
# Install docs dependencies
uv pip install -e ".[dev]"

# Serve docs locally
mkdocs serve

# Open http://localhost:8000 in browser
```

### Docs Structure

```
docs/
├── index.md                    # Home page
├── getting-started/           # Installation, quickstart
├── user-guide/               # Commands, config, usage
├── api-reference/            # Auto-generated from docstrings
└── architecture/             # Design docs, testing
```

## Getting Help

- **Questions**: Open a [Discussion](https://github.com/mpruvot/shh/discussions)
- **Bugs**: Open an [Issue](https://github.com/mpruvot/shh/issues)
- **Suggestions**: Open a [Discussion](https://github.com/mpruvot/shh/discussions)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
