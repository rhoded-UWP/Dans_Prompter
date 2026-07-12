from PySide6.QtCore import QRect

from dans_teleprompter.ui.geometry import ScreenArea, recover_geometry


SCREENS = (
    ScreenArea("primary", QRect(0, 0, 1920, 1040)),
    ScreenArea("side", QRect(1920, 0, 1280, 984)),
)


def test_keeps_visible_geometry_on_its_current_screen() -> None:
    saved = QRect(2100, 100, 700, 500)

    assert recover_geometry(saved, SCREENS, "side") == saved


def test_recovers_missing_monitor_geometry_to_primary_screen() -> None:
    recovered = recover_geometry(QRect(4000, 200, 700, 500), SCREENS, "missing")

    assert recovered == QRect(1220, 200, 700, 500)
    assert SCREENS[0].geometry.contains(recovered)


def test_clamps_oversized_geometry_to_available_screen() -> None:
    recovered = recover_geometry(QRect(-5000, -5000, 4000, 3000), (SCREENS[0],), "primary")

    assert recovered == SCREENS[0].geometry


def test_preserves_geometry_when_enough_of_it_is_reachable() -> None:
    saved = QRect(-200, 100, 300, 300)

    assert recover_geometry(saved, SCREENS) == saved


def test_returns_saved_geometry_when_no_screens_are_reported() -> None:
    saved = QRect(20, 30, 400, 300)

    assert recover_geometry(saved, ()) == saved
