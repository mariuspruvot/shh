# shh — Output Polish + History Feature

**Date:** 2026-05-28
**Status:** Draft, awaiting user review

---

## 1. Problem

Two distinct concerns surfaced from real usage of `shh -t french`:

**Output verbosity & a defect.** The current `RichUI` prints six lines for a five-second recording and *duplicates* the "Recording…" status line. The duplicate is caused by `rich.live.Live(auto_refresh=False)` being stopped without `transient=True`, so Rich commits the last live frame on stop. The remaining four lines (`Saving audio`, `Transcribing`, `Formatting`, then a Panel with the result) make a quick interaction feel chatty.

**No persistence.** Every transcription is lost the instant the panel scrolls off-screen. Users naturally want to retrieve a transcription they recorded a few minutes (or hours) ago without re-recording.

This spec covers two coordinated changes: (a) a slimmer single-spinner output that auto-adapts when piped, and (b) a history feature with an interactive picker.

## 2. Goals

- One-line live spinner that morphs through the pipeline phases — no duplicated lines, no scroll-jam after a short recording.
- When stdout is not a TTY (`shh | xclip`, `shh > out.md`, `$(shh)`), output **only** the raw text — but still copy to clipboard.
- Persist every successful transcription locally so the user can retrieve it later via an interactive Atuin-style picker.
- `shh history` opens the picker. Arrow keys navigate, Enter copies the selected entry to the clipboard, Esc quits.
- Pure-Python implementation, no new external binaries. Reuse `prompt_toolkit` already transitively present via `ipython`.

## 3. Non-goals

- **Replay / re-format.** Considered, then dropped during brainstorming. Re-formatting a stored formatted text is lossy (chain-of-LLM degradations), and storing the raw Whisper output to enable lossless replay was rejected as scope creep for the current iteration.
- **Audio retention.** Audio is deleted immediately after transcription. We never persist the WAV. Privacy + size.
- **Fuzzy search.** Substring match is enough for ≤200 entries. No `rapidfuzz` dependency.
- **JSON / scripting exports.** No `shh history --json`. Add later if a real need surfaces.
- **Cloud sync, multi-device, per-project history.** A single global `history.jsonl` is the only store.
- **Reintroducing the Textual TUI.** Out of scope (removed earlier today in `c74a5d8`).
- **A Rich Panel around the result.** The brainstorm explicitly picked "option A" (panel-less, text + dim confirmation line).

## 4. Output polish

### 4.1 UI selection

In `shh/cli/commands/record.py`, before instantiating any UI:

```python
import sys

if not sys.stdout.isatty():
    ui: UIOutput = PipeUI()
elif quiet or (settings.quiet_mode and not verbose):
    ui = QuietUI()
else:
    ui = RichUI()
```

The `--verbose` flag wins over `quiet_mode` in config (already the existing semantic).

### 4.2 `RichUI` refactor

Today, `RichUI` starts a `Live` in `show_recording_progress`, stops it in `show_recording_stopped`, then `console.print(...)`s each processing step as a new line. The new model uses **one** `Live` for the entire pipeline.

State held on the instance:
- `self._live: Live | None` — single live display.

