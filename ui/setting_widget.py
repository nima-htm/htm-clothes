"""
Settings Widget - Database Configuration Panel
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLabel, QLineEdit, QPushButton, QMessageBox,
                               QGroupBox, QTextEdit)
from PySide6.QtCore import Qt
from core.config import ConfigService


class SettingsWidget(QWidget):
    WIDGET_STYLESHEET = """
        QLabel { color: #1e293b; font-size: 13px; background-color: transparent; }
        QLabel#title { font-size: 20px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }

        QGroupBox {
            font-weight: bold; color: #334155; border: 1px solid #e2e8f0;
            border-radius: 8px; margin-top: 12px; padding: 15px 10px 10px 10px;
            background-color: #ffffff;
        }
        QGroupBox::title { subcontrol-origin: margin; right: 15px; padding: 0 8px; color: #1e293b; }

        QLineEdit {
            padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 6px;
            background-color: #f8fafc; color: #000000; direction: rtl; text-align: right;
        }
        QLineEdit:focus { border-color: #3b82f6; background-color: #ffffff; }

        QPushButton#save_btn { background-color: #10b981; font-weight: bold; }
        QPushButton#save_btn:hover { background-color: #059669; }
        QPushButton#reset_btn { background-color: #64748b; }
        QPushButton#reset_btn:hover { background-color: #475569; }
    """

    def __init__(self, config_service: ConfigService):
        super().__init__()
        self.config_service = config_service

        self.setStyleSheet(self.WIDGET_STYLESHEET)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(12)

        title = QLabel("تنظیمات برنامه")
        title.setObjectName("title")
        layout.addWidget(title)

        db_group = QGroupBox("اتصال به پایگاه داده")
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.db_url_edit = QLineEdit()
        self.db_url_edit.setText(self.config_service.db_connection_string)
        form.addRow("رشته اتصال:", self.db_url_edit)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMaximumHeight(80)
        help_text.setHtml("""
            <div style="font-size:12px; color:#475569;">
            <b>SQLite:</b> sqlite:///nima_clothes.db<br>
            <b>PostgreSQL:</b> postgresql://user:pass@host/dbname<br>
            <b>MySQL:</b> mysql+pymysql://user:pass@host/dbname
            </div>
        """)
        form.addRow("", help_text)

        db_group.setLayout(form)
        layout.addWidget(db_group)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.save_btn = QPushButton("ذخیره تنظیمات")
        self.save_btn.setObjectName("save_btn")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(self.save_btn)

        self.reset_btn = QPushButton("بازنشانی پیش‌فرض")
        self.reset_btn.setObjectName("reset_btn")
        self.reset_btn.setMinimumHeight(40)
        self.reset_btn.clicked.connect(self._reset_to_default)
        btn_layout.addWidget(self.reset_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

    def _save_settings(self):
        new_url = self.db_url_edit.text().strip()
        if not new_url:
            QMessageBox.warning(self, "خطا", "رشته اتصال نمی‌تواند خالی باشد")
            return

        self.config_service.db_connection_string = new_url
        QMessageBox.information(
            self, "موفق",
            "تنظیمات ذخیره شد.\nلطفاً برنامه را بسته و مجدداً اجرا کنید."
        )

    def _reset_to_default(self):
        self.db_url_edit.setText(ConfigService.DEFAULT_CONFIG["db_connection_string"])