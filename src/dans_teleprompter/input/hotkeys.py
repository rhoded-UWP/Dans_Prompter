"""Validated, rebindable global hotkeys behind a Qt-safe boundary."""

from dataclasses import dataclass
from typing import Any, Callable

from PySide6.QtCore import QObject, Signal


_MODIFIERS = {"ctrl", "alt", "shift", "win"}
_PYNPUT_MODIFIERS = {"ctrl": "<ctrl>", "alt": "<alt>", "shift": "<shift>", "win": "<cmd>"}


@dataclass(frozen=True, slots=True)
class HotkeyBindings:
    open_controls: str = "Ctrl+Alt+O"
    toggle_click_through: str = "Ctrl+Alt+C"


def normalize_hotkey(value: str) -> str:
    """Validate and return a stable display form such as ``Ctrl+Alt+O``."""

    raw_parts = [part.strip().lower() for part in value.split("+") if part.strip()]
    if len(raw_parts) != len(set(raw_parts)):
        raise ValueError("A hotkey cannot repeat a key.")
    modifiers = [part for part in raw_parts if part in _MODIFIERS]
    keys = [part for part in raw_parts if part not in _MODIFIERS]
    if not modifiers or len(keys) != 1:
        raise ValueError("Use one key plus at least one modifier, for example Ctrl+Alt+C.")
    key = keys[0]
    if len(key) != 1 or not key.isalnum():
        raise ValueError("The final hotkey key must be one letter or number.")
    ordered = [name for name in ("ctrl", "alt", "shift", "win") if name in modifiers]
    labels = {"ctrl": "Ctrl", "alt": "Alt", "shift": "Shift", "win": "Win"}
    return "+".join([*(labels[name] for name in ordered), key.upper()])


def validate_bindings(bindings: HotkeyBindings) -> HotkeyBindings:
    normalized = HotkeyBindings(
        normalize_hotkey(bindings.open_controls),
        normalize_hotkey(bindings.toggle_click_through),
    )
    if normalized.open_controls == normalized.toggle_click_through:
        raise ValueError("Global hotkeys must be unique.")
    return normalized


def to_pynput(value: str) -> str:
    parts = normalize_hotkey(value).lower().split("+")
    return "+".join(_PYNPUT_MODIFIERS.get(part, part) for part in parts)


class HotkeyBridge(QObject):
    """Signals emitted from listener threads are queued to the Qt thread."""

    open_controls_requested = Signal()
    toggle_click_through_requested = Signal()


class GlobalHotkeyListener:
    def __init__(self, bridge: HotkeyBridge, bindings: HotkeyBindings | None = None) -> None:
        self._bridge = bridge
        self.bindings = validate_bindings(bindings or HotkeyBindings())
        self._listener: Any | None = None
        self._running_requested = False
        self.error: str | None = None

    def start(self) -> None:
        self._running_requested = True
        if self._listener is not None:
            return
        try:
            from pynput import keyboard

            callbacks: dict[str, Callable[[], None]] = {
                to_pynput(self.bindings.open_controls): self._bridge.open_controls_requested.emit,
                to_pynput(self.bindings.toggle_click_through): self._bridge.toggle_click_through_requested.emit,
            }
            self._listener = keyboard.GlobalHotKeys(callbacks)
            self._listener.start()
            self.error = None
        except Exception as exc:  # OS integration can fail without a desktop session.
            self.error = str(exc)
            self._listener = None

    def update_bindings(self, bindings: HotkeyBindings) -> None:
        normalized = validate_bindings(bindings)
        was_running = self._running_requested
        self.stop()
        self.bindings = normalized
        if was_running:
            self.start()

    def stop(self) -> None:
        self._running_requested = False
        listener, self._listener = self._listener, None
        if listener is not None:
            listener.stop()
