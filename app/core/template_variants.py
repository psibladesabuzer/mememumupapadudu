from __future__ import annotations

from pathlib import Path
import re


def _comment_line(s: str) -> str:
    if s.lstrip().startswith("//"):
        return s
    return "// " + s


def _uncomment_first4(s: str) -> str:
    if len(s) >= 4:
        return s[4:]
    return ""


def _replace_dirnum_define(line: str, dir_num: str) -> str:
    """
    Ищем строку вида: define('DIR_NUM', 123);
    и заменяем <любое_число> на dir_num.
    """
    pattern = r"(define\s*\(\s*['\"]DIR_NUM['\"]\s*,\s*)(\d+|__DIR_NUM__)(\s*\)\s*;)"
    return re.sub(pattern, r"\g<1>" + dir_num + r"\g<3>", line, count=1)


def _comment_range(lines: list[str], a: int, b: int) -> None:
    for i in range(a, b + 1):
        if 1 <= i <= len(lines):
            lines[i - 1] = _comment_line(lines[i - 1])


def _apply_db_dirnum_all(variants: list[list[str]], dir_num: str) -> None:
    """
    DB: в строке 4 (index=3) заменяем define('DIR_NUM', N) на dir_num во всех вариантах.
    """
    dn = (dir_num or "").strip()
    if not dn:
        return

    for v in variants:
        if len(v) < 4:
            continue
        v[3] = _replace_dirnum_define(v[3], dn)


def _replace_html_url_dirnum_in_line(line: str, dir_num: str) -> str:
    """
    HTML: в строке $url = '.../SOME-PREFIX-BENL-1/'; заменить число после последнего '-'
    (перед '/...') на dir_num.

    Работает аккуратно:
    - сохраняет кавычки, пробелы и ';'
    - не ломает, если формат другой (вернёт исходную строку)
    """
    dn = (dir_num or "").strip()
    if not dn:
        return line

    # Быстрый отсев: строка должна начинаться с $url (после пробелов)
    if not line.lstrip().startswith("$url"):
        return line

    # Меняем число в "последнем сегменте":
    # ...-<digits>/<возможные кавычки/пробелы/; в конце>
    #
    # Группа 1: всё до числа включая последний '-'
    # Группа 2: само число
    # Группа 3: остаток начиная с / и дальше (/', /";, /' ; ...)
    pattern = r"(.*-)(\d+)(/\s*['\"]?\s*;?\s*)$"
    # Если в конце есть ещё символы после / (например /foo'), то этот паттерн не сработает.
    # Поэтому сделаем более общий вариант: "/" + любые символы до конца:
    pattern2 = r"(.*-)(\d+)(/.*)$"

    # Сначала пробуем строгий (когда /' ; в конце), потом общий.
    new_line, n = re.subn(pattern, r"\g<1>" + dn + r"\g<3>", line, count=1)
    if n:
        return new_line

    new_line, n = re.subn(pattern2, r"\g<1>" + dn + r"\g<3>", line, count=1)
    if n:
        return new_line

    return line


def _apply_html_dirnum_all(variants: list[list[str]], dir_num: str) -> None:
    """
    HTML: проверяем строки 5-7 (1-based) -> индексы 4..6.
    Если строка начинается с $url, меняем число в последнем сегменте пути.
    Применяем ко всем вариантам (HK1..HK4), чтобы DIR_NUM был одинаковый.
    """
    dn = (dir_num or "").strip()
    if not dn:
        return

    idxs = [4, 5, 6]  # строки 5,6,7
    for v in variants:
        for i in idxs:
            if 0 <= i < len(v):
                v[i] = _replace_html_url_dirnum_in_line(v[i], dn)

def _set_force_delete(text: str, value: str) -> str:
    v = (value or "").strip()
    if v not in {"0", "1"}:
        return text

    pattern = r"(define\s*\(\s*['\"]FORCE_DELETE['\"]\s*,\s*)([01])(\s*\)\s*;)"
    return re.sub(pattern, r"\g<1>" + v + r"\g<3>", text, count=1)


def _set_force_delete(text: str, value: str) -> str:
    v = (value or "").strip()
    if v not in {"0", "1"}:
        return text

    pattern = r"(define\s*\(\s*['\"]FORCE_DELETE['\"]\s*,\s*)([01])(\s*\)\s*;)"
    return re.sub(pattern, r"\g<1>" + v + r"\g<3>", text, count=1)



def build_variants(source_text: str, dir_num: str, *, mode: str = "db") -> dict[int, str]:
    """
    mode: "db" | "html"
    """
    lines = source_text.splitlines(keepends=True)

    v1 = lines.copy()
    v2 = lines.copy()
    v3 = lines.copy()
    v4 = lines.copy()

    # 1) DIR_NUM apply (different rules for DB / HTML)
    if mode == "html":
        _apply_html_dirnum_all([v1], dir_num)  # только v1!
        t1 = "".join(v1)
        t2 = _set_force_delete(t1, "1")
        return {1: t1, 2: t2}
    else:
        _apply_db_dirnum_all([v1, v2, v3, v4], dir_num)

    # 2) Variants logic (как было) — ТОЛЬКО для DB
    _comment_range(v2, 9, 15)
    if len(v2) >= 19:
        v2[18] = _uncomment_first4(v2[18])

    _comment_range(v3, 9, 15)
    if len(v3) >= 17:
        v3[16] = _uncomment_first4(v3[16])

    _comment_range(v4, 9, 11)
    _comment_range(v4, 13, 15)

    return {
        1: "".join(v1),
        2: "".join(v2),
        3: "".join(v3),
        4: "".join(v4),
    }


def write_variants(source_php_path: Path, target_dir: Path, dir_num: str) -> dict[int, Path]:
    source_text = source_php_path.read_text(encoding="utf-8")

    mode = "html" if "HTML" in source_php_path.parts else "db"
    variants = build_variants(source_text, dir_num, mode=mode)

    target_dir.mkdir(parents=True, exist_ok=True)

    # если HTML — удаляем старые HK2..HK4, чтобы не мешали
    if mode == "html":
        for n in (3, 4):
            p = target_dir / f"HK{n}.php"
            if p.exists():
                p.unlink()

    out_paths: dict[int, Path] = {}
    for n, text in variants.items():
        p = target_dir / f"HK{n}.php"
        p.write_text(text, encoding="utf-8")
        out_paths[n] = p

    return out_paths
