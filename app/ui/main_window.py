from __future__ import annotations

import sys
import shutil
from pathlib import Path
from PySide6.QtCore import QTimer


from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSystemTrayIcon,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QAction, QDesktopServices, QIcon
from PySide6.QtCore import QSize, Qt, QUrl

from app.core.templates import ensure_index_template
from app.core.paths import (
    rename_sitemap_template_path,
    meta_template_path,
    index_template_path,
    runtime_ahk_path,
    screenshots_dir,
    config_path,
    get_active_profile,
    set_active_profile,
    screenshot_hotkey_path,
    screenshots_enabled_path,
    scripts_dir,
)
from app.core.hotkeys_store import HotkeysStore, HotkeyItem
from app.ui.hotkeys_dialog import HotkeyDialog
from app.core.ahk_manager import AHKManager, build_runtime_ahk
from app.core.theme import load_theme_name, save_theme_name, apply_theme
from app.core.paths import prez_notag_path, prez_tag_path


def resource_path(relative: str) -> Path:
    if hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        return base / relative
    return Path(__file__).resolve().parents[2] / relative  # project root


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Worker Hotkeys")
        self.setMinimumSize(980, 600)

        app_icon_ico = resource_path("assets/appicona.ico")
        app_icon_png = resource_path("assets/appicona.png")
        if app_icon_ico.exists():
            self.setWindowIcon(QIcon(str(app_icon_ico)))
        elif app_icon_png.exists():
            self.setWindowIcon(QIcon(str(app_icon_png)))

        # =========================
        # STORE (активный профиль)
        # =========================
        self.store = HotkeysStore()
        self.store.load()

        # Профильные файлы (из active_profile)
        self.screenshot_hotkey_file = screenshot_hotkey_path()
        self.screenshots_enabled_file = screenshots_enabled_path()

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(12)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        icon_size = QSize(18, 18)

        # =========================================================
        # TAB 1: HOTKEYS
        # =========================================================
        tab_hotkeys = QWidget()
        hotkeys_layout = QVBoxLayout(tab_hotkeys)
        hotkeys_layout.setContentsMargins(0, 0, 0, 0)
        hotkeys_layout.setSpacing(12)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_add = QPushButton("Добавить")
        p = resource_path("assets/add.png")
        if p.exists():
            self.btn_add.setIcon(QIcon(str(p)))
            self.btn_add.setIconSize(icon_size)

        self.btn_edit = QPushButton("Редактировать")
        p = resource_path("assets/edit.png")
        if p.exists():
            self.btn_edit.setIcon(QIcon(str(p)))
            self.btn_edit.setIconSize(icon_size)

        self.btn_del = QPushButton("Удалить")
        p = resource_path("assets/delete.png")
        if p.exists():
            self.btn_del.setIcon(QIcon(str(p)))
            self.btn_del.setIconSize(icon_size)

        self.btn_screenshots = QPushButton("Скриншоты")
        p = resource_path("assets/folder.png")
        if p.exists():
            self.btn_screenshots.setIcon(QIcon(str(p)))
            self.btn_screenshots.setIconSize(icon_size)

        self.btn_apply = QPushButton("Применить")
        self.btn_apply.setObjectName("primary")
        p = resource_path("assets/apply.png")
        if p.exists():
            self.btn_apply.setIcon(QIcon(str(p)))
            self.btn_apply.setIconSize(icon_size)

        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_edit)
        btn_row.addWidget(self.btn_del)
        btn_row.addWidget(self.btn_screenshots)
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_apply)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Название", "Комбо", "Действие", "Payload"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)

        hotkeys_layout.addLayout(btn_row)
        hotkeys_layout.addWidget(self.table, 1)

        # =========================================================
        # TAB 2: SETTINGS
        # =========================================================
        tab_settings = QWidget()
        settings_layout = QVBoxLayout(tab_settings)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(12)

        self.lbl_info = QLabel()
        self._update_info_label()
        self.lbl_info.setWordWrap(True)
        self.lbl_info.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        row_cfg = QHBoxLayout()
        row_cfg.setSpacing(10)

        self.btn_export_cfg = QPushButton("Экспорт конфигурации…")
        p = resource_path("assets/export.png")
        if p.exists():
            self.btn_export_cfg.setIcon(QIcon(str(p)))
            self.btn_export_cfg.setIconSize(icon_size)

        self.btn_import_cfg = QPushButton("Импорт конфигурации…")
        p = resource_path("assets/import.png")
        if p.exists():
            self.btn_import_cfg.setIcon(QIcon(str(p)))
            self.btn_import_cfg.setIconSize(icon_size)

        row_cfg.addWidget(self.btn_export_cfg)
        row_cfg.addWidget(self.btn_import_cfg)
        row_cfg.addStretch(1)

        # --- profile switch (Индекс / Заливка) ---
        row_profile = QHBoxLayout()
        row_profile.setSpacing(10)

        lbl_profile = QLabel("Версия:")
        self.cmb_profile = QComboBox()
        self.cmb_profile.addItem("Индекс", "index")
        self.cmb_profile.addItem("Заливка", "zalivka")

        active = get_active_profile()
        self.cmb_profile.setCurrentIndex(0 if active == "index" else 1)

        self.btn_switch_profile = QPushButton("Переключить")
        p = resource_path("assets/apply.png")
        if p.exists():
            self.btn_switch_profile.setIcon(QIcon(str(p)))
            self.btn_switch_profile.setIconSize(icon_size)

        row_profile.addWidget(lbl_profile)
        row_profile.addWidget(self.cmb_profile, 0)
        row_profile.addWidget(self.btn_switch_profile)
        row_profile.addStretch(1)

        # --- theme switch ---
        row_theme = QHBoxLayout()
        row_theme.setSpacing(10)

        lbl_theme = QLabel("Тема:")
        self.cmb_theme = QComboBox()
        self.cmb_theme.addItem("Тёмная", "dark")
        self.cmb_theme.addItem("Светлая", "light")

        current_theme = load_theme_name()
        self.cmb_theme.setCurrentIndex(0 if current_theme == "dark" else 1)

        row_theme.addWidget(lbl_theme)
        row_theme.addWidget(self.cmb_theme, 0)
        row_theme.addStretch(1)

        # --- screenshot hotkey override ---
        row_shk = QHBoxLayout()
        row_shk.setSpacing(10)

        lbl_shk = QLabel("Хоткей скриншота:")
        self.edt_shk = QLineEdit()
        self.edt_shk.setPlaceholderText("^6  (Ctrl+6)  или  #n  (Win+N)")
        self.edt_shk.setText(self._load_screenshot_hotkey())

        self.btn_save_shk = QPushButton("Сохранить")
        p = resource_path("assets/save.png")
        if p.exists():
            self.btn_save_shk.setIcon(QIcon(str(p)))
            self.btn_save_shk.setIconSize(icon_size)

        row_shk.addWidget(lbl_shk)
        row_shk.addWidget(self.edt_shk, 1)
        row_shk.addWidget(self.btn_save_shk)

        hint = QLabel(
            "Подсказка: ^ = Ctrl, # = Win, ! = Alt, + = Shift. Пример: ^6, #n, ^+6.\n"
            "После изменения хоткея нажми «Применить», чтобы AHK перезапустился."
        )
        hint.setWordWrap(True)

        settings_layout.addWidget(self.lbl_info)
        settings_layout.addLayout(row_cfg)
        settings_layout.addLayout(row_profile)
        settings_layout.addLayout(row_theme)
        settings_layout.addLayout(row_shk)
        settings_layout.addWidget(hint)
        settings_layout.addStretch(1)

        # =========================================================
        # TAB: ZALIVKA (PreZ + Scripts picker)
        # =========================================================
        self.tab_zalivka = QWidget()

        zalivka_root = QHBoxLayout(self.tab_zalivka)
        zalivka_root.setContentsMargins(0, 0, 0, 0)
        zalivka_root.setSpacing(12)

        # ---- Left panel: PreZ ----
        self.prez_panel = QFrame()
        self.prez_panel.setObjectName("prezPanel")
        self.prez_panel.setFixedWidth(210)

        prez_layout = QVBoxLayout(self.prez_panel)
        prez_layout.setContentsMargins(12, 12, 12, 12)
        prez_layout.setSpacing(10)

        lbl_prez = QLabel("PreZ")
        lbl_prez.setStyleSheet("font-size: 16px; font-weight: 700;")

        self.btn_no_tag = QPushButton("NOTAG")
        self.btn_has_tag = QPushButton("TAG")
        self.btn_no_tag.setMinimumHeight(36)
        self.btn_has_tag.setMinimumHeight(36)

        prez_layout.addWidget(lbl_prez)
        prez_layout.addWidget(self.btn_no_tag)
        prez_layout.addWidget(self.btn_has_tag)
        prez_layout.addStretch(1)

        # PreZ state
        self._prez_selected: str | None = None
        self.btn_no_tag.clicked.connect(lambda: self._prez_copy("no_tag", seconds=4))
        self.btn_has_tag.clicked.connect(lambda: self._prez_copy("has_tag", seconds=4))
        self._update_prez_buttons()

        # ---- Right area: scripts picker ----
        self.zalivka_right = QWidget()
        right_layout = QVBoxLayout(self.zalivka_right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        self.lbl_pick_path = QLabel("Выбор: —")
        self.lbl_pick_path.setStyleSheet("font-weight: 600;")

        # Step 1: DB / HTML
        row_step1 = QHBoxLayout()
        row_step1.setSpacing(10)

        self.btn_pick_db = QPushButton("DB")
        self.btn_pick_html = QPushButton("HTML")
        self.btn_pick_db.setMinimumHeight(34)
        self.btn_pick_html.setMinimumHeight(34)

        row_step1.addWidget(QLabel("1) Тип:"))
        row_step1.addWidget(self.btn_pick_db)
        row_step1.addWidget(self.btn_pick_html)
        row_step1.addStretch(1)

        # Step 2: ZALIV / DOZALIV (only for DB)
        row_step2 = QHBoxLayout()
        row_step2.setSpacing(10)

        self.lbl_step2 = QLabel("2) Подтип:")
        self.btn_pick_zaliv = QPushButton("ZALIV")
        self.btn_pick_dozaliv = QPushButton("DOZALIV")
        self.btn_pick_zaliv.setMinimumHeight(34)
        self.btn_pick_dozaliv.setMinimumHeight(34)

        row_step2.addWidget(self.lbl_step2)
        row_step2.addWidget(self.btn_pick_zaliv)
        row_step2.addWidget(self.btn_pick_dozaliv)
        row_step2.addStretch(1)

        # Step 3: Languages grid
        self.lbl_step3 = QLabel("3) Язык:")
        self.lbl_step3.setStyleSheet("font-weight: 600;")

        self.lang_scroll = QScrollArea()
        self.lang_scroll.setWidgetResizable(True)
        self.lang_scroll.setFrameShape(QFrame.NoFrame)

        self.lang_container = QWidget()
        self.lang_grid = QGridLayout(self.lang_container)
        self.lang_grid.setContentsMargins(0, 0, 0, 0)
        self.lang_grid.setHorizontalSpacing(10)
        self.lang_grid.setVerticalSpacing(10)

        self.lang_scroll.setWidget(self.lang_container)

        right_layout.addWidget(self.lbl_pick_path)
        right_layout.addLayout(row_step1)
        right_layout.addLayout(row_step2)
        right_layout.addWidget(self.lbl_step3)
        right_layout.addWidget(self.lang_scroll, 1)

        # picker state
        self._pick_type: str | None = None       # "DB" | "HTML"
        self._pick_subtype: str | None = None    # "ZALIV" | "DOZALIV"
        self._pick_lang: str | None = None       # "EN" ...

        self.btn_pick_db.clicked.connect(lambda: self._set_pick_type("DB"))
        self.btn_pick_html.clicked.connect(lambda: self._set_pick_type("HTML"))
        self.btn_pick_zaliv.clicked.connect(lambda: self._set_pick_subtype("ZALIV"))
        self.btn_pick_dozaliv.clicked.connect(lambda: self._set_pick_subtype("DOZALIV"))

        self._refresh_pick_ui()

        # assemble zalivka
        zalivka_root.addWidget(self.prez_panel, 0)
        zalivka_root.addWidget(self.zalivka_right, 1)

        # =========================================================
        # Tabs order
        # =========================================================
        self.tabs.addTab(tab_hotkeys, "Хоткеи")
        self.tabs.addTab(self.tab_zalivka, "Заливка")
        self.tabs.addTab(tab_settings, "Настройки")

        # show/hide zalivka tab
        self._update_zalivka_tab_visibility()

        root_layout.addWidget(self.tabs, 1)
        self.setCentralWidget(root)

        # =========================================================
        # SIGNALS
        # =========================================================
        self.btn_add.clicked.connect(self.add_hotkey)
        self.btn_edit.clicked.connect(self.edit_hotkey)
        self.btn_del.clicked.connect(self.del_hotkey)
        self.btn_apply.clicked.connect(self.apply_hotkeys)
        self.btn_screenshots.clicked.connect(self.open_screenshots_folder)

        self.btn_export_cfg.clicked.connect(self.export_config)
        self.btn_import_cfg.clicked.connect(self.import_config)

        self.btn_switch_profile.clicked.connect(self.switch_profile)

        self.cmb_theme.currentIndexChanged.connect(self.on_theme_changed)
        self.btn_save_shk.clicked.connect(self.save_screenshot_hotkey)

        self.table.cellDoubleClicked.connect(lambda *_: self.edit_hotkey())

        # =========================================================
        # AHK manager
        # =========================================================
        self.ahk_exe = resource_path("AutoHotkeyUX.exe")
        self.ahk = AHKManager(self.ahk_exe)

        self.render()

        # =========================================================
        # TRAY
        # =========================================================
        self.tray: QSystemTrayIcon | None = None
        self._setup_tray()

    # =========================================================
    # PreZ toggle
    # =========================================================
    def _ensure_prez_files(self) -> None:
        p1 = prez_notag_path()
        p2 = prez_tag_path()
        p1.parent.mkdir(parents=True, exist_ok=True)

        if not p1.exists():
            raise FileNotFoundError(f"Не найден файл: {p1}")
        if not p2.exists():
            raise FileNotFoundError(f"Не найден файл: {p2}")

    def _prez_clear_highlight(self) -> None:
        self._prez_selected = None
        self._update_prez_buttons()

    def _prez_copy(self, mode: str, seconds: int = 4) -> None:
        try:
            if mode == "no_tag":
                p = prez_notag_path()
            elif mode == "has_tag":
                p = prez_tag_path()
            else:
                return

            # если файла нет — просто выходим (можно показать сообщение)
            if not p.exists():
                QMessageBox.warning(self, "PreZ", f"Не получилось: файл не найден\n\n{p}")
                return

            text = p.read_text(encoding="utf-8")

            # если пусто — тоже ничего не делаем
            if not text.strip():
                QMessageBox.warning(self, "PreZ", f"Не получилось: файл пустой\n\n{p}")
                return

            # копируем
            QApplication.clipboard().setText(text)

            # подсветка кнопки на N секунд
            self._prez_selected = mode
            self._update_prez_buttons()

            if not hasattr(self, "_prez_flash_timer"):
                self._prez_flash_timer = QTimer(self)
                self._prez_flash_timer.setSingleShot(True)
                self._prez_flash_timer.timeout.connect(self._prez_clear_highlight)

            self._prez_flash_timer.start(max(1, int(seconds)) * 1000)

        except Exception as e:
            QMessageBox.warning(self, "PreZ", f"Не получилось:\n\n{type(e).__name__}: {e}")

    def _update_prez_buttons(self) -> None:
        if self._prez_selected == "no_tag":
            self.btn_no_tag.setStyleSheet("background-color: #2e7d32; color: white; font-weight: 600;")
            self.btn_has_tag.setStyleSheet("")
        elif self._prez_selected == "has_tag":
            self.btn_has_tag.setStyleSheet("background-color: #2e7d32; color: white; font-weight: 600;")
            self.btn_no_tag.setStyleSheet("")
        else:
            self.btn_no_tag.setStyleSheet("")
            self.btn_has_tag.setStyleSheet("")

    # =========================================================
    # ZALIVKA tab visibility
    # =========================================================
    def _update_zalivka_tab_visibility(self) -> None:
        active = get_active_profile()
        idx = self.tabs.indexOf(self.tab_zalivka)
        if idx == -1:
            return
        self.tabs.setTabVisible(idx, active == "zalivka")

    # =========================================================
    # Info label
    # =========================================================
    def _update_info_label(self) -> None:
        prof = get_active_profile()
        prof_name = "Индекс" if prof == "index" else "Заливка"
        cfg = config_path()
        self.lbl_info.setText(
            "Здесь можно сохранить ваши хоткеи/настройки в файл и загрузить их на другом ПК.\n"
            f"Активная версия: {prof_name}\n"
            f"Конфигурация хранится в:\n{cfg}"
        )

    # =========================================================
    # Scripts picker
    # =========================================================

    def _scripts_root(self) -> Path:
        return scripts_dir()

    def _set_pick_type(self, v: str) -> None:
        self._pick_type = v
        self._pick_subtype = None
        self._pick_lang = None
        self._refresh_pick_ui()


    def _set_pick_subtype(self, v: str) -> None:
        self._pick_subtype = v
        self._pick_lang = None
        self._refresh_pick_ui()

    def _set_pick_lang(self, v: str) -> None:
        if self._pick_lang == v:
            self._pick_lang = None
        else:
            self._pick_lang = v
        self._refresh_pick_ui()

    def _refresh_pick_ui(self) -> None:
        is_db = (self._pick_type == "DB")
        self.lbl_step2.setVisible(is_db)
        self.btn_pick_zaliv.setVisible(is_db)
        self.btn_pick_dozaliv.setVisible(is_db)

        def paint(btn: QPushButton, active: bool) -> None:
            btn.setStyleSheet(
                "background-color: #2e7d32; color: white; font-weight: 700;" if active else ""
            )

        paint(self.btn_pick_db, self._pick_type == "DB")
        paint(self.btn_pick_html, self._pick_type == "HTML")
        paint(self.btn_pick_zaliv, self._pick_subtype == "ZALIV")
        paint(self.btn_pick_dozaliv, self._pick_subtype == "DOZALIV")

        self._rebuild_lang_buttons()

        parts: list[str] = []
        if self._pick_type:
            parts.append(self._pick_type)
        if self._pick_type == "DB" and self._pick_subtype:
            parts.append(self._pick_subtype)
        if self._pick_lang:
            parts.append(self._pick_lang)

        self.lbl_pick_path.setText("Выбор: " + (" → ".join(parts) if parts else "—"))

    def _rebuild_lang_buttons(self) -> None:
        while self.lang_grid.count():
            item = self.lang_grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not self._pick_type:
            return

        root = self._scripts_root()

        if self._pick_type == "HTML":
            base = root / "HTML"
        else:
            if not self._pick_subtype:
                return
            base = root / "DB" / self._pick_subtype

        if not base.exists():
            return

        langs = sorted([p.name for p in base.iterdir() if p.is_dir()])

        cols = 6
        try:
            w = self.lang_scroll.viewport().width()
            cols = max(3, min(10, w // 110))
        except Exception:
            pass

        r = 0
        c = 0
        for lang in langs:
            btn = QPushButton(lang)
            btn.setMinimumHeight(34)

            if self._pick_lang == lang:
                btn.setStyleSheet("background-color: #2e7d32; color: white; font-weight: 700;")

            btn.clicked.connect(lambda _=False, x=lang: self._set_pick_lang(x))
            self.lang_grid.addWidget(btn, r, c)

            c += 1
            if c >= cols:
                c = 0
                r += 1

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "lang_scroll"):
            self._rebuild_lang_buttons()

    # =========================================================
    # SCREENSHOT HOTKEY FILE
    # =========================================================
    def _load_screenshot_hotkey(self) -> str:
        try:
            if self.screenshot_hotkey_file.exists():
                v = self.screenshot_hotkey_file.read_text(encoding="utf-8").strip()
                if v:
                    return v
        except Exception:
            pass
        return "^6"

    def save_screenshot_hotkey(self) -> None:
        try:
            self.screenshot_hotkey_file.parent.mkdir(parents=True, exist_ok=True)

            v = (self.edt_shk.text() or "").strip()
            if not v:
                QMessageBox.warning(self, "Хоткей скриншота", "Введите хоткей, например: ^6 или #n")
                return

            if any(ch.isspace() for ch in v):
                QMessageBox.warning(self, "Хоткей скриншота", "Хоткей не должен содержать пробелы.")
                return

            self.screenshot_hotkey_file.write_text(v, encoding="utf-8")
            QMessageBox.information(
                self,
                "Готово",
                "Хоткей сохранён.\n\n"
                "Нажмите «Применить», чтобы AHK перезапустился и подхватил новый хоткей."
            )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"{type(e).__name__}: {e}")

    # =========================================================
    # PROFILE SWITCH
    # =========================================================
    def switch_profile(self) -> None:
        try:
            new_profile = self.cmb_profile.currentData()
            if new_profile not in ("index", "zalivka"):
                return

            current = get_active_profile()
            if new_profile == current:
                QMessageBox.information(self, "Профиль", "Этот профиль уже активен.")
                return

            try:
                self.ahk.stop()
            except Exception:
                pass

            set_active_profile(str(new_profile))
            self._update_zalivka_tab_visibility()

            self.screenshot_hotkey_file = screenshot_hotkey_path()
            self.screenshots_enabled_file = screenshots_enabled_path()

            self.store.load()
            self.render()
            self.edt_shk.setText(self._load_screenshot_hotkey())

            self._update_info_label()

            QMessageBox.information(
                self,
                "Профиль переключён",
                "Готово.\n\n"
                "Теперь активен другой режим.\n"
                "Нажмите «Применить», чтобы включить хоткеи этого профиля."
            )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"{type(e).__name__}: {e}")

    # =========================================================
    # TRAY
    # =========================================================
    def _setup_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        icon = self.windowIcon()
        if icon.isNull():
            p = resource_path("assets/appicona.ico")
            if p.exists():
                icon = QIcon(str(p))

        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip("Worker Hotkeys")

        menu = QMenu()

        act_show = QAction("Открыть", self)
        act_show.triggered.connect(self.show_from_tray)

        act_hide = QAction("Свернуть", self)
        act_hide.triggered.connect(self.hide)

        act_exit = QAction("Выход", self)
        act_exit.triggered.connect(self.quit_app)

        menu.addAction(act_show)
        menu.addAction(act_hide)
        menu.addSeparator()
        menu.addAction(act_exit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_from_tray()

    def show_from_tray(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def quit_app(self) -> None:
        if self.tray:
            self.tray.hide()
        QApplication.quit()

    def closeEvent(self, event) -> None:
        if self.tray and self.tray.isVisible():
            self.hide()
            try:
                self.tray.showMessage(
                    "Worker Hotkeys",
                    "Приложение свернуто в трей.\nОткрой двойным кликом по иконке.",
                    QSystemTrayIcon.Information,
                    2500
                )
            except Exception:
                pass
            event.ignore()
            return
        super().closeEvent(event)

    # =========================================================
    # UI helpers
    # =========================================================
    def render(self) -> None:
        self.table.setRowCount(len(self.store.items))
        for r, hk in enumerate(self.store.items):
            self.table.setItem(r, 0, QTableWidgetItem(hk.name))
            self.table.setItem(r, 1, QTableWidgetItem(hk.combo))
            self.table.setItem(r, 2, QTableWidgetItem(hk.action))
            preview = hk.payload if len(hk.payload) <= 120 else hk.payload[:120] + "…"
            self.table.setItem(r, 3, QTableWidgetItem(preview))

    def _selected_row(self) -> int:
        return self.table.currentRow()

    # =========================================================
    # Hotkeys actions
    # =========================================================
    def add_hotkey(self) -> None:
        dlg = HotkeyDialog(self)
        if dlg.exec() == QDialog.Accepted:
            hk = dlg.result_item()
            self.store.add(hk)
            self.store.save()
            self.render()
            self.table.selectRow(max(0, len(self.store.items) - 1))

    def edit_hotkey(self) -> None:
        row = self._selected_row()
        if row < 0:
            QMessageBox.information(self, "Редактирование", "Выберите хоткей в таблице.")
            return

        current: HotkeyItem = self.store.items[row]
        dlg = HotkeyDialog(self, initial=current)
        if dlg.exec() == QDialog.Accepted:
            updated = dlg.result_item()
            self.store.items[row] = updated
            self.store.save()
            self.render()
            self.table.selectRow(row)

    def del_hotkey(self) -> None:
        row = self._selected_row()
        if row < 0:
            QMessageBox.information(self, "Удаление", "Выберите хоткей в таблице.")
            return

        name = self.store.items[row].name
        confirm = QMessageBox.question(
            self, "Удаление", f"Удалить хоткей:\n\n{name}",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        self.store.remove_at(row)
        self.store.save()
        self.render()
        if self.store.items:
            self.table.selectRow(min(row, len(self.store.items) - 1))

    def open_screenshots_folder(self) -> None:
        p = screenshots_dir()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))

    # =========================================================
    # Settings: Export / Import config
    # =========================================================
    def export_config(self) -> None:
        try:
            src = config_path()
            if not src.exists():
                QMessageBox.warning(self, "Экспорт", f"Файл конфигурации не найден:\n{src}")
                return

            suggested = Path.home() / "WorkerHotkeys_config.json"
            dst_str, _ = QFileDialog.getSaveFileName(
                self, "Экспорт конфигурации", str(suggested), "JSON (*.json)"
            )
            if not dst_str:
                return

            dst = Path(dst_str)
            shutil.copy2(src, dst)
            QMessageBox.information(self, "Экспорт", f"Готово!\n\nСохранено в:\n{dst}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"{type(e).__name__}: {e}")

    def import_config(self) -> None:
        try:
            src_str, _ = QFileDialog.getOpenFileName(
                self, "Импорт конфигурации", str(Path.home()), "JSON (*.json)"
            )
            if not src_str:
                return

            src = Path(src_str)
            if not src.exists():
                QMessageBox.warning(self, "Импорт", "Файл не найден.")
                return

            confirm = QMessageBox.question(
                self, "Импорт конфигурации",
                "Импорт заменит текущие хоткеи/настройки на выбранный файл.\n\nПродолжить?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm != QMessageBox.Yes:
                return

            dst = config_path()
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

            self.store.load()
            self.render()

            QMessageBox.information(
                self, "Импорт",
                "Готово!\n\nНовая конфигурация применена.\n\n"
                "Чтобы хоткеи в фоне обновились — нажмите «Применить»."
            )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"{type(e).__name__}: {e}")

    # =========================================================
    # Settings: Theme switch
    # =========================================================
    def on_theme_changed(self) -> None:
        try:
            theme_name = self.cmb_theme.currentData()
            if theme_name not in ("dark", "light"):
                return

            save_theme_name(theme_name)

            app = QApplication.instance()
            if app is None:
                return

            dark_qss = resource_path("app/ui/style.qss")
            light_qss = resource_path("app/ui/style_light.qss")

            apply_theme(app, dark_qss, light_qss, theme_name)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"{type(e).__name__}: {e}")

    # =========================================================
    # Apply hotkeys
    # =========================================================
    def apply_hotkeys(self) -> None:
        try:
            template_path = resource_path("ahk/runner_template.ahk")
            if not template_path.exists():
                QMessageBox.critical(self, "Ошибка", f"Не найден шаблон AHK:\n{template_path}")
                return

            template = template_path.read_text(encoding="utf-8")
            begin = "; ====== PYTHON_BEGIN ======"
            end = "; ====== PYTHON_END ======"
            if begin not in template or end not in template:
                QMessageBox.critical(self, "Ошибка", "В runner_template.ahk нет маркеров PYTHON_BEGIN/PYTHON_END")
                return

            func_lines: list[str] = []
            reg_lines: list[str] = []

            for i, hk in enumerate(self.store.items, start=1):
                combo = (hk.combo or "").strip()
                name = (hk.name or "").replace('"', "'").strip()
                action = (hk.action or "").strip()
                payload = hk.payload or ""

                if not combo or not name:
                    continue

                fn_name = f"HK_{i}"

                func_lines.append(f"{fn_name}() {{")
                if action == "msgbox":
                    safe = payload.replace('"', "'")
                    func_lines.append(f'    MsgBox("{safe}")')
                elif action == "ahk_raw":
                    lines = payload.splitlines()
                    if not any(line.strip() for line in lines):
                        func_lines.append("    ; empty ahk_raw body")
                    else:
                        for line in lines:
                            func_lines.append("    " + line)
                else:
                    func_lines.append(f'    ToolTip("Hotkey: {name} | action={action}")')
                    func_lines.append("    SetTimer(() => ToolTip(), -700)")

                func_lines.append("}")
                func_lines.append("")

                reg_lines.append(f'Hotkey("$*{combo}", (*) => {fn_name}(), "On")')

            gen_lines: list[str] = []
            gen_lines.append("; ====== AUTOGENERATED HOTKEYS ======")
            gen_lines.append("; --- functions ---")
            gen_lines.extend(func_lines)
            gen_lines.append("; --- registration ---")
            gen_lines.extend(reg_lines)
            gen_lines.append("; ====== END AUTOGENERATED HOTKEYS ======")

            before = template.split(begin, 1)[0]
            after = template.split(end, 1)[1]
            final_text = before + begin + "\n" + "\n".join(gen_lines) + "\n" + end + after

            # tpl-шаблоны копируем в активный профиль (paths.py уже профильный)
            src_index = resource_path("assets/templates/index_php.tpl")
            if src_index.exists():
                ensure_index_template(src_index, index_template_path())

            src_meta = resource_path("assets/templates/meta_inject.tpl")
            if src_meta.exists():
                ensure_index_template(src_meta, meta_template_path())

            src_rename = resource_path("assets/templates/rename_sitemap.tpl")
            if src_rename.exists():
                ensure_index_template(src_rename, rename_sitemap_template_path())

            build_runtime_ahk(final_text)

            script_path = runtime_ahk_path()
            if not script_path.exists():
                QMessageBox.critical(self, "Ошибка", f"runtime.ahk не создан:\n{script_path}")
                return

            if not self.ahk_exe.exists():
                QMessageBox.critical(self, "Ошибка", f"AutoHotkeyUX.exe не найден:\n{self.ahk_exe}")
                return

            self.ahk.restart(script_path)
            QMessageBox.information(self, "Готово", "Хоткеи применены и AHK перезапущен.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"{type(e).__name__}: {e}")
