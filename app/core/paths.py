from __future__ import annotations

from pathlib import Path
import os
import shutil
import sys

APP_NAME = "WorkerHotkeys"

def appdata_worker_dir() -> Path:
    base = Path(os.environ.get("APPDATA", str(Path.home())))
    p = base / APP_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p


def ensure_appdata_layout_from_portable() -> Path:
    """
    На старте дублируем базовую структуру рядом с приложением в %APPDATA%\WorkerHotkeys.
    Нужно для совместимости старых хоткеев/скриптов, которые читают данные только из AppData.
    Копируем только отсутствующие файлы/папки, существующие пользовательские данные не перетираем.
    """
    dst_root = appdata_worker_dir()

    candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.extend([exe_dir / APP_NAME, exe_dir])
    else:
        project_root = Path(__file__).resolve().parents[2]
        candidates.extend([project_root / APP_NAME, project_root])

    src_root = None
    for candidate in candidates:
        if (candidate / "profiles").exists():
            src_root = candidate
            break

    if src_root is None:
        return dst_root

    for item in src_root.iterdir():
        target = dst_root / item.name
        if target.exists():
            continue

        try:
            if item.is_dir():
                shutil.copytree(item, target)
            elif item.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)
        except Exception:
            # best-effort sync: не ломаем запуск приложения из-за копирования
            continue

    return dst_root



def app_data_dir() -> Path:
    # В сборке храним данные рядом с exe:
    # - prefer <exe_dir>/WorkerHotkeys (структура релиза)
    # - fallback <exe_dir>, если там уже есть profiles
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        bundled_data_dir = exe_dir / APP_NAME

        if bundled_data_dir.exists() or not (exe_dir / "profiles").exists():
            p = bundled_data_dir
        else:
            p = exe_dir
    else:
        # Dev/запуск из исходников: %APPDATA%\WorkerHotkeys
        p = appdata_worker_dir()
    p.mkdir(parents=True, exist_ok=True)
    return p


# ====== ПРОФИЛИ ======

def profiles_dir() -> Path:
    p = app_data_dir() / "profiles"
    p.mkdir(parents=True, exist_ok=True)
    return p


def active_profile_path() -> Path:
    return app_data_dir() / "active_profile.txt"


def get_active_profile() -> str:
    p = active_profile_path()
    try:
        v = p.read_text(encoding="utf-8").strip()
        if v in ("index", "zalivka"):
            return v
    except Exception:
        pass
    return "index"


def set_active_profile(profile: str) -> None:
    profile = (profile or "").strip().lower()
    if profile not in ("index", "zalivka"):
        profile = "index"

    p = active_profile_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(profile, encoding="utf-8")


def profile_dir(profile: str | None = None) -> Path:
    profile = profile or get_active_profile()
    p = profiles_dir() / profile
    p.mkdir(parents=True, exist_ok=True)
    return p


# ====== SCRIPTS (папка, которой управляют сотрудники) ======
def _portable_base_dir() -> Path:
    """
    База рядом с приложением:
    - в dev: рядом с корнем проекта
    - в сборке: рядом с exe (или _MEIPASS для onefile, но нам нужен именно каталог exe)
    """
    # PyInstaller onefile/onedir: sys.executable указывает на exe
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    # Dev mode: app/core/paths.py -> app/core -> app -> project_root
    return Path(__file__).resolve().parents[2]


def scripts_dir() -> Path:
    candidates = [
        # Приоритет: профильная папка (актуальная для HK1..HK4 и выбранного профиля)
        profile_dir() / "Scripts",
        # Портативный вариант рядом с проектом/exe
        _portable_base_dir() / "Scripts",
        # Legacy fallback: общий AppData каталог
        app_data_dir() / "Scripts",
    ]

    for p in candidates:
        if not (p.exists() and p.is_dir()):
            continue
        if (p / "DB").exists() or (p / "HTML").exists():
            return p

    # Если структуры ещё нет — создаём в профильной папке по умолчанию.
    default_dir = profile_dir() / "Scripts"
    default_dir.mkdir(parents=True, exist_ok=True)
    return default_dir


# ====== ПУТИ ВНУТРИ ПРОФИЛЯ ======

def config_path(profile: str | None = None) -> Path:
    return profile_dir(profile) / "config.json"


def runtime_ahk_path(profile: str | None = None) -> Path:
    return profile_dir(profile) / "runtime.ahk"

def generated_templates_dir() -> Path:
    # HK1..HK4 всегда храним в zalivka, независимо от active_profile.
    # Это убирает путаницу, когда сотрудник случайно работает в профиле index,
    # а хоткеи ожидают шаблоны именно заливки.
    p = profile_dir("zalivka") / "generated_templates"
    p.mkdir(parents=True, exist_ok=True)
    return p



def index_template_path(profile: str | None = None) -> Path:
    return profile_dir(profile) / "index_php.tpl"


def meta_template_path(profile: str | None = None) -> Path:
    return profile_dir(profile) / "meta_inject.tpl"


def rename_sitemap_template_path(profile: str | None = None) -> Path:
    return profile_dir(profile) / "rename_sitemap.tpl"


def screenshots_dir() -> Path:
    # %APPDATA%\WorkerHotkeys\profiles\<active>\Screenshots
    p = profile_dir() / "Screenshots"
    p.mkdir(parents=True, exist_ok=True)
    return p

def perm_file_path() -> Path:
    return profile_dir() / "permfile.txt"

def perm_console_path() -> Path:
    return profile_dir() / "permconsole.txt"

def google_file_path(profile: str | None = None) -> Path:
    return profile_dir(profile) / "google_file.txt"


def screenshot_hotkey_path(profile: str | None = None) -> Path:
    return profile_dir(profile) / "screenshot_hotkey.txt"

def screenshot_screen_path(profile: str | None = None) -> Path:
    return profile_dir(profile) / "screenshot_screen.json"


def screenshots_enabled_path(profile: str | None = None) -> Path:
    return profile_dir(profile) / "screenshots_enabled.txt"


def theme_path(profile: str | None = None) -> Path:
    return profile_dir(profile) / "theme.txt"


def prez_notag_path() -> Path:
    return profile_dir() / "prez_notag.txt"

def dirnum_next_hotkey_path() -> Path:
    return profile_dir() / "dirnum_next_hotkey.txt"

def prez_tag_path() -> Path:
    return profile_dir() / "prez_tag.txt"

def dirnum_queue_path() -> Path:
    return profile_dir() / "dirnum_queue.txt"

def dirnum_queue_index_path() -> Path:
    return profile_dir() / "dirnum_queue_index.txt"

def dirnum_override_path() -> Path:
    return profile_dir() / "dirnum_override.txt"

def dirnum_floating_enabled_path() -> Path:
    return profile_dir() / "dirnum_floating_enabled.txt"

def homelinks_enabled_path() -> Path:
    return profile_dir() / "homelinks_enabled.txt"

def scripts_status() -> tuple[bool, str, Path]:
    p = scripts_dir()

    expected = [p / "DB", p / "HTML"]

    if not p.exists() or not p.is_dir():
        return False, "Папка Scripts не найдена.", p

    has_any = any(p.iterdir())
    if not has_any:
        return False, "Папка Scripts пустая.", p

    if not any(e.exists() for e in expected):
        return False, "В Scripts нет папок DB/HTML (или структура изменена).", p

    try:
        has_php = any(x.suffix.lower() == ".php" for x in p.rglob("*.php"))
    except Exception:
        has_php = True
    if not has_php:
        return False, "В Scripts не найдено ни одного .php файла.", p

    return True, "OK", p