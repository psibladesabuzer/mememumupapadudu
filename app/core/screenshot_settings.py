import json
from typing import TypedDict, Optional
from app.core.paths import screenshot_screen_path


class ScreenshotScreenSettings(TypedDict):
    mode: str              # "auto" | "screen"
    index: Optional[int]   # индекс экрана


def load_screenshot_screen_settings() -> ScreenshotScreenSettings:
    p = screenshot_screen_path()
    if not p.exists():
        return {"mode": "auto", "index": None}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        mode = data.get("mode", "auto")
        idx = data.get("index", None)
        if mode not in ("auto", "screen"):
            mode = "auto"
        if idx is not None:
            try:
                idx = int(idx)
            except Exception:
                idx = None
        return {"mode": mode, "index": idx}
    except Exception:
        return {"mode": "auto", "index": None}


def save_screenshot_screen_settings(mode: str, index: Optional[int]) -> None:
    if mode not in ("auto", "screen"):
        mode = "auto"
        index = None
    p = screenshot_screen_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps({"mode": mode, "index": index}, ensure_ascii=False),
        encoding="utf-8",
    )
