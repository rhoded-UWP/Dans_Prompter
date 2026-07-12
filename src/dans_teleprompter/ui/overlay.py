"""Frameless teleprompter reading surface."""

from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent, QPoint, QRect, Qt, Signal
from PySide6.QtGui import QCloseEvent, QKeyEvent, QMouseEvent, QResizeEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..controller.state import TeleprompterState
from .script_view import ScriptView

if TYPE_CHECKING:
    from ..controller.application import ApplicationController


class PrompterOverlay(QMainWindow):
    open_controls_requested = Signal()
    exit_requested = Signal()
    word_clicked = Signal(int)
    navigation_requested = Signal(str)
    text_size_requested = Signal(int)
    speed_requested = Signal(int)
    native_handle_changed = Signal()

    def __init__(self, controller: "ApplicationController") -> None:
        super().__init__()
        self._controller = controller
        self._drag_offset: QPoint | None = None
        self.setObjectName("prompterOverlay")
        self.setWindowTitle("Dan's Teleprompter — Overlay")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setMinimumSize(420, 240)
        self.resize(860, 460)

        self.header = QFrame()
        self.header.setObjectName("overlayHeader")
        header_layout = QVBoxLayout(self.header)
        header_layout.setContentsMargins(16, 9, 16, 5)
        self.open_controls = QPushButton("CONTROLS  ↗")
        self.open_controls.setObjectName("openControls")
        self.open_controls.setCursor(Qt.PointingHandCursor)
        self.open_controls.clicked.connect(self.open_controls_requested)
        self.exit_button = QPushButton("EXIT  ×")
        self.exit_button.setObjectName("exitApplication")
        self.exit_button.setCursor(Qt.PointingHandCursor)
        self.exit_button.setToolTip("Exit Dan's Teleprompter")
        self.exit_button.clicked.connect(self.exit_requested)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.open_controls, 0, Qt.AlignLeft)
        row.addStretch()
        row.addWidget(self.exit_button, 0, Qt.AlignRight)
        header_layout.addLayout(row)

        self.paused_banner = QLabel("PAUSED")
        self.paused_banner.setObjectName("pausedBanner")
        self.paused_banner.setAlignment(Qt.AlignCenter)
        self.script_view = ScriptView()
        self.script_view.word_clicked.connect(self.word_clicked)
        self.resize_handles = _create_resize_handles(self)

        layout = QVBoxLayout()
        layout.setContentsMargins(7, 7, 7, 7)
        layout.setSpacing(0)
        layout.addWidget(self.header)
        layout.addWidget(self.paused_banner)
        layout.addWidget(self.script_view, 1)
        self.container = QWidget()
        self.container.setObjectName("overlayBackground")
        self.container.setLayout(layout)
        self.setCentralWidget(self.container)
        self._apply_styles(88)
        controller.state_changed.connect(self.apply_state)

    def apply_state(self, state: TeleprompterState) -> None:
        self.paused_banner.setVisible(state.paused and state.script is not None)
        self._apply_styles(state.background_opacity)
        self.script_view.render(self._controller.presentation, state)

    def apply_click_through(self, enabled: bool) -> None:
        was_visible = self.isVisible()
        self.setWindowFlag(Qt.WindowTransparentForInput, enabled)
        if was_visible:
            self.show()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        _position_resize_handles(self.resize_handles, self.rect())

    def event(self, event: QEvent) -> bool:
        result = super().event(event)
        if event.type() == QEvent.WinIdChange:
            self.native_handle_changed.emit()
        return result

    def keyPressEvent(self, event: QKeyEvent) -> None:
        directions = {
            Qt.Key_Left: "left",
            Qt.Key_Right: "right",
            Qt.Key_Up: "up",
            Qt.Key_Down: "down",
        }
        if event.key() in directions:
            self.navigation_requested.emit(directions[event.key()])
            event.accept()
        elif event.key() in (Qt.Key_Plus, Qt.Key_Equal):
            self.text_size_requested.emit(2)
            event.accept()
        elif event.key() == Qt.Key_Minus:
            self.text_size_requested.emit(-2)
            event.accept()
        elif event.key() == Qt.Key_BracketLeft:
            self.speed_requested.emit(-10)
            event.accept()
        elif event.key() == Qt.Key_BracketRight:
            self.speed_requested.emit(10)
            event.accept()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self.header.geometry().contains(event.position().toPoint()):
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

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._controller.shutting_down:
            super().closeEvent(event)
            return
        event.ignore()
        self.hide()

    def _apply_styles(self, opacity: int) -> None:
        alpha = round(255 * opacity / 100)
        self.container.setStyleSheet(
            f"""
            #overlayBackground {{ background: rgba(18, 20, 24, {alpha}); }}
            #overlayHeader {{ background: rgba(28, 31, 36, {min(255, alpha + 15)}); border-bottom: 1px solid #343840; }}
            #openControls {{ color: #aeb5bf; background: transparent; border: 0; font: 600 11px 'Segoe UI'; letter-spacing: 1px; }}
            #openControls:hover {{ color: #f2b866; }}
            #exitApplication {{ color: #89909a; background: transparent; border: 0; font: 600 11px 'Segoe UI'; letter-spacing: 1px; }}
            #exitApplication:hover {{ color: #ff8a78; }}
            #pausedBanner {{ color: #17191d; background: #f2b866; padding: 7px; font: 700 13px 'Segoe UI'; letter-spacing: 3px; }}
            """
        )


