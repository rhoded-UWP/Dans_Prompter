"""Independent window geometry persistence and missing-monitor recovery."""

from dataclasses import dataclass

from PySide6.QtCore import QRect, QSettings
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget


@dataclass(frozen=True, slots=True)
class ScreenArea:
    name: str
    geometry: QRect


def recover_geometry(
    saved: QRect,
    screens: tuple[ScreenArea, ...],
    preferred_screen: str | None = None,
) -> QRect:
    """Return a visible geometry, preferring the recorded monitor when present."""

    if not screens:
        return QRect(saved)

    preferred = next((screen for screen in screens if screen.name == preferred_screen), None)
    if preferred is not None:
        target = preferred.geometry
    else:
        visible = next(
            (
                screen
                for screen in screens
                if saved.intersected(screen.geometry).width() >= 48
                and saved.intersected(screen.geometry).height() >= 48
            ),
            None,
        )
        if visible is not None:
            return QRect(saved)
        target = screens[0].geometry

    width = min(max(saved.width(), 240), target.width())
    height = min(max(saved.height(), 160), target.height())
    x = min(max(saved.x(), target.left()), target.right() - width + 1)
    y = min(max(saved.y(), target.top()), target.bottom() - height + 1)
    return QRect(x, y, width, height)


class WindowGeometryStore:
    """Save each primary window separately in QSettings."""

    def __init__(self, settings: QSettings | None = None) -> None:
        self._settings = settings or QSettings()

    def save(self, window: QWidget, key: str) -> None:
        self._settings.setValue(f"windows/{key}/geometry", window.normalGeometry())
        screen = window.screen()
        self._settings.setValue(f"windows/{key}/screen", screen.name() if screen else "")
        self._settings.sync()

    def restore(self, window: QWidget, key: str) -> None:
        value = self._settings.value(f"windows/{key}/geometry")
        if not isinstance(value, QRect) or not value.isValid():
            return
        screen_name = self._settings.value(f"windows/{key}/screen", "", str)
        screens = tuple(
            ScreenArea(screen.name(), screen.availableGeometry())
            for screen in QGuiApplication.screens()
        )
        window.setGeometry(recover_geometry(value, screens, screen_name or None))
