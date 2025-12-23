"""Clipboard operations for copying transcription results."""

import contextlib

import pyperclip  # type: ignore[import-untyped]


async def copy_to_clipboard(text: str) -> None:
    """
    Copy text to system clipboard.

    Args:
        text: Text to copy to clipboard

    Returns:
        None
    """
    # Fail silently if clipboard unavailable
    with contextlib.suppress(Exception):
        pyperclip.copy(text)
