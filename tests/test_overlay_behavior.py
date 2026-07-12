from unittest.mock import Mock

from PySide6.QtCore import QSettings, Qt

from dans_teleprompter.controller.application import ApplicationController
from dans_teleprompter.ui.geometry import WindowGeometryStore


class FakeCaptureExclusion:
    def __init__(self, supported: bool = True, succeeds: bool = True) -> None:
        self.supported = supported
        self.succeeds = succeeds
        self.last_error = None if succeeds else "capture failed"
        self.calls: list[tuple[int, bool]] = []

    def apply(self, window_id: int, enabled: bool) -> bool:
        self.calls.append((window_id, enabled))
        return self.succeeds


def _controller(qapp, tmp_path, monkeypatch, capture=None):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.IniFormat)
    monkeypatch.setattr("dans_teleprompter.controller.application.QSettings", lambda: settings)
    monkeypatch.setattr(
        "dans_teleprompter.controller.application.WindowGeometryStore",
        lambda: WindowGeometryStore(settings),
    )
    fake_capture = capture or FakeCaptureExclusion()
    monkeypatch.setattr(
        "dans_teleprompter.controller.application.CaptureExclusion", lambda: fake_capture
    )
    controller = ApplicationController(qapp)
    controller.hotkey_listener.start = Mock()
    controller.hotkey_listener.stop = Mock()
    controller.tray.show = Mock()
    controller.tray.hide = Mock()
    return controller, fake_capture


def test_overlay_is_always_on_top_frameless_and_has_all_resize_zones(
    qapp, qtbot, tmp_path, monkeypatch
) -> None:
    controller, _ = _controller(qapp, tmp_path, monkeypatch)
    qtbot.addWidget(controller.overlay)

    assert controller.overlay.windowFlags() & Qt.WindowStaysOnTopHint
    assert controller.overlay.windowFlags() & Qt.FramelessWindowHint
    assert len(controller.overlay.resize_handles) == 8


def test_click_through_toggle_changes_native_input_flag(qapp, qtbot, tmp_path, monkeypatch) -> None:
    controller, _ = _controller(qapp, tmp_path, monkeypatch)
    qtbot.addWidget(controller.overlay)

    controller.hotkey_bridge.toggle_click_through_requested.emit()
    assert controller.state.click_through
    assert controller.overlay.windowFlags() & Qt.WindowTransparentForInput

    controller.hotkey_bridge.toggle_click_through_requested.emit()
    assert not controller.state.click_through
    assert not controller.overlay.windowFlags() & Qt.WindowTransparentForInput


def test_capture_exclusion_is_off_by_default_and_calls_checked_adapter(
    qapp, qtbot, tmp_path, monkeypatch
) -> None:
    controller, capture = _controller(qapp, tmp_path, monkeypatch)
    qtbot.addWidget(controller.overlay)

    assert not controller.state.capture_exclusion
    assert capture.calls == []
    controller.set_capture_exclusion(True)

    assert controller.state.capture_exclusion
    assert capture.calls[-1][1] is True


def test_capture_exclusion_failure_remains_off(qapp, qtbot, tmp_path, monkeypatch) -> None:
    controller, _ = _controller(
        qapp, tmp_path, monkeypatch, FakeCaptureExclusion(succeeds=False)
    )
    qtbot.addWidget(controller.overlay)

    controller.set_capture_exclusion(True)

    assert not controller.state.capture_exclusion
    assert controller.state.status == "capture failed"


def test_vamp_restores_click_through_that_was_off(qapp, qtbot, tmp_path, monkeypatch) -> None:
    controller, _ = _controller(qapp, tmp_path, monkeypatch)
    qtbot.addWidget(controller.overlay)

    controller.set_vamp_overlay_mode(True)
    assert controller.state.click_through
    controller.set_vamp_overlay_mode(False)

    assert not controller.state.click_through


def test_vamp_restores_click_through_that_was_on(qapp, qtbot, tmp_path, monkeypatch) -> None:
    controller, _ = _controller(qapp, tmp_path, monkeypatch)
    qtbot.addWidget(controller.overlay)
    controller.set_click_through(True)

    controller.set_vamp_overlay_mode(True)
    controller.set_vamp_overlay_mode(False)

    assert controller.state.click_through


def test_valid_hotkey_rebind_is_persisted(qapp, qtbot, tmp_path, monkeypatch) -> None:
    controller, _ = _controller(qapp, tmp_path, monkeypatch)
    qtbot.addWidget(controller.control_window)
    controller.hotkey_listener.update_bindings = Mock()

    assert controller.update_hotkeys("Ctrl+Shift+O", "Alt+Shift+C")

    assert controller.state.hotkey_open_controls == "Ctrl+Shift+O"
    assert controller.state.hotkey_click_through == "Alt+Shift+C"
    controller.hotkey_listener.update_bindings.assert_called_once()


def test_duplicate_hotkey_rebind_is_rejected(qapp, qtbot, tmp_path, monkeypatch) -> None:
    controller, _ = _controller(qapp, tmp_path, monkeypatch)
    qtbot.addWidget(controller.control_window)
    controller.hotkey_listener.update_bindings = Mock()

    assert not controller.update_hotkeys("Ctrl+Alt+X", "Ctrl+Alt+X")
    assert "Hotkey error" in controller.state.status
    controller.hotkey_listener.update_bindings.assert_not_called()
