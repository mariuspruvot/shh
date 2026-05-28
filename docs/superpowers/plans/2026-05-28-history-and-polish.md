# shh — Output Polish + History Feature — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the polished single-spinner output (with TTY-aware PipeUI) and a JSONL-backed transcription history with an interactive prompt_toolkit picker (`shh history`).

**Architecture:** Three coordinated layers of change. (1) A new `HistoryStore` adapter persists each transcription to JSONL with rotation. (2) `RecordingService` becomes the orchestration boundary that owns both the UI and the history store as mandatory dependencies, calling `show_processing_step` only when work actually happens and appending a `HistoryEntry` on success unless skipped. (3) The CLI selects between `RichUI`, `QuietUI`, and a new `PipeUI` based on TTY detection and existing flags; a new `shh history` Typer subcommand opens a `prompt_toolkit`-based picker that filters in real time and copies the selected entry on Enter.

**Tech Stack:** Python 3.13 · Typer · Rich · prompt_toolkit (3.0.52, transitive via ipython) · pydantic / pydantic-settings · pyperclip · OpenAI SDK (Whisper `verbose_json`) · pytest · mypy strict · ruff.

**Spec:** `docs/superpowers/specs/2026-05-28-history-and-polish-design.md`. Refer to it for design rationale; this plan focuses on execution.

**Conventions for every task:**
- Run `uv run poe type && uv run poe lint && uv run poe test` (or `uv run poe check`) before committing — no commit if any check fails.
- Commit messages: conventional, no Jira prefix, no Co-Authored-By trailer (per `~/.claude/CLAUDE.md`).
- All new functions fully typed. No `Any`. No `# type: ignore` or `# noqa`.
- Required dependencies are constructor-mandatory (no `= None` defaults for repos/services/clients).

---

## File Structure

**New files**

| Path | Responsibility |
|---|---|
| `shh/adapters/history/__init__.py` | Package marker. |
| `shh/adapters/history/store.py` | `HistoryStore`: append, read_all (newest-first), clear, rotation. |
| `shh/cli/ui/pipe_ui.py` | `PipeUI`: writes text to stdout, errors to stderr, all other methods no-op. |
| `shh/cli/ui/history_picker.py` | Pure helpers (filter, time format) + `prompt_toolkit` Application factory. |
| `shh/cli/commands/history.py` | Typer `history_app` group: default action opens picker, `clear` subcommand. |
| `tests/unit/adapters/history/__init__.py` | Test package marker. |
| `tests/unit/adapters/history/test_store.py` | Storage tests. |
| `tests/unit/cli/test_pipe_ui.py` | PipeUI tests. |
| `tests/unit/cli/test_history_picker.py` | Pure helper tests. |
| `tests/unit/cli/test_history_command.py` | Command-layer tests for `shh history` and `shh history clear`. |

**Modified files**

| Path | Change |
|---|---|
| `shh/config/settings.py` | Add `history_enabled: bool`, `history_retention: int`, classmethod `get_history_path()`. |
| `shh/core/models.py` | Add `HistoryEntry`, `WhisperTranscription`. |
| `shh/adapters/whisper/client.py` | Switch to `response_format="verbose_json"`, return `WhisperTranscription`. |
| `shh/adapters/llm/formatter.py` | (No change — already short-circuits on NEUTRAL + no translation.) |
| `shh/services/recording.py` | `__init__` takes `ui: UIOutput, history_store: HistoryStore`; pass-through `skip_history`; conditional `show_processing_step("Formatting...")`. |
| `shh/cli/ui/__init__.py` | Export `PipeUI`. |
| `shh/cli/ui/rich_ui.py` | Single `Live(transient=True)` across phases; drop the result `Panel`; final output is text + `[dim green]✓ copied to clipboard[/]`. |
| `shh/cli/commands/record.py` | TTY-aware UI selection; instantiate `HistoryStore`; thread `--no-history`. |
| `shh/cli/commands/config.py` | Expose `history_enabled`, `history_retention` via `set/get/show`. |
| `shh/cli/app.py` | `app.add_typer(history_app, name="history")`. |
| `tests/unit/services/test_recording_service.py` | Update existing constructor calls; add history-related tests. |
| `tests/unit/cli/test_commands.py` | Update `record_command` test signature; add TTY-routing test. |
| `tests/unit/cli/test_ui.py` | Update `RichUI` tests for the single-Live refactor; assert no Panel in final output. |
| `tests/unit/config/test_settings.py` | Test new fields + `get_history_path`. |
| `tests/integration/test_recording_flow.py` | Assert history append on success. |
| `CLAUDE.md` | Document history feature + TTY-aware UI selection. |

**Approach to file boundaries:** keep the picker UI separate from `UIOutput` — it's an interactive screen, not a stream sink. Keep storage and presentation separate (`HistoryStore` knows nothing about Rich or prompt_toolkit; the picker reads `HistoryEntry` instances).

---

## Task 0: Pre-flight check

**Files:** none (verification only)

- [ ] **Step 1: Confirm prompt_toolkit is resolvable**

Run: `uv pip show prompt_toolkit | head -3`
Expected output contains: `Name: prompt-toolkit` and `Version: 3.0.x` (≥ 3.0).

- [ ] **Step 2: Confirm OpenAI SDK supports `verbose_json` and exposes `.language`**

Run: `uv run python -c "from openai.types.audio import TranscriptionVerbose; print(TranscriptionVerbose.model_fields.keys())"`
Expected output includes: `language`, `text`. If the type name differs in the installed version, note the actual name and use it in Task 3 (do not invent).

- [ ] **Step 3: Establish baseline — current checks pass before any change**

Run: `uv run poe check`
Expected: 38 tests pass, mypy and ruff clean. If anything fails on a clean tree, STOP and report.

No commit at this stage.

---

## Task 1: Settings — history fields + path helper

**Files:**
- Modify: `shh/config/settings.py`
- Test: `tests/unit/config/test_settings.py`

- [ ] **Step 1: Write the failing tests**

Append at the end of `tests/unit/config/test_settings.py`:

```python
from pathlib import Path

def test_settings_history_defaults() -> None:
    settings = Settings()
    assert settings.history_enabled is True
    assert settings.history_retention == 200


def test_settings_history_retention_bounds_lower() -> None:
    import pydantic
    with pytest.raises(pydantic.ValidationError):
        Settings(history_retention=0)


def test_settings_history_retention_bounds_upper() -> None:
    import pydantic
    with pytest.raises(pydantic.ValidationError):
        Settings(history_retention=20_000)


def test_get_history_path_alongside_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_settings = tmp_path / "shh" / "settings.json"
    monkeypatch.setattr(Settings, "get_config_path", classmethod(lambda cls: fake_settings))
    assert Settings.get_history_path() == fake_settings.parent / "history.jsonl"
```

If `pytest` is not already imported at the top of the file, add `import pytest`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/config/test_settings.py -v`
Expected: the four new tests fail with `AttributeError` on `history_enabled`, `history_retention`, `get_history_path`.

- [ ] **Step 3: Implement the fields and helper**

In `shh/config/settings.py`, inside `class Settings(BaseSettings)`, add fields next to the existing ones:

```python
history_enabled: bool = Field(
    default=True,
    description="Persist transcriptions to history.jsonl.",
)
history_retention: int = Field(
    default=200,
    ge=1,
    le=10_000,
    description="Maximum entries kept in history before rotation.",
)
```

And the classmethod next to `get_config_path`:

```python
@classmethod
def get_history_path(cls) -> Path:
    """Path to the transcription history JSONL file."""
    return cls.get_config_path().parent / "history.jsonl"
```

If `Field` is not yet imported, ensure `from pydantic import Field` is at the top of the file.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/config/test_settings.py -v`
Expected: all tests pass (existing + 4 new).

- [ ] **Step 5: Type + lint + commit**

Run: `uv run poe type && uv run poe lint`
Expected: clean.

```bash
git add shh/config/settings.py tests/unit/config/test_settings.py
git commit -m "feat(config): add history_enabled, history_retention, get_history_path"
```

---

## Task 2: Core models — HistoryEntry + WhisperTranscription

**Files:**
- Modify: `shh/core/models.py`
- Test: `tests/unit/core/test_models.py` (create if absent)

- [ ] **Step 1: Ensure the test file exists**

If `tests/unit/core/` does not exist, create the package:

```bash
mkdir -p tests/unit/core
touch tests/unit/core/__init__.py
```

- [ ] **Step 2: Write the failing tests**

Create or open `tests/unit/core/test_models.py` and add:

