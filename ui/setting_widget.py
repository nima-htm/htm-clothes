"""
Settings Widget - Database Configuration Panel
Theme: Warm Brown (Matching SalesInvoice & Reports Widgets)
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLabel, QLineEdit, QPushButton, QMessageBox,
                               QGroupBox, QTextEdit)
from PySide6.QtCore import Qt
from core.config import ConfigService


class SettingsWidget(QWidget):
    WIDGET_STYLESHEET = """
        QWidget {
            background-color: #A0522D;
        }

        QLabel {
            color: #592302;
            font-size: 14px;
            font-weight: bold;
            background-color: transparent;
        }

        QLabel#title {
            font-size: 22px;
            font-weight: bold;
            color: #592302;
            background: transparent;
            padding: 10px;
        }

        QGroupBox {
            border: 1px solid #CD853F;
            border-radius: 5px;
            color: white;
            font-weight: bold;
            background-color: transparent;
            margin-top: 12px;
            padding: 15px 10px 10px 10px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top right;
            right: 15px;
            padding: 0 5px;
            color: white;
        }

        QLineEdit {
            background-color: #FFE4E1;
            border: 1px solid #CD853F;
            border-radius: 2px;
            padding: 6px 10px;
            color: #2d1b1b;
            font-size: 14px;
            min-height: 24px;
        }

        QLineEdit:focus {
            border: 1px solid #DAA520;
            background-color: #FFF8DC;
        }

        QTextEdit {
            background-color: #FFE4E1;
            color: #2d1b1b;
            border: 1px solid #CD853F;
            border-radius: 2px;
            padding: 6px;
            font-size: 13px;
        }

        QPushButton {
            color: white;
            border: 1px solid #5d4037;
            border-radius: 3px;
            padding: 5px 20px;
            font-size: 14px;
            font-weight: bold;
            min-width: 80px;
        }

        QPushButton#save_btn {
            background-color: #6B8E6B;
        }
        QPushButton#save_btn:hover {
            border: 1px solid white;
        }

        QPushButton#reset_btn {
            background-color: #8B4513;
        }
        QPushButton#reset_btn:hover {
            border: 1px solid white;
        }

        QPushButton:disabled {
            background-color: #8B7355;
            color: #ccc;
        }
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
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        db_group = QGroupBox("اتصال به پایگاه داده")
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setSpacing(10)

        self.db_url_edit = QLineEdit()
        self.db_url_edit.setText(self.config_service.db_connection_string)
        self.db_url_edit.setPlaceholderText("مثال: sqlite:///nima_clothes.db")
        form.addRow("رشته اتصال:", self.db_url_edit)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        # help_text.setMaximumHeight(80)
        # ✅ رنگ‌های HTML داخلی هم با تم قهوه‌ای هماهنگ شدند
        help_text.setHtml("""
            <div style="font-size:14px; color:#592302;">
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
        btn_layout.addStretch()

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

        btn_layout.addStretch()
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