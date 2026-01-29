from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

from app.core.paths import runtime_ahk_path


def build_runtime_ahk(text: str) -> Path:
    """
    Пишет runtime.ahk в активный профиль:
    %APPDATA%\\WorkerHotkeys\\profiles\\<active>\\runtime.ahk
    """
    p = runtime_ahk_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


class AHKManager:
    def __init__(self, ahk_exe: Path):
        self.ahk_exe = Path(ahk_exe)
        self._proc: Optional[subprocess.Popen] = None

    def stop(self) -> None:
        """
        Останавливает текущий AHK (если запускали мы).
        Делает best-effort: сначала terminate по PID, потом taskkill.
        """
        # 1) если есть процесс, пробуем аккуратно
        if self._proc is not None:
            try:
                if self._proc.poll() is None:
                    self._proc.terminate()
                    try:
                        self._proc.wait(timeout=1.5)
                    except Exception:
                        pass
            except Exception:
                pass

            # если ещё жив — прибьём по PID
            try:
                if self._proc.poll() is None and self._proc.pid:
                    subprocess.run(
                        ["taskkill", "/PID", str(self._proc.pid), "/T", "/F"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        check=False,
                    )
            except Exception:
                pass

            self._proc = None
            return

        # 2) fallback: прибить по имени (если процесс запускался не в этой сессии)
        # В твоей логике важно, чтобы при переключении профиля не оставались хоткеи.
        try:
            subprocess.run(
                ["taskkill", "/IM", self.ahk_exe.name, "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=False,
            )
        except Exception:
            pass

    def restart(self, script_path: Path) -> None:
        """
        Перезапуск: stop + start.
        """
        self.stop()

        if not self.ahk_exe.exists():
            raise FileNotFoundError(f"AutoHotkey executable not found: {self.ahk_exe}")

        script_path = Path(script_path)
        if not script_path.exists():
            raise FileNotFoundError(f"AHK script not found: {script_path}")

        # запускаем
        self._proc = subprocess.Popen(
            [str(self.ahk_exe), str(script_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
