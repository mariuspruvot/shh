"""Tests for history picker pure helpers."""

from datetime import UTC, datetime, timedelta

from shh.cli.ui.history_picker import (
    PickerState,
    filter_entries,
    format_relative_time,
    render_row,
    truncate_text,
)
from shh.core.models import HistoryEntry
from shh.core.styles import TranscriptionStyle


def _entry(
    text: str,
    *,
    style: TranscriptionStyle = TranscriptionStyle.NEUTRAL,
    translate_to: str | None = None,
    ts: datetime | None = None,
) -> HistoryEntry:
    return HistoryEntry(
        id="abcd1234",
        ts=ts or datetime(2026, 5, 28, 8, 58, tzinfo=UTC),
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
    now = datetime(2026, 5, 28, 10, 0, tzinfo=UTC)
    ts = datetime(2026, 5, 28, 8, 58, tzinfo=UTC)
    assert format_relative_time(ts, now=now) == "08:58"


def test_format_relative_time_within_week() -> None:
    now = datetime(2026, 5, 28, 10, 0, tzinfo=UTC)
    ts = datetime(2026, 5, 25, 14, 11, tzinfo=UTC)  # Monday
    out = format_relative_time(ts, now=now)
    assert "14:11" in out
    assert len(out) == len("Mon 14:11")


def test_format_relative_time_older() -> None:
    now = datetime(2026, 5, 28, 10, 0, tzinfo=UTC)
    ts = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
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


def test_picker_state_move_clamps_to_bounds() -> None:
    state = PickerState(entries=[_entry("a"), _entry("b")])
    state.move(-10)
    assert state.cursor == 0
    state.move(10)
    assert state.cursor == 1


def test_picker_state_move_empty_visible_resets_cursor() -> None:
    state = PickerState(entries=[_entry("hello")])
    state.filter = "zzz"
    state.move(1)
    assert state.cursor == 0


def test_picker_state_selected_returns_none_when_empty() -> None:
    state = PickerState(entries=[])
    assert state.selected() is None


def test_picker_state_selected_clamps_stale_cursor() -> None:
    state = PickerState(entries=[_entry("a"), _entry("b"), _entry("c")])
    state.cursor = 2
    state.filter = "a"
    selected = state.selected()
    assert selected is not None
    assert selected.text == "a"
