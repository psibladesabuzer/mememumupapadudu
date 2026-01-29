from pathlib import Path
from datetime import datetime

from app.core.paths import app_data_dir


LOG_FILE = app_data_dir() / "app.log"


def log(msg: str):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}\n"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)