class _ResizeHandle(QFrame):
    def __init__(self, parent: QWidget, edges: Qt.Edge, cursor: Qt.CursorShape) -> None:
        super().__init__(parent)
        self.edges = edges
        self.setObjectName("resizeHandle")
        self.setCursor(cursor)
        self.setStyleSheet("background: transparent;")
        self.raise_()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self.window().windowHandle() is not None:
            self.window().windowHandle().startSystemResize(self.edges)
            event.accept()
            return
        super().mousePressEvent(event)


def _create_resize_handles(parent: QWidget) -> dict[str, _ResizeHandle]:
    return {
        "top": _ResizeHandle(parent, Qt.TopEdge, Qt.SizeVerCursor),
        "bottom": _ResizeHandle(parent, Qt.BottomEdge, Qt.SizeVerCursor),
        "left": _ResizeHandle(parent, Qt.LeftEdge, Qt.SizeHorCursor),
        "right": _ResizeHandle(parent, Qt.RightEdge, Qt.SizeHorCursor),
        "top_left": _ResizeHandle(parent, Qt.TopEdge | Qt.LeftEdge, Qt.SizeFDiagCursor),
        "top_right": _ResizeHandle(parent, Qt.TopEdge | Qt.RightEdge, Qt.SizeBDiagCursor),
        "bottom_left": _ResizeHandle(parent, Qt.BottomEdge | Qt.LeftEdge, Qt.SizeBDiagCursor),
        "bottom_right": _ResizeHandle(parent, Qt.BottomEdge | Qt.RightEdge, Qt.SizeFDiagCursor),
    }


def _position_resize_handles(handles: dict[str, _ResizeHandle], bounds: QRect) -> None:
    edge, corner = 7, 14
    handles["top"].setGeometry(corner, 0, max(0, bounds.width() - 2 * corner), edge)
    handles["bottom"].setGeometry(corner, bounds.height() - edge, max(0, bounds.width() - 2 * corner), edge)
    handles["left"].setGeometry(0, corner, edge, max(0, bounds.height() - 2 * corner))
    handles["right"].setGeometry(bounds.width() - edge, corner, edge, max(0, bounds.height() - 2 * corner))
    handles["top_left"].setGeometry(0, 0, corner, corner)
    handles["top_right"].setGeometry(bounds.width() - corner, 0, corner, corner)
    handles["bottom_left"].setGeometry(0, bounds.height() - corner, corner, corner)
    handles["bottom_right"].setGeometry(bounds.width() - corner, bounds.height() - corner, corner, corner)
    for handle in handles.values():
        handle.raise_()
