"""Global hotkey adapter with a Qt-safe boundary."""

from typing import Any

from PySide6.QtCore import QObject, Signal


class HotkeyBridge(QObject):
    """Signals emitted from listener threads are queued to the Qt thread."""

    open_controls_requested = Signal()


class GlobalHotkeyListener:
    """Register Ctrl+Alt+O without exposing pynput objects to the UI."""

    def __init__(self, bridge: HotkeyBridge) -> None:
        self._bridge = bridge
        self._listener: Any | None = None
        self.error: str | None = None

    def start(self) -> None:
        if self._listener is not None:
            return
        try:
            from pynput import keyboard

            self._listener = keyboard.GlobalHotKeys(
                {"<ctrl>+<alt>+o": self._bridge.open_controls_requested.emit}
            )
            self._listener.start()
        except Exception as exc:  # OS integration can fail without a desktop session.
            self.error = str(exc)
            self._listener = None

    def stop(self) -> None:
        listener, self._listener = self._listener, None
        if listener is not None:
            listener.stop()
