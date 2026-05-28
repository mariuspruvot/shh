"""Interactive history picker built on prompt_toolkit."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from prompt_toolkit.application import Application
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
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
        e
        for e in entries
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
    return f"{time_part:>11} {tag:<2}  {text}"


@dataclass
class PickerState:
    entries: list[HistoryEntry] = field(default_factory=list)
    filter: str = ""
    cursor: int = 0

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
    """Returns a prompt_toolkit Application: Enter -> copy + exit, Esc -> quit."""
    state = PickerState(entries=list(entries))

    def _now() -> datetime:
        if now_provider is not None:
            return now_provider()
        return datetime.now(tz=UTC)

    def get_list_lines() -> FormattedText:
        rows = state.visible
        if not rows:
            return FormattedText([("class:dim", f'No matches for "{state.filter}"\n')])
        out: list[tuple[str, str]] = []
        now = _now()
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
        return FormattedText(
            [
                ("", entry.text + "\n"),
                ("", "\n"),
                ("class:dim", f"· {meta}\n"),
            ]
        )

    def get_footer() -> FormattedText:
        suffix = f' · filter: "{state.filter}"' if state.filter else ""
        return FormattedText(
            [("class:dim", f"Type to filter · ↑↓ · Enter copy · Esc quit{suffix}")]
        )

    kb = KeyBindings()

    @kb.add(Keys.Up)
    def _up(event: KeyPressEvent) -> None:
        state.move(-1)

    @kb.add(Keys.Down)
    def _down(event: KeyPressEvent) -> None:
        state.move(1)

    @kb.add(Keys.Enter)
    def _enter(event: KeyPressEvent) -> None:
        entry = state.selected()
        if entry is not None:
            on_copy(entry)
            event.app.exit(result=entry)
        else:
            event.app.exit(result=None)

    @kb.add(Keys.Escape)
    @kb.add(Keys.ControlC)
    def _quit(event: KeyPressEvent) -> None:
        event.app.exit(result=None)

    @kb.add(Keys.Backspace)
    def _backspace(event: KeyPressEvent) -> None:
        state.filter = state.filter[:-1]
        state.cursor = 0

    @kb.add(Keys.Any)
    def _any(event: KeyPressEvent) -> None:
        ch = event.data
        if ch and ch.isprintable():
            state.filter += ch
            state.cursor = 0

    layout = Layout(
        HSplit(
            [
                Window(FormattedTextControl(get_list_lines), wrap_lines=False),
                Window(height=1, char="─"),
                Window(FormattedTextControl(get_preview), height=Dimension.exact(6)),
                Window(FormattedTextControl(get_footer), height=1),
            ]
        )
    )

    return Application(
        layout=layout,
        key_bindings=kb,
        full_screen=False,
        mouse_support=False,
    )
