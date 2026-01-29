from __future__ import annotations
from pathlib import Path
import os

APP_NAME = "WorkerHotkeys"


def app_data_dir() -> Path:
    # %APPDATA%\WorkerHotkeys
    base = Path(os.environ.get("APPDATA", str(Path.home())))
    p = base / APP_NAME
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


def set_active_profile(name: str) -> None:
    if name not in ("index", "zalivka"):
        return
    p = active_profile_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(name, encoding="utf-8")

def scripts_dir() -> Path:
    p = app_data_dir() / "Scripts"
    p.mkdir(parents=True, exist_ok=True)
    return p

def set_active_profile(profile: str) -> None:
    profile = profile.strip().lower()
    if profile not in ("index", "zalivka"):
        profile = "index"

    app_data_dir().mkdir(parents=True, exist_ok=True)
    active_profile_path().write_text(profile, encoding="utf-8")


def profile_dir(profile: str | None = None) -> Path:
    profile = profile or get_active_profile()
    p = profiles_dir() / profile
    p.mkdir(parents=True, exist_ok=True)
    return p


# ====== ПУТИ ВНУТРИ ПРОФИЛЯ ======

def config_path(profile: str | None = None) -> Path:
    return profile_dir(profile) / "config.json"


def runtime_ahk_path(profile: str | None = None) -> Path:
    return profile_dir(profile) / "runtime.ahk"


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



def google_file_path(profile: str | None = None) -> Path:
    return profile_dir(profile) / "google_file.txt"


def screenshot_hotkey_path(profile: str | None = None) -> Path:
    return profile_dir(profile) / "screenshot_hotkey"


def screenshots_enabled_path(profile: str | None = None) -> Path:
    return profile_dir(profile) / "screenshots_enabled"


def theme_path(profile: str | None = None) -> Path:
    return profile_dir(profile) / "theme"

def prez_notag_path() -> Path:
    return profile_dir() / "prez_notag.txt"

def prez_tag_path() -> Path:
    return profile_dir() / "prez_tag.txt"