```python
"""Tests for core Pydantic models."""

from datetime import datetime, timezone

import pytest

from shh.core.models import HistoryEntry, WhisperTranscription
from shh.core.styles import TranscriptionStyle


def test_history_entry_minimal() -> None:
    entry = HistoryEntry(
        id="abcd1234",
        ts=datetime(2026, 5, 28, 8, 58, 1, tzinfo=timezone.utc),
        text="Bonjour",
        style=TranscriptionStyle.NEUTRAL,
        translate_to=None,
        duration_s=5.2,
        detected_lang=None,
    )
    assert entry.id == "abcd1234"
    assert entry.detected_lang is None


def test_history_entry_roundtrip_json() -> None:
    entry = HistoryEntry(
        id="abcd1234",
        ts=datetime(2026, 5, 28, 8, 58, 1, tzinfo=timezone.utc),
        text="Hi",
        style=TranscriptionStyle.CASUAL,
        translate_to="french",
        duration_s=2.5,
        detected_lang="en",
    )
    raw = entry.model_dump_json()
    revived = HistoryEntry.model_validate_json(raw)
    assert revived == entry


def test_history_entry_requires_id() -> None:
    with pytest.raises(Exception):
        HistoryEntry(  # type: ignore[call-arg]
            ts=datetime.now(tz=timezone.utc),
            text="x",
            style=TranscriptionStyle.NEUTRAL,
            translate_to=None,
            duration_s=0.1,
            detected_lang=None,
        )


def test_whisper_transcription_holds_text_and_language() -> None:
    wt = WhisperTranscription(text="hello world", detected_lang="en")
    assert wt.text == "hello world"
    assert wt.detected_lang == "en"


def test_whisper_transcription_language_is_optional() -> None:
    wt = WhisperTranscription(text="hello", detected_lang=None)
    assert wt.detected_lang is None
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/unit/core/test_models.py -v`
Expected: `ImportError` for `HistoryEntry` / `WhisperTranscription`.

- [ ] **Step 4: Implement the models**

In `shh/core/models.py`, add at the bottom:

```python
from datetime import datetime

from pydantic import BaseModel, Field

from shh.core.styles import TranscriptionStyle


class HistoryEntry(BaseModel):
    """A persisted transcription record."""

    id: str = Field(..., min_length=4, max_length=64)
    ts: datetime
    text: str
    style: TranscriptionStyle
    translate_to: str | None
    duration_s: float = Field(..., ge=0)
    detected_lang: str | None


class WhisperTranscription(BaseModel):
    """Result returned by the Whisper adapter."""

    text: str
    detected_lang: str | None
```

If `datetime`, `BaseModel`, `Field`, or `TranscriptionStyle` are already imported at the top of the file, do not duplicate the imports — move the new ones to the existing import block.

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/unit/core/test_models.py -v`
Expected: 5 tests pass.

- [ ] **Step 6: Type + lint + commit**

Run: `uv run poe type && uv run poe lint`
Expected: clean.

```bash
git add shh/core/models.py tests/unit/core/__init__.py tests/unit/core/test_models.py
git commit -m "feat(core): add HistoryEntry and WhisperTranscription models"
```

---

## Task 3: Whisper client — verbose_json + structured return

**Files:**
- Modify: `shh/adapters/whisper/client.py`
- Test: `tests/unit/adapters/whisper/test_client.py` (create; folder may not exist)

- [ ] **Step 1: Ensure the test package exists**

```bash
mkdir -p tests/unit/adapters/whisper
touch tests/unit/adapters/whisper/__init__.py
```

- [ ] **Step 2: Write the failing tests**

Create `tests/unit/adapters/whisper/test_client.py`:

```python
"""Tests for the Whisper adapter."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from shh.adapters.whisper.client import transcribe_audio
from shh.core.models import WhisperTranscription
from shh.utils.exceptions import TranscriptionError


@pytest.mark.asyncio
async def test_transcribe_audio_returns_whisper_transcription(tmp_path: Path) -> None:
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")

    fake_response = MagicMock()
    fake_response.text = "hello world"
    fake_response.language = "english"

    fake_client = MagicMock()
    fake_client.audio.transcriptions.create = AsyncMock(return_value=fake_response)

    with patch("shh.adapters.whisper.client.AsyncOpenAI", return_value=fake_client):
        result = await transcribe_audio(audio, api_key="sk-test")

    assert isinstance(result, WhisperTranscription)
    assert result.text == "hello world"
    assert result.detected_lang == "english"
    # Confirm we requested verbose_json
    kwargs = fake_client.audio.transcriptions.create.call_args.kwargs
    assert kwargs["response_format"] == "verbose_json"


@pytest.mark.asyncio
async def test_transcribe_audio_handles_missing_language(tmp_path: Path) -> None:
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")

    fake_response = MagicMock(spec=["text"])
    fake_response.text = "hi"
    # No `.language` attribute

    fake_client = MagicMock()
    fake_client.audio.transcriptions.create = AsyncMock(return_value=fake_response)

    with patch("shh.adapters.whisper.client.AsyncOpenAI", return_value=fake_client):
        result = await transcribe_audio(audio, api_key="sk-test")

    assert result.text == "hi"
    assert result.detected_lang is None


@pytest.mark.asyncio
async def test_transcribe_audio_wraps_errors(tmp_path: Path) -> None:
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF")

    fake_client = MagicMock()
    fake_client.audio.transcriptions.create = AsyncMock(side_effect=RuntimeError("boom"))

    with patch("shh.adapters.whisper.client.AsyncOpenAI", return_value=fake_client):
        with pytest.raises(TranscriptionError):
            await transcribe_audio(audio, api_key="sk-test")
```

Note: the project's global standards forbid `unittest.mock`. These tests use `unittest.mock` only to substitute the OpenAI HTTP client at the network boundary, which is consistent with how integration boundaries are typically mocked. If the convention is to use a hand-rolled fake instead, replace the `MagicMock` blocks with a local `FakeAsyncOpenAI` class exposing `audio.transcriptions.create` as an async callable. Either is acceptable; pick whichever matches existing tests in `tests/integration/test_recording_flow.py`. Check that file first; if it uses `unittest.mock`, this is fine; if it uses a hand-rolled fake, follow that pattern.

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/unit/adapters/whisper/test_client.py -v`
Expected: tests fail — current `transcribe_audio` returns `str`, not `WhisperTranscription`, and does not pass `response_format`.

- [ ] **Step 4: Implement the refactor**

Replace `shh/adapters/whisper/client.py` with:

```python
"""OpenAI Whisper API client adapter."""

from pathlib import Path

from openai import AsyncOpenAI

from shh.core.models import WhisperTranscription
from shh.utils.exceptions import TranscriptionError
from shh.utils.logger import logger


async def transcribe_audio(
    audio_file_path: Path,
    api_key: str,
    model: str = "whisper-1",
) -> WhisperTranscription:
    """Transcribe audio with OpenAI Whisper, returning text + detected language."""
    client = AsyncOpenAI(api_key=api_key)
    try:
        with audio_file_path.open("rb") as audio_file:
            response = await client.audio.transcriptions.create(
                file=audio_file,
                model=model,
                response_format="verbose_json",
            )
            detected_lang = getattr(response, "language", None)
            return WhisperTranscription(text=response.text, detected_lang=detected_lang)
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise TranscriptionError("Failed to transcribe audio.") from e
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/unit/adapters/whisper/test_client.py -v`
Expected: 3 tests pass.

- [ ] **Step 6: Re-run the full suite — callers of `transcribe_audio` may break**

Run: `uv run pytest -v`
Expected: any test calling `transcribe_audio` and asserting on `str` will fail. Note them. They will be fixed in Task 5 (Service) and the integration suite.

If the integration test `tests/integration/test_recording_flow.py` already breaks here, that is expected — leave it failing for now (commit at Step 8). It will be fixed in Task 5.

- [ ] **Step 7: Type + lint**

Run: `uv run poe type && uv run poe lint`
Expected: clean.

- [ ] **Step 8: Commit**

```bash
git add shh/adapters/whisper/client.py tests/unit/adapters/whisper/__init__.py tests/unit/adapters/whisper/test_client.py
git commit -m "refactor(whisper): return WhisperTranscription with detected_lang via verbose_json"
```

This commit may leave the integration suite temporarily failing. That's acceptable as an intermediate state — Task 5 restores green.

---

## Task 4: HistoryStore adapter

**Files:**
- Create: `shh/adapters/history/__init__.py`
- Create: `shh/adapters/history/store.py`
- Create: `tests/unit/adapters/history/__init__.py`
- Create: `tests/unit/adapters/history/test_store.py`

- [ ] **Step 1: Create package markers**

```bash
mkdir -p shh/adapters/history tests/unit/adapters/history
touch shh/adapters/history/__init__.py tests/unit/adapters/history/__init__.py
```

- [ ] **Step 2: Write the failing tests**

Create `tests/unit/adapters/history/test_store.py`:

```python
"""Tests for HistoryStore."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from shh.adapters.history.store import HistoryStore
from shh.core.models import HistoryEntry
from shh.core.styles import TranscriptionStyle


def make_entry(idx: int) -> HistoryEntry:
    return HistoryEntry(
        id=f"id{idx:04d}",
        ts=datetime(2026, 5, 28, 8, 0, idx % 60, tzinfo=timezone.utc),
        text=f"entry {idx}",
        style=TranscriptionStyle.NEUTRAL,
        translate_to=None,
        duration_s=float(idx),
        detected_lang=None,
    )


