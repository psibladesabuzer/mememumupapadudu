from __future__ import annotations

from pathlib import Path
import shutil


def ensure_template(src_tpl: Path, dst_tpl: Path) -> None:
    """
    Копирует шаблон в dst, если:
    - файла нет
    - или содержимое отличается (обновление)
    """
    dst_tpl.parent.mkdir(parents=True, exist_ok=True)

    if not src_tpl.exists():
        raise FileNotFoundError(f"Template not found: {src_tpl}")

    if dst_tpl.exists():
        try:
            if src_tpl.read_bytes() == dst_tpl.read_bytes():
                return
        except Exception:
            pass

    shutil.copyfile(src_tpl, dst_tpl)


# Backward-compatible alias (если в проекте уже есть вызовы ensure_index_template)
def ensure_index_template(src_tpl: Path, dst_tpl: Path) -> None:
    ensure_template(src_tpl, dst_tpl)
