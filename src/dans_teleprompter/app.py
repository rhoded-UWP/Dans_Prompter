"""Qt application bootstrap."""

import sys
from collections.abc import Sequence

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from .controller.application import ApplicationController


def run_application(argv: Sequence[str] | None = None) -> int:
    """Create the two-window shell and enter the Qt event loop."""

    app = QApplication(list(argv) if argv is not None else sys.argv)
    QCoreApplication.setOrganizationName("Dan's Teleprompter")
    QCoreApplication.setApplicationName("Dan's Teleprompter")
    app.setQuitOnLastWindowClosed(False)

    controller = ApplicationController(app)
    controller.start()
    return app.exec()
