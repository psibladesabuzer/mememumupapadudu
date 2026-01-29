from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Any

from app.core.paths import config_path, app_data_dir


@dataclass
class HotkeyItem:
    name: str
    combo: str
    action: str
    payload: str


class HotkeysStore:
    def __init__(self):
        self.items: list[HotkeyItem] = []

    def _read_json_items(self, path) -> list[HotkeyItem]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []

        raw_items = data.get("items", [])
        if not isinstance(raw_items, list):
            return []

        result: list[HotkeyItem] = []
        for x in raw_items:
            if not isinstance(x, dict):
                continue
            result.append(
                HotkeyItem(
                    name=str(x.get("name", "")),
                    combo=str(x.get("combo", "")),
                    action=str(x.get("action", "")),
                    payload=str(x.get("payload", "")),
                )
            )
        return result

    def load(self) -> None:
        # Новый путь: %APPDATA%\WorkerHotkeys\profiles\<active>\config.json
        path = config_path()
        if path.exists():
            self.items = self._read_json_items(path)
            return

        # МИГРАЦИЯ: если в активном профиле конфига нет, но есть старый корневой config.json
        legacy = app_data_dir() / "config.json"
        if legacy.exists():
            items = self._read_json_items(legacy)
            self.items = items

            # сохраняем в профиль, чтобы дальше работало по-новому
            try:
                self.save()
            except Exception:
                pass
            return

        self.items = []

    def save(self) -> None:
        path = config_path()  # пишет в активный профиль
        payload: dict[str, Any] = {"items": [asdict(x) for x in self.items]}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add(self, item: HotkeyItem) -> None:
        self.items.append(item)

    def remove_at(self, idx: int) -> None:
        if 0 <= idx < len(self.items):
            self.items.pop(idx)