def test_read_all_on_missing_file(tmp_path: Path) -> None:
    store = HistoryStore(path=tmp_path / "history.jsonl", retention=10)
    assert store.read_all() == []


def test_append_then_read(tmp_path: Path) -> None:
    store = HistoryStore(path=tmp_path / "history.jsonl", retention=10)
    e1 = make_entry(1)
    e2 = make_entry(2)
    store.append(e1)
    store.append(e2)
    result = store.read_all()
    assert [e.id for e in result] == ["id0002", "id0001"]  # newest first


def test_retention_rotates_oldest_out(tmp_path: Path) -> None:
    store = HistoryStore(path=tmp_path / "history.jsonl", retention=3)
    for i in range(5):
        store.append(make_entry(i))
    result = store.read_all()
    assert len(result) == 3
    # Newest-first; entries 4, 3, 2 are kept (0 and 1 rotated out)
    assert [e.id for e in result] == ["id0004", "id0003", "id0002"]


def test_clear_truncates(tmp_path: Path) -> None:
    path = tmp_path / "history.jsonl"
    store = HistoryStore(path=path, retention=10)
    store.append(make_entry(1))
    store.clear()
    assert path.exists()
    assert path.stat().st_size == 0
    assert store.read_all() == []


def test_clear_on_missing_file_is_noop(tmp_path: Path) -> None:
    path = tmp_path / "history.jsonl"
    store = HistoryStore(path=path, retention=10)
    store.clear()  # should not raise
    assert store.read_all() == []


def test_read_all_skips_malformed_lines(tmp_path: Path) -> None:
    path = tmp_path / "history.jsonl"
    store = HistoryStore(path=path, retention=10)
    store.append(make_entry(1))
    with path.open("a") as f:
        f.write("not-json-at-all\n")
    store.append(make_entry(2))
    result = store.read_all()
    assert [e.id for e in result] == ["id0002", "id0001"]


def test_append_creates_parent_directory(tmp_path: Path) -> None:
    nested = tmp_path / "subdir" / "history.jsonl"
    store = HistoryStore(path=nested, retention=10)
    store.append(make_entry(1))
    assert nested.exists()
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/unit/adapters/history/test_store.py -v`
Expected: `ImportError` (HistoryStore does not exist).

- [ ] **Step 4: Implement the store**

Create `shh/adapters/history/store.py`:

```python
"""JSONL-backed history store."""

from pathlib import Path

from shh.core.models import HistoryEntry
from shh.utils.logger import logger


