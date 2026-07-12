"""Shared owner for the two-window application shell."""

from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QApplication

from ..input.hotkeys import GlobalHotkeyListener, HotkeyBridge
from ..ui.controls import ControlWindow
from ..ui.geometry import WindowGeometryStore
from ..ui.overlay import PrompterOverlay
from ..ui.tray import SystemTray


class ApplicationController(QObject):
    """Own exactly one overlay, control window, tray, and hotkey listener."""

    def __init__(self, app: QApplication) -> None:
        super().__init__()
        self._app = app
        self._shutting_down = False
        self.geometry_store = WindowGeometryStore()
        self.control_window = ControlWindow(self)
        self.overlay = PrompterOverlay(self)
        self.tray = SystemTray(self)
        self.hotkey_bridge = HotkeyBridge(self)
        self.hotkey_listener = GlobalHotkeyListener(self.hotkey_bridge)

        self.overlay.open_controls_requested.connect(self.open_controls)
        self.hotkey_bridge.open_controls_requested.connect(self.open_controls)
        self.tray.open_controls_requested.connect(self.open_controls)
        self.tray.toggle_overlay_requested.connect(self.toggle_overlay)
        self.tray.exit_requested.connect(self.exit_application)
        self._app.aboutToQuit.connect(self._prepare_shutdown)

    @property
    def shutting_down(self) -> bool:
        return self._shutting_down

    def start(self) -> None:
        """Restore and show both primary windows, then start integrations."""

        self.geometry_store.restore(self.overlay, "overlay")
        self.geometry_store.restore(self.control_window, "controls")
        self.overlay.show()
        self.control_window.show()
        self.tray.show()
        self.hotkey_listener.start()

    @Slot()
    def open_controls(self) -> None:
        """Restore the existing Control Window without changing session state."""

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
        self.geometry_store.save(self.overlay, "overlay")
        self.geometry_store.save(self.control_window, "controls")
        self.hotkey_listener.stop()
        self.tray.hide()