Lifecycle:
1. `show_recording_start()` — no-op (keep blank line for breathing room is fine).
2. `show_recording_progress(progress)` — first call constructs `Live(transient=True, refresh_per_second=12)` and `.start()`s it. Subsequent calls update the renderable to `⠋ Recording {elapsed:.1f}s (Enter to stop)`. The braille spinner glyph cycles via `rich.spinner.Spinner("dots")`.
3. `show_recording_stopped(reason)` — no-op (we don't tear down the Live yet; the next `show_processing_step` will repaint it).
4. `show_processing_step(step)` — update the Live renderable to `⠋ {step}` (e.g., `Transcribing`, `Formatting (french)`). The same Live continues — no flicker, no extra lines.
5. `show_result(result)` — `self._live.stop()` (transient=True erases the spinner line), then:
   ```
   {result.text}
   ✓ copied to clipboard
   ```
   The first line is printed plain; the second is `[dim green]✓ copied to clipboard[/dim green]`. No Panel.
6. `cleanup()` — defensive `self._live.stop()` if still running.

Errors during the pipeline (`show_error`) must call `self._live.stop()` first so the error message is visible on its own line.

### 4.3 `RecordingService` — skip the formatting phase when no-op

`shh/adapters/llm/formatter.py` already short-circuits when `style == TranscriptionStyle.NEUTRAL and target_language is None`. The service must align: only call `ui.show_processing_step("Formatting (...)")` when the LLM is actually invoked. Otherwise the spinner advertises work that doesn't happen and ends with a misleading state.

Concretely in `services/recording.py`:

```python
needs_formatting = options.style != TranscriptionStyle.NEUTRAL or options.translate_to is not None
if needs_formatting:
    label = "Formatting"
    if options.translate_to:
        label = f"Formatting ({options.translate_to})"
    self._ui.show_processing_step(label)
```

### 4.4 New `PipeUI`

New file `shh/cli/ui/pipe_ui.py`. Implements `UIOutput`. All visual methods are no-ops except:

- `show_result(result)` — `print(result.text)` (Python builtin, hits `sys.stdout` directly with the system default newline). **No** "copied to clipboard" line.
- `show_error(message, details)` — `print(...)` to `sys.stderr` so stdout stays clean.
- `show_warning(message)` — to stderr.

`show_info`, `show_recording_*`, `show_processing_step`, `cleanup` are all `pass`.

Export from `shh/cli/ui/__init__.py` alongside `RichUI` and `QuietUI`.

### 4.5 Tests for polish

- `tests/unit/cli/ui/test_pipe_ui.py` (new) — capture stdout/stderr, assert:
  - `show_result` writes the text and only the text to stdout.
  - `show_error` writes to stderr.
  - All other methods are no-ops (no stdout/stderr output).
- `tests/unit/cli/test_ui.py` (existing) — extend with a test that asserts `RichUI` uses a single Live across recording → processing → result and that no duplicate "Recording" frame leaks. Use a `MagicMock`-substituted `Live` to count `start`/`stop`/`update` calls.
- `tests/unit/cli/test_commands.py` (existing) — extend `record_command` test to assert `PipeUI` is chosen when stdout is non-TTY (monkeypatch `sys.stdout.isatty` to return `False`).

## 5. History feature

### 5.1 Data model

Extend `shh/core/models.py` with:

```python
class HistoryEntry(BaseModel):
    id: str               # short uuid, e.g. uuid4().hex[:8]
    ts: datetime          # iso8601 UTC at insertion
    text: str             # formatted text (the same string that landed in clipboard)
    style: TranscriptionStyle
    translate_to: str | None
    duration_s: float
    detected_lang: str | None
```

`detected_lang` is the language Whisper detected on the source audio. To populate it, `shh/adapters/whisper/client.py` switches from the current plain transcribe call to `response_format="verbose_json"`. The function signature changes from `-> str` to `-> WhisperTranscription` (a small new Pydantic model with `text: str` and `detected_lang: str | None`), and callers extract `.text` where they previously got a bare string.

### 5.2 Storage

Location: `Settings.get_config_path().parent / "history.jsonl"`. `get_config_path()` is the existing classmethod returning the path to `settings.json` (`shh/config/settings.py:48`); the history file sits alongside it in the same platform-aware config directory.

For clarity, add a small helper:

```python
@classmethod
def get_history_path(cls) -> Path:
    return cls.get_config_path().parent / "history.jsonl"
```

Mirrors the existing `get_config_path()` pattern instead of poking at `.parent` from callers.

Format: JSON Lines. Each line is a serialized `HistoryEntry`. Append-only writes.

Retention: when `append()` would push the total above `settings.history_retention` (default 200), the file is rewritten with the last `retention` entries. O(N) cost on each rotation, trivial at N=200.

New module: `shh/adapters/history/store.py`

```python
class HistoryStore:
    def __init__(self, path: Path, retention: int) -> None: ...
    def append(self, entry: HistoryEntry) -> None: ...
    def read_all(self) -> list[HistoryEntry]: ...  # most-recent first
    def clear(self) -> None: ...                   # truncates the file
```

`read_all` reads the file line by line, parses each JSON, returns the list reversed (newest first). On missing file → empty list. On a malformed line → skip it with a single warning logged once (do not crash the picker).

### 5.3 Settings additions

Extend `shh/config/settings.py`:

```python
history_enabled: bool = True
history_retention: int = Field(200, ge=1, le=10_000)
```

No default-None for dependencies elsewhere — the `RecordingService` constructor receives a `HistoryStore` instance explicitly (see 5.4).

### 5.4 Service integration

`RecordingService.__init__` signature changes:

```python
def __init__(
    self,
    settings: Settings,
    ui: UIOutput,
    history_store: HistoryStore,    # mandatory, no default
) -> None:
```

After a successful transcription (in `transcribe_and_format`), if `settings.history_enabled and not skip_history`, the service constructs a `HistoryEntry` and calls `history_store.append(entry)`. `skip_history` is a new bool parameter on `transcribe_and_format`, threaded from `--no-history`.

`record_command` (CLI) instantiates the store and passes it in:

```python
store = HistoryStore(
    path=Settings.get_history_path(),
    retention=settings.history_retention,
)
service = RecordingService(settings=settings, ui=ui, history_store=store)
```

### 5.5 Tests for history storage

- `tests/unit/adapters/history/test_store.py` (new):
  - `append` creates the file and writes one JSON line.
  - `read_all` returns entries newest-first.
  - Retention: after appending `retention + 5` entries, file holds exactly `retention` lines and they are the most recent ones.
  - `clear` truncates the file (file exists, zero size).
  - `read_all` on missing file returns `[]`.
  - `read_all` skips a single malformed line and returns the rest.
- `tests/unit/services/test_recording_service.py` (extend):
  - After a successful run, `HistoryStore.append` was called once with an entry matching the result.
  - When `skip_history=True`, `append` is not called.
  - When `settings.history_enabled=False`, `append` is not called.

## 6. Picker UI (`shh history`)

### 6.1 Layout

Built with `prompt_toolkit`. Single `Application` instance. `HSplit` of three regions:

```
┌─────────────────────────────────────────────────────────────┐
│ > 08:58  fr   Bonjour, je m'appelle Marius, ceci est un te… │
│   08:32  --   Hello, this is a quick voice memo about the … │
│   Mon 14:11 bz  Following up on our conversation from this … │
│   Mon 11:42 cs  Yeah so like, the thing is we need to figu… │
│   ...                                                       │
├─ Preview ───────────────────────────────────────────────────┤
│ Bonjour, je m'appelle Marius, ceci est un test.             │
│                                                             │
│ · 5.2s · translated to french · detected en                 │
└─────────────────────────────────────────────────────────────┘
 Type to filter · ↑↓ · Enter copy · Esc quit
```

- **List window** — `Window(FormattedTextControl(get_list_lines))`. Each entry rendered as `{time} {flag_tag:8} {text:.60}…`. The selected row uses `class:selected` style (reverse video).
- **Preview window** — `Window(FormattedTextControl(get_preview))`, fixed height = 6. Shows full text of the selected entry, then a dim footer line with metadata.
- **Footer** — single-line `Window(FormattedTextControl("Type to filter · ↑↓ · Enter copy · Esc quit"))`.

### 6.2 State

```python
@dataclass
class PickerState:
    entries: list[HistoryEntry]        # source data, newest-first
    filter: str                        # current substring filter
    cursor: int                        # index into filtered view
```

Derived: `filtered() -> list[HistoryEntry]` applies the filter:

```python
needle = filter.lower()
return [e for e in entries
        if needle in e.text.lower()
        or (e.translate_to or "").lower().startswith(needle)
        or e.style.value.lower().startswith(needle)]
```

### 6.3 Key bindings

| Key | Action |
|---|---|
| `Up` | `cursor = max(0, cursor - 1)` |
| `Down` | `cursor = min(len(filtered)-1, cursor + 1)` |
| `Enter` | If filtered non-empty, copy `filtered[cursor].text` to clipboard via `pyperclip.copy`, set return value to `entry`, exit app. |
| `Esc` / `Ctrl-C` | Exit app with return value `None`. |
| `Backspace` | Drop last char of `filter`, reset cursor to 0. |
| Any printable char | Append to `filter`, reset cursor to 0. |

After the `Application.run()` returns, the caller (`history_command`) prints a confirmation to stderr if an entry was copied — but **only** if stdout is a TTY (it's an interactive command, but be conservative).

### 6.4 Time formatting helper

`shh/cli/ui/history_picker.py`:

```python
def format_relative_time(ts: datetime, now: datetime) -> str:
    delta = now - ts
    if delta < timedelta(days=1) and ts.date() == now.date():
        return ts.strftime("%H:%M")
    if delta < timedelta(days=7):
        return ts.strftime("%a %H:%M")  # Mon 14:11
    return ts.strftime("%m-%d %H:%M")
```

Truncate `text` to 60 columns using `rich.text.Text.truncate(60)` semantics or a simple slice + `…` glyph.

### 6.5 Empty states

- Store has zero entries → instead of running the `Application`, `history_command` prints to stderr: `No history yet. Run \`shh\` first to create one.` and exits with code 0.
- Filter excludes everything → preview window shows `No matches for "<filter>"` in dim. The list area is just blank.

### 6.6 New commands

`shh/cli/commands/history.py` (new):

```python
history_app = typer.Typer(help="Browse and manage transcription history")

@history_app.callback(invoke_without_command=True)
def history_default(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        # open the picker
        ...

@history_app.command("clear")
def history_clear() -> None:
    # typer.confirm("Delete N entries? [y/N]")
    # store.clear()
    ...
```

Wire `history_app` into `shh/cli/app.py`:

```python
from shh.cli.commands.history import history_app
app.add_typer(history_app, name="history")
```

### 6.7 New flag on `record`

Both the default `shh` command and `shh record` get `--no-history`. Threaded into the service call.

### 6.8 Tests for picker

The interactive `Application` is not tested end-to-end (out of scope, would require a pseudo-tty). What **is** tested:

- `tests/unit/cli/ui/test_history_picker.py` (new):
  - `format_relative_time` produces expected strings for "today", "this week", "older".
  - `filtered()` correctly applies substring match across text/lang/style.
  - The "selected row" rendering vs. non-selected differs by style class only.
- `tests/unit/cli/commands/test_history.py` (new):
  - `history_clear` calls `HistoryStore.clear` when user confirms.
  - `history_clear` does not call `clear` when user declines.
  - `history` with empty store prints the empty-state message and does not start the Application.

## 7. CLI surface diff

**New**
- `shh history` — opens picker
- `shh history clear` — purges store (with confirmation)
- `--no-history` flag on default `shh` and `shh record`

**Modified**
- `shh` / `shh record` output is now single-spinner + final-text-with-dim-confirmation (no Panel)
- Non-TTY stdout auto-routes to `PipeUI` (text only, clipboard still copied)

**Unchanged**
- `shh setup`, `shh config`, `shh config set/get/reset/show`
- `--style`, `--translate`, `--quiet`, `--verbose`, `--duration`

## 8. Settings additions (full diff vs current)

```python
class Settings(BaseSettings):
    # ... existing fields ...
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

Update `shh/cli/commands/config.py` to expose these via `shh config set/get/show` so users can toggle without editing JSON by hand.

## 9. Module-by-module diff summary

| File | Action | Notes |
|---|---|---|
| `shh/cli/ui/rich_ui.py` | Modify | Single Live across phases; transient=True; drop Panel in `show_result`. |
| `shh/cli/ui/pipe_ui.py` | **New** | Plain stdout output. ~30 lines. |
| `shh/cli/ui/__init__.py` | Modify | Export `PipeUI`. |
| `shh/cli/ui/history_picker.py` | **New** | prompt_toolkit picker. ~150 lines. |
| `shh/cli/commands/record.py` | Modify | TTY-aware UI selection. Thread `--no-history`. |
| `shh/cli/commands/history.py` | **New** | `history_app` Typer subcommand group. |
| `shh/cli/commands/config.py` | Modify | Expose `history_enabled`, `history_retention`. |
| `shh/cli/app.py` | Modify | `add_typer(history_app, name="history")`. |
| `shh/services/recording.py` | Modify | Mandatory `history_store`; conditional formatting step; `skip_history` param. |
| `shh/adapters/history/__init__.py` | **New** | Empty (package marker). |
| `shh/adapters/history/store.py` | **New** | `HistoryStore`. |
| `shh/adapters/whisper/client.py` | Modify | `verbose_json` response, return `WhisperTranscription`. |
| `shh/core/models.py` | Modify | Add `HistoryEntry`, `WhisperTranscription`. |
| `shh/config/settings.py` | Modify | Add `history_enabled`, `history_retention`, `get_history_path()` classmethod. |
| `tests/unit/adapters/history/test_store.py` | **New** | Storage tests. |
| `tests/unit/cli/ui/test_pipe_ui.py` | **New** | PipeUI tests. |
| `tests/unit/cli/ui/test_history_picker.py` | **New** | Picker logic tests (non-interactive). |
| `tests/unit/cli/commands/test_history.py` | **New** | Command tests. |
| `tests/unit/cli/test_ui.py` | Modify | RichUI single-Live assertions. |
| `tests/unit/cli/test_commands.py` | Modify | TTY-detection routing test. |
| `tests/unit/services/test_recording_service.py` | Modify | History append behavior. |
| `CLAUDE.md` | Modify | Document the history feature + TTY-aware UI selection. |

## 10. Assumptions

- `prompt_toolkit` is installed transitively via `ipython>=9.8.0`. **Must verify** at implementation start with `uv pip show prompt_toolkit`. If the resolved version is unsuitable (very old, missing features), declare `prompt_toolkit>=3.0` as a direct dependency rather than relying on the transitive pin.
- The OpenAI Whisper API accepts `response_format="verbose_json"` and returns a `language` field — `[claude-guessed: based on OpenAI SDK conventions; confirm by reading `openai.types.audio.Transcription` or calling the API in a smoke test before extracting `.language`]`.
- `pyperclip.copy` works on the user's macOS without extra setup. Already in use elsewhere in the project, so this is not a new risk.
- `platformdirs`-derived config dir is writable. If not, the existing `Settings` code already fails loudly — we inherit that behavior.
- `uuid4().hex[:8]` collisions across 200 entries are vanishingly improbable. We do not deduplicate; if the cosmic ray lands, `id` is not load-bearing (it's display-only).
- Picker is not tested end-to-end with a real pseudo-tty. We rely on unit tests of the pure helpers and on manual smoke-test during development. Acceptable trade-off for the scope.

## 11. Open questions

None blocking. Two items to revisit after the first iteration:

- Whether to add `shh history --json` once we see real scripting needs.
- Whether to expose a `--limit N` flag to the picker (currently always shows up to `history_retention` items, which is fine at 200 but might warrant lazy rendering at 10k).

## 12. Definition of done

- All checks pass: `uv run poe check` (mypy strict + ruff + pytest).
- A user can run `shh -t french`, see a single morphing spinner, and the final output is text + dim `✓ copied to clipboard` — no Panel, no duplicate Recording line.
- `shh | cat` prints exactly the transcribed text and nothing else; clipboard still receives a copy.
- After three recordings, `shh history` opens an interactive list; arrow keys move the cursor; Enter copies the highlighted entry to the clipboard and exits; Esc exits without copying.
- `shh history clear` purges the file after a Y/N prompt.
- `shh --no-history` records normally but the entry is absent from `shh history`.
- `CLAUDE.md` reflects the history feature and the TTY-aware UI selection.
- Per project convention from `~/.claude/CLAUDE.md`, the implementation plan must include the `/claude-md-management:revise-claude-md` step.
