from __future__ import annotations
import re
from typing import List

from app.core import paths

def _dirnum_override_path():
    fn = getattr(paths, "dirnum_override_path", None)
    if callable(fn):
        return fn()
    # Backward compatibility if paths.py was partially updated
    return paths.profile_dir() / "dirnum_override.txt"

def parse_dirnums_from_lines(text: str) -> list[str]:
    out: list[str] = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue

        part = line.rsplit("/", 1)[-1].strip()
        if not part:
            continue

        m = re.search(r"\d+", part)
        if not m:
            continue

        out.append(m.group(0))
    return out


def _normalize_kind(kind: str | None) -> str:
    return "html" if (kind or "").strip().lower() == "html" else "db"


def _queue_path(kind: str | None = None):
    k = _normalize_kind(kind)
    if k == "html":
        return paths.profile_dir() / "dirnum_queue_html.txt"
    return paths.dirnum_queue_path()


def _queue_index_path(kind: str | None = None):
    k = _normalize_kind(kind)
    if k == "html":
        return paths.profile_dir() / "dirnum_queue_index_html.txt"
    return paths.dirnum_queue_index_path()


def save_queue(nums: List[str], kind: str | None = None) -> None:
    p = _queue_path(kind)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(nums) + ("\n" if nums else ""), encoding="utf-8")


def load_queue(kind: str | None = None) -> List[str]:
    p = _queue_path(kind)
    if not p.exists():
        return []
    return [x.strip() for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def load_index(kind: str | None = None) -> int:
    p = _queue_index_path(kind)
    if not p.exists():
        return 1
    try:
        raw = p.read_text(encoding="utf-8").strip().lstrip("\ufeff")
        m = re.search(r"\d+", raw)
        if not m:
            return 1
        return max(1, int(m.group(0)))
    except Exception:
        return 1

def save_index(i: int, kind: str | None = None) -> None:
    _queue_index_path(kind).write_text(str(max(1, i)), encoding="utf-8")

def set_override(value: str) -> None:
    v = (value or "").strip()
    p = _dirnum_override_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(v, encoding="utf-8")


def get_override() -> str:
    p = _dirnum_override_path()
    if not p.exists():
        return ""
    return (p.read_text(encoding="utf-8") or "").strip()