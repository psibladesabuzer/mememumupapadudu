from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon

from app.ui.main_window import MainWindow
from app.core.theme import load_theme_name, apply_theme


def resource_path(relative: str) -> Path:
    if hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        return base / relative
    return Path(__file__).resolve().parents[1] / relative


def main() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    dark_qss = resource_path("app/ui/style.qss")
    light_qss = resource_path("app/ui/style_light.qss")

    theme_name = load_theme_name()
    try:
        apply_theme(app, dark_qss, light_qss, theme_name)
    except Exception as e:
        QMessageBox.warning(None, "WorkerHotkeys", f"Не удалось применить тему'test.\n\n{type(e).__name__}: {e}")

    ico = resource_path("assets/appicona.ico")
    png = resource_path("assets/appicona.png")
    if ico.exists():
        app.setWindowIcon(QIcon(str(ico)))
    elif png.exists():
        app.setWindowIcon(QIcon(str(png)))

    w = MainWindow()
    w.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
