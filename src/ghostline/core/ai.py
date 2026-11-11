"""Choosing which captions go to the AI panel (kept free of Qt so it can be unit-tested)."""

from __future__ import annotations

from collections.abc import Sequence

from .transcript import Line

MODES = ("new", "last5", "all")


def captions_for_ai(lines: Sequence[Line], partial: str, mode: str, sent_count: int) -> tuple[str, int]:
    """Return ``(text, new_sent_count)``.

    * ``new``   — everything after the first ``sent_count`` lines (all lines if the transcript was cleared)
    * ``last5`` — the last five sentences
    * ``all``   — the whole transcript

    The sentence still being spoken (``partial``) is always appended, so the question that was *just*
    asked is included even before Live Captions finalises it.
    """
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}")
    if mode == "all":
        chosen = list(lines)
    elif mode == "last5":
        chosen = list(lines[-5:])
    else:
        chosen = list(lines[sent_count:]) if 0 <= sent_count <= len(lines) else list(lines)
    parts = [ln.text.strip() for ln in chosen if ln.text.strip()]
    if partial.strip():
        parts.append(partial.strip())
    return " ".join(parts), len(lines)
