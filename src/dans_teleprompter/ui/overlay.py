"""Frameless, movable, resizable Prompter Overlay shell."""

from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QLabel, QMainWindow, QPushButton, QSizeGrip, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from ..controller.application import ApplicationController


class PrompterOverlay(QMainWindow):
    open_controls_requested = Signal()

    def __init__(self, controller: "ApplicationController") -> None:
        super().__init__()
        self._controller = controller
        self._drag_offset: QPoint | None = None
        self.setObjectName("prompterOverlay")
        self.setWindowTitle("Dan's Teleprompter — Overlay")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setMinimumSize(320, 180)
        self.resize(760, 360)

        open_controls = QPushButton("Open Controls")
        open_controls.setObjectName("openControls")
        open_controls.setCursor(Qt.PointingHandCursor)
        open_controls.clicked.connect(self.open_controls_requested)
        prompt = QLabel("Open a script from the Control Window.")
        prompt.setObjectName("promptPlaceholder")
        prompt.setAlignment(Qt.AlignCenter)
        prompt.setStyleSheet("font-size: 28px; color: #f4f4f4;")
        grip = QSizeGrip(self)

        layout = QVBoxLayout()
        layout.addWidget(open_controls, 0, Qt.AlignLeft)
        layout.addStretch()
        layout.addWidget(prompt)
        layout.addStretch()
        layout.addWidget(grip, 0, Qt.AlignRight | Qt.AlignBottom)
        container = QWidget()
        container.setObjectName("overlayBackground")
        container.setStyleSheet("#overlayBackground { background: rgba(18, 18, 20, 225); }")
        container.setLayout(layout)
        self.setCentralWidget(container)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def closeEvent(self, event: object) -> None:  # type: ignore[override]
        if self._controller.shutting_down:
            super().closeEvent(event)  # type: ignore[arg-type]
            return
        event.ignore()  # type: ignore[attr-defined]
        self.hide()
