from __future__ import annotations

import sys
import shutil
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QPlainTextEdit
from app.core.dirnum_queue import parse_dirnums_from_lines, save_queue, load_queue, load_index

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
    QSizePolicy,
    QSplitter,
    QSystemTrayIcon,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QAction, QDesktopServices, QIcon, QIntValidator
from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QGuiApplication

from app.core.template_variants import write_variants
from app.core.paths import generated_templates_dir
from app.core.paths import scripts_status
from app.core.templates import ensure_index_template
from app.core.paths import (
    dirnum_floating_enabled_path,
    dirnum_next_hotkey_path,
    runtime_ahk_path,
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
from app.core.paths import prez_notag_path, prez_tag_path, perm_file_path, perm_console_path
from app.core.screenshot_settings import (
    load_screenshot_screen_settings,
    save_screenshot_screen_settings,
)

class DirnumFloatingWidget(QWidget):
    def __init__(self, *, on_prev, on_next, on_apply_manual):
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowTitle("DIR_NUM")
        self.setObjectName("dirnumFloating")
        self.setMinimumWidth(280)

        self._drag_offset = None
        self._on_prev = on_prev
        self._on_next = on_next
        self._on_apply_manual = on_apply_manual

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self.lbl_title = QLabel("DIR_NUM")
        self.lbl_title.setStyleSheet("font-weight: 700;")

        self.edt_dirnum = QLineEdit()
        self.edt_dirnum.setPlaceholderText("Введите DIR_NUM")
        self.edt_dirnum.setValidator(QIntValidator(0, 999999, self))
        self.edt_dirnum.returnPressed.connect(self._apply_manual)

        row_btns = QHBoxLayout()
        self.btn_prev = QPushButton("← Назад")
        self.btn_next = QPushButton("Дальше →")
        self.btn_prev.clicked.connect(self._on_prev)
        self.btn_next.clicked.connect(self._on_next)
        row_btns.addWidget(self.btn_prev)
        row_btns.addWidget(self.btn_next)

        root.addWidget(self.lbl_title)
        root.addWidget(self.edt_dirnum)
        root.addLayout(row_btns)

    def _apply_manual(self) -> None:
        self._on_apply_manual((self.edt_dirnum.text() or "").strip())

    def set_dirnum(self, value: str) -> None:
        self.edt_dirnum.setText((value or "").strip())

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._drag_offset and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._drag_offset = None
        super().mouseReleaseEvent(event)



def resource_path(relative: str) -> Path:
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        p = exe_dir / relative
        if p.exists():
            return p

        if hasattr(sys, "_MEIPASS"):
            p2 = Path(sys._MEIPASS) / relative  # type: ignore[attr-defined]
            return p2

        return p

    # Dev mode
    return Path(__file__).resolve().parents[2] / relative


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

        self.dirnum_floating_widget: DirnumFloatingWidget | None = None

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(12)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        icon_size = QSize(30, 30)

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

        row_screen = QHBoxLayout()
        row_screen.setSpacing(10)

        lbl_screen = QLabel("Экран для скриншотов:")
        self.cmb_screenshot_screen = QComboBox()

        row_screen.addWidget(lbl_screen)
        row_screen.addWidget(self.cmb_screenshot_screen, 1)
        row_screen.addStretch(1)

        row_dirnum_float = QHBoxLayout()
        row_dirnum_float.setSpacing(10)
        self.lbl_dirnum_float = QLabel("Плавающий виджет DIR_NUM:")
        self.btn_dirnum_float_toggle = QPushButton("Включить")
        self.btn_dirnum_float_toggle.clicked.connect(self._toggle_dirnum_floating_widget)
        row_dirnum_float.addWidget(self.lbl_dirnum_float)
        row_dirnum_float.addWidget(self.btn_dirnum_float_toggle)
        row_dirnum_float.addStretch(1)

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
        settings_layout.addLayout(row_screen)
        settings_layout.addLayout(row_dirnum_float)
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

        # --- PERM section ---
        lbl_perm = QLabel("perm")
        lbl_perm.setStyleSheet("font-size: 14px; font-weight: 700; margin-top: 6px;")

        self.btn_perm_file = QPushButton("FILE_PERMLINK")
        self.btn_perm_console = QPushButton("CONSOLE_PERMLINK")
        self.btn_perm_file.setMinimumHeight(34)
        self.btn_perm_console.setMinimumHeight(34)

        prez_layout.addWidget(lbl_perm)
        prez_layout.addWidget(self.btn_perm_file)
        prez_layout.addWidget(self.btn_perm_console)

        # --- DIR_NUM queue (bulk paste from Excel) ---
        self.dirnum_bulk = QPlainTextEdit()
        self.dirnum_bulk.setPlaceholderText(
            "Вставь сюда пути архивов (все), пример: CSN/OLDSINGLE/EN/1"
        )
        self.dirnum_bulk.setFixedHeight(120)

        self.lbl_dirnum_queue_info = QLabel("Очередь DIR_NUM: 0")
        self.lbl_dirnum_queue_info.setStyleSheet("color: rgba(226,232,240,0.8);")

        self.lbl_dirnum_queue_current = QLabel("Текущий DIR_NUM: —")
        self.lbl_dirnum_queue_current.setStyleSheet("color: rgba(226,232,240,0.9); font-weight: 700;")

        self.btn_dirnum_queue_apply = QPushButton("Сохранить")
        self.btn_dirnum_queue_next = QPushButton("Следующий")

        dirnum_btns = QHBoxLayout()
        dirnum_btns.setSpacing(8)
        dirnum_btns.addWidget(self.btn_dirnum_queue_apply, 1)
        dirnum_btns.addWidget(self.btn_dirnum_queue_next, 1)

        prez_layout.addSpacing(8)
        prez_layout.addWidget(self.dirnum_bulk)
        prez_layout.addWidget(self.lbl_dirnum_queue_info)
        prez_layout.addWidget(self.lbl_dirnum_queue_current)
        prez_layout.addLayout(dirnum_btns)

        prez_layout.addStretch(1)

        # PreZ state
        self._prez_selected: str | None = None
        self.btn_no_tag.clicked.connect(lambda: self._prez_copy("no_tag", seconds=4))
        self.btn_has_tag.clicked.connect(lambda: self._prez_copy("has_tag", seconds=4))
        self._update_prez_buttons()

        # Perm state
        self._perm_selected: str | None = None
        self.btn_perm_file.clicked.connect(lambda: self._perm_copy("file", seconds=4))
        self.btn_perm_console.clicked.connect(lambda: self._perm_copy("console", seconds=4))
        self._update_perm_buttons()

        # DIR_NUM queue
        self.btn_dirnum_queue_apply.clicked.connect(self._dirnum_queue_save_from_text)
        self.btn_dirnum_queue_next.clicked.connect(self._dirnum_queue_next)

        # self._dirnum_queue_refresh(apply_to_input=True)

        # ---- Right area: scripts picker ----
        self.zalivka_right = QWidget()
        right_layout = QVBoxLayout(self.zalivka_right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        # --- top info (left) ---
        self.lbl_pick_path = QLabel("Выбор: —")
        self.lbl_pick_path.setStyleSheet("font-weight: 600;")

        # --- search (top-right, above DIR_NUM) ---
        self.lbl_lang_search = QLabel("ПОИСК:")
        self.lbl_lang_search.setStyleSheet("font-weight: 700;")

        self.edt_lang_search = QLineEdit()
        self.edt_lang_search.setPlaceholderText("например FR или EN-FR")
        self.edt_lang_search.setFixedWidth(190)
        #self.edt_lang_search.textChanged.connect(self._on_lang_search_changed)

        self.lbl_lang_search.setVisible(True)
        self.edt_lang_search.setVisible(True)

        # --- DIR_NUM ---
        self.dir_num_label = QLabel("DIR_NUM:")
        self.dir_num_label.setStyleSheet("font-weight: 700;")

        self.dir_num_edit = QLineEdit()
        self._dirnum_queue_refresh(apply_to_input=True)
        self.dir_num_edit.setPlaceholderText("например 12")
        self.dir_num_edit.setFixedWidth(90)
        self.dir_num_edit.setValidator(QIntValidator(0, 999999, self))
        self.dir_num_edit.setText("")

        self.dir_num_label.setVisible(False)
        self.dir_num_edit.setVisible(False)

        # --- Save DIR_NUM button ---
        self.btn_dirnum_save = QPushButton("Сохранить")
        self.btn_dirnum_save.setMinimumHeight(30)
        self.btn_dirnum_save.setVisible(False)
        self.btn_dirnum_save.clicked.connect(self._regen_templates_with_new_dirnum)

        # ---- HOTKEY: следующий DIR_NUM ----
        self.lbl_dirnum_next_hotkey = QLabel("Хоткей следующий DIR_NUM:")
        self.lbl_dirnum_next_hotkey.setStyleSheet("font-size: 12px;")

        self.dirnum_next_hotkey_edit = QLineEdit()
        self.dirnum_next_hotkey_edit.setPlaceholderText("например: #m или ^!n")
        self.dirnum_next_hotkey_edit.setFixedWidth(90)
        self.dirnum_next_hotkey_edit.setText(self._load_dirnum_next_hotkey())

        self.btn_dirnum_next_hotkey_save = QPushButton("Сохранить")
        self.btn_dirnum_next_hotkey_save.setMinimumHeight(28)
        self.btn_dirnum_next_hotkey_save.clicked.connect(self._save_dirnum_next_hotkey)

        # ---- right top box: 2 rows (search row + dirnum row) ----
        right_top_box = QVBoxLayout()
        right_top_box.setSpacing(6)
        right_top_box.setContentsMargins(0, 0, 0, 0)

        row_search = QHBoxLayout()
        row_search.setSpacing(8)
        row_search.addWidget(self.lbl_lang_search)
        row_search.addWidget(self.edt_lang_search)

        row_dirnum = QHBoxLayout()
        row_dirnum.addWidget(self.lbl_dirnum_next_hotkey)
        row_dirnum.addWidget(self.dirnum_next_hotkey_edit)
        row_dirnum.addWidget(self.btn_dirnum_next_hotkey_save)
        row_dirnum.setSpacing(8)
        row_dirnum.addWidget(self.dir_num_label)
        row_dirnum.addWidget(self.dir_num_edit)
        row_dirnum.addWidget(self.btn_dirnum_save)

        right_top_box.addLayout(row_search)
        right_top_box.addLayout(row_dirnum)

        # ---- row_top: left label + right box ----
        row_top = QHBoxLayout()
        row_top.addWidget(self.lbl_pick_path, 1)
        row_top.addStretch(1)
        row_top.addLayout(right_top_box)

        # --- Split view: DB | HTML ---
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(3)
        self.splitter.setChildrenCollapsible(False)

        # =========================
        # DB PANEL
        # =========================
        self.db_panel = QWidget()
        db_layout = QVBoxLayout(self.db_panel)
        db_layout.setContentsMargins(10, 0, 10, 0)
        db_layout.setSpacing(10)
        self.btn_mode_db = QPushButton("DB")
        self.btn_mode_db.setObjectName("tileBtn")
        self.btn_mode_db.setMinimumHeight(56)
        self.btn_mode_db.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_mode_db.clicked.connect(self._toggle_db_panel)

        row_db_btns = QHBoxLayout()
        row_db_btns.setSpacing(10)

        self.btn_pick_zaliv = QPushButton("ZALIV")
        self.btn_pick_dozaliv = QPushButton("DOZALIV")
        self.btn_pick_zaliv.setMinimumHeight(34)
        self.btn_pick_dozaliv.setMinimumHeight(34)

        row_db_btns.addWidget(self.btn_pick_zaliv)
        row_db_btns.addWidget(self.btn_pick_dozaliv)
        row_db_btns.addStretch(1)
        db_layout.addLayout(row_db_btns)

        self.db_lang_scroll = QScrollArea()
        self.db_lang_scroll.setWidgetResizable(True)
        self.db_lang_scroll.setFrameShape(QFrame.NoFrame)

        self.db_lang_container = QWidget()
        self.db_lang_grid = QGridLayout(self.db_lang_container)
        self.db_lang_grid.setContentsMargins(0, 0, 0, 0)
        self.db_lang_grid.setHorizontalSpacing(10)
        self.db_lang_grid.setVerticalSpacing(10)

        self.db_lang_scroll.setWidget(self.db_lang_container)
        db_layout.addWidget(self.db_lang_scroll, 1)

        # =========================
        # HTML PANEL
        # =========================
        self.html_panel = QWidget()
        html_layout = QVBoxLayout(self.html_panel)
        html_layout.setContentsMargins(10, 0, 10, 0)
        html_layout.setSpacing(10)

        self.btn_mode_html = QPushButton("HTML")
        self.btn_mode_html.setObjectName("tileBtn")
        self.btn_mode_html.setMinimumHeight(56)
        self.btn_mode_html.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_mode_html.clicked.connect(self._toggle_html_panel)

        # HTML has no subtype row; keep a spacer with same height as DB subtype row for visual alignment
        self.html_subtype_spacer = QWidget()
        self.html_subtype_spacer.setFixedHeight(34)
        html_layout.addWidget(self.html_subtype_spacer)

        self.html_lang_scroll = QScrollArea()
        self.html_lang_scroll.setWidgetResizable(True)
        self.html_lang_scroll.setFrameShape(QFrame.NoFrame)

        self.html_lang_container = QWidget()
        self.html_lang_grid = QGridLayout(self.html_lang_container)
        self.html_lang_grid.setContentsMargins(0, 0, 0, 0)
        self.html_lang_grid.setHorizontalSpacing(10)
        self.html_lang_grid.setVerticalSpacing(10)

        self.html_lang_scroll.setWidget(self.html_lang_container)
        html_layout.addWidget(self.html_lang_scroll, 1)

        self.splitter.addWidget(self.db_panel)
        self.splitter.addWidget(self.html_panel)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)

        right_layout.addLayout(row_top)

        # --- top aligned buttons (DB / HTML) ---
        row_modes = QHBoxLayout()
        row_modes.setSpacing(16)
        row_modes.addWidget(self.btn_mode_db, 1)
        row_modes.addWidget(self.btn_mode_html, 1)
        right_layout.addLayout(row_modes)
        right_layout.addWidget(self.splitter, 1)

        #        right_layout.addWidget(self.lang_hint_panel)

        # --- HINT PANEL (3 columns) ---
        self.lang_hint_panel = QWidget()
        self.lang_hint_layout = QGridLayout(self.lang_hint_panel)
        self.lang_hint_layout.setContentsMargins(0, 10, 0, 0)
        self.lang_hint_layout.setHorizontalSpacing(20)

        self.lbl_hint_normal = QLabel()
        self.lbl_hint_rollback = QLabel()
        self.lbl_hint_sitemap = QLabel()

        for lbl in (self.lbl_hint_normal, self.lbl_hint_rollback, self.lbl_hint_sitemap):
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 14px; font-weight: 700;")
            lbl.setVisible(False)

        self.lang_hint_layout.addWidget(self.lbl_hint_normal, 0, 0)
        self.lang_hint_layout.addWidget(self.lbl_hint_rollback, 0, 1)
        self.lang_hint_layout.addWidget(self.lbl_hint_sitemap, 0, 2)

        right_layout.addWidget(self.lang_hint_panel)

        self._dir_num: str = ""
        self.dir_num_edit.textChanged.connect(self._on_dir_num_changed)

        # picker state
        self._state_db = {"subtype": "ZALIV", "lang": None, "stage": 0}
        self._state_html = {"lang": None, "stage": 0}

        self._pick_type: str | None = "DB"  # "DB" | "HTML"

        # mode visibility: show lists only after clicking DB/HTML
        self._mode: str | None = None
        self.btn_pick_zaliv.setVisible(False)
        self.btn_pick_dozaliv.setVisible(False)
        self.db_lang_scroll.setVisible(False)
        self.html_lang_scroll.setVisible(False)

        self._pick_subtype: str | None = "ZALIV"  # "ZALIV" | "DOZALIV"
        self._pick_lang: str | None = None  # "EN" ...
        self._pick_lang_stage: int = 0  # 0=нет, 1=желтый (предвыбор), 2=зелёный (подтвержден)

        self._lang_filter: str = ""

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
        self.cmb_screenshot_screen.currentIndexChanged.connect(self._on_screenshot_screen_changed)

        self.table.cellDoubleClicked.connect(lambda *_: self.edit_hotkey())

        # =========================================================
        # AHK manager
        # =========================================================
        self.ahk_exe = resource_path("AutoHotkeyUX.exe")
        self.ahk = AHKManager(self.ahk_exe)
        ok, msg, sp = scripts_status()
        if not ok:
            QMessageBox.critical(
                self,
                "Scripts не найдены",
                f"{msg}\n\nОжидается папка:\n{sp}\n\n"
                "Решение:\n"
                "1) Убедись, что ты распаковал всю папку dist целиком.\n"
                "2) Внутри папки приложения должна быть папка Scripts со всеми языками.\n"
            )
        self.render()
        # init screenshot screen list
        self._rebuild_screenshot_screens_combo()

        app = QGuiApplication.instance()
        if app:
            app.screenAdded.connect(lambda _s: self._rebuild_screenshot_screens_combo())
            app.screenRemoved.connect(lambda _s: self._rebuild_screenshot_screens_combo())

        # =========================================================
        # TRAY
        # =========================================================
        self.tray: QSystemTrayIcon | None = None
        self._setup_tray()

        self._set_dirnum_floating_enabled(self._load_dirnum_floating_enabled(), place=True)


        # =========================================================
        # DIR_NUM авто-обновление (если AHK переключил индекс)
        # =========================================================
        self._last_dirnum_seen = None

        self._dirnum_poll_timer = QTimer(self)
        self._dirnum_poll_timer.setInterval(400)
        self._dirnum_poll_timer.timeout.connect(self._poll_dirnum_and_regen_if_changed)
        self._dirnum_poll_timer.start()

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

    def _on_dir_num_changed(self, text: str) -> None:
        self._dir_num = text
        self._sync_dirnum_floating_widget(text)

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
    # PERM toggle
    # =========================================================
    def _perm_clear_highlight(self) -> None:
        self._perm_selected = None
        self._update_perm_buttons()

    def _perm_copy(self, mode: str, seconds: int = 4) -> None:
        try:
            if mode == "file":
                p = perm_file_path()
            elif mode == "console":
                p = perm_console_path()
            else:
                return

            if not p.exists():
                QMessageBox.warning(self, "perm", f"Не получилось: файл не найден\n\n{p}")
                return

            text = p.read_text(encoding="utf-8")

            if not text.strip():
                QMessageBox.warning(self, "perm", f"Не получилось: файл пустой\n\n{p}")
                return

            QApplication.clipboard().setText(text)

            self._perm_selected = mode
            self._update_perm_buttons()

            if not hasattr(self, "_perm_flash_timer"):
                self._perm_flash_timer = QTimer(self)
                self._perm_flash_timer.setSingleShot(True)
                self._perm_flash_timer.timeout.connect(self._perm_clear_highlight)

            self._perm_flash_timer.start(max(1, int(seconds)) * 1000)

        except Exception as e:
            QMessageBox.warning(self, "perm", f"Не получилось:\n\n{type(e).__name__}: {e}")

    def _update_perm_buttons(self) -> None:
        if getattr(self, "_perm_selected", None) == "file":
            self.btn_perm_file.setStyleSheet("background-color: #2e7d32; color: white; font-weight: 600;")
            self.btn_perm_console.setStyleSheet("")
        elif getattr(self, "_perm_selected", None) == "console":
            self.btn_perm_console.setStyleSheet("background-color: #2e7d32; color: white; font-weight: 600;")
            self.btn_perm_file.setStyleSheet("")
        else:
            self.btn_perm_file.setStyleSheet("")
            self.btn_perm_console.setStyleSheet("")

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
        if self._pick_type == v:
            self._pick_lang = None
            self._pick_lang_stage = 0
            if v == "DB":
                self._state_db["lang"] = None
                self._state_db["stage"] = 0
            else:
                self._state_html["lang"] = None
                self._state_html["stage"] = 0

            self._lang_filter = ""
            if hasattr(self, "edt_lang_search"):
                self.edt_lang_search.setText("")

            self._refresh_pick_ui()
            return

        self._save_current_picker_state()
        self._pick_type = v

        self._lang_filter = ""
        if hasattr(self, "edt_lang_search"):
            self.edt_lang_search.setText("")

        self._load_picker_state(v)
        self._refresh_pick_ui()

    def _set_pick_subtype(self, v: str) -> None:
        self._pick_type = "DB"
        self._pick_subtype = v

        self._pick_lang = None
        self._pick_lang_stage = 0

        self._lang_filter = ""
        if hasattr(self, "edt_lang_search"):
            self.edt_lang_search.setText("")

        self._state_db["subtype"] = v
        self._state_db["lang"] = self._pick_lang
        self._state_db["stage"] = self._pick_lang_stage

        self._refresh_pick_ui()

    def _set_pick_lang_db(self, v: str) -> None:
        # DB selection (independent state)
        if int(self._state_db.get("stage") or 0) == 2:
            return

        # ensure active selection context for template generation
        self._pick_type = "DB"
        self._pick_subtype = self._state_db.get("subtype") or self._pick_subtype or "ZALIV"

        cur = self._state_db.get("lang")
        stage = int(self._state_db.get("stage") or 0)

        if cur != v:
            self._state_db["lang"] = v
            self._state_db["stage"] = 1
            self._pick_lang = v
            self._pick_lang_stage = 1
            self._refresh_pick_ui()
            return

        if stage == 1:
            self._state_db["stage"] = 2
            self._pick_lang = v
            self._pick_lang_stage = 2

            # If HTML was confirmed earlier, mark it as "stale" (yellow) until user re-confirms it
            if int(self._state_html.get("stage") or 0) == 2 and self._state_html.get("lang"):
                self._state_html["stage"] = 1
                # repaint only; HTML stays selected but needs a click to become active again
                if getattr(self, "_html_active", False):
                    self._rebuild_lang_buttons_html()

            self._generate_lang_templates()
            self._refresh_pick_ui()
            return

        self._state_db["stage"] = 1
        self._pick_lang = v
        self._pick_lang_stage = 1
        self._refresh_pick_ui()

    def _set_pick_lang_html(self, v: str) -> None:
        # HTML selection (independent state)
        if int(self._state_html.get("stage") or 0) == 2:
            return

        self._pick_type = "HTML"
        self._pick_subtype = None

        cur = self._state_html.get("lang")
        stage = int(self._state_html.get("stage") or 0)

        if cur != v:
            self._state_html["lang"] = v
            self._state_html["stage"] = 1
            self._pick_lang = v
            self._pick_lang_stage = 1
            self._refresh_pick_ui()
            return

        if stage == 1:
            self._state_html["stage"] = 2
            self._pick_lang = v
            self._pick_lang_stage = 2

            # If DB was confirmed earlier, mark it as "stale" (yellow) until user re-confirms it
            if int(self._state_db.get("stage") or 0) == 2 and self._state_db.get("lang"):
                self._state_db["stage"] = 1
                if getattr(self, "_db_active", False):
                    self._rebuild_lang_buttons_db()

            self._generate_lang_templates()
            self._refresh_pick_ui()
            return

        self._state_html["stage"] = 1
        self._pick_lang = v
        self._pick_lang_stage = 1
        self._refresh_pick_ui()

    def _set_pick_lang(self, v: str) -> None:
        # legacy entrypoint
        if self._pick_type == "HTML":
            self._set_pick_lang_html(v)
        else:
            self._set_pick_lang_db(v)

    def _refresh_pick_ui(self) -> None:
        # Paint DB subtype buttons
        def paint(btn: QPushButton, active: bool) -> None:
            btn.setStyleSheet(
                "background-color: #2e7d32; color: white; font-weight: 700;" if active else ""
            )

        paint(self.btn_pick_zaliv, (self._state_db.get("subtype") == "ZALIV"))
        paint(self.btn_pick_dozaliv, (self._state_db.get("subtype") == "DOZALIV"))

        # Hints are shown only for the last confirmed (global) selection
        show_hint = (self._pick_lang_stage == 2 and self._pick_lang)

        if show_hint:
            lang = self._pick_lang
            self.lbl_hint_normal.setText(f"Заливка {lang}")
            self.lbl_hint_rollback.setText(f"Rollback {lang}")
            self.lbl_hint_sitemap.setText(f"Sitemap {lang}")

            self.lbl_hint_normal.setStyleSheet(
                "color: #2e7d32; background-color: rgba(46,125,50,0.15); "
                "padding: 10px; border-radius: 10px; font-size: 14px; font-weight: 700;"
            )
            self.lbl_hint_rollback.setStyleSheet(
                "color: #c62828; background-color: rgba(198,40,40,0.15); "
                "padding: 10px; border-radius: 10px; font-size: 14px; font-weight: 700;"
            )
            self.lbl_hint_sitemap.setStyleSheet(
                "color: #f9a825; background-color: rgba(249,168,37,0.15); "
                "padding: 10px; border-radius: 10px; font-size: 14px; font-weight: 700;"
            )

            self.lbl_hint_normal.setVisible(True)
            self.lbl_hint_rollback.setVisible(True)
            self.lbl_hint_sitemap.setVisible(True)
        else:
            self.lbl_hint_normal.setVisible(False)
            self.lbl_hint_rollback.setVisible(False)
            self.lbl_hint_sitemap.setVisible(False)

        # rebuild both panels
        self._rebuild_lang_buttons()

        # top-left breadcrumb (last active click)
        parts: list[str] = []
        if self._pick_type:
            parts.append(self._pick_type)
        if self._pick_type == "DB" and self._pick_subtype:
            parts.append(self._pick_subtype)
        if self._pick_lang:
            parts.append(self._pick_lang)
        self.lbl_pick_path.setText("Выбор: " + (" → ".join(parts) if parts else "—"))

        show_dir = bool(self._pick_lang) and self._pick_lang_stage in (1, 2)
        self.dir_num_label.setVisible(show_dir)
        self.dir_num_edit.setVisible(show_dir)
        self.btn_dirnum_save.setVisible(show_dir)

    def _toggle_db_panel(self) -> None:
        # DB и HTML независимы: включаем/выключаем только DB-зону
        self._db_active = not getattr(self, "_db_active", False)
        self.btn_pick_zaliv.setVisible(self._db_active)
        self.btn_pick_dozaliv.setVisible(self._db_active)
        self.db_lang_scroll.setVisible(self._db_active)

        if self._db_active:
            self._rebuild_lang_buttons_db()

        self._update_mode_styles()

    def _toggle_html_panel(self) -> None:
        # DB и HTML независимы: включаем/выключаем только HTML-зону
        self._html_active = not getattr(self, "_html_active", False)
        self.html_lang_scroll.setVisible(self._html_active)

        if self._html_active:
            self._rebuild_lang_buttons_html()

        self._update_mode_styles()

    def _update_mode_styles(self) -> None:
        # подсветка крупных кнопок (может быть активны обе)
        def paint(btn: QPushButton, active: bool) -> None:
            btn.setStyleSheet(
                "background-color: rgba(52, 120, 246, 0.30); border: 1px solid rgba(52, 120, 246, 0.55);"
                if active else ""
            )

        paint(self.btn_mode_db, getattr(self, "_db_active", False))
        paint(self.btn_mode_html, getattr(self, "_html_active", False))

    def _clear_grid(self, grid: QGridLayout) -> None:
        while grid.count():
            item = grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _calc_cols(self, scroll: QScrollArea) -> int:
        cols = 6
        try:
            w = scroll.viewport().width()
            cols = max(3, min(10, w // 110))
        except Exception:
            pass
        return cols

    def _norm_lang(self, s: str) -> str:
        return s.strip().upper().replace(" ", "").replace("_", "-")

    def _rebuild_lang_buttons_db(self) -> None:
        if not hasattr(self, "db_lang_grid"):
            return

        self._clear_grid(self.db_lang_grid)

        root = self._scripts_root()
        subtype = self._state_db.get("subtype")
        if not subtype:
            return

        base = root / "DB" / str(subtype)
        if not base.exists():
            return

        langs = sorted([p.name for p in base.iterdir() if p.is_dir()])

        flt = self._norm_lang(getattr(self, "_lang_filter", ""))
        stage = int(self._state_db.get("stage") or 0)
        selected = self._state_db.get("lang")

        if flt and not (stage == 2 and selected):
            langs = [x for x in langs if flt in self._norm_lang(x)]

        if stage == 2 and selected:
            langs = [selected] if selected in langs else []

        cols = self._calc_cols(self.db_lang_scroll)

        YELLOW = "background-color: #f9a825; color: #111827; font-weight: 800;"
        GREEN = "background-color: #2e7d32; color: white; font-weight: 800;"

        r = 0
        c = 0
        for lang in langs:
            btn = QPushButton(lang)
            btn.setMinimumHeight(34)

            if selected == lang and stage == 1:
                btn.setStyleSheet(YELLOW)
            elif selected == lang and stage == 2:
                btn.setStyleSheet(GREEN)

            btn.clicked.connect(lambda _=False, x=lang: self._set_pick_lang_db(x))
            self.db_lang_grid.addWidget(btn, r, c)

            c += 1
            if c >= cols:
                c = 0
                r += 1

    def _rebuild_lang_buttons_html(self) -> None:
        if not hasattr(self, "html_lang_grid"):
            return

        self._clear_grid(self.html_lang_grid)

        root = self._scripts_root()
        base = root / "HTML"
        if not base.exists():
            return

        langs = sorted([p.name for p in base.iterdir() if p.is_dir()])

        flt = self._norm_lang(getattr(self, "_lang_filter", ""))
        stage = int(self._state_html.get("stage") or 0)
        selected = self._state_html.get("lang")

        if flt and not (stage == 2 and selected):
            langs = [x for x in langs if flt in self._norm_lang(x)]

        if stage == 2 and selected:
            langs = [selected] if selected in langs else []

        cols = self._calc_cols(self.html_lang_scroll)

        YELLOW = "background-color: #f9a825; color: #111827; font-weight: 800;"
        GREEN = "background-color: #2e7d32; color: white; font-weight: 800;"

        r = 0
        c = 0
        for lang in langs:
            btn = QPushButton(lang)
            btn.setMinimumHeight(34)

            if selected == lang and stage == 1:
                btn.setStyleSheet(YELLOW)
            elif selected == lang and stage == 2:
                btn.setStyleSheet(GREEN)

            btn.clicked.connect(lambda _=False, x=lang: self._set_pick_lang_html(x))
            self.html_lang_grid.addWidget(btn, r, c)

            c += 1
            if c >= cols:
                c = 0
                r += 1

    def _rebuild_lang_buttons(self) -> None:
        # Перерисовываем только активные панели
        if getattr(self, "_db_active", False):
            self._rebuild_lang_buttons_db()
        if getattr(self, "_html_active", False):
            self._rebuild_lang_buttons_html()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._rebuild_lang_buttons()

    # =========================================================
    # SCREENSHOT SCREEN (monitor select)
    # =========================================================
    def _rebuild_screenshot_screens_combo(self) -> None:
        if not hasattr(self, "cmb_screenshot_screen"):
            return

        cb = self.cmb_screenshot_screen
        cb.blockSignals(True)
        cb.clear()

        screens = QGuiApplication.screens()
        primary = QGuiApplication.primaryScreen()

        # 0) Авто (Primary)
        cb.addItem("Авто (Primary)", {"mode": "auto", "index": None})

        # 1..N экраны
        for i, s in enumerate(screens):
            geom = s.geometry()
            is_primary = (primary is not None and s is primary)

            title = f"Экран {i + 1}"
            if is_primary:
                title += " (Primary)"
            title += f" — {geom.width()}×{geom.height()} @ ({geom.x()},{geom.y()})"

            cb.addItem(title, {"mode": "screen", "index": i})

        # выставляем сохранённое значение
        saved = load_screenshot_screen_settings()
        want_mode = saved.get("mode", "auto")
        want_idx = saved.get("index", None)

        set_index = 0  # по умолчанию авто
        if want_mode == "screen" and want_idx is not None:
            try:
                want_idx = int(want_idx)
            except Exception:
                want_idx = None

        if want_mode == "screen" and want_idx is not None:
            for k in range(cb.count()):
                data = cb.itemData(k)
                if data and data.get("mode") == "screen" and data.get("index") == want_idx:
                    set_index = k
                    break

        cb.setCurrentIndex(set_index)
        cb.blockSignals(False)

    def _on_screenshot_screen_changed(self) -> None:
        data = self.cmb_screenshot_screen.currentData()
        if not data:
            save_screenshot_screen_settings("auto", None)
            return

        mode = data.get("mode", "auto")
        idx = data.get("index", None)
        save_screenshot_screen_settings(mode, idx)

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

    def _load_dirnum_next_hotkey(self) -> str:
        p = dirnum_next_hotkey_path()
        try:
            if p.exists():
                v = (p.read_text(encoding="utf-8") or "").strip()
                if v:
                    return v
        except Exception:
            pass
        return "#m"  # default Win+M

    def _save_dirnum_next_hotkey(self) -> None:
        hk = (self.dirnum_next_hotkey_edit.text() or "").strip()
        if not hk:
            hk = "#m"

        p = dirnum_next_hotkey_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(hk, encoding="utf-8")

        # перезапуск AHK
        try:
            self.ahk.restart(runtime_ahk_path())
        except Exception:
            pass

    def _load_dirnum_floating_enabled(self) -> bool:
        p = dirnum_floating_enabled_path()
        if not p.exists():
            return False
        try:
            raw = (p.read_text(encoding="utf-8") or "").strip().lower()
            return raw in ("1", "true", "yes", "on")
        except Exception:
            return False

    def _save_dirnum_floating_enabled(self, enabled: bool) -> None:
        p = dirnum_floating_enabled_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("1" if enabled else "0", encoding="utf-8")

    def _place_dirnum_floating_widget(self) -> None:
        if not self.dirnum_floating_widget:
            return
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        w = self.dirnum_floating_widget
        x = geo.right() - w.width() - 24
        y = geo.top() + 24
        w.move(max(0, x), max(0, y))

    def _set_dirnum_floating_enabled(self, enabled: bool, *, place: bool = False) -> None:
        if enabled:
            if not self.dirnum_floating_widget:
                self.dirnum_floating_widget = DirnumFloatingWidget(
                    on_prev=self._dirnum_queue_prev,
                    on_next=self._dirnum_queue_next,
                    on_apply_manual=self._dirnum_queue_set_manual,
                )
            if place:
                self._place_dirnum_floating_widget()
            self.dirnum_floating_widget.show()
            self.dirnum_floating_widget.raise_()
            self.btn_dirnum_float_toggle.setText("Выключить")
        else:
            if self.dirnum_floating_widget:
                self.dirnum_floating_widget.hide()
            self.btn_dirnum_float_toggle.setText("Включить")

    def _toggle_dirnum_floating_widget(self) -> None:
        widget = getattr(self, "dirnum_floating_widget", None)
        is_enabled = bool(widget and widget.isVisible())
        new_enabled = not is_enabled
        self._set_dirnum_floating_enabled(new_enabled, place=new_enabled)
        self._save_dirnum_floating_enabled(new_enabled)

    def _sync_dirnum_floating_widget(self, value: str) -> None:
        widget = getattr(self, "dirnum_floating_widget", None)
        if widget and widget.isVisible():
            widget.set_dirnum(value)

    def _dirnum_queue_prev(self) -> None:
        try:
            queue = load_queue() or []
            idx = int(load_index() or 1)
        except Exception:
            queue = []
            idx = 1

        if not queue:
            self._dirnum_queue_refresh(apply_to_input=False)
            return

        total = len(queue)
        idx -= 1
        if idx < 1:
            idx = total

        try:
            from app.core.dirnum_queue import save_index
            save_index(idx)
        except Exception as e:
            QMessageBox.critical(self, "DIR_NUM", f"Не удалось сохранить индекс: {e}")
            return

        current = str(queue[idx - 1])
        self.dir_num_edit.setText(current)
        self._sync_dirnum_floating_widget(current)
        self._dirnum_queue_refresh(apply_to_input=False)

        try:
            self._regen_templates_with_new_dirnum()
        except Exception:
            pass

    def _dirnum_queue_set_manual(self, value: str) -> None:
        v = (value or "").strip()
        if not v:
            return
        if not v.isdigit():
            QMessageBox.warning(self, "DIR_NUM", "DIR_NUM должен содержать только цифры.")
            return

        try:
            queue = load_queue() or []
        except Exception:
            queue = []

        if v in queue:
            idx = queue.index(v) + 1
            try:
                from app.core.dirnum_queue import save_index
                save_index(idx)
            except Exception:
                pass

        self.dir_num_edit.setText(v)
        self._sync_dirnum_floating_widget(v)
        self._dirnum_queue_refresh(apply_to_input=False)
        try:
            self._regen_templates_with_new_dirnum(silent=True)
        except Exception:
            pass

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
            self._set_dirnum_floating_enabled(self._load_dirnum_floating_enabled(), place=True)

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
        if self.dirnum_floating_widget:
            self.dirnum_floating_widget.hide()
        if self.tray:
            self.tray.hide()
        QApplication.quit()

    def closeEvent(self, event) -> None:
        if self.tray and self.tray.isVisible():
            self.hide()
            if self.dirnum_floating_widget and self.dirnum_floating_widget.isVisible():
                self.dirnum_floating_widget.show()
                self.dirnum_floating_widget.raise_()
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
        if self.dirnum_floating_widget:
            self.dirnum_floating_widget.hide()
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
                combo_for_log = combo.replace('"', "'")
                name_for_log = name.replace('"', "'")

                func_lines.append(f"{fn_name}() {{")
                func_lines.append(f'    LogWrite("HOTKEY {combo_for_log} {name_for_log}")')
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

            active = get_active_profile()

            if active == "zalivka":

                # === end flag ===
                self._write_runtime_pick_state()
                reg_lines.append("RegisterGeneratedHotkeys()")

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

    def _selected_php_path(self) -> Path | None:
        if not self._pick_type or not self._pick_lang:
            return None

        root = self._scripts_root()

        if self._pick_type == "HTML":
            base = root / "HTML" / self._pick_lang
        else:
            if not self._pick_subtype:
                return None
            base = root / "DB" / self._pick_subtype / self._pick_lang

        if not base.exists():
            return None

        php_files = sorted([p for p in base.iterdir() if p.is_file() and p.suffix.lower() == ".php"])
        if len(php_files) != 1:
            return None
        return php_files[0]

    def _resolved_pick_lang(self) -> str | None:
        """Returns selected language, falling back to template source folder name."""
        if self._pick_lang:
            return self._pick_lang

        src = getattr(self, "_last_template_src", None)
        if isinstance(src, Path):
            try:
                return src.parent.name or None
            except Exception:
                return None
        return None

    def _generate_lang_templates(self) -> None:
        src = self._selected_php_path()
        if not src:
            QMessageBox.warning(self, "Шаблон", "В папке языка должен быть ровно 1 .php файл.")
            return
        self._last_template_src = src
        dir_num = (self.dir_num_edit.text() or "").strip()
        if not dir_num:
            QMessageBox.warning(self, "DIR_NUM", "Введите DIR_NUM (только цифры).")
            return

        out_dir = generated_templates_dir()
        write_variants(src, out_dir, dir_num)
        self._write_runtime_pick_state()

        # HTML uses only HK1..HK2; DB uses HK1..HK4
        if getattr(self, "_pick_type", None) == "HTML":
            for n in (3, 4):
                p = out_dir / f"HK{n}.php"
                if p.exists():
                    try:
                        p.unlink()
                    except Exception:
                        pass

    def _regen_templates_with_new_dirnum(self, *, silent: bool = False) -> None:
        try:
            if self._pick_lang_stage != 2 or not getattr(self, "_last_template_src", None):
                if not silent:
                    QMessageBox.information(self, "DIR_NUM", "Сначала выберите и подтвердите язык (зелёным).")
                return

            src = self._last_template_src
            if not src.exists():
                QMessageBox.warning(self, "DIR_NUM", f"Исходный шаблон не найден:\n{src}")
                return

            queue = load_queue() or []
            idx = int(load_index() or 1)

            if not queue:
                QMessageBox.warning(self, "DIR_NUM", "Очередь DIR_NUM пуста.")
                return

            if idx < 1:
                idx = 1
            if idx > len(queue):
                idx = 1

            dir_num = str(queue[idx - 1]).strip()
            self.dir_num_edit.setText(dir_num)
            if not dir_num:
                QMessageBox.warning(self, "DIR_NUM", "Введите DIR_NUM (только цифры).")
                return

            out_dir = generated_templates_dir()
            out_dir.mkdir(parents=True, exist_ok=True)

            # удаляем старые файлы
            for n in (1, 2, 3, 4):
                p = out_dir / f"HK{n}.php"
                if p.exists():
                    p.unlink()

            write_variants(src, out_dir, dir_num)
            self._write_runtime_pick_state()

            # визуальный фидбек
            self.btn_dirnum_save.setStyleSheet("background-color: #2e7d32; color: white; font-weight: 700;")
            if not hasattr(self, "_dirnum_save_timer"):
                self._dirnum_save_timer = QTimer(self)
                self._dirnum_save_timer.setSingleShot(True)
                self._dirnum_save_timer.timeout.connect(
                    lambda: self.btn_dirnum_save.setStyleSheet("")
                )
            self._dirnum_save_timer.start(1200)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"{type(e).__name__}: {e}")

    def _write_runtime_pick_state(self) -> None:
        mode_file = generated_templates_dir().parent / "mode.txt"
        mode = "html" if self._pick_type == "HTML" else "db"
        mode_file.write_text(mode, encoding="utf-8")

        toast_file = generated_templates_dir().parent / "toast_state.txt"
        toast_file.write_text(
            f"type={self._pick_type or ''}\n"
            f"lang={self._pick_lang or ''}\n"
            f"subtype={self._pick_subtype or ''}\n",
            encoding="utf-8",
        )

    def _update_dirnum_save_enabled(self) -> None:
        ok = bool((self.dir_num_edit.text() or "").strip())
        if hasattr(self, "btn_dirnum_save"):
            self.btn_dirnum_save.setEnabled(ok)

    # ================= DIR_NUM очередь (bulk из Excel) =================
    def _dirnum_queue_refresh(self, *, apply_to_input: bool = False) -> None:
        if not hasattr(self, "dir_num_edit"):
            return
        try:
            queue = load_queue() or []
            idx = int(load_index() or 1)
        except Exception:
            queue = []
            idx = 1

        total = len(queue)
        self.lbl_dirnum_queue_info.setText(f"Очередь DIR_NUM: {total}")

        current = None
        if total:
            if idx < 1:
                idx = 1
            if idx > total:
                idx = 1
            current = str(queue[idx - 1])

        self.lbl_dirnum_queue_current.setText(f"Текущий DIR_NUM: {current or '—'}")
        self.btn_dirnum_queue_next.setEnabled(total > 0)
        self._sync_dirnum_floating_widget(current or "")

        if apply_to_input and current:
            if not (self.dir_num_edit.text() or "").strip():
                self.dir_num_edit.setText(current)


    def _dirnum_queue_save_from_text(self) -> None:
        """Парсит текст из поля, сохраняет очередь и подставляет первый DIR_NUM."""
        raw = self.dirnum_bulk.toPlainText() or ""
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        if not lines:
            QMessageBox.information(self, "DIR_NUM", "Вставь сюда пути архивов (все), пример: CSN/OLDSINGLE/EN/1.")
            return

        try:
            queue = parse_dirnums_from_lines(raw) or []
        except Exception as e:
            QMessageBox.critical(self, "DIR_NUM", f"Ошибка разбора строк: {e}")
            return

        if not queue:
            QMessageBox.warning(self, "DIR_NUM", "Не удалось извлечь ни одного DIR_NUM из вставленных строк.")
            return

        # сохраняем очередь (модуль сам хранит в профиле)
        try:
            save_queue(queue)
        except Exception as e:
            QMessageBox.critical(self, "DIR_NUM", f"Не удалось сохранить очередь: {e}")
            return

        # подставляем первый
        self.dir_num_edit.setText(str(queue[0]))
        self._dirnum_queue_refresh(apply_to_input=True)

        # пересобираем HK под новый DIR_NUM из очереди (если язык уже подтверждён)
        try:
            self._regen_templates_with_new_dirnum()
        except Exception:
            pass

    def _dirnum_queue_next(self) -> None:
        try:
            queue = load_queue() or []
            idx = int(load_index() or 1)
        except Exception:
            queue = []
            idx = 1

        if not queue:
            self._dirnum_queue_refresh(apply_to_input=False)
            return

        total = len(queue)

        idx += 1
        if idx > total:
            idx = 1

        try:
            from app.core.dirnum_queue import save_index
            save_index(idx)
        except Exception as e:
            QMessageBox.critical(self, "DIR_NUM", f"Не удалось сохранить индекс: {e}")
            return

        current = str(queue[idx - 1])
        self.dir_num_edit.setText(current)
        self._sync_dirnum_floating_widget(current)

        self._dirnum_queue_refresh(apply_to_input=False)

        try:
            self._regen_templates_with_new_dirnum()
        except Exception:
            pass

    def _poll_dirnum_and_regen_if_changed(self) -> None:
        try:
            queue = load_queue() or []
            idx = int(load_index() or 1)
        except Exception:
            return

        if not queue:
            return

        if idx < 1:
            idx = 1
        if idx > len(queue):
            idx = len(queue)

        current = str(queue[idx - 1])

        # UI refresh
        self.lbl_dirnum_queue_current.setText(f"Текущий DIR_NUM: {current}")
        self.lbl_dirnum_queue_info.setText(f"Очередь DIR_NUM: {len(queue)}")

        # If changed -> regen templates
        if self._last_dirnum_seen != current:
            self._last_dirnum_seen = current

            self.dir_num_edit.setText(current)
            self._sync_dirnum_floating_widget(current)

            try:
                self._regen_templates_with_new_dirnum(silent=True)
            except Exception:
                pass


def _on_lang_search_changed(self, text: str) -> None:
    self._lang_filter = (text or "").strip()
    self._rebuild_lang_buttons()


def _save_current_picker_state(self) -> None:
    if self._pick_type == "DB":
        self._state_db["subtype"] = self._pick_subtype
        self._state_db["lang"] = self._pick_lang
        self._state_db["stage"] = self._pick_lang_stage
    elif self._pick_type == "HTML":
        self._state_html["lang"] = self._pick_lang
        self._state_html["stage"] = self._pick_lang_stage


def _load_picker_state(self, t: str) -> None:
    if t == "DB":
        self._pick_subtype = self._state_db.get("subtype")
        self._pick_lang = self._state_db.get("lang")
        self._pick_lang_stage = int(self._state_db.get("stage", 0) or 0)
    else:  # HTML
        self._pick_subtype = None
        self._pick_lang = self._state_html.get("lang")
        self._pick_lang_stage = int(self._state_html.get("stage", 0) or 0)
