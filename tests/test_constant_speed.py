from unittest.mock import Mock

from PySide6.QtCore import QSettings, Qt, QUrl

from dans_teleprompter.controller.application import ApplicationController
from dans_teleprompter.scripts import parse_text
from dans_teleprompter.ui.geometry import WindowGeometryStore


def _controller(qapp, tmp_path, monkeypatch):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.IniFormat)
    monkeypatch.setattr(
        "dans_teleprompter.controller.application.QSettings", lambda: settings
    )
    monkeypatch.setattr(
        "dans_teleprompter.controller.application.WindowGeometryStore",
        lambda configured=None: WindowGeometryStore(settings),
    )
    controller = ApplicationController(qapp)
    controller.hotkey_listener.start = Mock()
    controller.hotkey_listener.stop = Mock()
    controller.tray.show = Mock()
    controller.tray.hide = Mock()
    return controller


def test_renders_text_states_notes_vamp_and_take_count(qapp, qtbot, tmp_path, monkeypatch) -> None:
    controller = _controller(qapp, tmp_path, monkeypatch)
    qtbot.addWidget(controller.overlay)
    qtbot.addWidget(controller.control_window)
    controller.set_script(
        parse_text("## Intro\nFirst second third.\n-- Breathe\n<<VAMP: Demo now>>", "demo.txt")
    )
    controller.navigate("right")

    text = controller.overlay.script_view.toPlainText()
    html = controller.overlay.script_view.toHtml()

    assert "First" in text and "second" in text and "third" in text
    assert "Breathe" in text
    assert "VAMP OFF" in text and "Demo now" in text
    assert "TAKE 1" in text
    assert "#626871" in html  # spoken
    assert "#f2b866" in html  # current
    assert "#f5f1e9" in html  # upcoming


def test_exact_word_click_moves_cursor_and_backward_click_increments_take(
    qapp, qtbot, tmp_path, monkeypatch
) -> None:
    controller = _controller(qapp, tmp_path, monkeypatch)
    qtbot.addWidget(controller.overlay)
    qtbot.addWidget(controller.control_window)
    controller.set_script(parse_text("One two three four."))
    controller.set_cursor_from_click(3)

    controller.overlay.script_view._anchor_clicked(QUrl("word:1"))

    assert controller.state.cursor_word == 1
    assert controller.state.take_counts == (2,)


def test_arrow_navigation_moves_by_word_and_paragraph(qapp, qtbot, tmp_path, monkeypatch) -> None:
    controller = _controller(qapp, tmp_path, monkeypatch)
    qtbot.addWidget(controller.overlay)
    qtbot.addWidget(controller.control_window)
    controller.set_script(parse_text("One two.\n\nThree four."))

    qtbot.keyClick(controller.overlay, Qt.Key_Right)
    assert controller.state.cursor_word == 1
    qtbot.keyClick(controller.overlay, Qt.Key_Down)
    assert controller.state.cursor_word == 2
    qtbot.keyClick(controller.overlay, Qt.Key_Up)
    assert controller.state.cursor_word == 0
    assert controller.state.take_counts == (1,)


def test_text_size_speed_and_opacity_controls_are_bounded(qapp, qtbot, tmp_path, monkeypatch) -> None:
    controller = _controller(qapp, tmp_path, monkeypatch)
    qtbot.addWidget(controller.overlay)
    qtbot.addWidget(controller.control_window)

    controller.change_text_size(4)
    controller.change_speed(20)
    controller.set_background_opacity(72)

    assert controller.state.text_size == 42
    assert controller.state.speed_wpm == 150
    assert controller.state.background_opacity == 72
    assert controller._scroll_timer.interval() == 400
    assert "184" in controller.overlay.container.styleSheet()  # round(72% * 255)


def test_constant_speed_advances_and_pauses_at_end(qapp, qtbot, tmp_path, monkeypatch) -> None:
    controller = _controller(qapp, tmp_path, monkeypatch)
    qtbot.addWidget(controller.overlay)
    qtbot.addWidget(controller.control_window)
    controller.set_script(parse_text("One two."))

    controller.toggle_pause()
    assert not controller.state.paused
    assert controller._scroll_timer.isActive()
    controller.advance_word()
    assert controller.state.cursor_word == 1
    controller.advance_word()

    assert controller.state.paused
    assert controller.state.status == "Finished"
    assert not controller._scroll_timer.isActive()


def test_paused_banner_tracks_pause_state(qapp, qtbot, tmp_path, monkeypatch) -> None:
    controller = _controller(qapp, tmp_path, monkeypatch)
    qtbot.addWidget(controller.overlay)
    qtbot.addWidget(controller.control_window)
    controller.set_script(parse_text("One two."))

    assert not controller.overlay.paused_banner.isHidden()
    controller.toggle_pause()
    assert controller.overlay.paused_banner.isHidden()
