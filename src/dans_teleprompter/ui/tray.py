"""System tray recovery and lifecycle menu."""

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

if TYPE_CHECKING:
    from ..controller.application import ApplicationController


def _tray_icon() -> QIcon:
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setBrush(QColor("#4b8cf7"))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(2, 2, 28, 28, 6, 6)
    painter.setPen(QColor("white"))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "D")
    painter.end()
    return QIcon(pixmap)


class SystemTray(QObject):
    open_controls_requested = Signal()
    toggle_overlay_requested = Signal()
    exit_requested = Signal()

    def __init__(self, controller: "ApplicationController") -> None:
        super().__init__(controller)
        self.icon = QSystemTrayIcon(_tray_icon(), controller)
        self.icon.setToolTip("Dan's Teleprompter")
        menu = QMenu()
        menu.addAction("Open Control Window", self.open_controls_requested.emit)
        menu.addAction("Show or Hide Prompter Overlay", self.toggle_overlay_requested.emit)
        menu.addSeparator()
        menu.addAction("Exit Application", self.exit_requested.emit)
        self.icon.setContextMenu(menu)
        self.icon.activated.connect(self._activated)

    def show(self) -> None:
        self.icon.show()

    def hide(self) -> None:
        self.icon.hide()

    def _activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            self.open_controls_requested.emit()
