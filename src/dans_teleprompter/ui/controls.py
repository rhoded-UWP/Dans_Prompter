"""The conventional Control Window shell."""

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from ..controller.application import ApplicationController


class ControlWindow(QMainWindow):
    def __init__(self, controller: "ApplicationController") -> None:
        super().__init__()
        self._controller = controller
        self.setObjectName("controlWindow")
        self.setWindowTitle("Dan's Teleprompter — Controls")
        self.resize(560, 420)

        title = QLabel("Dan's Teleprompter")
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        state = QLabel("Ready — application shell")
        state.setObjectName("applicationState")
        state.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(state)
        layout.addStretch()
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def closeEvent(self, event: object) -> None:  # type: ignore[override]
        if self._controller.shutting_down:
            super().closeEvent(event)  # type: ignore[arg-type]
            return
        event.ignore()  # type: ignore[attr-defined]
        self.hide()
