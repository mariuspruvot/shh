# Testing Architecture

shh uses pytest with a comprehensive testing strategy that balances coverage, speed, and reliability.

## Testing Philosophy

**Goal: 80%+ coverage with fast, reliable tests**

- **Unit tests**: Test individual functions and classes in isolation
- **Integration tests**: Test full workflows with mocked external APIs
- **No E2E tests**: Avoid real API calls in CI (cost, speed, reliability)

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests (fast, isolated)
│   ├── config/
│   │   └── test_settings.py
│   └── cli/
│       └── test_commands.py
└── integration/             # Integration tests (mocked APIs)
    └── test_recording_flow.py
```

## Shared Fixtures (`conftest.py`)

### Configuration Fixtures

**`temp_config_dir`** - Isolated config directory for tests

```python
@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir
```

**`mock_settings`** - Pre-configured Settings instance

```python
@pytest.fixture
def mock_settings(temp_config_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Settings:
    monkeypatch.setattr(
        "shh.config.settings.Settings.get_config_path",
        lambda: temp_config_dir / "settings.json",
    )
    settings = Settings(openai_api_key="sk-test-key-1234567890")
    settings.save_to_file()
    return settings
```

### Audio Fixtures

**`sample_audio_1s`** - 1 second of test audio (440Hz sine wave)

```python
@pytest.fixture
def sample_audio_1s() -> np.ndarray:
    sample_rate = 16000
    t = np.linspace(0, 1.0, sample_rate, dtype=np.float32)
    return np.sin(2 * np.pi * 440.0 * t).astype(np.float32)
```

**`mock_audio_recorder`** - Mocked AudioRecorder for CLI tests

```python
@pytest.fixture
def mock_audio_recorder(sample_audio_1s: np.ndarray) -> MagicMock:
    mock = MagicMock()
    mock.__aenter__.return_value = mock
    mock.__aexit__.return_value = None
    mock.get_audio_data.return_value = sample_audio_1s
    return mock
```

### API Mock Fixtures

**`mock_whisper_response`** - Mock OpenAI Whisper API response

```python
@pytest.fixture
def mock_whisper_response() -> MagicMock:
    mock = MagicMock()
    mock.text = "This is a test transcription."
    return mock
```

**`mock_pydantic_ai_response`** - Mock PydanticAI formatting response

```python
@pytest.fixture
def mock_pydantic_ai_response() -> MagicMock:
    mock_result = MagicMock()
    mock_result.output.text = "This is a formatted test."
    return mock_result
```

## Unit Tests

### Configuration Tests (`tests/unit/config/test_settings.py`)

**What we test:**

- Default values are correct
- Settings can be saved and loaded from JSON
- Enum validation (TranscriptionStyle, WhisperModel)
- Platform-specific config path

**Example:**

```python
def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.default_style == TranscriptionStyle.NEUTRAL
    assert settings.show_progress is True
    assert settings.whisper_model == WhisperModel.WHISPER_1

def test_save_and_load(temp_config_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    config_file = temp_config_dir / "settings.json"
    monkeypatch.setattr(
        "shh.config.settings.Settings.get_config_path",
        lambda: config_file,
    )

    # Act
    settings = Settings(openai_api_key="sk-test-key")
    settings.save_to_file()
    loaded = Settings.load_from_file()

    # Assert
    assert loaded is not None
    assert loaded.openai_api_key == "sk-test-key"
```

### CLI Command Tests (`tests/unit/cli/test_commands.py`)

**What we test:**

- Help messages display correctly
- Setup command saves API key
- Config commands (show, get, set, reset) work correctly
- Validation errors show helpful messages
- Exit codes are correct (0 for success, 1 for errors)

**Example:**

```python
def test_setup_command(temp_config_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_file = temp_config_dir / "settings.json"
    monkeypatch.setattr(
        "shh.config.settings.Settings.get_config_path",
        lambda: config_file,
    )

    # Simulate user input
    result = runner.invoke(app, ["setup"], input="sk-test-key-12345678\n")

    assert result.exit_code == 0
    assert "Setup Complete" in result.stdout
    assert "sk-***5678" in result.stdout  # Masked display

    # Verify file was saved
    settings = Settings.load_from_file()
    assert settings is not None
    assert settings.openai_api_key == "sk-test-key-12345678"
```

**Key pattern: Typer's CliRunner**

```python
from typer.testing import CliRunner

runner = CliRunner()
result = runner.invoke(app, ["config", "set", "default_style", "casual"])

assert result.exit_code == 0
assert "Updated default_style = casual" in result.stdout
```

## Integration Tests

### Recording Flow Tests (`tests/integration/test_recording_flow.py`)

**What we test:**

- Full transcription pipeline with mocked APIs
- Whisper API integration (mocked)
- PydanticAI formatting (mocked)
- Translation workflow
- Error handling (API failures)

**Example: Transcribe with Mocked Whisper API**

```python
@pytest.mark.asyncio
async def test_transcribe_audio_success(tmp_path: Path) -> None:
    # Create sample audio
    audio_data = np.random.randn(16000).astype(np.float32) * 0.5
    wav_path = save_audio_to_wav(audio_data)

    try:
        # Mock OpenAI API
        with patch("shh.adapters.whisper.client.AsyncOpenAI") as mock_client:
            mock_transcription = MagicMock()
            mock_transcription.text = "Hello, this is a test."

            mock_instance = mock_client.return_value
            mock_instance.audio.transcriptions.create = AsyncMock(
                return_value=mock_transcription
            )

            # Call transcribe_audio
            result = await transcribe_audio(wav_path, "sk-test-key")

            assert result == "Hello, this is a test."
            mock_instance.audio.transcriptions.create.assert_called_once()

    finally:
        wav_path.unlink(missing_ok=True)
```

**Example: Full Pipeline Test**

```python
@pytest.mark.asyncio
async def test_full_pipeline_mock(tmp_path: Path) -> None:
    audio_data = np.random.randn(16000).astype(np.float32) * 0.5
    wav_path = save_audio_to_wav(audio_data)

    try:
        # Step 1: Mock Whisper API
        with patch("shh.adapters.whisper.client.AsyncOpenAI") as mock_whisper:
            mock_transcription = MagicMock()
            mock_transcription.text = "Um, this is a test transcription."

            mock_whisper_instance = mock_whisper.return_value
            mock_whisper_instance.audio.transcriptions.create = AsyncMock(
                return_value=mock_transcription
            )

            # Transcribe
            raw_text = await transcribe_audio(wav_path, "sk-test-key")
            assert raw_text == "Um, this is a test transcription."

            # Step 2: Mock PydanticAI for formatting
            with patch("shh.adapters.llm.formatter.OpenAIChatModel"):
                with patch("shh.adapters.llm.formatter.Agent") as mock_agent_class:
                    mock_agent = MagicMock()
                    mock_result = MagicMock()
                    mock_result.output.text = "This is a test transcription."

                    mock_agent.run = AsyncMock(return_value=mock_result)
                    mock_agent_class.return_value = mock_agent

                    # Format
                    formatted = await format_transcription(
                        raw_text,
                        style=TranscriptionStyle.CASUAL,
                        api_key="sk-test-key",
                    )

                    assert formatted.text == "This is a test transcription."

    finally:
        wav_path.unlink(missing_ok=True)
```

## Testing Async Code

### pytest-asyncio

All async tests use `@pytest.mark.asyncio` decorator:

```python
@pytest.mark.asyncio
async def test_async_function() -> None:
    result = await some_async_function()
    assert result == expected
```

**Configuration (pyproject.toml):**

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### Mocking Async Functions

Use `AsyncMock` for async functions:

```python
from unittest.mock import AsyncMock

mock_instance.audio.transcriptions.create = AsyncMock(
    return_value=mock_transcription
)
```

## Mocking Strategies

### Why We Mock External APIs

- **Speed**: API calls are slow (hundreds of ms), mocks are instant
- **Cost**: Real API calls cost money
- **Reliability**: External APIs can fail or rate-limit
- **Isolation**: Test our code, not OpenAI's

### How We Mock

**1. Patch at Import Point**

```python
with patch("shh.adapters.whisper.client.AsyncOpenAI") as mock_client:
    # Setup mock
    mock_instance = mock_client.return_value
    mock_instance.audio.transcriptions.create = AsyncMock(...)

    # Call code under test
    result = await transcribe_audio(...)
```

**2. Mock Return Values**

```python
mock_transcription = MagicMock()
mock_transcription.text = "Expected transcription"

mock_instance.audio.transcriptions.create = AsyncMock(
    return_value=mock_transcription
)
```

**3. Verify Calls**

```python
result = await transcribe_audio(wav_path, "sk-test-key")

# Verify API was called correctly
mock_instance.audio.transcriptions.create.assert_called_once()

# Verify call arguments (if needed)
call_args = mock_instance.audio.transcriptions.create.call_args
assert call_args.kwargs["file"] is not None
```

## Coverage

### Target: 80%+ Coverage

Run coverage with:

```bash
uv run poe test-cov
```

**Output:**

```
---------- coverage: platform darwin, python 3.11.9 -----------
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
shh/__init__.py                             0      0   100%
shh/adapters/audio/processor.py            12      0   100%
shh/adapters/audio/recorder.py             45      3    93%
shh/adapters/whisper/client.py             20      1    95%
shh/cli/commands/config.py                 75      5    93%
shh/config/settings.py                     35      2    94%
-----------------------------------------------------------
TOTAL                                     387     25    94%
```

### What We Don't Cover

- Error paths that are hard to trigger (rare edge cases)
- CLI display code (Rich output formatting)
- Platform-specific code paths

### Codecov Integration

Coverage is uploaded to Codecov on every CI run:

```yaml
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v4
  with:
    token: ${{ secrets.CODECOV_TOKEN }}
    files: ./coverage.xml
```

## Testing Best Practices

### 1. Arrange-Act-Assert Pattern

```python
def test_example():
    # Arrange
    settings = Settings(openai_api_key="sk-test")

    # Act
    result = settings.openai_api_key

    # Assert
    assert result == "sk-test"
```

### 2. Descriptive Test Names

```python
# ✅ Good - describes what is tested
def test_setup_command_saves_api_key()

# ❌ Bad - vague
def test_setup()
```

### 3. One Assertion Per Concept

```python
# ✅ Good
def test_config_set_valid():
    result = runner.invoke(app, ["config", "set", "default_style", "casual"])
    assert result.exit_code == 0
    assert "Updated default_style = casual" in result.stdout

# ⚠️ Acceptable (related assertions)
def test_multiple_related_assertions():
    settings = Settings()
    assert settings.default_style == TranscriptionStyle.NEUTRAL
    assert settings.show_progress is True
```

### 4. Isolate Tests with Fixtures

```python
@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir

def test_with_isolated_config(temp_config_dir: Path):
    # Each test gets its own config directory
    # No interference between tests
    pass
```

### 5. Clean Up Resources

```python
def test_with_cleanup(tmp_path: Path):
    wav_path = tmp_path / "audio.wav"

    try:
        # Use resource
        save_audio_to_wav(audio_data, wav_path)
    finally:
        # Always clean up
        wav_path.unlink(missing_ok=True)
```

## Running Tests

### Run All Tests

```bash
uv run poe test
```

### Run Unit Tests Only

```bash
uv run poe test-unit
```

### Run Integration Tests Only

```bash
uv run poe test-integration
```

### Run with Coverage

```bash
uv run poe test-cov
```

### Run Specific Test File

```bash
pytest tests/unit/config/test_settings.py
```

### Run Specific Test

```bash
pytest tests/unit/config/test_settings.py::test_settings_defaults
```

### Verbose Output

```bash
pytest -v
```

## CI Integration

Tests run on every push and PR via GitHub Actions:

```yaml
- name: Run type checking
  run: uv run poe type

- name: Run linting
  run: uv run poe lint

- name: Run tests with coverage
  run: uv run poe test-cov
```

**Matrix testing:**

- **OS**: Ubuntu, macOS, Windows
- **Python**: 3.11, 3.12, 3.13

This ensures cross-platform compatibility.

## Next Steps

- [Architecture Overview](overview.md) - High-level architecture
- [Design Decisions](design-decisions.md) - Why we made specific choices
- [API Reference](../api-reference/core.md) - Detailed code documentation
