from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from MOMM_frontend.backend_interface import BackendInterface


def main() -> int:
    app = QGuiApplication(sys.argv)
    app.setApplicationName("MOMM")
    app.setOrganizationName("MOMM")

    frontend_dir = Path(__file__).resolve().parent
    qml_file = frontend_dir / "qml" / "Main.qml"

    backend = BackendInterface()

    engine = QQmlApplicationEngine()
    context = engine.rootContext()
    context.setContextProperty("backend", backend)
    context.setContextProperty("mainListModel", backend.main_list_model)

    engine.load(str(qml_file))

    if not engine.rootObjects():
        return 1

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
