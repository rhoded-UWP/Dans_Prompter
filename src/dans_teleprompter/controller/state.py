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
    click_through: bool = False
    capture_exclusion: bool = False
    capture_exclusion_supported: bool = True
    vamping: bool = False
    hotkey_open_controls: str = "Ctrl+Alt+O"
    hotkey_click_through: str = "Ctrl+Alt+C"
    take_counts: tuple[int, ...] = (1,)
    status: str = "Open a .txt script to begin"