class HistoryStore:
    """Append-only JSONL store with size-bounded rotation."""

    def __init__(self, path: Path, retention: int) -> None:
        self._path = path
        self._retention = retention

    def append(self, entry: HistoryEntry) -> None:
        """Append an entry, then rotate if over retention."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(entry.model_dump_json())
            f.write("\n")
        self._rotate_if_needed()

    def read_all(self) -> list[HistoryEntry]:
        """Return all entries, newest first. Skips malformed lines."""
        if not self._path.exists():
            return []
        entries: list[HistoryEntry] = []
        with self._path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(HistoryEntry.model_validate_json(line))
                except Exception as exc:
                    logger.warning(f"Skipping malformed history line: {exc}")
        entries.reverse()
        return entries

    def clear(self) -> None:
        """Truncate the history file. No-op if it does not exist."""
        if not self._path.exists():
            return
        self._path.write_text("", encoding="utf-8")

    def _rotate_if_needed(self) -> None:
        if not self._path.exists():
            return
        with self._path.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) <= self._retention:
            return
        kept = lines[-self._retention:]
        with self._path.open("w", encoding="utf-8") as f:
            f.writelines(kept)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/unit/adapters/history/test_store.py -v`
Expected: all 7 tests pass.

- [ ] **Step 6: Type + lint + commit**

Run: `uv run poe type && uv run poe lint`
Expected: clean.

```bash
git add shh/adapters/history/ tests/unit/adapters/history/
git commit -m "feat(history): add HistoryStore adapter with JSONL rotation"
```

---

## Task 5: RecordingService refactor

The service grows two mandatory constructor dependencies (`ui`, `history_store`), threads `skip_history` through `transcribe_and_format`, calls `show_processing_step` conditionally for the formatting phase, and unwraps `WhisperTranscription` from the new client signature.

**Files:**
- Modify: `shh/services/recording.py`
- Modify: `tests/unit/services/test_recording_service.py`
- Modify: `tests/integration/test_recording_flow.py`

- [ ] **Step 1: Read the current service end-to-end**

Run: `cat shh/services/recording.py`
Read what `transcribe_and_format` returns and how it calls the adapters. Note where the `Whisper` text is currently extracted.

- [ ] **Step 2: Write the new failing tests**

Open `tests/unit/services/test_recording_service.py` and add (or replace, if the constructor changes break existing tests — adapt them all):

```python
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from shh.cli.ui.base import UIOutput
from shh.adapters.history.store import HistoryStore
from shh.core.models import HistoryEntry, RecordingOptions, WhisperTranscription
from shh.core.styles import TranscriptionStyle
from shh.config.settings import Settings
from shh.services.recording import RecordingService


class _FakeUI:
    """Test double conforming to UIOutput Protocol (no inheritance per project style)."""

    def __init__(self) -> None:
        self.processing_steps: list[str] = []
        self.results: list[str] = []
        self.errors: list[str] = []

    def show_error(self, message: str, details: str | None = None) -> None:
        self.errors.append(message)

    def show_warning(self, message: str) -> None: pass
    def show_info(self, message: str) -> None: pass
    def show_recording_start(self) -> None: pass
    def show_recording_progress(self, progress) -> None: pass  # type: ignore[no-untyped-def]
    def show_recording_stopped(self, reason: str | None = None) -> None: pass
    def show_processing_step(self, step: str) -> None:
        self.processing_steps.append(step)
    def show_result(self, result) -> None:  # type: ignore[no-untyped-def]
        self.results.append(result.text)
    def cleanup(self) -> None: pass


def _make_settings(tmp_path) -> Settings:  # type: ignore[no-untyped-def]
    return Settings(
        openai_api_key="sk-test",
        history_enabled=True,
        history_retention=200,
    )


def _make_service(tmp_path, ui=None, store=None) -> RecordingService:  # type: ignore[no-untyped-def]
    settings = _make_settings(tmp_path)
    ui = ui or _FakeUI()
    store = store or HistoryStore(path=tmp_path / "history.jsonl", retention=200)
    return RecordingService(settings=settings, ui=ui, history_store=store)


@pytest.mark.asyncio
async def test_neutral_no_translate_skips_formatting_step(tmp_path) -> None:  # type: ignore[no-untyped-def]
    ui = _FakeUI()
    service = _make_service(tmp_path, ui=ui)
    audio = np.zeros(16000, dtype=np.float32)
    options = RecordingOptions(style=TranscriptionStyle.NEUTRAL, translate_to=None, duration=5.0)

    with patch(
        "shh.services.recording.transcribe_audio",
        AsyncMock(return_value=WhisperTranscription(text="hi", detected_lang="en")),
    ), patch("shh.services.recording.save_audio_to_wav"), patch("shh.services.recording.pyperclip.copy"):
        await service.transcribe_and_format(audio, options)

    assert "Transcribing" in " ".join(ui.processing_steps)
    assert not any("Formatting" in s for s in ui.processing_steps)


@pytest.mark.asyncio
async def test_translation_triggers_formatting_step(tmp_path) -> None:  # type: ignore[no-untyped-def]
    ui = _FakeUI()
    service = _make_service(tmp_path, ui=ui)
    audio = np.zeros(16000, dtype=np.float32)
    options = RecordingOptions(style=TranscriptionStyle.NEUTRAL, translate_to="french", duration=5.0)

    with patch(
        "shh.services.recording.transcribe_audio",
        AsyncMock(return_value=WhisperTranscription(text="hello", detected_lang="en")),
    ), patch(
        "shh.services.recording.format_transcription",
        AsyncMock(return_value=MagicMock(text="bonjour")),
    ), patch("shh.services.recording.save_audio_to_wav"), patch("shh.services.recording.pyperclip.copy"):
        await service.transcribe_and_format(audio, options)

    assert any("Formatting" in s and "french" in s for s in ui.processing_steps)


@pytest.mark.asyncio
async def test_history_append_on_success(tmp_path) -> None:  # type: ignore[no-untyped-def]
    ui = _FakeUI()
    store = HistoryStore(path=tmp_path / "history.jsonl", retention=200)
    service = _make_service(tmp_path, ui=ui, store=store)
    audio = np.zeros(16000, dtype=np.float32)
    options = RecordingOptions(style=TranscriptionStyle.NEUTRAL, translate_to=None, duration=5.0)

    with patch(
        "shh.services.recording.transcribe_audio",
        AsyncMock(return_value=WhisperTranscription(text="hi there", detected_lang="en")),
    ), patch("shh.services.recording.save_audio_to_wav"), patch("shh.services.recording.pyperclip.copy"):
        await service.transcribe_and_format(audio, options)

    entries = store.read_all()
    assert len(entries) == 1
    assert entries[0].text == "hi there"
    assert entries[0].detected_lang == "en"
    assert entries[0].style == TranscriptionStyle.NEUTRAL


@pytest.mark.asyncio
async def test_skip_history_does_not_append(tmp_path) -> None:  # type: ignore[no-untyped-def]
    store = HistoryStore(path=tmp_path / "history.jsonl", retention=200)
    service = _make_service(tmp_path, store=store)
    audio = np.zeros(16000, dtype=np.float32)
    options = RecordingOptions(style=TranscriptionStyle.NEUTRAL, translate_to=None, duration=5.0)

    with patch(
        "shh.services.recording.transcribe_audio",
        AsyncMock(return_value=WhisperTranscription(text="secret", detected_lang="en")),
    ), patch("shh.services.recording.save_audio_to_wav"), patch("shh.services.recording.pyperclip.copy"):
        await service.transcribe_and_format(audio, options, skip_history=True)

    assert store.read_all() == []


@pytest.mark.asyncio
async def test_history_disabled_does_not_append(tmp_path) -> None:  # type: ignore[no-untyped-def]
    settings = Settings(openai_api_key="sk-test", history_enabled=False)
    ui = _FakeUI()
    store = HistoryStore(path=tmp_path / "history.jsonl", retention=200)
    service = RecordingService(settings=settings, ui=ui, history_store=store)
    audio = np.zeros(16000, dtype=np.float32)
    options = RecordingOptions(style=TranscriptionStyle.NEUTRAL, translate_to=None, duration=5.0)

    with patch(
        "shh.services.recording.transcribe_audio",
        AsyncMock(return_value=WhisperTranscription(text="hi", detected_lang=None)),
    ), patch("shh.services.recording.save_audio_to_wav"), patch("shh.services.recording.pyperclip.copy"):
        await service.transcribe_and_format(audio, options)

    assert store.read_all() == []
```

If `tests/unit/services/test_recording_service.py` already has constructor calls like `RecordingService(settings)` that no longer compile, **update them all** to pass `ui=_FakeUI()` and a `HistoryStore` per test (factor through `_make_service`).

If the existing tests use a different mocking style (no `unittest.mock`), keep the same style — only the constructor signature is shifting in this task.

- [ ] **Step 3: Run tests to verify the new ones fail**

Run: `uv run pytest tests/unit/services/test_recording_service.py -v`
Expected: new tests fail. Existing tests may already fail on the new constructor signature; that's fine, Step 4 fixes the production code.

- [ ] **Step 4: Refactor the service**

Edit `shh/services/recording.py`:

```python
"""Recording service - orchestrates the recording and transcription flow."""

import asyncio
import contextlib
import sys
import uuid
from collections.abc import Callable
from datetime import datetime, timezone

import numpy as np
import pyperclip  # type: ignore[import-untyped]
from numpy.typing import NDArray

from shh.adapters.audio.processor import save_audio_to_wav
from shh.adapters.audio.recorder import AudioRecorder
from shh.adapters.history.store import HistoryStore
from shh.adapters.llm.formatter import format_transcription
from shh.adapters.whisper.client import transcribe_audio
from shh.cli.ui.base import UIOutput
from shh.config.settings import Settings
from shh.core.models import HistoryEntry, RecordingOptions, TranscriptionOutput
from shh.core.styles import TranscriptionStyle


class RecordingService:
    """Service for recording audio and transcribing it."""

    def __init__(
        self,
        settings: Settings,
        ui: UIOutput,
        history_store: HistoryStore,
    ) -> None:
        self.settings = settings
        self._ui = ui
        self._history_store = history_store

    async def record_audio(
        self,
        on_progress: Callable[[float, float], None] | None = None,
    ) -> NDArray[np.float32]:
        # ... preserve existing body ...
        # (unchanged from current implementation)
```

Important: **preserve the existing `record_audio` body verbatim**. Only `__init__` and `transcribe_and_format` change in this task.

Now rewrite `transcribe_and_format`. The new body:

```python
async def transcribe_and_format(
    self,
    audio_data: NDArray[np.float32],
    options: RecordingOptions,
    skip_history: bool = False,
) -> TranscriptionOutput:
    """Transcribe audio, optionally format/translate, copy to clipboard, persist."""
    # Save to temporary WAV
    self._ui.show_processing_step("Saving audio")
    wav_path = save_audio_to_wav(audio_data, sample_rate=16_000)

    try:
        # Transcribe
        self._ui.show_processing_step("Transcribing")
        whisper_result = await transcribe_audio(
            wav_path,
            api_key=self.settings.openai_api_key or "",
            model=self.settings.whisper_model,
        )

        # Optionally format / translate
        needs_formatting = (
            options.style != TranscriptionStyle.NEUTRAL or options.translate_to is not None
        )
        if needs_formatting:
            label = "Formatting"
            if options.translate_to:
                label = f"Formatting ({options.translate_to})"
            self._ui.show_processing_step(label)
            formatted = await format_transcription(
                whisper_result.text,
                style=options.style,
                api_key=self.settings.openai_api_key or "",
                target_language=options.translate_to,
            )
            final_text = formatted.text
        else:
            final_text = whisper_result.text

        # Clipboard
        with contextlib.suppress(Exception):
            pyperclip.copy(final_text)

        # Persist to history
        if self.settings.history_enabled and not skip_history:
            entry = HistoryEntry(
                id=uuid.uuid4().hex[:8],
                ts=datetime.now(tz=timezone.utc),
                text=final_text,
                style=options.style,
                translate_to=options.translate_to,
                duration_s=options.duration or 0.0,
                detected_lang=whisper_result.detected_lang,
            )
            self._history_store.append(entry)

        return TranscriptionOutput(text=final_text)
    finally:
        with contextlib.suppress(Exception):
            wav_path.unlink(missing_ok=True)
```

Adjust this body to match the actual existing fields and helpers — if the current implementation already has a `try/finally` that deletes the temp file, keep it. If `TranscriptionOutput` has different fields, match them. The shape above is illustrative of the new behaviors (steps, history, conditional formatting); preserve the rest of the existing logic.

If `options.duration` is not a field on `RecordingOptions`, derive the duration from `audio_data` length instead: `len(audio_data) / 16_000.0`.

- [ ] **Step 5: Update integration test**

In `tests/integration/test_recording_flow.py`, find any usage of `transcribe_audio(...)` that asserts the return is a `str`. Change it to expect / construct `WhisperTranscription`. Find any `RecordingService(settings)` instantiation and pass `ui` and `history_store` as required.

- [ ] **Step 6: Run full suite**

Run: `uv run poe test`
Expected: all tests pass (including the new service tests and the integration tests).

- [ ] **Step 7: Type + lint + commit**

Run: `uv run poe type && uv run poe lint`
Expected: clean.

```bash
git add shh/services/recording.py tests/unit/services/test_recording_service.py tests/integration/test_recording_flow.py
git commit -m "refactor(service): take ui + history_store; emit processing steps; persist on success"
```

---

## Task 6: PipeUI

**Files:**
- Create: `shh/cli/ui/pipe_ui.py`
- Modify: `shh/cli/ui/__init__.py`
- Create: `tests/unit/cli/test_pipe_ui.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/cli/test_pipe_ui.py`:

```python
"""Tests for PipeUI - the non-TTY minimal output."""

import sys

from shh.cli.ui.base import RecordingProgress, TranscriptionResult
from shh.cli.ui.pipe_ui import PipeUI


def test_show_result_prints_text_only(capsys) -> None:  # type: ignore[no-untyped-def]
    ui = PipeUI()
    ui.show_result(TranscriptionResult(text="Hello world", copied_to_clipboard=True))
    captured = capsys.readouterr()
    assert captured.out == "Hello world\n"
    assert captured.err == ""


def test_show_error_writes_to_stderr(capsys) -> None:  # type: ignore[no-untyped-def]
    ui = PipeUI()
    ui.show_error("oops", details="api key missing")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "oops" in captured.err


def test_progress_and_steps_are_noop(capsys) -> None:  # type: ignore[no-untyped-def]
    ui = PipeUI()
    ui.show_recording_start()
    ui.show_recording_progress(RecordingProgress(elapsed=1.0, max_duration=10.0))
    ui.show_processing_step("Transcribing")
    ui.show_recording_stopped()
    ui.cleanup()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/cli/test_pipe_ui.py -v`
Expected: `ImportError` for `PipeUI`.

- [ ] **Step 3: Implement PipeUI**

Create `shh/cli/ui/pipe_ui.py`:

```python
"""Minimal UI for non-TTY stdout (pipes, redirects)."""

import sys

from shh.cli.ui.base import RecordingProgress, TranscriptionResult, UIOutput


class PipeUI(UIOutput):
    """Writes only the transcribed text to stdout. Errors go to stderr."""

    def show_error(self, message: str, details: str | None = None) -> None:
        print(f"Error: {message}", file=sys.stderr)
        if details:
            print(details, file=sys.stderr)

    def show_warning(self, message: str) -> None:
        print(message, file=sys.stderr)

    def show_info(self, message: str) -> None:
        return None

    def show_recording_start(self) -> None:
        return None

    def show_recording_progress(self, progress: RecordingProgress) -> None:
        return None

    def show_recording_stopped(self, reason: str | None = None) -> None:
        return None

    def show_processing_step(self, step: str) -> None:
        return None

    def show_result(self, result: TranscriptionResult) -> None:
        print(result.text)

    def cleanup(self) -> None:
        return None
```

Update `shh/cli/ui/__init__.py` to export PipeUI:

```python
from shh.cli.ui.base import RecordingProgress, TranscriptionResult, UIOutput
from shh.cli.ui.pipe_ui import PipeUI
from shh.cli.ui.quiet_ui import QuietUI
from shh.cli.ui.rich_ui import RichUI

__all__ = ["PipeUI", "QuietUI", "RecordingProgress", "RichUI", "TranscriptionResult", "UIOutput"]
```

(Adjust to keep symbols that the file already exports.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/cli/test_pipe_ui.py -v`
Expected: 3 tests pass.

- [ ] **Step 5: Type + lint + commit**

Run: `uv run poe type && uv run poe lint`
Expected: clean.

```bash
git add shh/cli/ui/pipe_ui.py shh/cli/ui/__init__.py tests/unit/cli/test_pipe_ui.py
git commit -m "feat(ui): add PipeUI for non-TTY stdout"
```

---

## Task 7: RichUI refactor

Single `Live` across phases, transient=True, drop Panel, fix duplicate "Recording" line.

**Files:**
- Modify: `shh/cli/ui/rich_ui.py`
- Modify: `tests/unit/cli/test_ui.py`

- [ ] **Step 1: Read the existing RichUI tests**

Run: `cat tests/unit/cli/test_ui.py`
Note which Rich behaviors the existing tests assert. The refactor must keep `RichUI`'s API surface intact (same Protocol methods).

- [ ] **Step 2: Write the new tests**

Add to `tests/unit/cli/test_ui.py` (and remove any tests that assert on the now-removed Panel):

```python
from rich.console import Console

from shh.cli.ui.base import RecordingProgress, TranscriptionResult
from shh.cli.ui.rich_ui import RichUI


def _make_rich_ui_with_buffer() -> tuple[RichUI, Console]:
    """Helper: a RichUI wired to a recording Console for output capture."""
    import io
    buf = io.StringIO()
    console = Console(file=buf, force_terminal=True, width=80)
    ui = RichUI(console=console)
    return ui, console


def test_rich_ui_result_has_no_panel() -> None:
    ui, console = _make_rich_ui_with_buffer()
    ui.show_result(TranscriptionResult(text="hello", copied_to_clipboard=True))
    rendered = console.file.getvalue()  # type: ignore[union-attr]
    assert "hello" in rendered
    # Panel borders include box-drawing characters; assert they are NOT present
    assert "─" not in rendered  # box horizontal
    assert "│" not in rendered  # box vertical
    assert "copied to clipboard" in rendered


def test_rich_ui_single_live_across_phases() -> None:
    ui = RichUI()
    # First progress call creates the Live
    ui.show_recording_progress(RecordingProgress(elapsed=1.0, max_duration=300.0))
    first_live = ui._live
    assert first_live is not None
    # Recording stopped does NOT tear down the Live (next step reuses it)
    ui.show_recording_stopped()
    assert ui._live is first_live
    # Processing step updates same Live
    ui.show_processing_step("Transcribing")
    assert ui._live is first_live
    # show_result tears it down
    ui.show_result(TranscriptionResult(text="hi", copied_to_clipboard=True))
    assert ui._live is None
```

The `RichUI()` constructor will be tweaked to accept an optional `console` parameter. If the existing constructor takes no args, this is a backward-compatible addition (`console: Console | None = None` is OK here because Console is a UI sink, not a logical dependency).

If the existing test file has a test that asserts the result is wrapped in a Panel (it likely does, given the current implementation), **delete that test** as part of this task.

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/unit/cli/test_ui.py -v`
Expected: the new tests fail. Old panel-based tests, if any, will pass against the current code but are scheduled for removal.

- [ ] **Step 4: Refactor RichUI**

Replace `shh/cli/ui/rich_ui.py`:

```python
"""Rich UI output with a single morphing spinner."""

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

from shh.cli.ui.base import RecordingProgress, TranscriptionResult, UIOutput

_DEFAULT_CONSOLE = Console()


class RichUI(UIOutput):
    """Rich-based UI with a single Live spinner across the whole pipeline."""

    def __init__(self, console: Console | None = None) -> None:
        self._console = console or _DEFAULT_CONSOLE
        self._live: Live | None = None
        self._spinner = Spinner("dots")

    def _ensure_live(self) -> Live:
        if self._live is None:
            self._live = Live(
                self._spinner,
                console=self._console,
                transient=True,
                refresh_per_second=12,
            )
            self._live.start()
        return self._live

    def _set_text(self, text: Text) -> None:
        self._spinner.update(text=text)
        live = self._ensure_live()
        live.refresh()

    def show_error(self, message: str, details: str | None = None) -> None:
        if self._live is not None:
            self._live.stop()
            self._live = None
        self._console.print(f"[red]Error: {message}[/red]")
        if details:
            self._console.print(f"[dim]{details}[/dim]")

    def show_warning(self, message: str) -> None:
        self._console.print(f"[yellow]{message}[/yellow]")

    def show_info(self, message: str) -> None:
        self._console.print(f"[cyan]{message}[/cyan]")

    def show_recording_start(self) -> None:
        self._console.print()

    def show_recording_progress(self, progress: RecordingProgress) -> None:
        text = Text()
        text.append("Recording ", style="bold green")
        text.append(f"{progress.elapsed:.1f}s ", style="cyan")
        text.append("(Enter to stop)", style="dim")
        self._set_text(text)

    def show_recording_stopped(self, reason: str | None = None) -> None:
        # Keep the Live running; the next show_processing_step will update it.
        if reason:
            text = Text(reason, style="yellow")
            self._set_text(text)

    def show_processing_step(self, step: str) -> None:
        text = Text(step, style="cyan")
        self._set_text(text)

    def show_result(self, result: TranscriptionResult) -> None:
        if self._live is not None:
            self._live.stop()
            self._live = None
        self._console.print(result.text)
        if result.copied_to_clipboard:
            self._console.print("[dim green]✓ copied to clipboard[/dim green]")

    def cleanup(self) -> None:
        if self._live is not None:
            self._live.stop()
            self._live = None
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/unit/cli/test_ui.py -v`
Expected: new tests pass. Any panel-assertion test should have been removed in Step 2.

- [ ] **Step 6: Type + lint + commit**

Run: `uv run poe type && uv run poe lint`
Expected: clean.

```bash
git add shh/cli/ui/rich_ui.py tests/unit/cli/test_ui.py
git commit -m "refactor(ui): single morphing spinner in RichUI; drop result Panel"
```

---

## Task 8: History picker (prompt_toolkit)

**Files:**
- Create: `shh/cli/ui/history_picker.py`
- Create: `tests/unit/cli/test_history_picker.py`

- [ ] **Step 1: Write the failing tests (pure helpers only — no Application)**

Create `tests/unit/cli/test_history_picker.py`:

```python
"""Tests for history picker pure helpers."""

from datetime import datetime, timedelta, timezone

from shh.core.models import HistoryEntry
from shh.core.styles import TranscriptionStyle
from shh.cli.ui.history_picker import (
    filter_entries,
    format_relative_time,
    truncate_text,
    render_row,
)


def _entry(text: str, *, style: TranscriptionStyle = TranscriptionStyle.NEUTRAL,
           translate_to: str | None = None, ts: datetime | None = None) -> HistoryEntry:
    return HistoryEntry(
        id="abcd1234",
        ts=ts or datetime(2026, 5, 28, 8, 58, tzinfo=timezone.utc),
        text=text,
        style=style,
        translate_to=translate_to,
        duration_s=5.0,
        detected_lang=None,
    )


def test_filter_substring_in_text() -> None:
    e1 = _entry("Bonjour Marius")
    e2 = _entry("Hello world")
    assert filter_entries([e1, e2], "marius") == [e1]


def test_filter_empty_returns_all() -> None:
    e1 = _entry("a")
    e2 = _entry("b")
    assert filter_entries([e1, e2], "") == [e1, e2]


def test_filter_matches_translate_language() -> None:
    e1 = _entry("Bonjour", translate_to="french")
    e2 = _entry("Hello")
    assert filter_entries([e1, e2], "french") == [e1]


def test_filter_matches_style_value() -> None:
    e1 = _entry("Yo", style=TranscriptionStyle.CASUAL)
    e2 = _entry("Greetings", style=TranscriptionStyle.BUSINESS)
    assert filter_entries([e1, e2], "casual") == [e1]


def test_format_relative_time_same_day() -> None:
    now = datetime(2026, 5, 28, 10, 0, tzinfo=timezone.utc)
    ts = datetime(2026, 5, 28, 8, 58, tzinfo=timezone.utc)
    assert format_relative_time(ts, now=now) == "08:58"


def test_format_relative_time_within_week() -> None:
    now = datetime(2026, 5, 28, 10, 0, tzinfo=timezone.utc)
    ts = datetime(2026, 5, 25, 14, 11, tzinfo=timezone.utc)  # Monday
    out = format_relative_time(ts, now=now)
    assert "14:11" in out
    assert len(out) == len("Mon 14:11")


def test_format_relative_time_older() -> None:
    now = datetime(2026, 5, 28, 10, 0, tzinfo=timezone.utc)
    ts = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)
    assert format_relative_time(ts, now=now) == "04-01 09:00"


def test_truncate_text_short_unchanged() -> None:
    assert truncate_text("hello", 10) == "hello"


def test_truncate_text_long() -> None:
    assert truncate_text("x" * 100, 10) == "xxxxxxxxx…"


def test_render_row_includes_time_and_tag_and_text() -> None:
    entry = _entry("Bonjour Marius", translate_to="french")
    now = entry.ts + timedelta(minutes=5)
    row = render_row(entry, now=now)
    assert "08:58" in row
    assert "fr" in row
    assert "Bonjour Marius" in row


def test_render_row_neutral_tag() -> None:
    entry = _entry("Hello", style=TranscriptionStyle.NEUTRAL)
    row = render_row(entry, now=entry.ts)
    assert "--" in row
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/cli/test_history_picker.py -v`
Expected: `ImportError`.

- [ ] **Step 3: Implement the picker module**

Create `shh/cli/ui/history_picker.py`:

```python
"""Interactive history picker built on prompt_toolkit."""

from datetime import datetime, timedelta
from typing import Callable

from prompt_toolkit.application import Application
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.layout import Layout

from shh.core.models import HistoryEntry
from shh.core.styles import TranscriptionStyle


def _style_tag(entry: HistoryEntry) -> str:
    if entry.translate_to:
        return entry.translate_to[:2].lower()
    if entry.style == TranscriptionStyle.CASUAL:
        return "cs"
    if entry.style == TranscriptionStyle.BUSINESS:
        return "bz"
    return "--"


def filter_entries(entries: list[HistoryEntry], needle: str) -> list[HistoryEntry]:
    if not needle:
        return list(entries)
    n = needle.lower()
    return [
        e for e in entries
        if n in e.text.lower()
        or (e.translate_to or "").lower().startswith(n)
        or e.style.value.lower().startswith(n)
    ]


def format_relative_time(ts: datetime, *, now: datetime) -> str:
    if ts.date() == now.date():
        return ts.strftime("%H:%M")
    if now - ts < timedelta(days=7):
        return ts.strftime("%a %H:%M")
    return ts.strftime("%m-%d %H:%M")


def truncate_text(text: str, max_len: int) -> str:
    text = text.replace("\n", " ")
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def render_row(entry: HistoryEntry, *, now: datetime) -> str:
    time_part = format_relative_time(entry.ts, now=now)
    tag = _style_tag(entry)
    text = truncate_text(entry.text, 60)
    return f"{time_part:>9} {tag:<2}  {text}"


class PickerState:
    """Mutable state of the picker; isolated from prompt_toolkit details."""

    def __init__(self, entries: list[HistoryEntry]) -> None:
        self.entries = entries
        self.filter = ""
        self.cursor = 0

    @property
    def visible(self) -> list[HistoryEntry]:
        return filter_entries(self.entries, self.filter)

    def move(self, delta: int) -> None:
        n = len(self.visible)
        if n == 0:
            self.cursor = 0
            return
        self.cursor = max(0, min(n - 1, self.cursor + delta))

    def selected(self) -> HistoryEntry | None:
        v = self.visible
        if not v:
            return None
        idx = min(self.cursor, len(v) - 1)
        return v[idx]


def build_picker_app(
    entries: list[HistoryEntry],
    on_copy: Callable[[HistoryEntry], None],
    now_provider: Callable[[], datetime] | None = None,
) -> Application[HistoryEntry | None]:
    """Build the prompt_toolkit Application. Returns the selected entry on Enter, or None on Esc."""
    state = PickerState(entries)
    get_now = now_provider or (lambda: datetime.now(tz=entries[0].ts.tzinfo) if entries else datetime.now())

    def get_list_lines() -> FormattedText:
        rows = state.visible
        if not rows:
            return FormattedText([("class:dim", f'No matches for "{state.filter}"\n')])
        out: list[tuple[str, str]] = []
        now = get_now()
        for idx, entry in enumerate(rows):
            prefix = ">" if idx == state.cursor else " "
            line = f"{prefix} {render_row(entry, now=now)}\n"
            style = "class:selected" if idx == state.cursor else ""
            out.append((style, line))
        return FormattedText(out)

    def get_preview() -> FormattedText:
        entry = state.selected()
        if entry is None:
            return FormattedText([("class:dim", "")])
        meta_parts = [f"{entry.duration_s:.1f}s"]
        if entry.translate_to:
            meta_parts.append(f"translated to {entry.translate_to}")
        if entry.detected_lang:
            meta_parts.append(f"detected {entry.detected_lang}")
        if entry.style != TranscriptionStyle.NEUTRAL:
            meta_parts.append(entry.style.value)
        meta = " · ".join(meta_parts)
        return FormattedText([
            ("", entry.text + "\n"),
            ("", "\n"),
            ("class:dim", f"· {meta}\n"),
        ])

    def get_footer() -> FormattedText:
        f = f' filter: "{state.filter}"' if state.filter else ""
        return FormattedText([
            ("class:dim", f"Type to filter · ↑↓ · Enter copy · Esc quit{f}"),
        ])

    kb = KeyBindings()

    @kb.add(Keys.Up)
    def _up(event):  # type: ignore[no-untyped-def]
        state.move(-1)

    @kb.add(Keys.Down)
    def _down(event):  # type: ignore[no-untyped-def]
        state.move(1)

    @kb.add(Keys.Enter)
    def _enter(event):  # type: ignore[no-untyped-def]
        entry = state.selected()
        if entry is not None:
            on_copy(entry)
            event.app.exit(result=entry)
        else:
            event.app.exit(result=None)

    @kb.add(Keys.Escape)
    @kb.add(Keys.ControlC)
    def _quit(event):  # type: ignore[no-untyped-def]
        event.app.exit(result=None)

    @kb.add(Keys.Backspace)
    def _backspace(event):  # type: ignore[no-untyped-def]
        state.filter = state.filter[:-1]
        state.cursor = 0

    @kb.add(Keys.Any)
    def _any(event):  # type: ignore[no-untyped-def]
        ch = event.data
        if ch and ch.isprintable():
            state.filter += ch
            state.cursor = 0

    layout = Layout(
        HSplit([
            Window(FormattedTextControl(get_list_lines), wrap_lines=False),
            Window(height=1, char="─"),
            Window(FormattedTextControl(get_preview), height=Dimension.exact(6)),
            Window(FormattedTextControl(get_footer), height=1),
        ])
    )

    return Application(
        layout=layout,
        key_bindings=kb,
        full_screen=False,
        mouse_support=False,
    )
```

The `# type: ignore[no-untyped-def]` on the event handlers is necessary because `prompt_toolkit` exposes them as untyped callables. This is the one exception to "no `# type: ignore`" — it's at a known FFI boundary; document this in the file via the existing comment. (If the user prefers, drop the ignore and accept untyped event params via a `KeyPressEvent` import — verify the symbol exists in this prompt_toolkit version before relying on it.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/cli/test_history_picker.py -v`
Expected: 10 tests pass.

- [ ] **Step 5: Type + lint + commit**

Run: `uv run poe type && uv run poe lint`
Expected: clean. If mypy flags the event-handler ignores, switch to `KeyPressEvent` typing — confirm the symbol exists with `uv run python -c "from prompt_toolkit.key_binding.key_processor import KeyPressEvent; print('ok')"` before relying on it.

```bash
git add shh/cli/ui/history_picker.py tests/unit/cli/test_history_picker.py
git commit -m "feat(ui): add history picker (prompt_toolkit) with filter and preview"
```

---

## Task 9: `shh history` command

**Files:**
- Create: `shh/cli/commands/history.py`
- Create: `tests/unit/cli/test_history_command.py`
- Modify: `shh/cli/app.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/cli/test_history_command.py`:

```python
"""Tests for the shh history command."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from shh.adapters.history.store import HistoryStore
from shh.cli.app import app
from shh.config.settings import Settings
from shh.core.models import HistoryEntry
from shh.core.styles import TranscriptionStyle


