"""Shared owner for the two-window teleprompter application."""

from pathlib import Path

from PySide6.QtCore import QObject, QSettings, QTimer, Signal, Slot
from PySide6.QtWidgets import QApplication

from ..input.hotkeys import GlobalHotkeyListener, HotkeyBridge
from ..scripts.parser import ScriptParseError, parse_text
from ..scripts.presentation import ScriptPresentation, build_presentation
from ..ui.controls import ControlWindow
from ..ui.geometry import WindowGeometryStore
from ..ui.overlay import PrompterOverlay
from ..ui.tray import SystemTray
from .state import TeleprompterState


class ApplicationController(QObject):
    """Own application state and route every UI intent through one authority."""

    state_changed = Signal(object)

    def __init__(self, app: QApplication) -> None:
        super().__init__()
        self._app = app
        self._shutting_down = False
        self._settings = QSettings()
        self.geometry_store = WindowGeometryStore()
        self.presentation: ScriptPresentation | None = None
        self.state = TeleprompterState(
            speed_wpm=self._setting_int("teleprompter/speed_wpm", 130, 40, 400),
            text_size=self._setting_int("overlay/text_size", 38, 20, 80),
            background_opacity=self._setting_int("overlay/background_opacity", 88, 20, 100),
        )
        self._scroll_timer = QTimer(self)
        self._scroll_timer.timeout.connect(self.advance_word)

        self.control_window = ControlWindow(self)
        self.overlay = PrompterOverlay(self)
        self.tray = SystemTray(self)
        self.hotkey_bridge = HotkeyBridge(self)
        self.hotkey_listener = GlobalHotkeyListener(self.hotkey_bridge)

        self.overlay.open_controls_requested.connect(self.open_controls)
        self.overlay.exit_requested.connect(self.exit_application)
        self.overlay.word_clicked.connect(self.set_cursor_from_click)
        self.overlay.navigation_requested.connect(self.navigate)
        self.overlay.text_size_requested.connect(self.change_text_size)
        self.overlay.speed_requested.connect(self.change_speed)
        self.hotkey_bridge.open_controls_requested.connect(self.open_controls)
        self.tray.open_controls_requested.connect(self.open_controls)
        self.tray.toggle_overlay_requested.connect(self.toggle_overlay)
        self.tray.exit_requested.connect(self.exit_application)
        self.control_window.exit_requested.connect(self.exit_application)
        self._app.aboutToQuit.connect(self._prepare_shutdown)
        self._apply_timer_interval()

    @property
    def shutting_down(self) -> bool:
        return self._shutting_down

    def start(self) -> None:
        self.geometry_store.restore(self.overlay, "overlay")
        self.geometry_store.restore(self.control_window, "controls")
        self.overlay.show()
        self.control_window.show()
        self.tray.show()
        self.hotkey_listener.start()
        self.state_changed.emit(self.state)

    def load_script_file(self, path: str | Path) -> bool:
        source = Path(path)
        try:
            text = source.read_text(encoding="utf-8")
            script = parse_text(text, source)
        except (OSError, UnicodeError, ScriptParseError) as exc:
            self._replace_state(status=str(exc), paused=True)
            return False
        return self.set_script(script)

    def set_script(self, script: object) -> bool:
        from ..scripts.model import Script

        if not isinstance(script, Script):
            raise TypeError("set_script requires a parsed Script")
        self.presentation = build_presentation(script)
        self._scroll_timer.stop()
        self._replace_state(
            script=script,
            cursor_word=0,
            word_count=len(self.presentation.words),
            paused=True,
            take_counts=(1,) * self.presentation.section_count,
            status=f"Ready — {script.source.name} · {len(self.presentation.words)} words",
        )
        return True

    @Slot()
    def toggle_pause(self) -> None:
        if self.state.script is None or self.state.word_count == 0:
            self._replace_state(status="Open a script before starting")
            return
        paused = not self.state.paused
        if paused:
            self._scroll_timer.stop()
        else:
            self._scroll_timer.start()
        self._replace_state(paused=paused, status="Paused" if paused else "Constant speed")

    @Slot()
    def advance_word(self) -> None:
        if self.state.paused or self.state.word_count == 0:
            return
        if self.state.cursor_word >= self.state.word_count - 1:
            self._scroll_timer.stop()
            self._replace_state(paused=True, status="Finished")
            return
        self._replace_state(cursor_word=self.state.cursor_word + 1)

    @Slot(int)
    def set_cursor_from_click(self, word_index: int) -> None:
        if self.presentation is None or not 0 <= word_index < self.state.word_count:
            return
        takes = list(self.state.take_counts)
        if word_index < self.state.cursor_word:
            section = self.presentation.section_at(self.state.cursor_word)
            takes[section] += 1
        self._replace_state(cursor_word=word_index, take_counts=tuple(takes))

    @Slot(str)
    def navigate(self, direction: str) -> None:
        if self.presentation is None or self.state.word_count == 0:
            return
        cursor = self.state.cursor_word
        if direction == "left":
            cursor = max(0, cursor - 1)
        elif direction == "right":
            cursor = min(self.presentation.last_word, cursor + 1)
        elif direction == "up":
            cursor = self.presentation.previous_line(cursor)
        elif direction == "down":
            cursor = self.presentation.next_line(cursor)
        self._replace_state(cursor_word=cursor)

    @Slot(int)
    def change_text_size(self, delta: int) -> None:
        size = min(80, max(20, self.state.text_size + delta))
        self._settings.setValue("overlay/text_size", size)
        self._replace_state(text_size=size)

    @Slot(int)
    def set_background_opacity(self, opacity: int) -> None:
        opacity = min(100, max(20, opacity))
        self._settings.setValue("overlay/background_opacity", opacity)
        self._replace_state(background_opacity=opacity)

    @Slot(int)
    def change_speed(self, delta: int) -> None:
        speed = min(400, max(40, self.state.speed_wpm + delta))
        self._settings.setValue("teleprompter/speed_wpm", speed)
        self._replace_state(speed_wpm=speed)
        self._apply_timer_interval()

    @Slot()
    def open_controls(self) -> None:
        self.control_window.showNormal()
        self.control_window.show()
        self.control_window.raise_()
        self.control_window.activateWindow()

    @Slot()
    def toggle_overlay(self) -> None:
        self.overlay.setVisible(not self.overlay.isVisible())

    @Slot()
    def exit_application(self) -> None:
        self._prepare_shutdown()
        self._app.quit()

    @Slot()
    def _prepare_shutdown(self) -> None:
        if self._shutting_down:
            return
        self._shutting_down = True
        self._scroll_timer.stop()
        self.geometry_store.save(self.overlay, "overlay")
        self.geometry_store.save(self.control_window, "controls")
        self._settings.sync()
        self.hotkey_listener.stop()
        self.tray.hide()

    def _replace_state(self, **changes: object) -> None:
        values = {
            field: getattr(self.state, field)
            for field in self.state.__dataclass_fields__
        }
        values.update(changes)
        self.state = TeleprompterState(**values)
        self.state_changed.emit(self.state)

    def _apply_timer_interval(self) -> None:
        self._scroll_timer.setInterval(round(60_000 / self.state.speed_wpm))

    def _setting_int(self, key: str, default: int, minimum: int, maximum: int) -> int:
        try:
            value = int(self._settings.value(key, default))
        except (TypeError, ValueError):
            value = default
        return min(maximum, max(minimum, value))
