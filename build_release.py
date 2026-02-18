import shutil
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).parent
SRC_SCRIPTS = ROOT / "Scripts"
DIST_APP = ROOT / "dist" / "WorkerHotkeys"  # onedir

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

def main():
    # 1) check before build
    check_scripts(SRC_SCRIPTS)

    # 2) build
    run([
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--name", "WorkerHotkeys",
        "--windowed",
        "--onedir",
        "--add-data", f"{ROOT/'assets'};assets",
        "--add-data", f"{ROOT/'ahk'};ahk",
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

    # 4) verify dist contains scripts
    check_scripts(dst_scripts)

    print("RELEASE OK:", DIST_APP)

if __name__ == "__main__":
    main()