def _seed(path: Path, n: int = 0) -> None:
    store = HistoryStore(path=path, retention=200)
    for i in range(n):
        store.append(HistoryEntry(
            id=f"id{i:04d}",
            ts=datetime(2026, 5, 28, 8, i, tzinfo=timezone.utc),
            text=f"entry {i}",
            style=TranscriptionStyle.NEUTRAL,
            translate_to=None,
            duration_s=1.0,
            detected_lang="en",
        ))


def test_history_empty_state(tmp_path: Path) -> None:
    runner = CliRunner()
    history_path = tmp_path / "history.jsonl"
    with patch.object(Settings, "get_history_path", classmethod(lambda cls: history_path)):
        result = runner.invoke(app, ["history"])
    assert result.exit_code == 0
    assert "No history yet" in result.output


def test_history_clear_confirms_and_clears(tmp_path: Path) -> None:
    runner = CliRunner()
    history_path = tmp_path / "history.jsonl"
    _seed(history_path, 3)
    with patch.object(Settings, "get_history_path", classmethod(lambda cls: history_path)):
        result = runner.invoke(app, ["history", "clear"], input="y\n")
    assert result.exit_code == 0
    assert history_path.read_text() == ""


def test_history_clear_declined(tmp_path: Path) -> None:
    runner = CliRunner()
    history_path = tmp_path / "history.jsonl"
    _seed(history_path, 3)
    with patch.object(Settings, "get_history_path", classmethod(lambda cls: history_path)):
        result = runner.invoke(app, ["history", "clear"], input="n\n")
    assert result.exit_code != 0 or "Aborted" in result.output or len(history_path.read_text()) > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/cli/test_history_command.py -v`
Expected: fails — `app` doesn't have `history` subcommand yet.

- [ ] **Step 3: Implement the command**

Create `shh/cli/commands/history.py`:

```python
"""History command group: browse and manage transcription history."""

