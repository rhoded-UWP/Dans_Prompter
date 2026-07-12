import pytest

from dans_teleprompter.input.hotkeys import (
    GlobalHotkeyListener,
    HotkeyBridge,
    HotkeyBindings,
    normalize_hotkey,
    to_pynput,
    validate_bindings,
)


def test_normalizes_rebindable_hotkey() -> None:
    assert normalize_hotkey(" alt + shift + 7 ") == "Alt+Shift+7"
    assert to_pynput("Ctrl+Alt+C") == "<ctrl>+<alt>+c"


@pytest.mark.parametrize("value", ["C", "Ctrl+Alt", "Ctrl+Ctrl+C", "Ctrl+F12", ""])
def test_rejects_invalid_global_hotkey(value: str) -> None:
    with pytest.raises(ValueError):
        normalize_hotkey(value)


def test_rejects_duplicate_bindings() -> None:
    with pytest.raises(ValueError, match="unique"):
        validate_bindings(HotkeyBindings("Ctrl+Alt+C", "Ctrl+Alt+C"))


def test_rebinding_retries_when_registration_was_requested(monkeypatch) -> None:
    listener = GlobalHotkeyListener(HotkeyBridge())
    listener._running_requested = True
    starts = []
    monkeypatch.setattr(listener, "start", lambda: starts.append(True))

    listener.update_bindings(HotkeyBindings("Ctrl+Shift+O", "Ctrl+Shift+C"))

    assert starts == [True]
