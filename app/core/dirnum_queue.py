from __future__ import annotations
from pathlib import Path
import re
from typing import List, Tuple

from app.core.paths import dirnum_queue_path, dirnum_queue_index_path, dirnum_override_path


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


def save_queue(nums: List[str]) -> None:
    p = dirnum_queue_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(nums) + ("\n" if nums else ""), encoding="utf-8")


def load_queue() -> List[str]:
    p = dirnum_queue_path()
    if not p.exists():
        return []
    return [x.strip() for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def load_index() -> int:
    p = dirnum_queue_index_path()
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

def save_index(i: int) -> None:
    dirnum_queue_index_path().write_text(str(max(1, i)), encoding="utf-8")

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