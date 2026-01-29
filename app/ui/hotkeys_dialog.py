from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPlainTextEdit,
    QPushButton, QMessageBox
)

from app.core.hotkeys_store import HotkeyItem


class HotkeyDialog(QDialog):
    """
    Диалог для добавления/редактирования хоткея.
    initial: HotkeyItem | None
    """
    def __init__(self, parent=None, initial: HotkeyItem | None = None):
        super().__init__(parent)
        self.setWindowTitle("Хоткей")
        self.setMinimumWidth(640)

        layout = QVBoxLayout(self)

        # name
        layout.addWidget(QLabel("Название"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)

        # combo
        layout.addWidget(QLabel("Комбо (AHK v2). Примеры: ^!j, ^', #q, ^!F1"))
        self.combo_edit = QLineEdit()
        layout.addWidget(self.combo_edit)

        # action
        layout.addWidget(QLabel("Действие"))
        self.action_combo = QComboBox()
        self.action_combo.addItems(["msgbox", "ahk_raw"])
        layout.addWidget(self.action_combo)

        # payload
        layout.addWidget(QLabel("Payload (для msgbox — текст, для ahk_raw — AHK-код)"))
        self.payload_edit = QPlainTextEdit()
        self.payload_edit.setPlaceholderText(
            "msgbox: просто текст\n"
            "ahk_raw: AHK-команды, например:\n"
            "old := ClipboardAll()\n"
            "A_Clipboard := \"Hello\"\n"
            "Send(\"^v\")\n"
            "A_Clipboard := old"
        )
        layout.addWidget(self.payload_edit, 1)

        # buttons
        row = QHBoxLayout()
        row.addStretch(1)
        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Отмена")
        row.addWidget(self.btn_ok)
        row.addWidget(self.btn_cancel)
        layout.addLayout(row)

        self.btn_ok.clicked.connect(self._on_ok)
        self.btn_cancel.clicked.connect(self.reject)

        # fill initial
        if initial is not None:
            self.name_edit.setText(initial.name)
            self.combo_edit.setText(initial.combo)
            idx = self.action_combo.findText(initial.action)
            if idx >= 0:
                self.action_combo.setCurrentIndex(idx)
            self.payload_edit.setPlainText(initial.payload)

    def _on_ok(self):
        name = self.name_edit.text().strip()
        combo = self.combo_edit.text().strip()
        action = self.action_combo.currentText().strip()
        payload = self.payload_edit.toPlainText()

        if not name:
            QMessageBox.warning(self, "Ошибка", "Укажи название хоткея.")
            return
        if not combo:
            QMessageBox.warning(self, "Ошибка", "Укажи комбинацию (комбо).")
            return
        if action not in ("msgbox", "ahk_raw"):
            QMessageBox.warning(self, "Ошибка", "Неизвестное действие.")
            return

        self.accept()

    def result_item(self) -> HotkeyItem:
        return HotkeyItem(
            name=self.name_edit.text().strip(),
            combo=self.combo_edit.text().strip(),
            action=self.action_combo.currentText().strip(),
            payload=self.payload_edit.toPlainText(),
        )
