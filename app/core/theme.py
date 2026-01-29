from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.core.paths import app_data_dir

THEME_FILE = app_data_dir() / "theme.txt"


def load_theme_name() -> str:
    try:
        v = THEME_FILE.read_text(encoding="utf-8").strip().lower()
        return v if v in {"dark", "light"} else "dark"
    except Exception:
        return "dark"


def save_theme_name(name: str) -> None:
    THEME_FILE.parent.mkdir(parents=True, exist_ok=True)
    THEME_FILE.write_text(name, encoding="utf-8")


def apply_theme(app: QApplication, dark_qss: Path, light_qss: Path, theme_name: str) -> None:
    qss_path = dark_qss if theme_name == "dark" else light_qss
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
    else:
        app.setStyleSheet("")
