from unittest.mock import Mock

from PySide6.QtCore import QSettings

from dans_teleprompter.controller.application import ApplicationController
from dans_teleprompter.ui.geometry import WindowGeometryStore


def _controller(qapp, tmp_path, monkeypatch):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.IniFormat)
    monkeypatch.setattr(
        "dans_teleprompter.controller.application.WindowGeometryStore",
        lambda: WindowGeometryStore(settings),
    )
    controller = ApplicationController(qapp)
    controller.hotkey_listener.start = Mock()
    controller.hotkey_listener.stop = Mock()
    controller.tray.show = Mock()
    controller.tray.hide = Mock()
    return controller


def test_both_windows_open_at_launch(qapp, qtbot, tmp_path, monkeypatch) -> None:
    controller = _controller(qapp, tmp_path, monkeypatch)
    qtbot.addWidget(controller.control_window)
    qtbot.addWidget(controller.overlay)

    controller.start()

    assert controller.control_window.isVisible()
    assert controller.overlay.isVisible()


def test_open_controls_link_restores_same_control_window(qapp, qtbot, tmp_path, monkeypatch) -> None:
    controller = _controller(qapp, tmp_path, monkeypatch)
    qtbot.addWidget(controller.control_window)
    qtbot.addWidget(controller.overlay)
    controller.start()
    original = controller.control_window
    original.hide()

    controller.overlay.findChild(object, "openControls").click()

    assert controller.control_window is original
    assert original.isVisible()


def test_hotkey_bridge_restores_controls(qapp, qtbot, tmp_path, monkeypatch) -> None:
    controller = _controller(qapp, tmp_path, monkeypatch)
    qtbot.addWidget(controller.control_window)
    qtbot.addWidget(controller.overlay)
    controller.start()
    controller.control_window.hide()

    controller.hotkey_bridge.open_controls_requested.emit()

    assert controller.control_window.isVisible()


def test_closing_controls_hides_it_without_closing_overlay(qapp, qtbot, tmp_path, monkeypatch) -> None:
    controller = _controller(qapp, tmp_path, monkeypatch)
    qtbot.addWidget(controller.control_window)
    qtbot.addWidget(controller.overlay)
    controller.start()

    controller.control_window.close()

    assert not controller.control_window.isVisible()
    assert controller.overlay.isVisible()


def test_geometry_is_stored_independently(qapp, qtbot, tmp_path, monkeypatch) -> None:
    controller = _controller(qapp, tmp_path, monkeypatch)
    qtbot.addWidget(controller.control_window)
    qtbot.addWidget(controller.overlay)
    controller.start()
    controller.control_window.setGeometry(40, 50, 500, 400)
    controller.overlay.setGeometry(700, 100, 800, 300)

    controller.geometry_store.save(controller.control_window, "controls")
    controller.geometry_store.save(controller.overlay, "overlay")

    settings = controller.geometry_store._settings
    assert settings.value("windows/controls/geometry") != settings.value("windows/overlay/geometry")
