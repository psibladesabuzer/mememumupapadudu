import shutil
from pathlib import Path
import subprocess
import sys
import os

ROOT = Path(__file__).parent
SRC_SCRIPTS = ROOT / "Scripts"
DIST_APP = ROOT / "dist" / "WorkerHotkeys"  # onedir
DIST_USERDATA = DIST_APP / "WorkerHotkeys"
ADD_DATA_SEP = ";" if sys.platform.startswith("win") else ":"

def die(msg: str):
    print("ERROR:", msg)
    raise SystemExit(1)

def run(cmd: list[str]) -> None:
    print(">", " ".join(cmd))
    subprocess.check_call(cmd)

def check_scripts(p: Path):
    if not p.exists():
        die(f"Scripts папка не найдена: {p}")
    php = list(p.rglob("*.php"))
    if not php:
        die(f"Scripts есть, но .php не найдено: {p}")
    print(f"Scripts OK: {len(php)} php files")


def check_required_file(path: Path, title: str):
    if not path.exists() or not path.is_file():
        die(f"{title} не найден: {path}")


def add_data(src: Path, dst: str) -> str:
    return f"{src}{ADD_DATA_SEP}{dst}"
def copy_appdata_workerhotkeys(dst: Path) -> None:
    appdata = os.getenv("APPDATA")
    if not appdata:
        die("Переменная APPDATA не задана")

    src = Path(appdata) / "WorkerHotkeys"
    if not src.exists() or not src.is_dir():
        die(f"Папка WorkerHotkeys не найдена в APPDATA: {src}")

    excluded_dirs = {"logs", "screenshots"}

    def ignore(_: str, names: list[str]) -> set[str]:
        return {name for name in names if name.lower() in excluded_dirs}

    if dst.exists():
        shutil.rmtree(dst)

    shutil.copytree(src, dst, ignore=ignore)
    print(f"User data copied: {src} -> {dst} (excluding: logs, Screenshots)")

def main():
    # 1) check before build
    check_scripts(SRC_SCRIPTS)
    check_required_file(ROOT / "AutoHotkeyUX.exe", "AutoHotkeyUX.exe")

    # 2) build
    run([
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--name", "WorkerHotkeys",
        "--windowed",
        "--onedir",
        "--add-data", f"{ROOT/'assets'};assets",
        "--add-data", f"{ROOT/'ahk'};ahk",
        "--add-data", add_data(ROOT / "assets", "assets"),
        "--add-data", add_data(ROOT / "ahk", "ahk"),
        "--add-data", add_data(ROOT / "app" / "ui" / "style.qss", "app/ui"),
        "--add-data", add_data(ROOT / "app" / "ui" / "style_light.qss", "app/ui"),
        str(ROOT / "app" / "main.py"),
    ])

    # 3) copy runtime deps into dist
    DIST_APP.mkdir(parents=True, exist_ok=True)

    # AutoHotkeyUX.exe
    shutil.copy2(ROOT / "AutoHotkeyUX.exe", DIST_APP / "AutoHotkeyUX.exe")

    # Scripts
    dst_scripts = DIST_APP / "Scripts"
    if dst_scripts.exists():
        shutil.rmtree(dst_scripts)
    shutil.copytree(SRC_SCRIPTS, dst_scripts)

    # %APPDATA%\WorkerHotkeys (excluding logs and Screenshots)
    copy_appdata_workerhotkeys(DIST_USERDATA)

    # 4) verify dist contains scripts
    check_scripts(dst_scripts)

    print("RELEASE OK:", DIST_APP)

if __name__ == "__main__":
    main()