"""Immutable state published by the application controller."""

from dataclasses import dataclass

from ..scripts.model import Script


@dataclass(frozen=True, slots=True)
class TeleprompterState:
    script: Script | None = None
    cursor_word: int = 0
    word_count: int = 0
    paused: bool = True
    speed_wpm: int = 130
    text_size: int = 38
    background_opacity: int = 88
    take_counts: tuple[int, ...] = (1,)
    status: str = "Open a .txt script to begin"
