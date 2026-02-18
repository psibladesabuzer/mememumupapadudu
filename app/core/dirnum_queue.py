from __future__ import annotations
from pathlib import Path
import re
from typing import List, Tuple

from app.core.paths import dirnum_queue_path, dirnum_queue_index_path, dirnum_override_path


def parse_dirnums_from_lines(text: str) -> List[str]:
    """
    Принимает 1..200 строк формата: OLDSINGLE/DE/12345 (и т.п.)
    Забирает только числа после последнего '/'.
    """
    out: List[str] = []
    seen = set()

    for raw in (text or "").splitlines():
        s = raw.strip()
        if not s:
            continue
        m = re.search(r"/(\d+)\s*$", s)
        if not m:
            continue
        num = m.group(1)
        if num not in seen:
            seen.add(num)
            out.append(num)

    return out


def save_queue(nums: List[str]) -> None:
    p = dirnum_queue_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(nums) + ("\n" if nums else ""), encoding="utf-8")
    dirnum_queue_index_path().write_text("0", encoding="utf-8")


def load_queue() -> List[str]:
    p = dirnum_queue_path()
    if not p.exists():
        return []
    return [x.strip() for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def load_index() -> int:
    p = dirnum_queue_index_path()
    if not p.exists():
        return 0
    try:
        return max(0, int(p.read_text(encoding="utf-8").strip()))
    except Exception:
        return 0


def save_index(i: int) -> None:
    dirnum_queue_index_path().write_text(str(max(0, i)), encoding="utf-8")


def set_override(value: str) -> None:
    v = (value or "").strip()
    p = dirnum_override_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(v, encoding="utf-8")


def get_override() -> str:
    p = dirnum_override_path()
    if not p.exists():
        return ""
    return (p.read_text(encoding="utf-8") or "").strip()