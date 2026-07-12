"""Windows screen-capture exclusion adapter."""

import ctypes
import sys


WDA_NONE = 0x00000000
WDA_EXCLUDEFROMCAPTURE = 0x00000011


class CaptureExclusion:
    """Apply SetWindowDisplayAffinity and retain a useful failure reason."""

    def __init__(self) -> None:
        self.supported = sys.platform == "win32"
        self.last_error: str | None = None

    def apply(self, window_id: int, enabled: bool) -> bool:
        if not self.supported:
            self.last_error = "Capture exclusion is available only on Windows."
            return False
        affinity = WDA_EXCLUDEFROMCAPTURE if enabled else WDA_NONE
        try:
            success = bool(ctypes.windll.user32.SetWindowDisplayAffinity(window_id, affinity))
        except (AttributeError, OSError) as exc:
            self.last_error = f"Capture exclusion API unavailable: {exc}"
            return False
        if not success:
            code = ctypes.get_last_error()
            self.last_error = f"Windows rejected capture exclusion (error {code})."
            return False
        self.last_error = None
        return True