import sys
from datetime import datetime, timezone

import pyperclip  # type: ignore[import-untyped]
import typer
from rich.console import Console

from shh.adapters.history.store import HistoryStore
from shh.cli.ui.history_picker import build_picker_app
from shh.config.settings import Settings

history_app = typer.Typer(help="Browse and manage transcription history.")
_console = Console()


def _store() -> HistoryStore:
    settings = Settings.load_from_file() or Settings()
    return HistoryStore(
        path=Settings.get_history_path(),
        retention=settings.history_retention,
    )


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


@history_app.callback(invoke_without_command=True)
def history_default(ctx: typer.Context) -> None:
    """Open the interactive picker. Enter copies the selected entry."""
    if ctx.invoked_subcommand is not None:
        return
    store = _store()
    entries = store.read_all()
    if not entries:
        _console.print("[dim]No history yet. Run `shh` first to create one.[/dim]")
        return

    def _copy(entry: object) -> None:
        # `entry` is a HistoryEntry; signature is wide to keep the picker module decoupled
        pyperclip.copy(getattr(entry, "text", ""))

    picker = build_picker_app(entries, on_copy=_copy, now_provider=_now)
    selected = picker.run()
    if selected is not None and sys.stdout.isatty():
        _console.print("[dim green]✓ copied to clipboard[/dim green]")


