"""Control Window for the constant-speed teleprompter."""

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ..controller.state import TeleprompterState

if TYPE_CHECKING:
    from ..controller.application import ApplicationController


class ControlWindow(QMainWindow):
    exit_requested = Signal()

    def __init__(self, controller: "ApplicationController") -> None:
        super().__init__()
        self._controller = controller
        self.setObjectName("controlWindow")
        self.setWindowTitle("Dan's Teleprompter — Controls")
        self.setMinimumSize(480, 500)
        self.resize(560, 590)

        title = QLabel("DAN'S TELEPROMPTER")
        title.setObjectName("title")
        subtitle = QLabel("CONSTANT-SPEED STUDIO")
        subtitle.setObjectName("subtitle")
        self.state_label = QLabel("Open a .txt script to begin")
        self.state_label.setObjectName("applicationState")
        self.state_label.setWordWrap(True)

        self.open_button = QPushButton("OPEN .TXT SCRIPT")
        self.open_button.setObjectName("primaryButton")
        self.open_button.clicked.connect(self._open_script)
        self.play_button = QPushButton("START")
        self.play_button.setObjectName("transportButton")
        self.play_button.clicked.connect(controller.toggle_pause)
        self.exit_button = QPushButton("EXIT APPLICATION")
        self.exit_button.setObjectName("exitButton")
        self.exit_button.setToolTip("Gracefully close both windows and stop the application")
        self.exit_button.clicked.connect(self.exit_requested)

        self.speed_value = QLabel("130 WPM")
        self.text_value = QLabel("38 PX")
        self.opacity_value = QLabel("88%")
        self.section_value = QLabel("SECTION 1  ·  TAKE 1")

        slower = QPushButton("[")
        faster = QPushButton("]")
        smaller = QPushButton("−")
        larger = QPushButton("+")
        slower.clicked.connect(lambda: controller.change_speed(-10))
        faster.clicked.connect(lambda: controller.change_speed(10))
        smaller.clicked.connect(lambda: controller.change_text_size(-2))
        larger.clicked.connect(lambda: controller.change_text_size(2))

        opacity = QSlider(Qt.Horizontal)
        opacity.setObjectName("opacitySlider")
        opacity.setRange(20, 100)
        opacity.setValue(controller.state.background_opacity)
        opacity.valueChanged.connect(controller.set_background_opacity)
        self.opacity_slider = opacity

        transport = QHBoxLayout()
        transport.addWidget(self.open_button, 2)
        transport.addWidget(self.play_button, 1)

        tuning = QGridLayout()
        tuning.setHorizontalSpacing(8)
        tuning.setVerticalSpacing(12)
        tuning.addWidget(QLabel("SCROLL RATE"), 0, 0)
        tuning.addWidget(self.speed_value, 0, 1)
        tuning.addWidget(slower, 0, 2)
        tuning.addWidget(faster, 0, 3)
        tuning.addWidget(QLabel("TEXT SIZE"), 1, 0)
        tuning.addWidget(self.text_value, 1, 1)
        tuning.addWidget(smaller, 1, 2)
        tuning.addWidget(larger, 1, 3)
        tuning.addWidget(QLabel("BACKGROUND"), 2, 0)
        tuning.addWidget(self.opacity_value, 2, 1)
        tuning.addWidget(opacity, 2, 2, 1, 2)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        layout = QVBoxLayout()
        layout.setContentsMargins(28, 26, 28, 24)
        layout.setSpacing(13)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addWidget(self.state_label)
        layout.addLayout(transport)
        layout.addWidget(divider)
        layout.addWidget(self.section_value)
        layout.addSpacing(6)
        layout.addLayout(tuning)
        layout.addStretch()
        hint = QLabel("OVERLAY KEYS  ← → WORD  ·  ↑ ↓ PARAGRAPH  ·  + − TEXT  ·  [ ] SPEED")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addWidget(self.exit_button)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.setStyleSheet(self._stylesheet())
        controller.state_changed.connect(self.apply_state)

    def apply_state(self, state: TeleprompterState) -> None:
        self.state_label.setText(state.status)
        self.play_button.setText("START" if state.paused else "PAUSE")
        self.speed_value.setText(f"{state.speed_wpm} WPM")
        self.text_value.setText(f"{state.text_size} PX")
        self.opacity_value.setText(f"{state.background_opacity}%")
        self.opacity_slider.blockSignals(True)
        self.opacity_slider.setValue(state.background_opacity)
        self.opacity_slider.blockSignals(False)
        section = 0
        if self._controller.presentation is not None:
            section = self._controller.presentation.section_at(state.cursor_word)
        take = state.take_counts[min(section, len(state.take_counts) - 1)]
        self.section_value.setText(f"SECTION {section + 1}  ·  TAKE {take}")

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._controller.shutting_down:
            super().closeEvent(event)
            return
        event.ignore()
        self.hide()

    def _open_script(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open Teleprompter Script", str(Path.home()), "Text Scripts (*.txt)")
        if path:
            self._controller.load_script_file(path)

    def _stylesheet(self) -> str:
        return """
            QMainWindow, QWidget { background: #202329; color: #e7e3db; font-family: 'Segoe UI'; }
            #title { color: #f2b866; font: 700 23px 'Georgia'; letter-spacing: 2px; }
            #subtitle, #hint { color: #777f8a; font: 600 10px 'Segoe UI'; letter-spacing: 1px; }
            #applicationState { color: #c8cbd0; background: #292d34; border-left: 3px solid #f2b866; padding: 12px; }
            QPushButton { color: #dfe2e6; background: #30353d; border: 1px solid #434954; padding: 9px 12px; font-weight: 600; }
            QPushButton:hover { border-color: #f2b866; color: #f2b866; }
            #primaryButton { background: #f2b866; color: #1a1c20; border: 0; }
            #transportButton { background: #343a43; }
            #exitButton { color: #b8bec6; background: transparent; border-color: #4b5059; }
            #exitButton:hover { color: #ff8a78; border-color: #ff8a78; }
            QSlider::groove:horizontal { height: 4px; background: #414751; }
            QSlider::handle:horizontal { width: 15px; margin: -6px 0; border-radius: 7px; background: #f2b866; }
            QFrame[frameShape="4"] { color: #3a3f48; }
        """