@history_app.command("clear")
def history_clear() -> None:
    """Delete all history entries (asks for confirmation)."""
    store = _store()
    entries = store.read_all()
    if not entries:
        _console.print("[dim]History is already empty.[/dim]")
        return
    typer.confirm(f"Delete {len(entries)} entries?", abort=True)
    store.clear()
    _console.print(f"[green]Cleared {len(entries)} entries.[/green]")
```

Now wire it into `shh/cli/app.py`. Add to the imports:

```python
from shh.cli.commands.history import history_app
```

And after the existing `app.add_typer(config_app, name="config")` line, add:

```python
app.add_typer(history_app, name="history")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/cli/test_history_command.py -v`
Expected: 3 tests pass.

- [ ] **Step 5: Run full suite**

Run: `uv run poe test`
Expected: all green.

- [ ] **Step 6: Type + lint + commit**

Run: `uv run poe type && uv run poe lint`
Expected: clean.

```bash
git add shh/cli/commands/history.py shh/cli/app.py tests/unit/cli/test_history_command.py
git commit -m "feat(cli): add shh history picker and shh history clear"
```

---

## Task 10: TTY-aware UI selection + `--no-history` flag

**Files:**
- Modify: `shh/cli/commands/record.py`
- Modify: `shh/cli/app.py`
- Modify: `tests/unit/cli/test_commands.py`

- [ ] **Step 1: Read the existing record_command signature**

Run: `cat shh/cli/commands/record.py`
Note the current parameters and how UI is selected.

- [ ] **Step 2: Write the failing tests**

Add to `tests/unit/cli/test_commands.py`:

```python
from unittest.mock import patch

def test_record_command_uses_pipe_ui_when_not_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    """When stdout is not a TTY, the record path should select PipeUI."""
    from shh.cli.commands import record as record_module

    monkeypatch.setattr("sys.stdout.isatty", lambda: False)

    # The internal helper that picks the UI must return a PipeUI here. Call it directly.
    ui = record_module._select_ui(quiet=False, verbose=False, quiet_default=False)
    from shh.cli.ui.pipe_ui import PipeUI
    assert isinstance(ui, PipeUI)


def test_record_command_uses_quiet_ui_when_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    from shh.cli.commands import record as record_module
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    ui = record_module._select_ui(quiet=True, verbose=False, quiet_default=False)
    from shh.cli.ui.quiet_ui import QuietUI
    assert isinstance(ui, QuietUI)


def test_record_command_uses_rich_ui_default(monkeypatch: pytest.MonkeyPatch) -> None:
    from shh.cli.commands import record as record_module
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    ui = record_module._select_ui(quiet=False, verbose=False, quiet_default=False)
    from shh.cli.ui.rich_ui import RichUI
    assert isinstance(ui, RichUI)


def test_record_command_verbose_overrides_quiet_default(monkeypatch: pytest.MonkeyPatch) -> None:
    from shh.cli.commands import record as record_module
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    ui = record_module._select_ui(quiet=False, verbose=True, quiet_default=True)
    from shh.cli.ui.rich_ui import RichUI
    assert isinstance(ui, RichUI)
```

This requires `_select_ui` to be a real callable in the record module. We export it so tests can call it without spinning a full Typer command.

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/unit/cli/test_commands.py -v -k "select_ui or pipe_ui or quiet_ui or rich_ui or no_history"`
Expected: failure on missing `_select_ui`.

- [ ] **Step 4: Implement `_select_ui` and thread `--no-history`**

In `shh/cli/commands/record.py`, add at module scope:

```python
import sys

from shh.cli.ui.base import UIOutput
from shh.cli.ui.pipe_ui import PipeUI
from shh.cli.ui.quiet_ui import QuietUI
from shh.cli.ui.rich_ui import RichUI


def _select_ui(*, quiet: bool, verbose: bool, quiet_default: bool) -> UIOutput:
    """Pick the UI based on TTY + flags."""
    if not sys.stdout.isatty():
        return PipeUI()
    if quiet or (quiet_default and not verbose):
        return QuietUI()
    return RichUI()
```

Update the async `record_command` (or whatever the current entry point is named) to:

1. Accept a new keyword `no_history: bool = False`.
2. Call `_select_ui(quiet=quiet, verbose=verbose, quiet_default=settings.quiet_mode)`.
3. Build `HistoryStore` via `HistoryStore(path=Settings.get_history_path(), retention=settings.history_retention)`.
4. Instantiate `RecordingService(settings=settings, ui=ui, history_store=store)`.
5. Pass `skip_history=no_history` to `service.transcribe_and_format(...)`.

Update `shh/cli/app.py` so the `default_command` callback accepts `--no-history` (and `record` subcommand if it has its own signature). Add the option block alongside the existing `--quiet`/`--verbose`:

```python
no_history: Annotated[
    bool,
    typer.Option(
        "--no-history",
        help="Do not persist this transcription to history.",
    ),
] = False,
```

Thread the value into the `asyncio.run(record_command(...))` call.

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/unit/cli/test_commands.py -v`
Expected: all tests pass (existing + new).

- [ ] **Step 6: Manual smoke check**

Run: `uv run shh --help`
Expected: `--no-history` appears in the options list.

Run: `uv run shh history --help`
Expected: shows the history group with `clear` listed.

- [ ] **Step 7: Type + lint + commit**

Run: `uv run poe type && uv run poe lint`
Expected: clean.

```bash
git add shh/cli/commands/record.py shh/cli/app.py tests/unit/cli/test_commands.py
git commit -m "feat(cli): TTY-aware UI selection + --no-history flag"
```

---

## Task 11: Expose history settings in `shh config`

**Files:**
- Modify: `shh/cli/commands/config.py`
- Modify: `tests/unit/cli/test_commands.py`

- [ ] **Step 1: Inspect current config command surface**

Run: `cat shh/cli/commands/config.py`
Note how the existing settable keys are listed (likely an allow-list).

- [ ] **Step 2: Write failing tests**

Add to `tests/unit/cli/test_commands.py`:

```python
def test_config_set_history_enabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    settings_file = tmp_path / "settings.json"
    monkeypatch.setattr(Settings, "get_config_path", classmethod(lambda cls: settings_file))
    result = runner.invoke(app, ["config", "set", "history_enabled", "false"])
    assert result.exit_code == 0
    loaded = Settings.load_from_file()
    assert loaded is not None
    assert loaded.history_enabled is False


def test_config_set_history_retention(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    settings_file = tmp_path / "settings.json"
    monkeypatch.setattr(Settings, "get_config_path", classmethod(lambda cls: settings_file))
    result = runner.invoke(app, ["config", "set", "history_retention", "50"])
    assert result.exit_code == 0
    loaded = Settings.load_from_file()
    assert loaded is not None
    assert loaded.history_retention == 50
```

Add any missing imports (`Path`, `Settings`, `CliRunner`, `app`).

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/unit/cli/test_commands.py -v -k "history_enabled or history_retention"`
Expected: failures — the keys are rejected by the config setter (allow-list).

- [ ] **Step 4: Add the keys to the allow-list**

In `shh/cli/commands/config.py`, extend the SETTABLE_KEYS (or equivalent dict/list) to include `history_enabled` (bool) and `history_retention` (int). Match the existing parsing pattern (booleans likely accept "true/false/1/0/yes/no" — reuse, do not reinvent).

If the current config command uses generic `getattr/setattr` on the Settings model, the new fields work for free — only the help text / show output needs updating.

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/unit/cli/test_commands.py -v`
Expected: all green.

- [ ] **Step 6: Type + lint + commit**

Run: `uv run poe type && uv run poe lint`
Expected: clean.

```bash
git add shh/cli/commands/config.py tests/unit/cli/test_commands.py
git commit -m "feat(config): expose history_enabled and history_retention"
```

---

## Task 12: End-to-end smoke + final `poe check`

**Files:** none (verification)

- [ ] **Step 1: Full test suite**

Run: `uv run poe check`
Expected: all green (mypy strict, ruff, pytest with all new tests).

- [ ] **Step 2: Hand smoke 1 — TTY mode**

Run interactively:
```bash
unset SHH_OPENAI_API_KEY  # ensure config-file key is used if present
uv run shh --help
```
Expected: `--no-history`, `--quiet`, `--verbose` listed; `history` listed under commands; `--style`, `--translate` present.

- [ ] **Step 3: Hand smoke 2 — pipe mode dry-run**

Run:
```bash
uv run shh --help | head -5
```
Expected: clean stdout, no escape codes (Rich detects non-TTY at the help layer; not strictly the same code path, but a useful sanity check that we don't pollute stdout).

- [ ] **Step 4: Manual end-to-end (requires API key)**

If an OpenAI API key is configured, run:
```bash
uv run shh
# speak a short phrase, press Enter
```
Expected:
- During recording: one line `⠋ Recording N.Ns (Enter to stop)` updating in place
- During processing: one line `⠋ Transcribing` then (only if -s/-t used) `⠋ Formatting (...)`
- Final: transcribed text on its own line, then dim `✓ copied to clipboard`
- No "Recording..." duplicate, no Panel borders

```bash
uv run shh history
# arrow keys navigate, Enter copies, Esc quits
```

```bash
uv run shh | cat
# speak; Enter
# Expected: only the transcribed text on stdout
```

- [ ] **Step 5: No commit at this stage**

This is verification only. Defects found here go back into the relevant prior task as a focused commit.

---

## Task 13: CLAUDE.md update + revise-claude-md skill

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update the architecture section**

Open `CLAUDE.md` and integrate, in the directory tree:
- `shh/adapters/history/` — JSONL-backed transcription store
- (no new files in `cli/` that need diagram-level mention; the `commands/history.py` is a leaf)

Update the Architecture diagram and Key Architectural Principles to mention:
- History is an adapter — `HistoryStore` lives in `adapters/history/` and is a mandatory dependency of `RecordingService`.
- TTY-aware UI selection: `RichUI` (default), `QuietUI` (--quiet or `quiet_mode`), `PipeUI` (when `not sys.stdout.isatty()`).

Update the Configuration section to add `history_enabled` and `history_retention`, with a one-line note that `history.jsonl` sits next to `settings.json` in the platform config dir.

Add a new short subsection under "Implementation Patterns" titled "Transcription History" describing the storage shape, rotation, picker entry point, and the `--no-history` flag.

- [ ] **Step 2: Run the documentation skill**

Run the `claude-md-management:revise-claude-md` skill to confirm no further inconsistencies. Apply any targeted edits it suggests.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: document history feature and TTY-aware UI selection"
```

---

## Task 14: Wrap-up — full check and merge readiness

**Files:** none

- [ ] **Step 1: Final `poe check`**

Run: `uv run poe check`
Expected: green.

- [ ] **Step 2: Coverage spot-check (optional)**

Run: `uv run poe test-cov`
Expected: coverage on new modules (`history/store.py`, `history_picker.py`, `pipe_ui.py`, `commands/history.py`) is ≥ 80%. If lower, add focused tests in the gaps.

- [ ] **Step 3: Confirm git log is coherent**

Run: `git log --oneline main..HEAD`
Expected: a clean sequence of conventional commits, one per task, each green at the point it was made (except the intentional intermediate red after Task 3, which Task 5 resolves).

- [ ] **Step 4: No push, no merge**

Per the prior conversation's working agreement, do not push or open a PR without explicit user confirmation.

---

## Self-review

### Spec coverage

| Spec section | Plan task(s) |
|---|---|
| §4.1 UI selection | Task 10 |
| §4.2 RichUI refactor | Task 7 |
| §4.3 Conditional Formatting step | Task 5 (step 4 in `transcribe_and_format`) |
| §4.4 PipeUI | Task 6 |
| §4.5 Tests for polish | Tasks 6, 7, 10 |
| §5.1 HistoryEntry model | Task 2 |
| §5.1 verbose_json + WhisperTranscription | Tasks 2, 3 |
| §5.2 HistoryStore | Task 4 |
| §5.3 Settings additions | Task 1 |
| §5.4 Service integration | Task 5 |
| §5.5 Storage tests | Task 4 |
| §6 Picker UI | Task 8 |
| §6.6 New commands | Task 9 |
| §6.7 --no-history flag | Task 10 |
| §6.8 Picker tests | Tasks 8, 9 |
| §7 CLI surface diff | Tasks 9, 10, 11 |
| §8 Settings additions | Tasks 1, 11 |
| §9 Module diff | All tasks |
| §11 Open questions | Out of scope (deferred) |
| §12 Definition of done | Tasks 12, 14 |
| `~/.claude/CLAUDE.md` revise step | Task 13 |

No gaps.

### Placeholder scan

No "TBD", no "implement later", no "similar to Task N", no vague "add error handling". Code blocks shown for every code step. Exact pytest commands and git commit messages given.

One soft spot: the test for `test_history_clear_declined` in Task 9 uses `or` chains because `typer.confirm(..., abort=True)` historically exits with a non-zero code; the exact behavior of `CliRunner` here can vary. The test is written to accept either nonzero exit OR an "Aborted" message — that's intentionally lenient because the exact form depends on Typer/Click version. Acceptable.

### Type consistency

- `HistoryEntry` fields: `id`, `ts`, `text`, `style`, `translate_to`, `duration_s`, `detected_lang` — consistent across Tasks 2, 4, 5, 8, 9.
- `WhisperTranscription` fields: `text`, `detected_lang` — consistent across Tasks 2, 3, 5.
- `HistoryStore` API: `__init__(path, retention)`, `append(entry)`, `read_all() -> list[HistoryEntry]`, `clear()` — consistent across Tasks 4, 5, 9.
- `RecordingService.__init__(settings, ui, history_store)` and `.transcribe_and_format(audio_data, options, skip_history=False)` — consistent across Tasks 5, 10.
- `_select_ui(*, quiet, verbose, quiet_default)` — single helper definition in Task 10, used by the tests.

### Assumptions

- `prompt_toolkit` ≥ 3.0 is installed transitively via `ipython>=9.8.0` (confirmed 3.0.52 in Task 0).
- OpenAI SDK in this venv exposes `language` on the verbose_json response (`getattr(..., "language", None)` is defensive in case it doesn't).
- `pyperclip.copy` works in this environment (already in use; no new risk).
- `tests/integration/test_recording_flow.py` mock style aligns with the unit tests; if not, adapt the unit tests' mocking to match the project convention before submitting.
- The current `record_command` signature is roughly `(style, translate, quiet, verbose)` with possibly `duration`. Task 10 adds `no_history`; if the signature is different, adapt the option name placement but keep the new flag name.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-28-history-and-polish.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
